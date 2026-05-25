import logging
import os
import requests
from urllib.parse import quote
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
AFFILIATE_ID = os.environ.get("AFFILIATE_ID")
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

CATEGORY_MAP = {
    "home": "01 Home",
    "kitchen": "02 Kitchen & Cooking",
    "cooking": "02 Kitchen & Cooking",
    "fitness": "03 Fitness & Running",
    "running": "03 Fitness & Running",
    "beauty": "04 Beauty & Wellness",
    "wellness": "04 Beauty & Wellness",
    "fashion": "05 Fashion",
    "lifestyle": "05 Fashion",
    "daily life": "06 Daily life",
    "daily": "06 Daily life",
    "groceries": "07 Groceries & Food",
    "food": "07 Groceries & Food",
    "travel": "08 Travel",
    "content creation": "09 Content Creation",
    "content": "09 Content Creation",
    "cats": "10 Cats",
    "games": "11 Board & Card Games",
    "board games": "11 Board & Card Games",
    "card games": "11 Board & Card Games",
}

SUBCATEGORY_MAP = {
    "homeowner": "Homeowner essentials",
    "essentials": "Homeowner essentials",
    "appliances": "Appliances (Home)",
    "cleaning": "Cleaning & laundry",
    "laundry": "Cleaning & laundry",
    "sleep": "Sleep & bed & bath",
    "bedding": "Sleep & bed & bath",
    "bath": "Sleep & bed & bath",
    "bed": "Sleep & bed & bath",
    "office": "Home office",
    "home office": "Home office",
    "storage": "Storage & organisation",
    "organisation": "Storage & organisation",
    "organization": "Storage & organisation",
    "cooking tools": "Cooking essentials/tools",
    "kitchen tools": "Cooking essentials/tools",
    "cookware": "Cookware",
    "pots": "Cookware",
    "pans": "Cookware",
    "air fryer": "Air fryers/grills",
    "airfryer": "Air fryers/grills",
    "grill": "Air fryers/grills",
    "food storage": "Food storage",
    "containers": "Food storage",
    "sauces": "Sauces & condiments",
    "condiments": "Sauces & condiments",
    "seasoning": "Sauces & condiments",
    "activewear": "Activewear",
    "sportswear": "Activewear",
    "workout": "Workout equipment",
    "equipment": "Workout equipment",
    "gym": "Workout equipment",
    "running shoes": "Shoes (fitness)",
    "sports shoes": "Shoes (fitness)",
    "skincare": "Skincare",
    "skin": "Skincare",
    "serum": "Skincare",
    "moisturiser": "Skincare",
    "moisturizer": "Skincare",
    "makeup": "Makeup",
    "cosmetics": "Makeup",
    "hair": "Hair",
    "haircare": "Hair",
    "beauty devices": "Beauty devices",
    "devices": "Beauty devices",
    "ipl": "Beauty devices",
    "fragrance": "Fragrance",
    "perfume": "Fragrance",
    "scent": "Fragrance",
    "supplements": "Wellness & supplements",
    "vitamins": "Wellness & supplements",
    "outfits": "Outfits",
    "clothes": "Outfits",
    "tops": "Outfits",
    "skirts": "Outfits",
    "dresses": "Outfits",
    "undergarments": "Undergarments",
    "bra": "Undergarments",
    "underwear": "Undergarments",
    "bags": "Bags shoes & accessories",
    "accessories": "Bags shoes & accessories",
    "home wear": "Comfy home wear",
    "homewear": "Comfy home wear",
    "pyjamas": "Comfy home wear",
    "pajamas": "Comfy home wear",
    "lounge": "Comfy home wear",
    "fresh produce": "Fresh produce",
    "fresh": "Fresh produce",
    "seafood": "Fresh produce",
    "fish": "Fresh produce",
    "pantry": "Pantry",
    "snacks": "Pantry",
}

TAG_MAP = {
    "gift idea": "gift idea",
    "gift": "gift idea",
    "under $20": "under $20",
    "under $50": "under $50",
    "favourite": "favourite",
    "favorite": "favourite",
    "bestseller": "bestseller",
    "tried & tested": "tried & tested",
    "new find": "new find",
    "non-toxic": "non-toxic",
    "cat-safe": "cat-safe",
    "currently using": "currently using",
    "hot weather approved": "hot weather approved",
    "sale": "sale",
    "voucher": "voucher",
}

def convert_to_affiliate_link(original_url):
    original_url = original_url.strip()
    if "shopee.sg" not in original_url:
        return None
    encoded_url = quote(original_url, safe="")
    return f"https://s.shopee.sg/an_redir?origin_link={encoded_url}&affiliate_id={AFFILIATE_ID}"

def search_notion(query):
    logger.info(f"Searching Notion for: {query}")
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    category = CATEGORY_MAP.get(query.lower())
    subcategory = SUBCATEGORY_MAP.get(query.lower())
    tag = TAG_MAP.get(query.lower())

    if category:
        data = {
            "filter": {
                "and": [
                    {"property": "Active", "checkbox": {"equals": True}},
                    {"property": "Category", "select": {"equals": category}}
                ]
            },
            "page_size": 5
        }
    elif subcategory:
        data = {
            "filter": {
                "and": [
                    {"property": "Active", "checkbox": {"equals": True}},
                    {"property": "Sub-category", "select": {"equals": subcategory}}
                ]
            },
            "page_size": 5
        }
    elif tag:
        data = {
            "filter": {
                "and": [
                    {"property": "Active", "checkbox": {"equals": True}},
                    {"property": "Tags", "multi_select": {"contains": tag}}
                ]
            },
            "page_size": 5
        }
    else:
        data = {
            "filter": {
                "and": [
                    {"property": "Active", "checkbox": {"equals": True}},
                    {"property": "Product name", "rich_text": {"contains": query}}
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
    logger.info(f"Notion status: {response.status_code}")
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
            line = f"*{name}*"
            if notes:
                line += f"\n_{notes}_"
            line += f"\n{link}"
            lines.append(line)
    return "\n\n".join(lines)

async def start(update, context):
    await update.message.reply_text(
        "Welcome! Here is how to use this bot \U0001f447\n\n"
        "*\U0001f50d Browse by category or keyword:*\n"
        "`home` \u00b7 `kitchen` \u00b7 `fitness` \u00b7 `beauty` \u00b7 `fashion` \u00b7 `daily life` \u00b7 `groceries` \u00b7 `travel` \u00b7 `content creation` \u00b7 `cats` \u00b7 `games`\n\n"
        "These are just ideas - feel free to type anything you are looking for!\n\n"
        "\U0001f3f7\ufe0f On sale days, type `voucher` to get the latest voucher links!\n\n"
        "*\U0001f517 Convert a Shopee link:*\n"
        "Paste any Shopee URL and I will generate a fff link for you\n\n"
        "Try it now! \U0001f6cd\ufe0f",
        parse_mode="Markdown"
    )

async def help_command(update, context):
    await update.message.reply_text(
        "*Quick reference* \U0001f447\n\n"
        "*\U0001f50d Browse:* Type a category or keyword\n"
        "`home` \u00b7 `kitchen` \u00b7 `fitness` \u00b7 `beauty` \u00b7 `fashion` \u00b7 `daily life` \u00b7 `groceries` \u00b7 `travel` \u00b7 `content creation` \u00b7 `cats` \u00b7 `games`\n\n"
        "\U0001f3f7\ufe0f On sale days, type `voucher` to get the latest voucher links!\n\n"
        "*\U0001f517 Convert:* Paste any Shopee URL to get a fff link\n\n"
        "Cant find what you are looking for? Try a different keyword!",
        parse_mode="Markdown"
    )

async def handle_message(update, context):
    text = update.message.text.strip()
    if "http" in text and "shopee.sg" in text:
        link = convert_to_affiliate_link(text)
        if link:
            await update.message.reply_text(f"Here is your link:\n\n{link}\n\nHappy shopping! \U0001f6cd\ufe0f")
        else:
            await update.message.reply_text("That does not look like a Shopee link! Make sure it contains shopee.sg and try again.")
        return
    await update.message.reply_text("\U0001f50d Searching the link library...")
    results = search_notion(text)
    formatted = format_results(results)
    if formatted:
        await update.message.reply_text(
            f"Here is what I found for *{text}*:\n\n{formatted}\n\nType another keyword to search more! \U0001f6cd\ufe0f",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"No results found for *{text}*. Try a different keyword or category like `home`, `beauty`, `cats`, `kitchen`!",
            parse_mode="Markdown"
        )

app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()
