import logging
import requests
from urllib.parse import quote
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

TELEGRAM_BOT_TOKEN = "8219986272:AAFlsz3BoQOxvtiqJz-FqW0KkyLNes93Ucs"
AFFILIATE_ID = "14325930001"
BITLY_TOKEN = "fd5f6507eebae9d79d26851e50206616fc4d812b"

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

def shorten_url(long_url):
    try:
        response = requests.post(
            "https://api-ssl.bitly.com/v4/shorten",
            headers={
                "Authorization": f"Bearer {BITLY_TOKEN}",
                "Content-Type": "application/json"
            },
            json={"long_url": long_url},
            timeout=10
        )
        if response.status_code == 200 or response.status_code == 201:
            return response.json().get("link", long_url)
    except Exception as e:
        print(f"Shortener error: {e}")
    return long_url

def convert_to_affiliate_link(original_url):
    original_url = original_url.strip()
    if "shopee.sg" not in original_url:
        return None
    encoded_url = quote(original_url, safe="")
    long_link = f"https://s.shopee.sg/an_redir?origin_link={encoded_url}&affiliate_id={AFFILIATE_ID}"
    return shorten_url(long_link)

async def start(update, context):
    await update.message.reply_text("👋 Hi! Paste any Shopee link here and I'll generate a short link for you — quick and easy! 🛍️")

async def handle_message(update, context):
    text = update.message.text.strip()
    if "http" not in text:
        await update.message.reply_text("Please send me a Shopee link! 🛍️")
        return
    link = convert_to_affiliate_link(text)
    if link:
        await update.message.reply_text(f"✅ Here's your link:\n\n{link}\n\nHappy shopping! 🛍️")
    else:
        await update.message.reply_text("❌ That doesn't look like a Shopee link! Make sure it contains shopee.sg and try again 😊")

app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()
