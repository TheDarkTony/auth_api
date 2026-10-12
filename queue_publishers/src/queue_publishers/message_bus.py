from queue import Queue, Empty, Full

from core_contracts.queue.bus import Message, IMessageInBus, IMessageOutBus


class MemoryMessageBus(IMessageOutBus, IMessageInBus):

    def __init__(self) -> None:
        self._queue_bus: Queue = Queue()


    def dequeue(self) -> Message|None:
        if self._queue_bus.qsize() == 0:
            return None

        try:
            item = self._queue_bus.get(block=False)
            self._queue_bus.task_done()
            return item
        except Empty:
            return None


    def enqueue(self, message: Message):
        try:
            self._queue_bus.put(message, block=False)
        except Full:
            raise Exception('Failed on putting message to message bus')
