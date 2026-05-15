import requests
import xml.etree.ElementTree as ET
import asyncio
import logging
import io
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timezone
from html import escape
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest, TelegramError, TimedOut
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

import db
from messages import LANGUAGES, get_message

TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ====== COIN MAP ======
COINS = {
    "BTC": {"id": "bitcoin", "name": "Bitcoin"},
    "ETH": {"id": "ethereum", "name": "Ethereum"},
    "USDT": {"id": "tether", "name": "Tether"},
    "SOL": {"id": "solana", "name": "Solana"},
    "BNB": {"id": "binancecoin", "name": "BNB Coin"},
    "XRP": {"id": "ripple", "name": "XRP"},
    "TON": {"id": "the-open-network", "name": "Toncoin"},
    "DOGE": {"id": "dogecoin", "name": "Dogecoin"},
    "ADA": {"id": "cardano", "name": "Cardano"},
    "TRX": {"id": "tron", "name": "TRON"},
    "AVAX": {"id": "avalanche-2", "name": "Avalanche"},
    "LINK": {"id": "chainlink", "name": "Chainlink"},
    "DOT": {"id": "polkadot", "name": "Polkadot"},
    "MATIC": {"id": "polygon-ecosystem-token", "name": "Polygon"},
    "LTC": {"id": "litecoin", "name": "Litecoin"}
}

# ====== LANGUAGES ======
LANGS = list(LANGUAGES.keys())
FIAT_CURRENCIES = {
    "usd": {"name": "US Dollar", "symbol": "$"},
    "eur": {"name": "Euro", "symbol": "€"},
    "inr": {"name": "Indian Rupee", "symbol": "₹"},
    "gbp": {"name": "British Pound", "symbol": "£"},
    "aed": {"name": "UAE Dirham", "symbol": "د.إ"},
    "jpy": {"name": "Japanese Yen", "symbol": "¥"},
    "cad": {"name": "Canadian Dollar", "symbol": "C$"},
    "aud": {"name": "Australian Dollar", "symbol": "A$"},
    "chf": {"name": "Swiss Franc", "symbol": "CHF"},
    "cny": {"name": "Chinese Yuan", "symbol": "¥"}
}

# ====== CONVERTER STATES ======
SELECT_COIN, SELECT_TARGET_TYPE, SELECT_TARGET, ENTER_AMOUNT = range(4)


# =========================
# API FUNCTIONS
# =========================

def format_large_number(num):
    if num >= 1_000_000_000_000:
        return f"${num / 1_000_000_000_000:.2f} Trillion"
    elif num >= 1_000_000_000:
        return f"${num / 1_000_000_000:.2f} Billion"
    elif num >= 1_000_000:
        return f"${num / 1_000_000:.2f} Million"
    else:
        return f"${num:,.2f}"

def generate_chart(coin_id, coin_name):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=1"
    res = requests.get(url, timeout=20)
    res.raise_for_status()
    data = res.json()
    prices = data.get("prices", [])
    
    if not prices:
        return None
        
    times = [datetime.fromtimestamp(p[0]/1000.0, tz=timezone.utc) for p in prices]
    vals = [p[1] for p in prices]
    
    is_up = vals[-1] >= vals[0]
    color = '#2ecc71' if is_up else '#e74c3c'
    
    plt.figure(figsize=(10, 5), facecolor='#1e1e1e')
    ax = plt.axes()
    ax.set_facecolor('#1e1e1e')
    
    plt.plot(times, vals, color=color, linewidth=2)
    plt.fill_between(times, vals, min(vals)*0.99, color=color, alpha=0.1)
    
    plt.title(f"{coin_name} - 24h Price Chart", color='white', pad=20, fontsize=16, fontweight='bold')
    plt.grid(color='#333333', linestyle='--', alpha=0.5)
    
    ax.tick_params(colors='#888888', which='both')
    for spine in ax.spines.values():
        spine.set_color('#333333')
        
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=100, facecolor='#1e1e1e')
    buf.seek(0)
    plt.close('all')
    
    return buf

def get_price(coin_id, currency="usd"):
    url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency={currency}&ids={coin_id}"
    res = requests.get(url, timeout=20)
    res.raise_for_status()
    data = res.json()
    print(f"Api call happened {data} for {coin_id} {currency}")
    if not data:
        raise ValueError(f"No price data found for {coin_id}")

    return data[0]


def get_news():
    url = "https://www.coindesk.com/arc/outboundfeeds/rss/"
    res = requests.get(url, timeout=20)
    res.raise_for_status()
    root = ET.fromstring(res.content)

    news = []
    for item in root.findall(".//item")[:5]:
        news.append({
            "title": item.findtext("title", default="Untitled"),
            "link": item.findtext("link", default="")
        })
    return news


def format_news(items, heading):
    text = f"<b>{heading}</b>\n\n"
    for i, item in enumerate(items, 1):
        title = escape(item["title"])
        link = escape(item["link"], quote=True)
        text += f'{i}. <a href="{link}">{title}</a>\n\n'
    return text


def user_lang(user_id):
    user = db.get_user(user_id)
    return user.get("language") if user and user.get("language") else "en"


def tr(update_or_query, key, **kwargs):
    user = getattr(update_or_query, "effective_user", None) or getattr(update_or_query, "from_user", None)
    lang = user_lang(user.id) if user else "en"
    return get_message(lang, key, **kwargs)


def rows(items, columns=2):
    return [items[i:i + columns] for i in range(0, len(items), columns)]


def coin_button(symbol):
    coin = COINS[symbol]
    return InlineKeyboardButton(f"{coin['name']} ({symbol})", callback_data=f"coin_{symbol}")


def convert_coin_button(symbol):
    coin = COINS[symbol]
    return InlineKeyboardButton(f"{coin['name']} ({symbol})", callback_data=f"src_{symbol}")


def news_actions_keyboard(query):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(tr(query, "check_news_button"), callback_data="news_now"),
            InlineKeyboardButton(tr(query, "back_button"), callback_data="back"),
        ]
    ])


def main_menu_keyboard(lang):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(get_message(lang, "prices_button"), callback_data="prices"),
            InlineKeyboardButton(get_message(lang, "news_button"), callback_data="news"),
        ],
        [
            InlineKeyboardButton(get_message(lang, "converter_button"), callback_data="convert"),
            InlineKeyboardButton(get_message(lang, "settings_button"), callback_data="settings"),
        ],
    ])


async def safe_edit_message(query, text, **kwargs):
    for attempt in range(2):
        try:
            return await query.edit_message_text(text, **kwargs)
        except TimedOut:
            logger.warning("Telegram edit timed out; retrying")
            await asyncio.sleep(1 + attempt)
        except BadRequest as exc:
            if "Message is not modified" in str(exc):
                return None
            raise

    try:
        return await query.message.reply_text(text, **kwargs)
    except TelegramError as exc:
        logger.warning("Telegram fallback reply failed: %s", exc)
        return None


# =========================
# START + LANGUAGE
# =========================

def language_keyboard(back_label=None):
    buttons = [
        InlineKeyboardButton(name, callback_data=f"lang_{code}")
        for code, name in LANGUAGES.items()
    ]
    keyboard = rows(buttons, 2)
    if back_label:
        keyboard.append([InlineKeyboardButton(back_label, callback_data="settings")])
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not db.get_user(user_id):
        db.create_user(user_id)

    user = db.get_user(user_id)

    if not user["language"]:
        await update.message.reply_text(
            get_message("en", "choose_language"),
            parse_mode="HTML",
            reply_markup=language_keyboard()
        )
        return

    await show_menu(update, context)


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lang = query.data.split("_")[1]
    db.update_user(query.from_user.id, "language", lang)

    await query.edit_message_text(
        f"{get_message(lang, 'language_saved')}\n\n{get_message(lang, 'main_menu')}",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(lang)
    )


async def language_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        tr(query, "choose_language"),
        parse_mode="HTML",
        reply_markup=language_keyboard(tr(query, "back_button"))
    )


# =========================
# MENU
# =========================

async def show_menu(update, context):
    source = update.callback_query if update.callback_query else update
    user = getattr(source, "effective_user", None) or getattr(source, "from_user", None)
    lang = user_lang(user.id) if user else "en"

    if update.message:
        await update.message.reply_text(
            get_message(lang, "main_menu"),
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(lang)
        )
    else:
        await update.callback_query.edit_message_text(
            get_message(lang, "main_menu"),
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(lang)
        )


async def back_to_menu(update, context):
    query = update.callback_query
    await query.answer()
    context.user_data.pop("converter_step", None)
    context.user_data.pop("coin", None)
    context.user_data.pop("target_type", None)
    context.user_data.pop("target", None)
    await show_menu(update, context)


# =========================
# PRICES
# =========================

async def prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = rows([coin_button(k) for k in COINS.keys()], 3)
    keyboard.append([InlineKeyboardButton(tr(query, "back_button"), callback_data="back")])

    text = tr(query, "prices_title")
    if query.message.photo:
        await query.message.delete()
        await query.message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def show_coin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Inform user we are generating chart
    await safe_edit_message(query, tr(query, "fetching_news"), parse_mode="HTML")

    symbol = query.data.split("_")[1]
    coin_id = COINS[symbol]["id"]
    coin_name = COINS[symbol]["name"]
    
    try:
        coin_data = await asyncio.to_thread(get_price, coin_id)
        chart_buf = await asyncio.to_thread(generate_chart, coin_id, coin_name)
    except Exception as e:
        logger.error(f"Error fetching data or generating chart for {symbol}: {e}")
        await safe_edit_message(query, "⚠️ Error fetching data. Please try again later.")
        return

    change_24h = coin_data.get("price_change_percentage_24h") or 0.0
    high_24h = coin_data.get("high_24h") or 0.0
    low_24h = coin_data.get("low_24h") or 0.0
    market_cap = coin_data.get("market_cap") or 0.0
    volume = coin_data.get("total_volume") or 0.0
    current_price = coin_data.get("current_price") or 0.0

    caption = tr(
        query,
        "coin_price",
        name=escape(coin_name),
        symbol=symbol,
        price=f"{current_price:,.4f}",
        change=f"{'+' if change_24h >= 0 else ''}{change_24h:.2f}",
        high=f"{high_24h:,.4f}",
        low=f"{low_24h:,.4f}",
        market_cap=format_large_number(market_cap),
        volume=format_large_number(volume)
    )

    keyboard = [
        [
            #InlineKeyboardButton(tr(query, "refresh_button"), callback_data=f"coin_{symbol}"),
            InlineKeyboardButton(tr(query, "back_button"), callback_data="prices"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.delete()
    if chart_buf:
        await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=chart_buf,
            caption=caption,
            parse_mode="HTML",
            reply_markup=reply_markup
        )
    else:
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=caption,
            parse_mode="HTML",
            reply_markup=reply_markup
        )


# =========================
# NEWS FLOW
# =========================

async def news_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton(tr(query, "yes_button"), callback_data="news_yes"),
            InlineKeyboardButton(tr(query, "no_button"), callback_data="news_no"),
        ],
        [
            InlineKeyboardButton(tr(query, "check_news_button"), callback_data="news_now"),
            InlineKeyboardButton(tr(query, "back_button"), callback_data="back"),
        ],
    ]

    await query.edit_message_text(
        tr(query, "news_prompt"),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def news_yes(update, context):
    query = update.callback_query
    await query.answer()
    db.update_user(query.from_user.id, "news_subscription", True)
    await query.edit_message_text(
        tr(query, "news_enabled"),
        parse_mode="HTML",
        reply_markup=news_actions_keyboard(query)
    )


async def news_no(update, context):
    query = update.callback_query
    await query.answer()
    db.update_user(query.from_user.id, "news_subscription", False)

    await query.edit_message_text(
        tr(query, "news_disabled"),
        parse_mode="HTML",
        reply_markup=news_actions_keyboard(query)
    )


async def news_now(update, context):
    query = update.callback_query
    await query.answer()

    await safe_edit_message(query, tr(query, "fetching_news"), parse_mode="HTML")

    try:
        news = await asyncio.to_thread(get_news)
    except (requests.RequestException, ET.ParseError) as exc:
        logger.warning("News fetch failed: %s", exc)
        await safe_edit_message(query, tr(query, "news_unavailable"), parse_mode="HTML")
        return

    text = format_news(news, tr(query, "latest_news"))
    await safe_edit_message(
        query,
        text,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=news_actions_keyboard(query)
    )


# =========================
# SCHEDULER
# =========================

async def fetch_news_job(context):
    try:
        news = await asyncio.to_thread(get_news)
        for n in news:
            db.add_news_item(n)
    except (requests.RequestException, ET.ParseError) as exc:
        logger.warning("Scheduled news fetch failed: %s", exc)


async def broadcast_news_job(context):
    users = db.get_all_users()
    batch = db.pop_news_batch(10)

    if not batch:
        return

    for uid, u in users.items():
        if u.get("news_subscription"):
            try:
                lang = u.get("language") or "en"
                text = format_news(batch, get_message(lang, "latest_updates"))
                await context.bot.send_message(
                    chat_id=int(uid),
                    text=text,
                    parse_mode="HTML",
                    disable_web_page_preview=True
                )
                await asyncio.sleep(0.05)
            except TelegramError as exc:
                logger.warning("News broadcast to %s failed: %s", uid, exc)
                continue


# =========================
# SETTINGS
# =========================

async def settings(update, context):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton(tr(query, "language_button"), callback_data="lang_menu"),
            InlineKeyboardButton(tr(query, "toggle_news_button"), callback_data="toggle_news"),
        ],
        [InlineKeyboardButton(tr(query, "back_button"), callback_data="back")]
    ]

    await query.edit_message_text(
        tr(query, "settings_title"),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def toggle_news(update, context):
    query = update.callback_query
    await query.answer()

    user = db.get_user(query.from_user.id)
    new_val = not user["news_subscription"]

    db.update_user(query.from_user.id, "news_subscription", new_val)

    status = tr(query, "on") if new_val else tr(query, "off")
    keyboard = [
        [
            InlineKeyboardButton(tr(query, "check_news_button"), callback_data="news_now"),
            InlineKeyboardButton(tr(query, "back_button"), callback_data="settings"),
        ]
    ]
    await query.edit_message_text(
        tr(query, "news_status", status=status),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# CONVERTER
# =========================

async def convert_start(update, context):
    query = update.callback_query
    await query.answer()
    context.user_data["converter_step"] = SELECT_COIN

    keyboard = rows([convert_coin_button(k) for k in COINS], 3)
    keyboard.append([InlineKeyboardButton(tr(query, "back_button"), callback_data="back")])
    await query.edit_message_text(
        tr(query, "select_coin_convert"),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECT_COIN


async def select_target_type(update, context):
    query = update.callback_query
    await query.answer()

    if context.user_data.get("converter_step") != SELECT_COIN:
        return

    context.user_data["coin"] = query.data.replace("src_", "")
    context.user_data["converter_step"] = SELECT_TARGET_TYPE

    keyboard = [
        [
            InlineKeyboardButton(tr(query, "real_cash_button"), callback_data="target_fiat"),
            InlineKeyboardButton(tr(query, "crypto_button"), callback_data="target_crypto"),
        ],
        [InlineKeyboardButton(tr(query, "back_button"), callback_data="back")]
    ]

    await query.edit_message_text(
        tr(query, "select_target_type"),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECT_TARGET_TYPE


async def select_target(update, context):
    query = update.callback_query
    await query.answer()

    if context.user_data.get("converter_step") != SELECT_TARGET_TYPE:
        return

    context.user_data["target_type"] = query.data
    context.user_data["converter_step"] = SELECT_TARGET

    if query.data == "target_fiat":
        buttons = [InlineKeyboardButton(f"{v['name']} ({k.upper()})", callback_data=f"fiat_{k}") for k, v in FIAT_CURRENCIES.items()]
        keyboard = rows(buttons, 2)
        text_key = "select_target_fiat"
    else:
        source_coin = context.user_data["coin"]
        buttons = [InlineKeyboardButton(f"{v['name']} ({k})", callback_data=f"tgt_{k}") for k, v in COINS.items() if k != source_coin]
        keyboard = rows(buttons, 3)
        text_key = "select_target_crypto"

    keyboard.append([InlineKeyboardButton(tr(query, "back_button"), callback_data="back")])

    await query.edit_message_text(
        tr(query, text_key),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECT_TARGET


async def enter_amount(update, context):
    query = update.callback_query
    await query.answer()

    if context.user_data.get("converter_step") != SELECT_TARGET:
        return

    target = query.data.replace("fiat_", "").replace("tgt_", "")
    context.user_data["target"] = target
    context.user_data["converter_step"] = ENTER_AMOUNT
    coin = context.user_data["coin"]
    await query.edit_message_text(
        tr(query, "enter_amount", coin=f"{COINS[coin]['name']} ({coin})"),
        parse_mode="HTML"
    )


async def calculate(update, context):
    if context.user_data.get("converter_step") != ENTER_AMOUNT:
        return

    try:
        amount = float(update.message.text)
    except ValueError:
        await update.message.reply_text(tr(update, "invalid_number"), parse_mode="HTML")
        return ENTER_AMOUNT

    coin_symbol = context.user_data["coin"] # e.g., "BTC"
    target_symbol = context.user_data["target"]
    target_type = context.user_data["target_type"]

    # Fetch fresh prices from Redis
    all_prices = await db.get_cached_prices()
    
    # Locate source and target coins in the cache
    source_coin = next((c for c in all_prices if c["symbol"] == coin_symbol), None)
    
    if not source_coin:
        await update.message.reply_text("⚠️ Connection error with market data. Please try later.")
        return

    try:
        price_usd = float(source_coin["price_usd"])
        
        if target_type == "target_fiat":
            # Rough conversion for non-USD fiats (USD is base in your Redis)
            fiat_rates = {"usd": 1.0, "inr": 83.5, "eur": 0.92, "aed": 3.67}
            rate = fiat_rates.get(target_symbol.lower(), 1.0)
            result = amount * price_usd * rate
            currency_prefix = FIAT_CURRENCIES.get(target_symbol.lower(), {}).get("symbol", "$")
        else:
            # Crypto to Crypto
            target_coin = next((c for c in all_prices if c["symbol"] == target_symbol), None)
            if not target_coin:
                raise ValueError("Target coin not in Redis cache")
            
            result = amount * (price_usd / float(target_coin["price_usd"]))
            currency_prefix = ""

        await update.message.reply_text(
            tr(update, "conversion_result",
               amount=f"{amount:g}", coin=coin_symbol,
               currency=currency_prefix, result=f"{result:,.4f}",
               target=target_symbol.upper()),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Converter error: {e}")
        await update.message.reply_text("❌ Failed to calculate. Rates might be updating.")

    # Reset states
    for key in ["converter_step", "coin", "target_type", "target"]:
        context.user_data.pop(key, None)


# =========================
# ERRORS
# =========================

async def error_handler(update, context):
    if isinstance(context.error, TimedOut):
        logger.warning("Telegram request timed out")
        return

    logger.error("Unhandled bot error: %r", context.error)


# =========================
# MAIN
# =========================

def main():
    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .connect_timeout(30)
        .read_timeout(60)
        .write_timeout(60)
        .pool_timeout(30)
        .build()
    )
    coin_pattern = f"^({'|'.join(COINS.keys())})$"
    lang_pattern = f"^lang_({'|'.join(LANGS)})$"

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(set_language, pattern=lang_pattern))
    app.add_handler(CallbackQueryHandler(language_menu, pattern="^lang_menu$"))

    app.add_handler(CallbackQueryHandler(prices, pattern="^prices$"))
    app.add_handler(CallbackQueryHandler(show_coin, pattern="^coin_"))

    app.add_handler(CallbackQueryHandler(news_entry, pattern="^news$"))
    app.add_handler(CallbackQueryHandler(news_yes, pattern="^news_yes$"))
    app.add_handler(CallbackQueryHandler(news_no, pattern="^news_no$"))
    app.add_handler(CallbackQueryHandler(news_now, pattern="^news_now$"))

    app.add_handler(CallbackQueryHandler(settings, pattern="^settings$"))
    app.add_handler(CallbackQueryHandler(toggle_news, pattern="^toggle_news$"))

    app.add_handler(CallbackQueryHandler(convert_start, pattern="^convert$"))
    app.add_handler(CallbackQueryHandler(select_target_type, pattern="^src_"))
    app.add_handler(CallbackQueryHandler(select_target, pattern="^(target_fiat|target_crypto)$"))
    app.add_handler(CallbackQueryHandler(enter_amount, pattern="^(fiat_|tgt_)"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, calculate))
    app.add_handler(CallbackQueryHandler(back_to_menu, pattern="^back$"))
    app.add_error_handler(error_handler)

    app.job_queue.run_repeating(fetch_news_job, interval=300)
    app.job_queue.run_repeating(broadcast_news_job, interval=43200)

    app.run_polling()


if __name__ == "__main__":
    main()