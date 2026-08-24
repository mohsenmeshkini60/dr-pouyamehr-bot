import os
import time
import requests
from pathlib import Path
from flask import Flask, jsonify
from threading import Thread

# --- تنظیمات مسیر و توکن ---
BASE_DIR = Path.cwd()
CARD_FILE = BASE_DIR / "card.jpg"

TOKEN = os.getenv("BOT_TOKEN", "").strip()

if not TOKEN:
    print("⚠️ هشدار: متغیر محیطی BOT_TOKEN تنظیم نشده است!")

BASE_URL = f"https://api.telegram.org/bot{TOKEN}" if TOKEN else ""

# ==========================================================

WELCOME_TEXT = """
✨ *به دستیار هوشمند دکتر مرجان پویامهر خوش آمدید* ✨
🩺 فوق‌تخصص ریه (بالغین) | عضو هیئت علمی دانشگاه جندی شاپور اهواز

این دستیار جهت تسهیل ارتباط بیماران گرامی با مطب و ارائه آموزش‌های ضروری طراحی شده است.

⚠️ *توجه بسیار مهم:*
این سامانه جایگزین ویزیت و مراجعه حضوری به پزشک نیست. در صورت مشاهده علائم حاد مانند تنگی نفس شدید، درد قفسه سینه یا کبودی لب‌ها، فوراً با اورژانس تماس بگیرید.
"""

DOCTOR_INFO_TEXT = """
👩‍⚕️ *بیوگرافی و سوابق علمی*
• دکتر مرجان پویامهر
• متخصص بیماری‌های داخلی
• فوق‌تخصص بیماری های ریه 
• عضو هیئت علمی دانشگاه علوم پزشکی جندی‌شاپور اهواز
• دارای رتبه برتر بورد فوق‌تخصصی کشوری
• شماره نظام پزشکی: ۱۵۳۹۹۹
"""

SPIROMETRY_TEXT = """
🫁 *راهنمای انجام اسپیرومتری (نوار ریه)*
نکات پیش از مراجعه:
۱. حداقل یک ساعت پیش از تست سیگار نکشید.
۲. از مصرف وعده غذایی سنگین خودداری کنید.
۳. لباس راحت بپوشید.
۴. فهرست داروهای مصرفی خود را همراه داشته باشید.
"""

PREOP_TEXT = """
📋 *مشاوره ریه پیش از عمل جراحی*
مدارک مورد نیاز:
• نام دقیق عمل جراحی و نامه پزشک جراح
• عکس قفسه سینه، در صورت وجود
• فهرست داروهای مصرفی (به‌ویژه داروهای قلبی و ریوی)
"""

APPOINTMENT_TEXT = """
📍 *اطلاعات آدرس و نوبت‌دهی*
کلینیک ریه بیمارستان امام خمینی(ره)
📞 تلفن: \u200e۰۶۱-۳۲۹۳۳۹۸۵-۸۷\u200e
🗓️ پذیرش: یکشنبه‌ها ساعت ۱۴:۰۰
کلینیک تخصصی بیمارستان گلستان
📞 تلفن: \u200e۰۶۱-۳۳۳۷۴۳۰۰۱\u200e
🗓️ پذیرش: چهارشنبه‌ها صبح
"""

EMERGENCY_TEXT = """
🚨 *موارد اورژانسی*
در صورت بروز موارد زیر فوراً به اورژانس مراجعه کنید:
- تنگی نفس شدید و ناگهانی
- درد یا فشار در قفسه سینه
- کبودی لب‌ها
- کاهش سطح هوشیاری
"""

DEVELOPER_TEXT = """
🤖 *طراحی و توسعه دستیار هوشمند*
این دستیار هوشمند توسط آقای محسن مشکینی،فارغ التحصیل دکتری مهندسی مکانیک طراحی،انجام و بارگذاری شده است
"""

# ==========================================================

# منوی اصلی (کیبورد معمولی)
MAIN_REPLY_KEYBOARD = {
    "keyboard": [
        [{"text": "👩‍⚕️ معرفی پزشک"}, {"text": "🫁 اسپیرومتری"}],
        [{"text": "📋 مشاوره قبل عمل"}, {"text": "📍 آدرس و نوبت"}],
        [{"text": "🪪 مشاهده کارت ویزیت"}, {"text": "🚨 موارد اورژانسی"}],
        [{"text": "🤖 طراحی و توسعه دستیار"}]
    ],
    "resize_keyboard": True
}

# دکمه بازگشت (Inline)
BACK_INLINE_KEYBOARD = {
    "inline_keyboard": [
        [{"text": "🔙 بازگشت به منو اصلی", "callback_data": "back_to_main"}]
    ]
}

# ==========================================================
# توابع اجرایی ربات
# ==========================================================

def send_message(chat_id, text, reply_markup=None, is_inline=False):
    if not BASE_URL:
        print("❌ توکن ربات تنظیم نشده است!")
        return
        
    url = f"{BASE_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    
    if reply_markup:
        payload["reply_markup"] = reply_markup
            
    response = requests.post(url, json=payload)
    if not response.json().get("ok"):
        print(f"⚠️ پاسخ نامعتبر از تلگرام: {response.text}", flush=True)

def send_card_image(chat_id):
    if not BASE_URL:
        return
        
    url = f"{BASE_URL}/sendPhoto"
    if CARD_FILE.exists():
        with open(CARD_FILE, "rb") as photo:
            requests.post(url, files={"photo": photo}, data={
                "chat_id": chat_id,
                "reply_markup": '{"inline_keyboard": [[{"text": "🔙 بازگشت به منو اصلی", "callback_data": "back_to_main"}]]}'
            })
    else:
        send_message(chat_id, "⚠️ فایل کارت ویزیت پیدا نشد.", BACK_INLINE_KEYBOARD, is_inline=True)

def handle_update(update):
    # 1. پردازش پیام‌های متنی
    if "message" in update:
        message = update["message"]
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")
        
        if chat_id:
            if text == "/start":
                send_message(chat_id, WELCOME_TEXT, MAIN_REPLY_KEYBOARD, is_inline=False)
            elif text == "👩‍⚕️ معرفی پزشک":
                send_message(chat_id, DOCTOR_INFO_TEXT, BACK_INLINE_KEYBOARD, is_inline=True)
            elif text == "🫁 اسپیرومتری":
                send_message(chat_id, SPIROMETRY_TEXT, BACK_INLINE_KEYBOARD, is_inline=True)
            elif text == "📋 مشاوره قبل عمل":
                send_message(chat_id, PREOP_TEXT, BACK_INLINE_KEYBOARD, is_inline=True)
            elif text == "📍 آدرس و نوبت":
                send_message(chat_id, APPOINTMENT_TEXT, BACK_INLINE_KEYBOARD, is_inline=True)
            elif text == "🪪 مشاهده کارت ویزیت":
                send_card_image(chat_id)
            elif text == "🚨 موارد اورژانسی":
                send_message(chat_id, EMERGENCY_TEXT, BACK_INLINE_KEYBOARD, is_inline=True)
            elif text == "🤖 طراحی و توسعه دستیار":
                send_message(chat_id, DEVELOPER_TEXT, BACK_INLINE_KEYBOARD, is_inline=True)

    # 2. پردازش کلیک روی دکمه بازگشت (Callback Query)
    elif "callback_query" in update:
        cb = update["callback_query"]
        chat_id = cb.get("message", {}).get("chat", {}).get("id")
        data = cb.get("data")
        
        if not chat_id or not data: return

        requests.post(f"{BASE_URL}/answerCallbackQuery", json={"callback_query_id": cb.get("id")})

        if data == "back_to_main":
            send_message(chat_id, WELCOME_TEXT, MAIN_REPLY_KEYBOARD, is_inline=False)

# --- حلقه اصلی دریافت پیام‌ها (Polling) ---
def main_bot_loop():
    offset = 0
    print("✅ ربات تلگرام با موفقیت اجرا شد.", flush=True)
    while True:
        try:
            if not BASE_URL:
                time.sleep(5)
                continue
                
            url = f"{BASE_URL}/getUpdates?offset={offset}&timeout=30"
            res = requests.get(url, timeout=40).json()
            if "result" in res:
                for update in res["result"]:
                    handle_update(update)
                    offset = update["update_id"] + 1
        except Exception as e:
            print(f"❌ خطا در دریافت آپدیت‌ها: {e}", flush=True)
            time.sleep(5)

# --- وب‌سرور Flask برای Render ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return jsonify({"status": "active", "bot": "Dr. Marjan Pouyamehr Telegram Bot"})

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    # اجرای وب‌سرور در یک ترد جداگانه
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    # اجرای حلقه اصلی ربات
    main_bot_loop()
