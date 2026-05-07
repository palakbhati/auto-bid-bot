
# 🤖 Auto Bidding Bot — LinkedIn & X Automation

An automated system that detects posts where users are looking for freelancers/developers on LinkedIn and X (Twitter), and automatically posts a personalized AI-generated bid comment.

## 🏗️ Architecture

n8n (Orchestrator)
↕ HTTP calls
Python Flask Server (localhost:5000)
↕ Browser automation
Playwright (LinkedIn + X)

## 🛠️ Tech Stack

| Component              | Technology                      |
| ---------------------- | ------------------------------- |
| Workflow Orchestration | n8n                             |
| Browser Automation     | Python + Playwright             |
| API Server             | Flask                           |
| AI Comment Generation  | Groq API (llama-3.1-8b-instant) |
| Deduplication          | Google Sheets                   |

## 📁 Project Structure

auto_bid_bot/
├── server.py # Flask API server with Playwright endpoints
├── save_sessions.py # One-time login session saver
├── requirements.txt # Python dependencies
└── README.md # This file

￼

## ⚙️ Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Save Login Sessions (run once)

```bash
python3 save_sessions.py
```

### 3. Start Flask Server

```bash
python3 server.py
```

### 4. Set up n8n Workflow

- Open n8n at http://localhost:5678
- Import the 13-node workflow
- Add your Groq API key
- Connect Google Sheets OAuth
- Click Publish

## 🔌 API Endpoints

| Endpoint          | Method | Purpose               |
| ----------------- | ------ | --------------------- |
| /linkedin/search  | GET    | Search LinkedIn posts |
| /linkedin/comment | POST   | Post LinkedIn comment |
| /x/search         | GET    | Search X posts        |
| /x/reply          | POST   | Post X reply          |

## 📊 Features

- ✅ Automated post discovery with keyword search
- ✅ AI-generated personalized bids via Groq
- ✅ Human-like behavior (random delays, char-by-char typing)
- ✅ Deduplication via Google Sheets
- ✅ Business hours only (9am-6pm)
- ✅ Rate limiting (12/day LinkedIn, 8/day X)
- ✅ Persistent session management
