# ================================
# Ahourai Agent Bot (Flask Core)
# Author: Omid Meysami
# Powered by OpenRouter + Telegram
# ================================

from flask import Flask, request
import requests
import os
from pymongo import MongoClient

# === Flask config ===
app = Flask(__name__)

# === Environment Variables ===
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENROUTER_KEY = os.environ.get("OPENROUTER_KEY")
MONGO_URI = os.environ.get("MONGO_URI")

# === Telegram constants ===
TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# === MongoDB (اختیاری) ===
db = None
if MONGO_URI:
    try:
        client = MongoClient(MONGO_URI)
        db = client["ahourai_agent_bot"]
        print("✅ Connected to MongoDB Atlas")
    except Exception as e:
        print("⚠️ MongoDB connection failed:", e)


# === Core AI interaction ===
def ask_openrouter(user_input: str) -> str:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "HTTP-Referer": "https://ahourai.com",
        "X-Title": "Ahourai Agent Bot"
    }

    payload = {
        "model": "@preset/ahourai-ai-assistent",
        "messages": [
            {"role": "user", "content": user_input}
        ]
    }

    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
        data = response.json()
        ai_text = data["choices"][0]["message"]["content"]
        return ai_text
    except Exception as e:
        return f"⚠️ خطا در ارتباط با سرویس هوش مصنوعی: {e}"


# === Telegram handler ===
def handle_telegram_message(update: dict):
    if "message" not in update:
        return

    chat_id = update["message"]["chat"]["id"]
    user_text = update["message"].get("text", "")

    # ذخیره پیام در DB (در صورت موجود بودن)
    if db:
        db.logs.insert_one({"chat_id": chat_id, "user_text": user_text})

    # پاسخ هوش مصنوعی
    ai_reply = ask_openrouter(user_text)

    # ارسال پاسخ به تلگرام
    payload = {"chat_id": chat_id, "text": ai_reply}
    requests.post(TELEGRAM_URL, json=payload)


# === Webhook route ===
@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    handle_telegram_message(update)
    return "ok", 200


# === Health check route ===
@app.route('/', methods=['GET'])
def index():
    return "✅ Ahourai Agent Bot active — Powered by @OmidMeysami", 200


# === App entry ===
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
