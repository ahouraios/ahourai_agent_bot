# =======================
#  Ahourai Agent Bot (Final)
#  by Omid Meysami | ahourai.com
# =======================

from flask import Flask, request
import requests
import os
from pymongo import MongoClient
from datetime import datetime

# === Flask App ===
app = Flask(__name__)

# === Environment Variables ===
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_KEY")
MONGO_URI = os.environ.get("MONGO_URI")

TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# === MongoDB Connection ===
db = None
if MONGO_URI is not None and MONGO_URI.strip() != "":
    try:
        client = MongoClient(MONGO_URI)
        db = client["ahourai_agent_bot"]
        print("✅ Connected to MongoDB Atlas")
    except Exception as e:
        db = None
        print("⚠️ MongoDB connection failed:", e)

# === Function: Ask OpenRouter ===
def ask_openrouter(prompt_text: str) -> str:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "@preset/ahourai-ai-assistent",
        "messages": [
            {"role": "user", "content": prompt_text}
        ]
    }

    try:
        res = requests.post(OPENROUTER_URL, headers=headers, json=data, timeout=20)
        response_json = res.json()
        return response_json["choices"][0]["message"]["content"]
    except Exception as e:
        print("⚠️ OpenRouter request failed:", e)
        return "در حال حاضر سامانه پاسخگو نیست، لطفاً بعداً تلاش کنید."

# === Function: Handle Telegram Messages ===
def handle_telegram_message(update: dict):
    if "message" not in update:
        return

    chat_id = update["message"]["chat"]["id"]
    user_text = update["message"].get("text", "")

    # --- ذخیره در MongoDB ---
    if db is not None:
        try:
            db.logs.insert_one({
                "chat_id": chat_id,
                "user_text": user_text,
                "timestamp": datetime.utcnow()
            })
        except Exception as e:
            print("⚠️ DB insert failed:", e)

    # --- دریافت پاسخ ---
    ai_reply = ask_openrouter(user_text)

    # --- ارسال پاسخ به تلگرام ---
    try:
        requests.post(TELEGRAM_URL, json={
            "chat_id": chat_id,
            "text": ai_reply
        })
    except Exception as e:
        print("⚠️ Telegram send failed:", e)

# === Webhook Route ===
@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    handle_telegram_message(update)
    return "OK", 200

# === Basic Route ===
@app.route('/')
def home():
    return "🤖 Ahourai Agent Bot Active — Powered by Omid Meysami", 200

# === Run (for local dev only) ===
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
