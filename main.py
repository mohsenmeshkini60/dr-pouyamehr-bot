import json
import os
import time
import requests
from pathlib import Path

# --- تنظیمات مسیر ---
BASE_DIR = Path(__file__).resolve().parent
CARD_FILE = BASE_DIR / "card.jpg"

# --- خواندن توکن فقط از متغیر محیطی ---
TOKEN = os.getenv("BOT_TOKEN", "").strip()

if not TOKEN:
    raise RuntimeError(
        "❌ متغیر محیطی BOT_TOKEN تنظیم نشده است."
    )

BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

# --- متون ربات ---
WELCOME_TEXT = (
    "✨ *به دستیار هوشمند دکتر مرجان پویامهر خوش آمدید* ✨\n"
    "🩺 فوق‌تخصص ریه (بالغین)"
)

DOCTOR_INFO_TEXT = (
    "👩‍⚕️ *بیوگرافی*\n"
    "دکتر مرجان پویامهر\n"
    "فوق‌تخصص ریه"
)

SPIROMETRY_TEXT = (
    "🫁 *راهنمای انجام اسپیرومتری*\n"
    "نکات پیش از مراجعه..."
)

PREOP_TEXT = (
    "📋 *مشاوره ریه پیش از عمل*\n"
    "مدارک مورد نیاز..."
)

APPOINTMENT_TEXT = (
    "📍 *اطلاعات آدرس و نوبت‌دهی*\n"
    "تلفن: ۰۶۱-۳۲۹۳۳۹۸۵"
)

EMERGENCY_TEXT = (
    "🚨 *موارد اورژانسی*\n"
    "فوراً به اورژانس مراجعه کنید."
)

DEVELOPER_TEXT = (
    "🤖 *توسعه‌دهنده*\n"
    "این دستیار هوشمند توسط آقای محسن مشکینی، "
    "فارغ‌التحصیل دکتری مهندسی مکانیک، "
    "طراحی، اجرا و توسعه یافته است."
)

# --- منوها ---
MAIN_REPLY_KEYBOARD = {
    "keyboard": [
        [{"text": "👩‍⚕️ معرفی پزشک"}, {"text": "🫁 اسپیرومتری"}],
        [{"text": "📋 مشاوره قبل عمل"}, {"text": "📍 آدرس و نوبت"}],
        [{"text": "🪪 مشاهده کارت ویزیت"}, {"text": "🚨 موارد اورژانسی"}],
        [{"text": "🤖 طراحی و توسعه دستیار"}]
    ],
    "resize_keyboard": True
}

BACK_INLINE_KEYBOARD = {
    "inline_keyboard": [
        [{"text": "🔙 بازگشت به منوی اصلی", "callback_data": "back_to_main"}]
    ]
}


# --- توابع ارتباط با تلگرام ---
def send_message(chat_id, text, reply_markup=None):
    url = f"{BASE_URL}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }

    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)

    response = requests.post(url, json=payload, timeout=40)
    response.raise_for_status()
    return response.json()


def send_card_image(chat_id):
    url = f"{BASE_URL}/sendPhoto"

    if CARD_FILE.exists():
        with open(CARD_FILE, "rb") as photo:
            response = requests.post(
                url,
                files={"photo": photo},
                data={
                    "chat_id": chat_id,
                    "reply_markup": json.dumps(BACK_INLINE_KEYBOARD)
                },
                timeout=40
            )

        response.raise_for_status()
        return response.json()

    send_message(
        chat_id,
        "⚠️ فایل کارت ویزیت پیدا نشد."
    )


def handle_update(update):
    # پردازش پیام‌های متنی
    if "message" in update:
        message = update["message"]
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")

        actions = {
            "/start": (WELCOME_TEXT, MAIN_REPLY_KEYBOARD),
            "👩‍⚕️ معرفی پزشک": (DOCTOR_INFO_TEXT, BACK_INLINE_KEYBOARD),
            "🫁 اسپیرومتری": (SPIROMETRY_TEXT, BACK_INLINE_KEYBOARD),
            "📋 مشاوره قبل عمل": (PREOP_TEXT, BACK_INLINE_KEYBOARD),
            "📍 آدرس و نوبت": (APPOINTMENT_TEXT, BACK_INLINE_KEYBOARD),
            "🚨 موارد اورژانسی": (EMERGENCY_TEXT, BACK_INLINE_KEYBOARD),
            "🤖 طراحی و توسعه دستیار": (
                DEVELOPER_TEXT,
                BACK_INLINE_KEYBOARD
            )
        }

        if text in actions:
            content, keyboard = actions[text]
            send_message(chat_id, content, keyboard)

        elif text == "🪪 مشاهده کارت ویزیت":
            send_card_image(chat_id)

    # پردازش دکمه‌های شیشه‌ای
    elif "callback_query" in update:
        callback = update["callback_query"]
        chat_id = callback.get("message", {}).get("chat", {}).get("id")
        callback_id = callback.get("id")
        data = callback.get("data")

        if data == "back_to_main":
            requests.post(
                f"{BASE_URL}/answerCallbackQuery",
                json={"callback_query_id": callback_id},
                timeout=40
            )

            send_message(
                chat_id,
                WELCOME_TEXT,
                MAIN_REPLY_KEYBOARD
            )


def main():
    offset = 0

    print("✅ ربات تلگرام در حال اجراست...", flush=True)

    while True:
        try:
            response = requests.get(
                f"{BASE_URL}/getUpdates",
                params={
                    "offset": offset,
                    "timeout": 30
                },
                timeout=40
            )

            response.raise_for_status()
            result = response.json()

            if result.get("ok") is not True:
                print(f"⚠️ پاسخ نامعتبر از تلگرام: {result}", flush=True)
                time.sleep(5)
                continue

            for update in result.get("result", []):
                handle_update(update)
                offset = update["update_id"] + 1

        except Exception as error:
            print(f"❌ خطا: {error}", flush=True)
            time.sleep(5)


from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route("/")
def home():
    return "Dr Pouyamehr Telegram Bot is running.", 200

@app.route("/health")
def health():
    return {"status": "ok"}, 200


if __name__ == "__main__":
    Thread(target=main, daemon=True).start()

    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
