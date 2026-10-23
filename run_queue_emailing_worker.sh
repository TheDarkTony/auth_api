cd "$(dirname "$0")"

source .venv/bin/activate

cd queue_workers/src/queue_workers

python3 emailing_2fa_worker.py
