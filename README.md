# 📘 OpenAlgo to Google Sheets Real-Time Market Tracker

This Python project enables real-time **live market data tracking in Google Sheets** using OpenAlgo’s REST API or Websocket APIs.

It is broker-agnostic and works with any broker supported by OpenAlgo (e.g., Flattrade, Alice Blue, etc.).

Track live market data from OpenAlgo API directly into Google Sheets using either HTTP polling or WebSocket streaming.

---

## 🔧 Features

* ✅ Live LTP updates via OpenAlgo REST API
* 📉 Trend indicators (📈/📉/➖) based on LTP movement
* 📊 Volatility emojis based on % change from previous close
* ↺ Updates each row in-place (not append-only)
* 🎨 Conditional formatting (green/red row highlights)
* 🧐 `.env`-based config for API key, sheet name, interval

---

## 📌 Why HTTP Polling?

| Reason              | Explanation                                              |
| ------------------- | -------------------------------------------------------- |
| ✅ Broker-Agnostic   | REST API is supported for **all brokers** in OpenAlgo    |
| ✅ WebSocket Limit   | WebSocket only works with AngelOne (as of June 2025)     |
| ✅ Sheets Friendly   | Google Sheets are not built for high-frequency tick data |
| ✅ Simple & Reliable | Easy to set up, debug, and extend                        |

---

## ⚙️ WebSocket Version (`openalgo_live_dashboard_ws.py`)

### ✅ What It Does:
- Connects to OpenAlgo WebSocket server
- Subscribes to live LTP quote updates
- Dynamically tracks instruments across:
  - `Equity`
  - `Futures`
  - `Options`
  - `Currency`
  - `Commodities`
- Updates only when ticks arrive (no polling)
- Updates Google Sheets with:
  - LTP, Δ, Open, High, Low, Volume, Timestamp, Prev Close, % Change
  - Conditional formatting (green/red rows)

### 🧪 Sheets Setup:
- Each sheet must be named exactly: `Equity`, `Futures`, `Options`, etc.
- Sheet tab must be `Sheet1`
- Headers in row 1 must be:

  ```text
  Exchange | Symbol | LTP | Δ | Open | High | Low | Volume | Timestamp | Prev Close | % Change
  ```

- Rows 2+ should have `Exchange` and `Symbol`; other fields are auto-filled.

---

## 💡 Tip: Fallback to HTTP Polling
Use `openalgo_live_dashboard.py` if WebSocket is not available (e.g. firewall, offline mode). This version polls `client.quotes()` every `POLL_INTERVAL` seconds.

---

## 💼 Tech Stack

* `openalgo`: Python SDK for OpenAlgo API
* `gspread`: Read/write access to Google Sheets
* `gspread-formatting`: Cell formatting (color, fonts)
* `python-dotenv`: Loads config values from `.env`
* `oauth2client`: Auth for Google APIs

---

## 📂 Folder Structure

```
/your-project/
├── .env
├── creds.json
├── openalgo_live_dashboard.py
├── openalgo_live_dashboard_ws.py
├── requirements.txt
└── README.md
```

---

## ☁️ Google Sheets API Setup

### 1. Create a Google Cloud Project

* Go to [https://console.cloud.google.com/](https://console.cloud.google.com/)
* Create a new project

### 2. Enable APIs

* Enable **Google Sheets API**
* Enable **Google Drive API**

### 3. Create a Service Account

* IAM → Service Accounts → Create
* Skip role selection
* After creation, go to "Keys" tab → Add Key → JSON → Download

### 4. Rename downloaded file to:

```
creds.json
```

### 5. Share your target Google Sheet

* Open the Sheet → Share
* Add your service account’s email (e.g., `bot@your-project.iam.gserviceaccount.com`)
* Grant **Editor** access

---

## 📝 .env Configuration

Create a `.env` file in the same folder or rename the sample.env and update it:

```
# OpenAlgo Live Feed Configuration
OPENALGO_API_KEY=Your-OpenAlgo-API-KEY
GOOGLE_SHEET_NAME=OpenAlgo Live Feed

# Polling interval (in seconds) for http requests
POLL_INTERVAL=20

# Service Account file path
GOOGLE_CREDS_PATH=creds.json
```

> ⚠️ Do not use quotes. Ensure the key was generated after logging in to your broker in the OpenAlgo app.

---

## 🔧 Setup Instructions

1. Clone the repo
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Prepare your `.env` file
4. Place your `creds.json` (Google Service Account key) in the root folder.
5. Run the script:
```bash
python openalgo_live_dashboard.py
```
for HTTP Polling for all brokers or
```bash
python openalgo_live_dashboard_ws.py
```
for AngelOne using Websockets.

---

## 📆 requirements.txt

```
openalgo
gspread
oauth2client
python-dotenv
gspread-formatting
```

---

## 🔐 .gitignore

```
.env
creds.json
__pycache__/
*.pyc
.DS_Store
.ipynb_checkpoints/
```

---

## 🔢 Sample Terminal Output

```
🔁 OpenAlgo Python Bot is running.
✅ SBIN: LTP=752.3 Δ=-0.25 📉 Vol=1.2% ⚡
✅ RELIANCE: LTP=2890.5 Δ=+1.0 📈 Vol=0.8% 📊
```

---

## 📊 Example Google Sheet Output

| Exchange | Symbol | LTP | Δ     | Trend | Open | High | Low | Volume | Volatility | Timestamp           |
| -------- | ------ | --- | ----- | ----- | ---- | ---- | --- | ------ | ---------- | ------------------- |
| NSE      | SBIN   | 752 | -0.25 | 📉    | 755  | 758  | 750 | 520000 | 1.2% ⚡     | 2025-06-03 15:00:01 |

---

## 🚑 Help & Support

📚 Docs: [https://docs.openalgo.in](https://docs.openalgo.in)
💬 Discord: [https://openalgo.in/discord](https://openalgo.in/discord)
# openalgo-gsheet-tracker
