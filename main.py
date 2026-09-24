#!/usr/bin/env python3

import requests
import json
import os
import time
import re
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

# ================= CONFIGURATION =================
BOT_TOKEN = "8839114711:AAFh3ErE0aGLXk-NbTRaWYuI5bpf4J-4qao"

CHANNEL_1 = "Sankiworld28"
CHANNEL_2 = "Sankiworld288"

CHANNEL_3_ID = -1003930906926
CHANNEL_3_LINK = "https://t.me/+wGjtBnLBxco5ZjNl"

API_URL = "https://nmdllpezcocquamhgpmb.supabase.co/functions/v1/lookup?number={value}"

OWNER_ID = 7301992915
OWNER_USERNAME = "@Sankiromeo"

CREDITS_FILE = "credits.json"
REDEEM_FILE = "redeem_codes.json"
CONFIG_FILE = "config.json"
REFERRALS_FILE = "referrals.json"
PENDING_REFS_FILE = "pending_refs.json"
BANNED_FILE = "banned.json"

NEW_USER_CREDITS = 5
DEFAULT_REFER_REWARD = 2

CREDIT_EXPIRY_DAYS = 30
CREDIT_EXPIRY_SECONDS = CREDIT_EXPIRY_DAYS * 24 * 60 * 60
# =================================================


# ============ CONFIG HELPERS ============
def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {"refer_reward": DEFAULT_REFER_REWARD, "maintenance": False}
    try:
        with open(CONFIG_FILE, "r") as f:
            cfg = json.load(f)
            cfg.setdefault("refer_reward", DEFAULT_REFER_REWARD)
            cfg.setdefault("maintenance", False)
            return cfg
    except Exception:
        return {"refer_reward": DEFAULT_REFER_REWARD, "maintenance": False}


def save_config(data):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Save Config Error: {e}")


def get_refer_reward():
    return load_config().get("refer_reward", DEFAULT_REFER_REWARD)


def set_refer_reward(amount):
    cfg = load_config()
    cfg["refer_reward"] = amount
    save_config(cfg)


def is_maintenance():
    return load_config().get("maintenance", False)


def set_maintenance(status):
    cfg = load_config()
    cfg["maintenance"] = status
    save_config(cfg)
# =================================================


# ============ BAN HELPERS ============
def load_banned():
    if not os.path.exists(BANNED_FILE):
        return []
    try:
        with open(BANNED_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []


def save_banned(data):
    try:
        with open(BANNED_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Save Banned Error: {e}")


def is_banned(user_id):
    return user_id in load_banned()


def ban_user(user_id):
    data = load_banned()
    if user_id not in data:
        data.append(user_id)
        save_banned(data)


def unban_user(user_id):
    data = load_banned()
    if user_id in data:
        data.remove(user_id)
        save_banned(data)
# =================================================


# ============ REFERRAL HELPERS ============
def load_referrals():
    if not os.path.exists(REFERRALS_FILE):
        return {}
    try:
        with open(REFERRALS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def save_referrals(data):
    try:
        with open(REFERRALS_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Save Referrals Error: {e}")


def add_referral(referrer_id, new_user_id):
    data = load_referrals()
    rid = str(referrer_id)
    if rid not in data:
        data[rid] = {"referred_users": []}
    if new_user_id not in data[rid]["referred_users"]:
        data[rid]["referred_users"].append(new_user_id)
    save_referrals(data)
    return len(data[rid]["referred_users"])


def get_refer_count(user_id):
    data = load_referrals()
    rid = str(user_id)
    if rid not in data:
        return 0
    return len(data[rid].get("referred_users", []))


def is_user_already_referred(new_user_id):
    data = load_referrals()
    for rid, info in data.items():
        if new_user_id in info.get("referred_users", []):
            return True
    return False


def load_pending_refs():
    if not os.path.exists(PENDING_REFS_FILE):
        return {}
    try:
        with open(PENDING_REFS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def save_pending_refs(data):
    try:
        with open(PENDING_REFS_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Save Pending Refs Error: {e}")


def set_pending_ref(user_id, referrer_id):
    data = load_pending_refs()
    data[str(user_id)] = referrer_id
    save_pending_refs(data)


def get_pending_ref(user_id):
    data = load_pending_refs()
    return data.get(str(user_id))


def clear_pending_ref(user_id):
    data = load_pending_refs()
    if str(user_id) in data:
        del data[str(user_id)]
        save_pending_refs(data)
# =================================================


# ============ CREDIT STORAGE HELPERS ============
def load_credits():
    if not os.path.exists(CREDITS_FILE):
        return {}
    try:
        with open(CREDITS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def save_credits(data):
    try:
        with open(CREDITS_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Save Credits Error: {e}")


def user_exists(user_id):
    data = load_credits()
    return str(user_id) in data


def get_user_credits(user_id):
    data = load_credits()
    uid = str(user_id)
    if uid not in data:
        return None
    user_info = data[uid]
    if isinstance(user_info, int):
        return user_info
    now = int(time.time())
    credits = user_info.get("credits", 0)
    expires_at = user_info.get("expires_at", 0)
    if now >= expires_at:
        return 0
    return credits


def set_user_credits(user_id, amount):
    data = load_credits()
    uid = str(user_id)
    now = int(time.time())
    data[uid] = {"credits": amount, "expires_at": now + CREDIT_EXPIRY_SECONDS}
    save_credits(data)


def add_user_credits(user_id, amount):
    data = load_credits()
    uid = str(user_id)
    now = int(time.time())
    if uid in data:
        user_info = data[uid]
        if isinstance(user_info, int):
            current = user_info
        else:
            current = user_info.get("credits", 0)
    else:
        current = 0
    new_total = current + amount
    data[uid] = {"credits": new_total, "expires_at": now + CREDIT_EXPIRY_SECONDS}
    save_credits(data)
    return new_total


def deduct_user_credits(user_id, amount=1):
    data = load_credits()
    uid = str(user_id)
    now = int(time.time())
    if uid not in data:
        return False, 0
    user_info = data[uid]
    if isinstance(user_info, int):
        user_info = {"credits": user_info, "expires_at": now + CREDIT_EXPIRY_SECONDS}
    credits = user_info.get("credits", 0)
    expires_at = user_info.get("expires_at", 0)
    if now >= expires_at:
        credits = 0
    if credits < amount:
        user_info["credits"] = credits
        data[uid] = user_info
        save_credits(data)
        return False, credits
    user_info["credits"] = credits - amount
    data[uid] = user_info
    save_credits(data)
    return True, user_info["credits"]


def ensure_user_exists(user_id):
    data = load_credits()
    uid = str(user_id)
    now = int(time.time())
    if uid not in data:
        data[uid] = {"credits": NEW_USER_CREDITS, "expires_at": now + CREDIT_EXPIRY_SECONDS}
        save_credits(data)
        return NEW_USER_CREDITS, True
    user_info = data[uid]
    if isinstance(user_info, int):
        user_info = {"credits": user_info, "expires_at": now + CREDIT_EXPIRY_SECONDS}
    credits = user_info.get("credits", 0)
    expires_at = user_info.get("expires_at", 0)
    if now >= expires_at:
        credits = 0
    user_info["credits"] = credits
    data[uid] = user_info
    save_credits(data)
    return credits, False
# =================================================


# ============ REDEEM CODE HELPERS ============
def load_redeem_codes():
    if not os.path.exists(REDEEM_FILE):
        return {}
    try:
        with open(REDEEM_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def save_redeem_codes(data):
    try:
        with open(REDEEM_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Save Redeem Error: {e}")


def format_time_remaining(seconds):
    if seconds <= 0:
        return "Expired"
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    if days > 0:
        return f"{days}d {hours}h"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"
# =================================================


# ============ KEYBOARDS ============
def user_keyboard():
    keyboard = [
        [KeyboardButton("🔢 Number Information")],
        [KeyboardButton("💳 My Credits"), KeyboardButton("🎁 Redeem Code")],
        [KeyboardButton("👥 Refer & Earn"), KeyboardButton("📞 Contact Owner")],
        [KeyboardButton("📖 Help"), KeyboardButton("❌ Close Menu")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def admin_keyboard():
    cfg = load_config()
    maint_status = "🔴 ON" if cfg.get("maintenance") else "🟢 OFF"

    keyboard = [
        [KeyboardButton("🔢 Number Information")],
        [KeyboardButton("👥 Total Users"), KeyboardButton("📊 Live Stats")],
        [KeyboardButton("🎁 Create Code"), KeyboardButton("📋 List Codes")],
        [KeyboardButton("💎 Add Credits"), KeyboardButton("👤 User Info")],
        [KeyboardButton("🚫 Ban User"), KeyboardButton("✅ Unban User")],
        [KeyboardButton("📢 Broadcast"), KeyboardButton("⚙️ Refer Reward")],
        [KeyboardButton(f"🔧 Maintenance: {maint_status}"), KeyboardButton("🔄 Refresh Panel")],
        [KeyboardButton("❌ Close Menu")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def remove_keyboard():
    return ReplyKeyboardMarkup(
        [[KeyboardButton("📋 Open Menu")]],
        resize_keyboard=True
    )


def force_join_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("Join Channel 1", url=f"https://t.me/{CHANNEL_1}"),
            InlineKeyboardButton("Join Channel 2", url=f"https://t.me/{CHANNEL_2}")
        ],
        [InlineKeyboardButton("Join Channel 3 🔒", url=CHANNEL_3_LINK)],
        [InlineKeyboardButton("🔄 Try Again", callback_data="verify_join")]
    ]
    return InlineKeyboardMarkup(keyboard)
# =================================================


async def is_user_joined(context, user_id):
    try:
        member1 = await context.bot.get_chat_member(chat_id=f"@{CHANNEL_1}", user_id=user_id)
        member2 = await context.bot.get_chat_member(chat_id=f"@{CHANNEL_2}", user_id=user_id)
        member3 = await context.bot.get_chat_member(chat_id=CHANNEL_3_ID, user_id=user_id)
        if (member1.status in ["left", "kicked"] or
            member2.status in ["left", "kicked"] or
            member3.status in ["left", "kicked"]):
            return False
        return True
    except Exception as e:
        print(f"Force Join Error: {e}")
        return False


def get_number_info(number):
    try:
        url = API_URL.format(value=number)
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return response.json()
        print("API Status:", response.status_code)
        return None
    except Exception as e:
        print(f"API Error: {e}")
        return None


def clean_data(data):
    if not data:
        return data
    unwanted_keys = ["credit", "telegram", "channel", "api_info", "remaining", "tabbo"]
    if isinstance(data, dict):
        for key in unwanted_keys:
            data.pop(key, None)
        if "data" in data and isinstance(data["data"], list):
            for record in data["data"]:
                if isinstance(record, dict):
                    record.pop("id", None)
                    record.pop("alt_number", None)
    return data


async def send_welcome_message(context, chat_id, user_id, user_name):
    """Verification successful + full purana text with credits."""
    was_new_user = not user_exists(user_id)
    credits, is_new = ensure_user_exists(user_id)

    refer_msg = ""
    pending_ref = get_pending_ref(user_id)

    if was_new_user and pending_ref and pending_ref != user_id:
        if not is_user_already_referred(user_id):
            reward = get_refer_reward()
            add_user_credits(pending_ref, reward)
            total_refs = add_referral(pending_ref, user_id)
            try:
                await context.bot.send_message(
                    chat_id=pending_ref,
                    text=(
                        f"🎉 𝗡𝗘𝗪 𝗥𝗘𝗙𝗘𝗥𝗥𝗔𝗟! 🎉\n\n"
                        f"👤 {user_name} ne aapki link se bot join kiya!\n"
                        f"➕ Aapko mile: {reward} credits\n"
                        f"👥 Total Referrals: {total_refs}"
                    )
                )
            except Exception as e:
                print(f"Referrer notify error: {e}")
            refer_msg = f"\n\n🎁 𝗥𝗘𝗙𝗘𝗥𝗥𝗔𝗟 𝗕𝗢𝗡𝗨𝗦!\nAapke referrer ko {reward} credits mil gaye hain!"
        clear_pending_ref(user_id)

    welcome_extra = ""
    if is_new:
        welcome_extra = (
            f"\n\n🎁 𝗔𝗔𝗣𝗞𝗢 𝗠𝗜𝗟𝗘 𝗛𝗔𝗜𝗡 {NEW_USER_CREDITS} 𝗙𝗥𝗘𝗘 𝗖𝗥𝗘𝗗𝗜𝗧𝗦! 🎉\n"
            f"⚠️ 𝗬𝗲 𝗰𝗿𝗲𝗱𝗶𝘁𝘀 {CREDIT_EXPIRY_DAYS} 𝗱𝗶𝗻 𝗯𝗮𝗮𝗱 𝗲𝘅𝗽𝗶𝗿𝗲 𝗵𝗼 𝗷𝗮𝘆𝗲𝗻𝗴𝗲!"
        )

    if user_id == OWNER_ID:
        kb = admin_keyboard()
    else:
        kb = user_keyboard()

    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            "✅ 𝗩𝗘𝗥𝗜𝗙𝗜𝗖𝗔𝗧𝗜𝗢𝗡 𝗦𝗨𝗖𝗖𝗘𝗦𝗦𝗙𝗨𝗟 🎉\n\n"
            "💀🔥 𝗡𝗨𝗠𝗕𝗘𝗥 𝗜𝗡𝗙𝗢𝗥𝗠𝗔𝗧𝗜𝗢𝗡 𝗧𝗢𝗢𝗟 🔥\n"
            "👑 𝗕𝗬 𝗣𝗥𝗢𝗙𝗘𝗦𝗦𝗢𝗥 𝗟𝗢𝗩𝗘𝗞𝗨𝗦𝗛 👑\n\n"
            f"💳 𝗬𝗢𝗨𝗥 𝗖𝗥𝗘𝗗𝗜𝗧𝗦: {credits}\n\n"
            "📱 Number ki jankari lene ke liye:\n"
            "➤ Menu mai 🔢 Number Information button pe click kro\n"
            "➤ Fir 10 digit number bhejo (e.g., 9876543210)\n\n"
            "📋 Saare functions niche keyboard me hai"
            f"{welcome_extra}{refer_msg}"
        ),
        reply_markup=kb
    )


async def send_start_message(context, chat_id, user_id):
    """/start ke liye full purana message."""
    credits, _ = ensure_user_exists(user_id)

    if user_id == OWNER_ID:
        kb = admin_keyboard()
    else:
        kb = user_keyboard()

    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            "💀🔥 𝗡𝗨𝗠𝗕𝗘𝗥 𝗜𝗡𝗙𝗢𝗥𝗠𝗔𝗧𝗜𝗢𝗡 𝗧𝗢𝗢𝗟 🔥\n"
            "👑 𝗕𝗬 𝗣𝗥𝗢𝗙𝗘𝗦𝗦𝗢𝗥 𝗟𝗢𝗩𝗘𝗞𝗨𝗦𝗛 👑\n\n"
            f"💳 𝗬𝗢𝗨𝗥 𝗖𝗥𝗘𝗗𝗜𝗧𝗦: {credits}\n\n"
            "📱 Number ki jankari lene ke liye:\n"
            "➤ Menu mai 🔢 Number Information button pe click kro\n"
            "➤ Fir 10 digit number bhejo (e.g., 9876543210)\n\n"
            "📋 Saare functions niche keyboard me hai"
        ),
        reply_markup=kb
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name

    if is_banned(user_id):
        await update.message.reply_text("🚫 𝗔𝗔𝗣𝗞𝗢 𝗕𝗔𝗡 𝗞𝗔𝗥 𝗗𝗜𝗬𝗔 𝗚𝗔𝗬𝗔 𝗛𝗔𝗜!")
        return

    referrer_id = None
    if context.args and len(context.args) > 0:
        payload = context.args[0]
        if payload.startswith("ref_"):
            try:
                referrer_id = int(payload[4:])
            except ValueError:
                referrer_id = None

    if referrer_id and referrer_id != user_id:
        if not user_exists(user_id):
            set_pending_ref(user_id, referrer_id)

    if not await is_user_joined(context, user_id):
        await update.message.reply_text(
            f"Hi {user_name} ❤️\n\n"
            "Bot ko use krne ke liye teeno channel join kro 👇",
            reply_markup=force_join_keyboard()
        )
        return

    if is_maintenance() and user_id != OWNER_ID:
        await update.message.reply_text("🔧 𝗕𝗢𝗧 𝗠𝗔𝗜𝗡𝗧𝗘𝗡𝗔𝗡𝗖𝗘 𝗠𝗘 𝗛𝗔𝗜!\n\nThodi der baad try karo.")
        return

    await send_start_message(context, update.message.chat_id, user_id)


async def verify_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_name = query.from_user.first_name

    if await is_user_joined(context, user_id):
        await query.message.delete()
        await send_welcome_message(context, query.message.chat_id, user_id, user_name)
    else:
        await query.answer(
            "❌ ⚠️ 𝗔𝗔𝗣𝗡𝗘 𝗔𝗕𝗛𝗜 𝗧𝗔𝗞 𝗧𝗘𝗘𝗡𝗢 𝗖𝗛𝗔𝗡𝗡𝗘𝗟𝗦 𝗝𝗢𝗜𝗡 𝗡𝗔𝗛𝗜 𝗞𝗜𝗬𝗘! ❌",
            show_alert=True
        )


# ============ PANEL COMMAND ============
async def panel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if is_banned(user_id):
        await update.message.reply_text("🚫 Aapko ban kar diya gaya hai!")
        return

    if not await is_user_joined(context, user_id):
        await update.message.reply_text(
            "⚠️ 🔥 𝗣𝗘𝗛𝗟𝗘 𝗧𝗘𝗘𝗡𝗢 𝗖𝗛𝗔𝗡𝗡𝗘𝗟𝗦 𝗝𝗢𝗜𝗡 𝗞𝗔𝗥𝗘𝗜𝗡! 🔥",
            reply_markup=force_join_keyboard()
        )
        return

    ensure_user_exists(user_id)

    if user_id == OWNER_ID:
        await update.message.reply_text(
            "👑 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟 👑\n\nNiche keyboard se option choose karo:",
            reply_markup=admin_keyboard()
        )
    else:
        await update.message.reply_text(
            "📋 𝗨𝗦𝗘𝗥 𝗠𝗘𝗡𝗨 📋\n\nNiche keyboard se option choose karo:",
            reply_markup=user_keyboard()
        )
# =================================================


# ============ KEYBOARD BUTTON HANDLER ============
async def handle_keyboard_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if is_banned(user_id):
        await update.message.reply_text("🚫 Aapko ban kar diya gaya hai!")
        return

    # ============ PENDING STATE HANDLERS (Owner only) ============
    awaiting = context.user_data.get("awaiting")
    if awaiting and user_id == OWNER_ID and awaiting in ["ban_user", "unban_user", "broadcast"]:
        if text.lower() == "/cancel":
            context.user_data.pop("awaiting", None)
            await update.message.reply_text("❌ Cancel kar diya.", reply_markup=admin_keyboard())
            return

        if awaiting == "ban_user":
            context.user_data.pop("awaiting", None)
            try:
                target = int(text)
                ban_user(target)
                await update.message.reply_text(f"✅ User `{target}` ban kar diya!", parse_mode="Markdown", reply_markup=admin_keyboard())
            except ValueError:
                await update.message.reply_text("❌ Invalid user ID!", reply_markup=admin_keyboard())
            return

        if awaiting == "unban_user":
            context.user_data.pop("awaiting", None)
            try:
                target = int(text)
                unban_user(target)
                await update.message.reply_text(f"✅ User `{target}` unban kar diya!", parse_mode="Markdown", reply_markup=admin_keyboard())
            except ValueError:
                await update.message.reply_text("❌ Invalid user ID!", reply_markup=admin_keyboard())
            return

        if awaiting == "broadcast":
            context.user_data.pop("awaiting", None)
            credits_data = load_credits()
            success = 0
            fail = 0
            for uid in credits_data.keys():
                try:
                    await context.bot.send_message(chat_id=int(uid), text=f"📢 𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧\n\n{text}")
                    success += 1
                except Exception:
                    fail += 1
            await update.message.reply_text(
                f"✅ Broadcast complete!\n\n✔️ Sent: {success}\n❌ Failed: {fail}",
                reply_markup=admin_keyboard()
            )
            return

    # ============ FORCE JOIN CHECK ============
    if not await is_user_joined(context, user_id):
        await update.message.reply_text(
            "⚠️ 🔥 𝗣𝗘𝗛𝗟𝗘 𝗧𝗘𝗘𝗡𝗢 𝗖𝗛𝗔𝗡𝗡𝗘𝗟𝗦 𝗝𝗢𝗜𝗡 𝗞𝗔𝗥𝗘𝗜𝗡! 🔥",
            reply_markup=force_join_keyboard()
        )
        return

    if is_maintenance() and user_id != OWNER_ID:
        await update.message.reply_text("🔧 𝗕𝗢𝗧 𝗠𝗔𝗜𝗡𝗧𝗘𝗡𝗔𝗡𝗖𝗘 𝗠𝗘 𝗛𝗔𝗜!")
        return

    # ============ NUMBER INFORMATION BUTTON ============
    if text == "🔢 Number Information":
        context.user_data["awaiting"] = "number_lookup"
        credits, _ = ensure_user_exists(user_id)

        await update.message.reply_text(
            "📱 🔥 𝗡𝗨𝗠𝗕𝗘𝗥 𝗜𝗡𝗙𝗢𝗥𝗠𝗔𝗧𝗜𝗢𝗡 𝗧𝗢𝗢𝗟 𝗕𝗬 𝗣𝗥𝗢𝗙𝗘𝗦𝗦𝗘𝗥 𝗟𝗢𝗩𝗘𝗞𝗨𝗦𝗛 🔥\n\n"
            f"💳 𝗬𝗢𝗨𝗥 𝗖𝗥𝗘𝗗𝗜𝗧𝗦: {credits}\n\n"
            "Ab 10 digit number bhejo:\n"
            "Example: 9876543210\n\n"
            "💰 Har lookup pe 1 credit lagega."
        )
        return

    # ============ IF AWAITING NUMBER (button pehle click kiya) ============
    if context.user_data.get("awaiting") == "number_lookup":
        await process_number_lookup(update, context, user_id, text)
        return

    # ============ USER BUTTONS ============
    if text == "💳 My Credits":
        credits, _ = ensure_user_exists(user_id)
        ref_count = get_refer_count(user_id)
        await update.message.reply_text(
            f"💳 𝗬𝗢𝗨𝗥 𝗖𝗥𝗘𝗗𝗜𝗧𝗦: {credits}\n"
            f"👥 𝗬𝗢𝗨𝗥 𝗥𝗘𝗙𝗘𝗥𝗥𝗔𝗟𝗦: {ref_count}\n\n"
            f"Har number lookup pe 1 credit lagega.\n"
            f"⚠️ Credits {CREDIT_EXPIRY_DAYS} din me expire ho jayenge."
        )
        return

    if text == "🎁 Redeem Code":
        await update.message.reply_text(
            "🎁 𝗥𝗘𝗗𝗘𝗘𝗠 𝗖𝗢𝗗𝗘\n\n"
            "Redeem code use karne ke liye ye bhejo:\n\n"
            "`/redeem <code>`\n\n"
            "Example: `/redeem WELCOME50`",
            parse_mode="Markdown"
        )
        return

    if text == "👥 Refer & Earn":
        bot_username = context.bot.username
        ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
        reward = get_refer_reward()
        total_refs = get_refer_count(user_id)
        credits = get_user_credits(user_id)

        share_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📤 Share Link", url=f"https://t.me/share/url?url={ref_link}&text=Ye%20bot%20try%20karo!")]
        ])

        await update.message.reply_text(
            "🎁 𝗬𝗢𝗨𝗥 𝗥𝗘𝗙𝗘𝗥𝗥𝗔𝗟 𝗟𝗜𝗡𝗞 🎁\n\n"
            f"🔗 `{ref_link}`\n\n"
            f"📊 Stats:\n"
            f"👥 Total Referrals: {total_refs}\n"
            f"💳 Current Credits: {credits}\n\n"
            f"💰 Reward: {reward} credits per referral",
            parse_mode="Markdown",
            reply_markup=share_kb,
            disable_web_page_preview=True
        )
        return

    if text == "📞 Contact Owner":
        await update.message.reply_text(
            f"📞 𝗖𝗢𝗡𝗧𝗔𝗖𝗧 𝗢𝗪𝗡𝗘𝗥\n\n"
            f"Credits kharidne ya kisi problem ke liye contact karo:\n\n"
            f"👤 {OWNER_USERNAME}"
        )
        return

    if text == "📖 Help":
        await update.message.reply_text(
            "📖 𝗖𝗢𝗠𝗠𝗔𝗡𝗗𝗦:\n\n"
            "/start - Bot start\n"
            "/panel - Menu open karo\n"
            "/mycredits - Apne credits dekho\n"
            "/refer - Apna referral link lo\n"
            "/redeem <code> - Redeem code\n\n"
            "💡 Har number lookup pe 1 credit lagega."
        )
        return

    if text == "❌ Close Menu":
        await update.message.reply_text(
            "❌ Menu band kar diya.\n\n"
            "Wapas kholne ke liye /panel bhejo.",
            reply_markup=remove_keyboard()
        )
        return

    if text == "📋 Open Menu":
        if user_id == OWNER_ID:
            await update.message.reply_text("👑 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟 👑", reply_markup=admin_keyboard())
        else:
            await update.message.reply_text("📋 𝗨𝗦𝗘𝗥 𝗠𝗘𝗡𝗨 📋", reply_markup=user_keyboard())
        return

    # ============ ADMIN BUTTONS ============
    if text in ["👥 Total Users", "📊 Live Stats", "🎁 Create Code", "📋 List Codes",
                "💎 Add Credits", "👤 User Info", "🚫 Ban User", "✅ Unban User",
                "📢 Broadcast", "⚙️ Refer Reward", "🔄 Refresh Panel"] or text.startswith("🔧 Maintenance"):
        if user_id != OWNER_ID:
            await update.message.reply_text("❌ Ye sirf owner use kar sakta hai!")
            return

    if text == "👥 Total Users":
        credits_data = load_credits()
        total_users = len(credits_data)
        banned = load_banned()
        active = 0
        now = int(time.time())
        for uid, info in credits_data.items():
            if isinstance(info, int):
                if info > 0:
                    active += 1
            else:
                c = info.get("credits", 0)
                e = info.get("expires_at", 0)
                if c > 0 and now < e:
                    active += 1
        await update.message.reply_text(
            f"👥 𝗧𝗢𝗧𝗔𝗟 𝗨𝗦𝗘𝗥𝗦\n\n"
            f"Total: {total_users}\n"
            f"Activated: {active}\n"
            f"Banned: {len(banned)}"
        )
        return

    if text == "📊 Live Stats":
        credits_data = load_credits()
        redeem_data = load_redeem_codes()
        ref_data = load_referrals()
        total_credits = 0
        for uid, info in credits_data.items():
            if isinstance(info, int):
                total_credits += info
            else:
                total_credits += info.get("credits", 0)
        await update.message.reply_text(
            f"📊 𝗟𝗜𝗩𝗘 𝗦𝗧𝗔𝗧𝗦\n\n"
            f"👥 Total Users: {len(credits_data)}\n"
            f"💳 Total Credits: {total_credits}\n"
            f"🎁 Redeem Codes: {len(redeem_data)}\n"
            f"👥 Referrers: {len(ref_data)}\n"
            f"🚫 Banned: {len(load_banned())}"
        )
        return

    if text == "🎁 Create Code":
        await update.message.reply_text(
            "🎁 𝗖𝗥𝗘𝗔𝗧𝗘 𝗥𝗘𝗗𝗘𝗘𝗠 𝗖𝗢𝗗𝗘\n\n"
            "Ye command bhejo:\n\n"
            "`/createredeem <code> <credits> <limit> <hours>`\n\n"
            "Example:\n"
            "`/createredeem WELCOME50 50 100 24`",
            parse_mode="Markdown"
        )
        return

    if text == "📋 List Codes":
        data = load_redeem_codes()
        if not data:
            await update.message.reply_text("📋 𝗥𝗘𝗗𝗘𝗘𝗠 𝗖𝗢𝗗𝗘𝗦\n\n(Abhi koi code nahi bana)")
        else:
            now = int(time.time())
            out = "📋 𝗥𝗘𝗗𝗘𝗘𝗠 𝗖𝗢𝗗𝗘𝗦\n\n"
            for code, info in data.items():
                expires_in = info["expires_at"] - now
                used = len(info["used_by"])
                status = "✅" if expires_in > 0 and used < info["member_limit"] else "❌"
                out += f"{status} `{code}` — {used}/{info['member_limit']}\n"
            await update.message.reply_text(out, parse_mode="Markdown")
        return

    if text == "💎 Add Credits":
        await update.message.reply_text(
            "💎 𝗔𝗗𝗗 𝗖𝗥𝗘𝗗𝗜𝗧𝗦\n\n"
            "Ye command bhejo:\n\n"
            "`/addcredits <user_id> <amount>`\n\n"
            "Example:\n"
            "`/addcredits 123456789 10`",
            parse_mode="Markdown"
        )
        return

    if text == "👤 User Info":
        await update.message.reply_text(
            "👤 𝗨𝗦𝗘𝗥 𝗜𝗡𝗙𝗢\n\n"
            "Ye command bhejo:\n\n"
            "`/checkcredits <user_id>`\n\n"
            "Example:\n"
            "`/checkcredits 123456789`",
            parse_mode="Markdown"
        )
        return

    if text == "🚫 Ban User":
        context.user_data["awaiting"] = "ban_user"
        await update.message.reply_text(
            "🚫 𝗕𝗔𝗡 𝗨𝗦𝗘𝗥\n\nUser ID bhejo jo ban karna hai:\n\n(/cancel bhejo cancel karne ke liye)"
        )
        return

    if text == "✅ Unban User":
        context.user_data["awaiting"] = "unban_user"
        await update.message.reply_text(
            "✅ 𝗨𝗡𝗕𝗔𝗡 𝗨𝗦𝗘𝗥\n\nUser ID bhejo jo unban karna hai:\n\n(/cancel bhejo cancel karne ke liye)"
        )
        return

    if text == "📢 Broadcast":
        context.user_data["awaiting"] = "broadcast"
        await update.message.reply_text(
            "📢 𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧\n\nBroadcast message bhejo jo sabhi users ko jayega:\n\n(/cancel bhejo cancel karne ke liye)"
        )
        return

    if text == "⚙️ Refer Reward":
        current = get_refer_reward()
        await update.message.reply_text(
            f"⚙️ 𝗥𝗘𝗙𝗘𝗥 𝗥𝗘𝗪𝗔𝗥𝗗\n\n"
            f"Current: {current} credits per referral\n\n"
            "Ye command se change karo:\n\n"
            "`/setreferreward <amount>`",
            parse_mode="Markdown"
        )
        return

    if text.startswith("🔧 Maintenance"):
        cfg = load_config()
        new_status = not cfg.get("maintenance", False)
        set_maintenance(new_status)
        await update.message.reply_text(
            f"🔧 𝗠𝗔𝗜𝗡𝗧𝗘𝗡𝗔𝗡𝗖𝗘 {'🔴 ON' if new_status else '🟢 OFF'}",
            reply_markup=admin_keyboard()
        )
        return

    if text == "🔄 Refresh Panel":
        await update.message.reply_text("🔄 Panel refresh ho gaya!", reply_markup=admin_keyboard())
        return

    # ============ DIRECT NUMBER BHEJA (button nahi click kiya) ============
    if re.match(r'^\d{10}$', text):
        await update.message.reply_text(
            "⚠️ 𝗡𝘂𝗺𝗯𝗲𝗿 𝗶𝗻𝗳𝗼𝗿𝗺𝗮𝘁𝗶𝗼𝗻 𝗹𝗲𝗻𝗲 𝗸𝗲 𝗹𝗶𝘆𝗲\n\n"
            "🔢 𝗡𝘂𝗺𝗯𝗲𝗿 𝗜𝗻𝗳𝗼𝗿𝗺𝗮𝘁𝗶𝗼𝗻 𝗯𝘂𝘁𝘁𝗼𝗻 𝗽𝗲 𝗰𝗹𝗶𝗰𝗸 𝗸𝗿𝗼\n\n"
            "Menu niche keyboard me hai 👇"
        )
        return
# =================================================


# ============ NUMBER LOOKUP PROCESSOR ============
async def process_number_lookup(update, context, user_id, number):
    if not re.match(r'^\d{10}$', number):
        await update.message.reply_text(
            "❌ 𝗔𝗥𝗘 𝗠𝗨𝗥𝗞𝗛! 🫡\n"
            "⚠️ 𝗦𝗔𝗛𝗜 𝗡𝗨𝗠𝗕𝗘𝗥 𝗗𝗔𝗔𝗟! (e.g., 9876543210)"
        )
        return

    # Clear awaiting state
    context.user_data.pop("awaiting", None)

    credits, _ = ensure_user_exists(user_id)

    if credits <= 0:
        await update.message.reply_text(
            f"❌ 𝗔𝗔𝗣𝗞𝗘 𝗖𝗥𝗘𝗗𝗜𝗧𝗦 𝗞𝗛𝗔𝗧𝗔𝗠 𝗛𝗢 𝗚𝗔𝗬𝗘 𝗛𝗔𝗜𝗡! 😢\n\n"
            f"💰 𝗔𝗨𝗥 𝗖𝗥𝗘𝗗𝗜𝗧𝗦 𝗞𝗘 𝗟𝗜𝗬𝗘:\n"
            f"🎁 /redeem <code> se redeem karo\n"
            f"👥 /refer se referral link lo\n"
            f"📞 Contact: {OWNER_USERNAME}"
        )
        return

    msg = await update.message.reply_text("✨🔍 𝗡𝗨𝗠𝗕𝗘𝗥 𝗞𝗜 𝗜𝗡𝗙𝗢𝗥𝗠𝗔𝗧𝗜𝗢𝗡 𝗡𝗜𝗞𝗔𝗟𝗜 𝗝𝗔 𝗥𝗔𝗛𝗜 𝗛𝗔𝗜... ⏳ ")

    data = get_number_info(number)

    if data:
        clean_data(data)
        success, remaining = deduct_user_credits(user_id, 1)

        result = json.dumps(data, indent=2, ensure_ascii=False)
        if len(result) > 4000:
            result = result[:4000] + "\n... (truncated)"

        footer = f"\n\n💳 𝗥𝗘𝗠𝗔𝗜𝗡𝗜𝗡𝗚 𝗖𝗥𝗘𝗗𝗜𝗧𝗦: {remaining}"

        try:
            await msg.edit_text(f"```json\n{result}\n```{footer}", parse_mode="Markdown")
        except Exception:
            await msg.edit_text(result + footer)

        if remaining <= 0:
            await update.message.reply_text(
                f"❌ 𝗔𝗔𝗣𝗞𝗘 𝗖𝗥𝗘𝗗𝗜𝗧𝗦 𝗞𝗛𝗔𝗧𝗔𝗠 𝗛𝗢 𝗚𝗔𝗬𝗘 𝗛𝗔𝗜𝗡! 😢\n\n"
                f"🎁 /redeem <code> se redeem karo\n"
                f"👥 /refer se referral link lo\n"
                f"📞 Contact: {OWNER_USERNAME}"
            )
    else:
        await msg.edit_text(
            "⚠️ 𝗜𝗦 𝗡𝗨𝗠𝗕𝗘𝗥 𝗞𝗔 𝗗𝗔𝗧𝗔 𝗡𝗔𝗛𝗜 𝗠𝗜𝗟𝗔!\n(Credit nahi kata gaya)"
        )
# =================================================


# ============ REFERRAL COMMAND ============
async def refer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await is_user_joined(context, user_id):
        await update.message.reply_text(
            "⚠️ 🔥 𝗣𝗘𝗛𝗟𝗘 𝗧𝗘𝗘𝗡𝗢 𝗖𝗛𝗔𝗡𝗡𝗘𝗟𝗦 𝗝𝗢𝗜𝗡 𝗞𝗔𝗥𝗘𝗜𝗡! 🔥",
            reply_markup=force_join_keyboard()
        )
        return

    ensure_user_exists(user_id)
    bot_username = context.bot.username
    ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    reward = get_refer_reward()
    total_refs = get_refer_count(user_id)
    credits = get_user_credits(user_id)

    share_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Share Link", url=f"https://t.me/share/url?url={ref_link}&text=Ye%20bot%20try%20karo!")]
    ])

    await update.message.reply_text(
        "🎁 𝗬𝗢𝗨𝗥 𝗥𝗘𝗙𝗘𝗥𝗥𝗔𝗟 𝗟𝗜𝗡𝗞 🎁\n\n"
        f"🔗 `{ref_link}`\n\n"
        f"📊 Stats:\n"
        f"👥 Total Referrals: {total_refs}\n"
        f"💳 Current Credits: {credits}\n\n"
        f"💰 Reward: {reward} credits per referral",
        parse_mode="Markdown",
        reply_markup=share_keyboard,
        disable_web_page_preview=True
    )


# ============ REDEEM COMMANDS ============
async def redeem_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await is_user_joined(context, user_id):
        await update.message.reply_text(
            "⚠️ 🔥 𝗣𝗘𝗛𝗟𝗘 𝗧𝗘𝗘𝗡𝗢 𝗖𝗛𝗔𝗡𝗡𝗘𝗟𝗦 𝗝𝗢𝗜𝗡 𝗞𝗔𝗥𝗘𝗜𝗡! 🔥",
            reply_markup=force_join_keyboard()
        )
        return

    if len(context.args) != 1:
        await update.message.reply_text("⚠️ 𝗨𝘀𝗮𝗴𝗲: /redeem <code>\nExample: /redeem WELCOME50")
        return

    code = context.args[0].strip().upper()
    data = load_redeem_codes()

    if code not in data:
        await update.message.reply_text("❌ 𝗥𝗘𝗗𝗘𝗘𝗠 𝗖𝗢𝗗𝗘 𝗜𝗡𝗩𝗔𝗟𝗜𝗗 𝗛𝗔𝗜!")
        return

    info = data[code]
    now = int(time.time())

    if now >= info["expires_at"]:
        await update.message.reply_text("❌ 𝗥𝗘𝗗𝗘𝗘𝗠 𝗖𝗢𝗗𝗘 𝗘𝗫𝗣𝗜𝗥𝗘 𝗛𝗢 𝗚𝗔𝗬𝗔! ⏰")
        return

    if len(info["used_by"]) >= info["member_limit"]:
        await update.message.reply_text("❌ 𝗠𝗘𝗠𝗕𝗘𝗥 𝗟𝗜𝗠𝗜𝗧 𝗙𝗨𝗟𝗟 𝗛𝗢 𝗚𝗔𝗬𝗔! 👥")
        return

    if user_id in info["used_by"]:
        await update.message.reply_text("❌ 𝗔𝗔𝗣𝗡𝗘 𝗬𝗘 𝗖𝗢𝗗𝗘 𝗣𝗘𝗛𝗟𝗘 𝗛𝗜 𝗨𝗦𝗘 𝗞𝗜𝗬𝗔 𝗛𝗔𝗜! 🙁")
        return

    new_total = add_user_credits(user_id, info["credits"])
    info["used_by"].append(user_id)
    data[code] = info
    save_redeem_codes(data)

    await update.message.reply_text(
        f"🎉 𝗥𝗘𝗗𝗘𝗘𝗠 𝗦𝗨𝗖𝗖𝗘𝗦𝗦! 🎉\n\n"
        f"🎁 Code: `{code}`\n"
        f"➕ Credits Added: {info['credits']}\n"
        f"💳 Total Credits: {new_total}",
        parse_mode="Markdown"
    )


async def create_redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id != OWNER_ID:
        await update.message.reply_text("❌ Ye command sirf owner use kar sakta hai!")
        return

    if len(context.args) != 4:
        await update.message.reply_text("⚠️ 𝗨𝘀𝗮𝗴𝗲: /createredeem <code> <credits> <member_limit> <hours>")
        return

    code = context.args[0].strip().upper()

    try:
        credits = int(context.args[1])
        member_limit = int(context.args[2])
        hours = float(context.args[3])
    except ValueError:
        await update.message.reply_text("❌ Invalid values!")
        return

    if credits <= 0 or member_limit <= 0 or hours <= 0:
        await update.message.reply_text("❌ Saare values positive hone chahiye!")
        return

    if not re.match(r'^[A-Z0-9_-]+$', code):
        await update.message.reply_text("❌ Code me sirf A-Z, 0-9, _ aur - allowed hai!")
        return

    data = load_redeem_codes()

    if code in data:
        await update.message.reply_text(f"❌ Ye code `{code}` pehle se exist karta hai!", parse_mode="Markdown")
        return

    now = int(time.time())
    data[code] = {
        "credits": credits,
        "member_limit": member_limit,
        "used_by": [],
        "created_at": now,
        "expires_at": now + int(hours * 3600)
    }
    save_redeem_codes(data)

    await update.message.reply_text(
        f"✅ 𝗥𝗘𝗗𝗘𝗘𝗠 𝗖𝗢𝗗𝗘 𝗖𝗥𝗘𝗔𝗧𝗘𝗗!\n\n"
        f"🎁 Code: `{code}`\n"
        f"💳 Credits: {credits}\n"
        f"👥 Member Limit: {member_limit}\n"
        f"⏳ Time Limit: {hours} hours",
        parse_mode="Markdown"
    )


async def list_redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id != OWNER_ID:
        await update.message.reply_text("❌ Ye command sirf owner use kar sakta hai!")
        return

    data = load_redeem_codes()
    if not data:
        await update.message.reply_text("❌ Abhi koi redeem code nahi hai.")
        return

    now = int(time.time())
    text = "🎁 𝗔𝗟𝗟 𝗥𝗘𝗗𝗘𝗘𝗠 𝗖𝗢𝗗𝗘𝗦:\n\n"

    for code, info in data.items():
        expires_in = info["expires_at"] - now
        time_str = format_time_remaining(expires_in)
        used = len(info["used_by"])
        status = "✅ Active" if expires_in > 0 and used < info["member_limit"] else "❌ Expired/Full"
        text += (
            f"🎁 `{code}`\n"
            f"   📊 {status}\n"
            f"   💳 Credits: {info['credits']}\n"
            f"   👥 Used: {used}/{info['member_limit']}\n"
            f"   ⏳ Time Left: {time_str}\n\n"
        )

    try:
        await update.message.reply_text(text, parse_mode="Markdown")
    except Exception:
        await update.message.reply_text(text)


async def del_redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id != OWNER_ID:
        await update.message.reply_text("❌ Ye command sirf owner use kar sakta hai!")
        return

    if len(context.args) != 1:
        await update.message.reply_text("⚠️ 𝗨𝘀𝗮𝗴𝗲: /delredeem <code>")
        return

    code = context.args[0].strip().upper()
    data = load_redeem_codes()

    if code not in data:
        await update.message.reply_text(f"❌ Code `{code}` exist nahi karta!")
        return

    del data[code]
    save_redeem_codes(data)
    await update.message.reply_text(f"✅ Code `{code}` delete kar diya!")
# =================================================


# ============ REFER SETTINGS ============
async def setreferreward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id != OWNER_ID:
        await update.message.reply_text("❌ Ye command sirf owner use kar sakta hai!")
        return

    if len(context.args) != 1:
        current = get_refer_reward()
        await update.message.reply_text(f"⚠️ 𝗨𝘀𝗮𝗴𝗲: /setreferreward <amount>\n\nCurrent: {current}")
        return

    try:
        amount = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Amount number hona chahiye!")
        return

    if amount <= 0:
        await update.message.reply_text("❌ Amount positive hona chahiye!")
        return

    set_refer_reward(amount)
    await update.message.reply_text(f"✅ 𝗥𝗘𝗙𝗘𝗥 𝗥𝗘𝗪𝗔𝗥𝗗 𝗨𝗣𝗗𝗔𝗧𝗘𝗗!\n\n💰 New Reward: {amount} credits per referral")


async def referstats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id != OWNER_ID:
        await update.message.reply_text("❌ Ye command sirf owner use kar sakta hai!")
        return

    if len(context.args) == 1:
        try:
            target_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid user_id!")
            return

        count = get_refer_count(target_id)
        credits = get_user_credits(target_id)

        await update.message.reply_text(
            f"📊 𝗥𝗘𝗙𝗘𝗥 𝗦𝗧𝗔𝗧𝗦\n\n"
            f"👤 User ID: {target_id}\n"
            f"👥 Total Referrals: {count}\n"
            f"💳 Current Credits: {credits}\n"
            f"💰 Current Reward Rate: {get_refer_reward()}"
        )
    else:
        data = load_referrals()
        if not data:
            await update.message.reply_text("❌ Abhi tak koi referral nahi hua.")
            return

        sorted_refs = sorted(data.items(), key=lambda x: len(x[1].get("referred_users", [])), reverse=True)[:10]

        text = "🏆 𝗧𝗢𝗣 𝟭𝟬 𝗥𝗘𝗙𝗘𝗥𝗥𝗘𝗥𝗦:\n\n"
        for i, (rid, info) in enumerate(sorted_refs, 1):
            cnt = len(info.get("referred_users", []))
            text += f"{i}. User `{rid}` → {cnt} referrals\n"

        text += f"\n💰 Current Reward: {get_refer_reward()} credits/referral"
        await update.message.reply_text(text, parse_mode="Markdown")
# =================================================


# ============ CREDIT COMMANDS ============
async def addcredits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id != OWNER_ID:
        await update.message.reply_text("❌ Ye command sirf owner use kar sakta hai!")
        return

    if len(context.args) != 2:
        await update.message.reply_text("⚠️ 𝗨𝘀𝗮𝗴𝗲: /addcredits <user_id> <amount>")
        return

    try:
        target_id = int(context.args[0])
        amount = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Invalid user_id ya amount!")
        return

    if amount <= 0:
        await update.message.reply_text("❌ Amount positive hona chahiye!")
        return

    new_total = add_user_credits(target_id, amount)

    await update.message.reply_text(
        f"✅ 𝗦𝗨𝗖𝗖𝗘𝗦𝗦!\n\n"
        f"👤 User ID: {target_id}\n"
        f"➕ Added: {amount}\n"
        f"💳 New Total: {new_total}\n"
        f"⏳ Expiry: Aaj se {CREDIT_EXPIRY_DAYS} din baad"
    )

    try:
        await context.bot.send_message(
            chat_id=target_id,
            text=(
                f"🎉 𝗬𝗢𝗨𝗥 𝗖𝗥𝗘𝗗𝗜𝗧𝗦 𝗛𝗔𝗩𝗘 𝗕𝗘𝗘𝗡 𝗨𝗣𝗗𝗔𝗧𝗘𝗗!\n\n"
                f"➕ 𝗔𝗱𝗱𝗲𝗱: {amount}\n"
                f"💳 𝗧𝗼𝘁𝗮𝗹 𝗖𝗿𝗲𝗱𝗶𝘁𝘀: {new_total}\n"
                f"⏳ 𝗬𝗲 𝗰𝗿𝗲𝗱𝗶𝘁𝘀 {CREDIT_EXPIRY_DAYS} 𝗱𝗶𝗻 𝗯𝗮𝗮𝗱 𝗲𝘅𝗽𝗶𝗿𝗲 𝗵𝗼 𝗷𝗮𝘆𝗲𝗻𝗴𝗲!"
            )
        )
    except Exception as e:
        print(f"Notify user error: {e}")


async def setcredits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id != OWNER_ID:
        await update.message.reply_text("❌ Ye command sirf owner use kar sakta hai!")
        return

    if len(context.args) != 2:
        await update.message.reply_text("⚠️ 𝗨𝘀𝗮𝗴𝗲: /setcredits <user_id> <amount>")
        return

    try:
        target_id = int(context.args[0])
        amount = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Invalid user_id ya amount!")
        return

    if amount < 0:
        await update.message.reply_text("❌ Amount negative nahi ho sakta!")
        return

    set_user_credits(target_id, amount)

    await update.message.reply_text(
        f"✅ 𝗦𝗘𝗧 𝗦𝗨𝗖𝗖𝗘𝗦𝗦!\n\n"
        f"👤 User ID: {target_id}\n"
        f"💳 New Credits: {amount}\n"
        f"⏳ Expiry: Aaj se {CREDIT_EXPIRY_DAYS} din baad"
    )

    try:
        await context.bot.send_message(
            chat_id=target_id,
            text=(
                f"🎉 𝗬𝗢𝗨𝗥 𝗖𝗥𝗘𝗗𝗜𝗧𝗦 𝗛𝗔𝗩𝗘 𝗕𝗘𝗘𝗡 𝗨𝗣𝗗𝗔𝗧𝗘𝗗!\n\n"
                f"💳 𝗧𝗼𝘁𝗮𝗹 𝗖𝗿𝗲𝗱𝗶𝘁𝘀: {amount}\n"
                f"⏳ 𝗬𝗲 𝗰𝗿𝗲𝗱𝗶𝘁𝘀 {CREDIT_EXPIRY_DAYS} 𝗱𝗶𝗻 𝗯𝗮𝗮𝗱 𝗲𝘅𝗽𝗶𝗿𝗲 𝗵𝗼 𝗷𝗮𝘆𝗲𝗻𝗴𝗲!"
            )
        )
    except Exception as e:
        print(f"Notify user error: {e}")


async def checkcredits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id != OWNER_ID:
        await update.message.reply_text("❌ Ye command sirf owner use kar sakta hai!")
        return

    if len(context.args) != 1:
        await update.message.reply_text("⚠️ 𝗨𝘀𝗮𝗴𝗲: /checkcredits <user_id>")
        return

    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid user_id!")
        return

    credits = get_user_credits(target_id)
    ref_count = get_refer_count(target_id)

    if credits is None:
        await update.message.reply_text(f"👤 User ID: {target_id}\n❌ Ye user registered nahi hai.")
    else:
        await update.message.reply_text(
            f"👤 𝗨𝗦𝗘𝗥 𝗜𝗡𝗙𝗢\n\n"
            f"🆔 ID: {target_id}\n"
            f"💳 Credits: {credits}\n"
            f"👥 Referrals: {ref_count}\n"
            f"🚫 Banned: {'Yes' if is_banned(target_id) else 'No'}"
        )


async def mycredits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    credits, _ = ensure_user_exists(user_id)
    ref_count = get_refer_count(user_id)

    await update.message.reply_text(
        f"💳 𝗬𝗢𝗨𝗥 𝗖𝗥𝗘𝗗𝗜𝗧𝗦: {credits}\n"
        f"👥 𝗬𝗢𝗨𝗥 𝗥𝗘𝗙𝗘𝗥𝗥𝗔𝗟𝗦: {ref_count}\n\n"
        f"Har number lookup pe 1 credit lagega.\n"
        f"⚠️ Credits {CREDIT_EXPIRY_DAYS} din me expire ho jayenge."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id == OWNER_ID:
        text = (
            "🛠 𝗢𝗪𝗡𝗘𝗥 𝗖𝗢𝗠𝗠𝗔𝗡𝗗𝗦:\n\n"
            "/panel - Admin panel kholo\n"
            "/addcredits <user_id> <amount>\n"
            "/setcredits <user_id> <amount>\n"
            "/checkcredits <user_id>\n"
            "/createredeem <code> <credits> <limit> <hours>\n"
            "/listredeem\n"
            "/delredeem <code>\n"
            "/setreferreward <amount>\n"
            "/referstats [user_id]\n"
        )
    else:
        text = (
            "📖 𝗖𝗢𝗠𝗠𝗔𝗡𝗗𝗦:\n\n"
            "/start - Bot start\n"
            "/panel - Menu open karo\n"
            "/mycredits - Apne credits dekho\n"
            "/refer - Apna referral link lo\n"
            "/redeem <code> - Redeem code\n\n"
            f"💡 Har lookup pe 1 credit lagega.\n"
            f"⚠️ Credits {CREDIT_EXPIRY_DAYS} din me expire honge.\n"
            f"Contact: {OWNER_USERNAME}"
        )

    await update.message.reply_text(text)
# =================================================


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("mycredits", mycredits))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("redeem", redeem_code))
    app.add_handler(CommandHandler("refer", refer_command))
    app.add_handler(CommandHandler("panel", panel_command))

    app.add_handler(CommandHandler("addcredits", addcredits))
    app.add_handler(CommandHandler("setcredits", setcredits))
    app.add_handler(CommandHandler("checkcredits", checkcredits))
    app.add_handler(CommandHandler("createredeem", create_redeem))
    app.add_handler(CommandHandler("listredeem", list_redeem))
    app.add_handler(CommandHandler("delredeem", del_redeem))
    app.add_handler(CommandHandler("setreferreward", setreferreward))
    app.add_handler(CommandHandler("referstats", referstats))

    app.add_handler(CallbackQueryHandler(verify_join, pattern="^verify_join$"))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_keyboard_button))

    print("💀 Bot is running (Keyboard + Number Info Button + Redeem + Referral)!")

    app.run_polling()


if __name__ == "__main__":
    main()