from datetime import datetime
import json
import time

from pika.spec  import Basic, BasicProperties
from sqlalchemy.orm import Session
from repo_sqlalchemy.logging.entities import EventsLog

from queue_workers._worker import Worker, utcnow, ConfigIssue


CONTENT_TYPE = 'application/json'
PREFETCH_COUNT = 3
MAX_RETRY_ATTEMPTS = 2
BATCH_DELAY = 5 #sec

IDLING_PERIODS = 2
IDLING_TIME = 5 #sec


def parse_json(body):
    data: dict = json.loads(body)
    
    level: str = data.get('level', 'unknown')
    correlation_id: str|None = data.get('correlation_id')
    happened_at: str|None = data.get('happened_at')
    
    message: str|None = data.get('message')
    traceback: str|None = data.get('traceback')
    application: str|None = data.get('application')
    demand_args: str|None = data.get('demand_args')

    event_datetime = utcnow() if happened_at is None else datetime.fromisoformat(happened_at)

    log_entry = EventsLog(
        level=level,
        correlation_id=correlation_id,
        happened_at=event_datetime,
        message=message,
        traceback=traceback,
        demand_args=demand_args,
        application=application
    )

    return log_entry

class Batcher:

    def __init__(self, channel, queue_name) -> None:
        self.channel = channel
        self.queue_name = queue_name
        self.stopped = False

    def __next__(self) -> list[tuple[Basic.GetOk, BasicProperties, bytes|None]]:

        if self.stopped:
            raise StopIteration

        batch = []
        idling_periods = 0
        try:
            while True:
                method, properties, body = self.channel.basic_get(self.queue_name)
                if method is None and properties is None and body is None:
                    idling_periods +=1
                    time.sleep(IDLING_TIME)
                else:
                    assert method is not None
                    assert properties is not None
        
                    if properties.content_type != CONTENT_TYPE:
                        self.channel.basic_reject(method.delivery_tag)
                        continue
        
                    batch.append((method, properties, body))
                    idling_periods = 0

                if len(batch) == PREFETCH_COUNT or idling_periods == IDLING_PERIODS:
                    break
        
            return batch
        
        except KeyboardInterrupt:
            self.stopped = True
            return batch

    def __iter__(self):
        return self


def commit_batch(db_engine, channel, batch: list[tuple[Basic.GetOk, BasicProperties, bytes|None]]):
    last_tag = None
    with Session(db_engine) as session:
        for m, p, b in batch:
            log_entry = parse_json(b)
            session.add(log_entry)
            last_tag = m.delivery_tag
        
        session.commit()

    channel.basic_ack(delivery_tag=last_tag, multiple=True)


class LoggingDBWorker(Worker):

    def handle(self, channel, queue_name, db_engine):
        channel.basic_qos(prefetch_count=PREFETCH_COUNT)
        batcher = Batcher(channel, queue_name)
        for batch in batcher:
            if len(batch) > 0:
                commit_batch(db_engine, channel, batch)
            if not batcher.stopped:
                time.sleep(BATCH_DELAY)
                super().handle(channel, queue_name, db_engine)


if __name__ == '__main__':
    try:
        worker = LoggingDBWorker('logging_db')
        worker.start()
    except ConfigIssue as ex:
        print('Failed on starting app: ', str(ex))
