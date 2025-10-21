import os
import requests
from flask import Flask, request
from pymongo import MongoClient
import datetime

# ----------- Environment Variables (set in Render Dashboard) -----------
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MONGO_URI = os.getenv("MONGO_URI")

# ----------- Telegram API URLs -----------
BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# ----------- Flask App -----------
app = Flask(__name__)

# ----------- MongoDB Connection -----------
if MONGO_URI:
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client["ahourai_agent_db"]
    messages_col = db["messages"]
else:
    mongo_client = None
    messages_col = None


# ----------- Helper: Save Message -----------
def save_message(sender, text, reply):
    if messages_col:
        messages_col.insert_one({
            "sender": sender,
            "text": text,
            "reply": reply,
            "timestamp": datetime.datetime.utcnow()
        })


# ----------- Route: Home (for Render health-check) -----------
@app.route("/", methods=["GET"])
def home():
    return "✅ Ahourai Agent Bot active — Powered by @OmidMeysami", 200


# ----------- Route: Telegram Webhook -----------
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    try:
        chat_id = data["message"]["chat"]["id"]
        user_msg = data["message"]["text"]
    except KeyError:
        return "No valid message", 200

    # --- Generate AI Reply via OpenRouter Preset ---
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "@preset/ahourai-ai-assistent",
            "messages": [
                {"role": "user", "content": user_msg}
            ]
        }

        r = requests.post(OPENROUTER_URL, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()

        reply = data["choices"][0]["message"]["content"]

    except Exception as e:
        reply = f"⚠️ خطا در پاسخ‌دهی مدل: {e}"

    # --- Send reply to Telegram ---
    requests.post(f"{BASE_URL}/sendMessage", json={
        "chat_id": chat_id,
        "text": reply
    })

    # --- Save chat record in MongoDB ---
    save_message(sender=chat_id, text=user_msg, reply=reply)

    return "OK", 200


# ----------- Run Locally ----------- #
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
