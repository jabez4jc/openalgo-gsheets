import os
import time
from datetime import datetime
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from openalgo import api
from gspread_formatting import *
import threading


print("\U0001F501 OpenAlgo Python Bot is running.")

# === Load .env ===
load_dotenv()
api_key = os.getenv("OPENALGO_API_KEY")
poll_interval = int(os.getenv("POLL_INTERVAL", "5"))

if not api_key:
    raise ValueError("\u274c OPENALGO_API_KEY not found in .env file.")

# === Google Sheets Auth ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
gc = gspread.authorize(creds)

# === Sheet Config by Segment ===
sheet_names = {
    "NSE": "Equity",
    "NFO": "Options",
    "BFO": "Futures",
    "CDS": "Currency",
    "MCX": "Commodities",
    "NCDEX": "Commodities"
}

# === Format ===
GREEN = Color(0.8, 1, 0.8)
RED = Color(1, 0.8, 0.8)
DEFAULT = Color(1, 1, 1)

# === In-memory trackers ===
prev_ltp_map = {}

# === Connect to OpenAlgo WebSocket ===
client = api(api_key=api_key, host="http://127.0.0.1:5000", ws_url="ws://127.0.0.1:8765")
client.connect()

# === Read symbols from all sheets and subscribe ===
symbol_map = {}  # key: symbol_id, value: (worksheet, row_number)

for exchange, sheet_name in sheet_names.items():
    try:
        ws = gc.open(sheet_name).sheet1
        rows = ws.get_all_values()
        for idx, row in enumerate(rows[1:], start=2):
            if len(row) < 2 or not row[0] or not row[1]:
                continue
            exch = row[0].strip()
            symbol = row[1].strip()
            if exch != exchange:
                continue
            symbol_id = f"{exch}:{symbol}"
            symbol_map[symbol_id] = (ws, idx)
    except Exception as e:
        print(f"❌ Unable to load sheet '{sheet_name}': {e}")

# === Subscribe to Quotes ===
quote_symbols = [{"exchange": s.split(":")[0], "symbol": s.split(":")[1]} for s in symbol_map.keys()]

# === WebSocket Callback ===
def on_data(data):
    try:
        exch = data.get("exchange")
        symbol = data.get("symbol")
        if not exch or not symbol:
            return

        key = f"{exch}:{symbol}"
        if key not in symbol_map:
            return

        ws, idx = symbol_map[key]
        qd = data.get("data", {})
        ltp = qd.get("ltp")
        open_price = qd.get("open")
        high = qd.get("high")
        low = qd.get("low")
        volume = qd.get("volume")
        prev_close = qd.get("prev_close")
        ts = qd.get("timestamp")

        timestamp_str = datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d %H:%M:%S") if ts else datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Calculate delta and arrow
        prev_ltp = prev_ltp_map.get(key)
        if prev_ltp is not None and ltp is not None:
            delta = ltp - prev_ltp
            arrow = "\U0001F4C8" if delta > 0 else ("\U0001F4C9" if delta < 0 else "")
            delta_str = f"{arrow} {delta:.2f}"
        else:
            delta_str = "-"

        prev_ltp_map[key] = ltp

        # Update sheet
        update_data = [[ltp, delta_str, open_price, high, low, volume, timestamp_str, prev_close]]
        ws.update(range_name=f"C{idx}:J{idx}", values=update_data)

        # Insert formula for % change
        formula = f"=IFERROR((C{idx}-J{idx})/J{idx},\"\")"
        ws.update_acell(f"K{idx}", formula)

        # Highlight row
        if prev_ltp is not None and ltp is not None:
            if ltp > prev_ltp:
                fmt = cellFormat(backgroundColor=GREEN)
            elif ltp < prev_ltp:
                fmt = cellFormat(backgroundColor=RED)
            else:
                fmt = cellFormat(backgroundColor=DEFAULT)
            format_cell_range(ws, f"A{idx}:K{idx}", fmt)

        print(f"📈 {key}: LTP={ltp} Δ={delta_str} Vol={volume}")
    except Exception as e:
        print(f"❌ WebSocket processing error: {e}")

client.subscribe_quote(quote_symbols, on_data_received=on_data)

# Keep alive
threading.Event().wait()