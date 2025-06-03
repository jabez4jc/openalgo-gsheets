import time
import os
from datetime import datetime

from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from openalgo import api
from gspread_formatting import *

# === Load .env ===
load_dotenv()
api_key = os.getenv("OPENALGO_API_KEY")
sheet_name = os.getenv("GOOGLE_SHEET_NAME", "OpenAlgo Live Feed")
poll_interval = int(os.getenv("POLL_INTERVAL", "20"))

if not api_key:
    raise ValueError("❌ OPENALGO_API_KEY not found in .env file.")

print("🔁 OpenAlgo Python Bot is running.")

# === OpenAlgo API Setup ===
client = api(api_key=api_key, host="http://127.0.0.1:5000")

# === Google Sheets Auth ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
gc = gspread.authorize(creds)
sheet = gc.open(sheet_name).sheet1

# === Define expected header
expected_header = ["Exchange", "Symbol", "LTP", "Δ", "Trend", "Open", "High", "Low", "Volume", "Volatility", "Timestamp"]
current = sheet.get_all_values()

if not current:
    # Sheet is empty — write full header
    sheet.update(range_name="A1:K1", values=[expected_header])
elif current[0][:2] != expected_header[:2]:
    # Header missing or corrupted — update just first row
    sheet.update(range_name="A1:K1", values=[expected_header])
# else: header exists — do nothing

# === In-memory tracker for LTP
prev_ltp_map = {}

# === Colors
GREEN = Color(0.8, 1, 0.8)
RED = Color(1, 0.8, 0.8)
DEFAULT = Color(1, 1, 1)

# === Polling Loop ===
while True:
    all_rows = sheet.get_all_values()
    for idx, row in enumerate(all_rows[1:], start=2):
        try:
            if len(row) < 2 or not row[0] or not row[1]:
                continue

            exchange = row[0].strip()
            symbol = row[1].strip()
            key = f"{exchange}:{symbol}"

            response = client.quotes(symbol=symbol, exchange=exchange)
            if response["status"] == "success" and response["data"]:
                quote = response["data"][0]
                ltp = quote.get("ltp")
                open_price = quote.get("open")
                high = quote.get("high")
                low = quote.get("low")
                volume = quote.get("volume")
                prev_close = quote.get("prev_close")
                ts = quote.get("timestamp")

                timestamp_str = datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d %H:%M:%S") if ts else datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # === Delta and Trend
                prev_ltp = prev_ltp_map.get(key)
                delta = ltp - prev_ltp if prev_ltp is not None and ltp is not None else 0
                trend_arrow = "📈" if delta > 0 else "📉" if delta < 0 else "➖"

                # === Volatility
                if ltp and prev_close:
                    volatility_pct = ((ltp - prev_close) / prev_close) * 100
                    if abs(volatility_pct) > 2:
                        volatility_emoji = "⚡"
                    elif abs(volatility_pct) < 0.3:
                        volatility_emoji = "💤"
                    else:
                        volatility_emoji = "📊"
                else:
                    volatility_pct = 0
                    volatility_emoji = "❓"

                # === Alert on high move
                if abs(volatility_pct) >= 1.0:
                    direction = "⬆️" if volatility_pct > 0 else "⬇️"
                    print(f"⚠️ {symbol} moved {direction} {volatility_pct:.2f}% from prev close")

                # === Update row
                sheet.update(
                    range_name=f"C{idx}:K{idx}",
                    values=[[ltp, round(delta, 2), trend_arrow, open_price, high, low, volume, f"{volatility_pct:.2f}% {volatility_emoji}", timestamp_str]]
                )

                # === Color row
                fmt = cellFormat(backgroundColor=GREEN if delta > 0 else RED if delta < 0 else DEFAULT)
                format_cell_range(sheet, f"A{idx}:K{idx}", fmt)

                prev_ltp_map[key] = ltp
                print(f"✅ {symbol}: LTP={ltp} Δ={delta:.2f} {trend_arrow} Vol={volatility_pct:.2f}% {volatility_emoji}")
            else:
                print(f"⚠️ No data for {exchange}:{symbol}")
        except Exception as e:
            print(f"❌ Error on row {idx} ({row}): {e}")

    time.sleep(poll_interval)