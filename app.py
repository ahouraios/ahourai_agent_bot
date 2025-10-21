# ============================================
# Ahourai Agent Bot — Flask + Telegram + OpenRouter
# بدون وابستگی به MongoDB
# Author: Omid Meysami
# ============================================

from flask import Flask, request, jsonify
import requests
import os
import logging

# --------------------------------------------
# تنظیمات عمومی
# --------------------------------------------
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")  # توکن ربات تلگرام
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")  # کلید API از OpenRouter
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

# مدل مخصوص (می‌توان preset را تغییر داد)
OPENROUTER_MODEL = "@preset/ahourai-ai-assistent"

# --------------------------------------------
# توابع کمکی
# --------------------------------------------

def send_message(chat_id: int, text: str):
    """ارسال پاسخ به کاربر تلگرام"""
    url = f"{BASE_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        logging.error(f"❌ خطا در ارسال پیام: {e}")

# =============== نسخه‌ی اصلی واقعی (فعلاً غیرفعال) ===============
# def ask_openrouter(prompt: str) -> str:
#     """ارسال پیام به مدل OpenRouter و دریافت پاسخ از preset مخصوص اهورایی"""
#     try:
#         headers = {
#             "Authorization": f"Bearer {OPENROUTER_KEY}",
#             "Content-Type": "application/json",
#         }
#         payload = {
#             "model": "@preset/ahourai-ai-assistent",
#             "messages": [{"role": "user", "content": prompt}],
#         }
#         response = requests.post(
#             "https://openrouter.ai/api/v1/chat/completions",
#             headers=headers,
#             json=payload,
#             timeout=20,
#         )
#         data = response.json()
#         if "choices" in data and data["choices"]:
#             reply = data["choices"][0]["message"]["content"]
#         else:
#             reply = f"⚠️ پاسخ نامعتبر از OpenRouter:\n{data}"
#         return reply.strip()
#     except Exception as e:
#         logging.error(f"⚠️ خطا از OpenRouter: {e}")
#         return "❌ خطا در اتصال به هوش مصنوعی اهورایی. لطفاً کمی بعد مجددا تلاش کنید."


# =============== نسخه‌ی تست (Echo Mode) ===============
def ask_openrouter(prompt: str) -> str:
    """ارسال پیام به مدل OpenRouter (فعلاً حالت تست لوکال)"""
    try:
        # شبیه‌سازی پاسخ OpenRouter برای تست پایداری
        return f"👋 پیام شما دریافت شد: {prompt}"

    except Exception as e:
        logging.error(f"⚠️ خطا از OpenRouter: {e}")
        return "❌ خطا در اتصال به هوش مصنوعی اهورایی. لطفاً کمی بعد مجددا تلاش کنید."


# --------------------------------------------
# مسیرهای Flask
# --------------------------------------------

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "✅ Ahourai Agent Bot active — Powered by Omid Meysami"})


@app.route("/webhook", methods=["POST"])
def webhook():
    """دریافت پیام از تلگرام"""
    try:
        data = request.get_json()
        message = data.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "").strip()

        if not text or not chat_id:
            return jsonify({"ok": False})

        # پاسخ پیش‌فرض اولیه برای تجربه طبیعی‌تر
        if text == "/start":
            send_message(chat_id, "سلام 👋\nمن دستیار اهورایی‌هستم. چطور میتونم کمکتون کنم؟.")
            return jsonify({"ok": True})

        # ارسال پرسش به مدل هوش مصنوعی
        reply = ask_openrouter(text)
        send_message(chat_id, reply)
        return jsonify({"ok": True})

    except Exception as e:
        logging.error(f"❌ خطا در پردازش پیام: {e}")
        return jsonify({"ok": False})


# --------------------------------------------
# اجرای برنامه روی Render
# --------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
