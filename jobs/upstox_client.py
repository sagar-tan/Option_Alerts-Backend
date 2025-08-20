# UPSTOXclient.py

import os
import json
import requests
import pandas as pd
from dotenv import load_dotenv

# Load .env values
load_dotenv()
ACCESS_TOKEN = os.getenv("UPSTOX_ACCESS_TOKEN")

BASE_URL = "https://api.upstox.com/v2"


def get_option_chain(instrument_key: str, expiry_date: str):
    url = f"{BASE_URL}/option/chain"
    params = {
        "instrument_key": instrument_key,
        "expiry_date": expiry_date
    }
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }

    try:
        resp = requests.get(url, params=params, headers=headers)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None


def option_chain_to_table(data: dict):
    if not data or "data" not in data:
        print("Invalid data format")
        return None

    rows = []
    for item in data["data"]:
        rows.append({
            "Expiry": item["expiry"],
            "Strike": item["strike_price"],
            "PCR": item["pcr"],
            "Spot": item["underlying_spot_price"],

            # CALL side
            "Call_LTP": item["call_options"]["market_data"]["ltp"],
            "Call_OI": item["call_options"]["market_data"]["oi"],
            "Call_IV": item["call_options"]["option_greeks"]["iv"],
            "Call_Delta": item["call_options"]["option_greeks"]["delta"],
            "Call_Theta": item["call_options"]["option_greeks"]["theta"],


            # PUT side
            "Put_LTP": item["put_options"]["market_data"]["ltp"],
            "Put_OI": item["put_options"]["market_data"]["oi"],
            "Put_IV": item["put_options"]["option_greeks"]["iv"],
            "Put_Delta": item["put_options"]["option_greeks"]["delta"],
            "Put_Theta": item["put_options"]["option_greeks"]["theta"]
                                                                    
        })

    df = pd.DataFrame(rows)
    return df


if __name__ == "__main__":
    # Example call
    data = get_option_chain("NSE_INDEX|Nifty 50", "2025-08-28")

    if data:
        df = option_chain_to_table(data)
        if df is not None:
            print(df.to_string(index=False))
