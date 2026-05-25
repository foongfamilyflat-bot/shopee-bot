import logging
import os
import requests
from urllib.parse import quote
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
AFFILIATE_ID = os.environ.get("AFFILIATE_ID")
BITLY_TOKEN = os.environ.get("BITLY_TOKEN")
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

def shorten_url(long_url):
    try:
        response = requests.post(
            "https://api-ssl.bitly.com/v4/shorten",
            headers={"Authorization": f"Bearer {BITLY_TOKEN}", "Content-Type": "application/json"},
            json={"long_url": long_url},
            timeout=10
        )
        if response.status_code in [200, 201]:
            return response.json().get("link", long_url)
    except Exception as e:
        logger.error(f"Shortener error: {e}")
    return long_url

def convert_to_affiliate_link(original_url):
    original_url = original_url.strip()
    if "shopee.sg" not in original_url:
        return None
    encoded_url = quote(original_url, safe="")
    long_link = f"https://s.shopee.sg/an_redir?origin_link={encoded_url}&affiliate_id={AFFILIATE_ID}"
    return shorten_url(long_link)

def search_notion(query):
    logger.info(f"Searching Notion for: {query}")
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    data = {
        "filter": {
            "and": [
                {"property": "Active", "checkbox": {"equals": True}},
                {"or": [
                    {"property": "Product name", "rich_text": {"contains": query}},
                    {"property": "Category", "select": {"equals": query.title()}},
                    {"property": "Sub-category", "select": {"equals": query.title()}},
                    {"property": "Tags", "multi_select": {"contains": query.lower()}}
                ]}
            ]
        },
        "page_size": 5
    }
    response = requests.post(
        f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query",
        headers=headers,
        json=data,
        timeout=10
    )
    logger.info(f"Notion status: {response.status_code} response: {response.text[:300]}")
    if response.status_code == 200:
        return response.json().get("results", [])
    return []

def format_results(results):
    if not results:
        return None
    lines = []
    for item in results:
        props = item.get("properties", {})
        name = props.get("Product name", {}).get("title", [{}])
        name = name[0].get("plain_text", "Unknown") if name else "Unknown"
        link = props.get("Link", {}).get("url", "")
        notes = props.get("Notes", {}).get("rich_text", [{}])
        notes = notes[0].get("plain_text", "") if notes else ""
        if link:
            affiliate = convert_to_affiliate_link(link)
            line = f"x {name}"
            if notes:
                line += f" - {notes}"
            line += f" {affiliate}"
            lines.append(line)
    return "\n\n".join(lines)

async def start(update, context):
    await update.message.reply_text("Hi! Paste any Shopee link to get a short link, or type a category like skincare, home, cats, kitchen to browse recommendations. Happy shopping!")

async def help_command(update, context):
    await update.message.reply_text("How to use: 1. Convert a link: Paste any Shopee product URL. 2. Browse by category: Type home, beauty, cats, kitchen, fashion, fitness, groceries, games. 3. Search: Type any keyword like air fryer or skincare.")

async def handle_message(update, context):
    text = update.message.text.strip()
    if "http" in text and "shopee.sg" in text:
        link = convert_to_affiliate_link(text)
        if link:
            await update.message.reply_text(f"Here is your link: {link} Happy shopping!")
        else:
            await update.message.reply_text("That does not look like a Shopee link! Make sure it contains shopee.sg and try again.")
        return
    await update.message.reply_text("Searching the link library...")
    results = search_notion(text)
    formatted = format_results(results)
    if formatted:
        await update.message.reply_text(f"Here is what I found for {text}: {formatted} Type another keyword to search more!")
    else:
        await update.message.reply_text(f"No results found for {text}. Try a different keyword or category like home, beauty, cats, kitchen!")

app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()
