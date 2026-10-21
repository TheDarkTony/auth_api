cd "$(dirname "$0")"

source .venv/bin/activate

cd queue_workers/src/queue_workers

python3 logging_db_worker.py
