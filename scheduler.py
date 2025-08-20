#scheduler processes option chain data from Upstox API
# and evaluates alerts
import requests
import os
from apscheduler.schedulers.blocking import BlockingScheduler
from app import db, Alert  # reuse models
from datetime import datetime

UPSTOX_URL = "https://api.upstox.com/v2/option/chain"
INTERVAL = int(os.getenv("SCHEDULER_INTERVAL", 1))

scheduler = BlockingScheduler()

def fetch_option_chain():
    # TODO: add auth headers + symbol params
    response = requests.get(UPSTOX_URL)
    data = response.json()["data"]
    process_option_chain(data)

def process_option_chain(data):
    # TODO: insert/update into option_chain table
    # TODO: evaluate alerts
    print(f"[{datetime.now()}] Processed {len(data)} option chain records")

scheduler.add_job(fetch_option_chain, "interval", seconds=INTERVAL)

if __name__ == "__main__":
    scheduler.start()
