import asyncio, os, sys, logging, subprocess, psutil, sqlite3, hashlib, zipfile, shutil, re
from datetime import datetime, timedelta
from html import escape
from aiogram import Bot, Dispatcher, types, F, BaseMiddleware
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiohttp import web
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "8600719967:AAGvVMGLog8KUnQx8YtNsuCfV4z3DxK1U_g"
OWNER_ID = 8013504737
ADMIN_ID = 8885352363
ADMIN_ID_2 = 6241213553
YOUR_USERNAME = "@Exodus_OWN3R"
BRANDING_NAME = "𝑫𝒂𝒓𝒌𝒏𝒚𝒕𝒆 𝒆𝒙𝒐𝒅𝒖𝒔"
UPDATE_CHANNEL = "https://t.me/main_exodus"
BACKUP_CHANNEL = "https://t.me/DARKNYTEEXODUS_backup"
YOUTUBE_CHANNEL = "https://youtube.com/@darknyteexodus?si=tfyunbFvcuko7i-4"
HELP_VIDEO_LINK = "https://youtu.be/vLWoJRMRJKc?si=AKvAYHwtZw4yn26F"
FORCE_JOIN_MESSAGE = "🔒 Bot STOPPED! Admin added new channel. Join all, click I've Joined — bot ON again."

BASE_DIR = Path(__file__).parent.absolute()
UPLOAD_BOTS_DIR = BASE_DIR / 'upload_bots'
IROTECH_DIR = BASE_DIR / 'inf'
DATABASE_PATH = IROTECH_DIR / 'bot_data.db'
LOGS_DIR = IROTECH_DIR / 'logs'
BACKUP_DIR = IROTECH_DIR / 'backups'
UPLOAD_BOTS_DIR.mkdir(exist_ok=True)
IROTECH_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
BACKUP_DIR.mkdir(exist_ok=True)

FREE_USER_LIMIT = 2
SUBSCRIBED_USER_LIMIT = 5
ADMIN_LIMIT = 999
OWNER_LIMIT = float('inf')
FREE_USER_STORAGE_MB = 30
FREE_TRIAL_DAYS = 2
REFERRALS_NEEDED = 5
REFERRAL_REWARD_DAYS = 30

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
BOT_START_TIME = datetime.now()

bot_scripts = {}
user_subscriptions = {}
user_files = {}
user_favorites = {}
user_languages = {}
user_trial = {}
user_referrals = {}
user_ref_by = {}
banned_users = set()
active_users = set()
admin_ids = {OWNER_ID, ADMIN_ID, ADMIN_ID_2}
bot_locked = False
bot_stats = {'total_uploads': 0, 'total_downloads': 0, 'total_runs': 0}
required_channels = []

class AdminStates(StatesGroup):
    waiting_add_channel = State()
    waiting_remove_channel = State()
    waiting_edit_msg = State()
    waiting_broadcast = State()
    waiting_add_admin = State()
    waiting_remove_admin = State()
    waiting_ban = State()
    waiting_unban = State()
    waiting_premium = State()
    waiting_import_db = State()

class UserStates(StatesGroup):
    waiting_search = State()

TEXTS = {
    'hi': {
        'welcome_user': "👋 <b>नमस्ते, {name}!</b>",
        'your_id': "🆔 <b>ID:</b> <code>{uid}</code>",
        'account': "💎 <b>अकाउंट:</b> {acc}",
        'limit': "📦 <b>लिमिट:</b> {lim}",
        'storage': "💾 <b>स्टोरेज:</b> {used}/{total} MB",
        'btn_upload': "📤 फाइल अपलोड", 'btn_files': "📁 मेरी फाइलें",
        'btn_search': "🔍 खोजें", 'btn_fav': "⭐ पसंदीदा",
        'btn_speed': "⚡ स्पीड", 'btn_stats': "📊 आंकड़े",
        'btn_premium': "💎 प्रीमियम", 'btn_help': "ℹ️ सहायता",
        'btn_admin': "👑 एडमिन पैनल", 'btn_youtube': "🎥 YouTube",
        'btn_main_ch': "📢 मुख्य चैनल", 'btn_backup_ch': "📢 बैकअप",
        'btn_contact': "💬 संपर्क", 'btn_main_menu': "🏠 मुख्य मेनू",
        'btn_back': "🔙 वापस", 'btn_cancel': "❌ रद्द",
        'btn_run': "▶️ चलाएं", 'btn_stop': "🛑 रोकें",
        'btn_log': "📋 आउटपुट", 'btn_delete': "🗑️ हटाएं",
        'btn_info': "ℹ️ जानकारी", 'btn_favorite': "⭐ पसंदीदा",
        'btn_extract': "📦 ZIP खोलें", 'btn_lang': "🌐 भाषा",
        'developed': "⚡ <b>डेवलपर</b>",
        'join_required': "🔒 <b>बॉट बंद है</b>",
        'join_msg': "एडमिन ने नया चैनल जोड़ा। सभी जॉइन करें, फिर ✅ I've Joined दबाएं।",
        'join_channels': "📢 <b>जॉइन करें:</b>",
        'join_after': "जॉइन के बाद ✅ I've Joined दबाएं।",
        'btn_joined': "✅ मैंने जॉइन किया",
        'verified': "✅ वेरिफाइड!", 'not_joined': "❌ सभी जॉइन नहीं किए!",
        'upload_ok': "✅ <b>अपलोड सफल!</b>",
        'only_files': "❌ केवल .py, .js, .zip, requirements.txt",
        'limit_reached': "❌ लिमिट पूरी!", 'storage_full': "❌ 30 MB फुल!",
        'script_started': "✅ शुरू! (PID: {pid})",
        'script_stopped': "✅ रोक दी!", 'already_running': "⚠️ पहले से चल रही!",
        'no_files': "📭 कोई फाइल नहीं!", 'search_prompt': "🔍 नाम भेजें 👇",
        'banned': "🚫 बैन हैं!", 'bot_locked': "🔒 मेंटेनेंस!",
        'help_title': "ℹ️ <b>सहायता</b>", 'premium_title': "💎 <b>प्रीमियम</b>",
        'trial_active': "🆓 <b>ट्रायल:</b> {days} दिन बाकी",
        'trial_expired': "⚠️ <b>ट्रायल खत्म!</b>",
        'trial_expired_msg': "⚠️ <b>2 दिन का ट्रायल खत्म!</b>\n\n🎁 <b>2 ऑप्शन:</b>\n1️⃣ 5 रेफरल → 1 महीना फ्री\n2️⃣ प्रीमियम खरीदें",
        'ref_info': "🎁 <b>रेफरल</b>\n\n👥 रेफरल: <b>{count}/5</b>\n\n🔗 <code>{link}</code>\n\n5 रेफरल = 1 महीना फ्री!",
        'ref_btn': "🎁 रेफरल लिंक", 'premium_btn': "💎 खरीदें", 'renew_btn': "🎁 5 रेफरल करें",
    },
    'bn': {
        'welcome_user': "👋 <b>স্বাগতম, {name}!</b>",
        'your_id': "🆔 <b>ID:</b> <code>{uid}</code>",
        'account': "💎 <b>অ্যাকাউন্ট:</b> {acc}",
        'limit': "📦 <b>সীমা:</b> {lim}",
        'storage': "💾 <b>স্টোরেজ:</b> {used}/{total} MB",
        'btn_upload': "📤 আপলোড", 'btn_files': "📁 আমার ফাইল",
        'btn_search': "🔍 খুঁজুন", 'btn_fav': "⭐ প্রিয়",
        'btn_speed': "⚡ স্পিড", 'btn_stats': "📊 পরিসংখ্যান",
        'btn_premium': "💎 প্রিমিয়াম", 'btn_help': "ℹ️ সহায়তা",
        'btn_admin': "👑 অ্যাডমিন", 'btn_youtube': "🎥 YouTube",
        'btn_main_ch': "📢 মূল চ্যানেল", 'btn_backup_ch': "📢 ব্যাকআপ",
        'btn_contact': "💬 যোগাযোগ", 'btn_main_menu': "🏠 মূল মেনু",
        'btn_back': "🔙 পিছনে", 'btn_cancel': "❌ বাতিল",
        'btn_run': "▶️ চালান", 'btn_stop': "🛑 থামান",
        'btn_log': "📋 আউটপুট", 'btn_delete': "🗑️ মুছুন",
        'btn_info': "ℹ️ তথ্য", 'btn_favorite': "⭐ প্রিয়",
        'btn_extract': "📦 ZIP", 'btn_lang': "🌐 ভাষা",
        'developed': "⚡ <b>ডেভেলপার</b>",
        'join_required': "🔒 <b>বট বন্ধ</b>",
        'join_msg': "নতুন চ্যানেল যোগ হয়েছে। সব জয়েন করুন, তারপর ✅ I've Joined চাপুন।",
        'join_channels': "📢 <b>জয়েন করুন:</b>",
        'join_after': "জয়েনের পর ✅ I've Joined চাপুন।",
        'btn_joined': "✅ জয়েন করেছি",
        'verified': "✅ ভেরিফাইড!", 'not_joined': "❌ সব জয়েন করেননি!",
        'upload_ok': "✅ <b>সফল!</b>",
        'only_files': "❌ শুধু .py, .js, .zip, requirements.txt",
        'limit_reached': "❌ সীমা শেষ!", 'storage_full': "❌ 30 MB ফুল!",
        'script_started': "✅ শুরু! (PID: {pid})",
        'script_stopped': "✅ থামানো!", 'already_running': "⚠️ আগে থেকেই চলছে!",
        'no_files': "📭 ফাইল নেই!", 'search_prompt': "🔍 নাম পাঠান 👇",
        'banned': "🚫 নিষিদ্ধ!", 'bot_locked': "🔒 মেইনটেন্যান্স!",
        'help_title': "ℹ️ <b>সহায়তা</b>", 'premium_title': "💎 <b>প্রিমিয়াম</b>",
        'trial_active': "🆓 <b>ট্রায়াল:</b> {days} দিন বাকি",
        'trial_expired': "⚠️ <b>ট্রায়াল শেষ!</b>",
        'trial_expired_msg': "⚠️ <b>2 দিনের ট্রায়াল শেষ!</b>\n\n🎁 <b>2 অপশন:</b>\n1️⃣ 5 রেফারেল → 1 মাস ফ্রি\n2️⃣ প্রিমিয়াম কিনুন",
        'ref_info': "🎁 <b>রেফারেল</b>\n\n👥 রেফারেল: <b>{count}/5</b>\n\n🔗 <code>{link}</code>\n\n5 রেফারেল = 1 মাস ফ্রি!",
        'ref_btn': "🎁 রেফারেল লিংক", 'premium_btn': "💎 কিনুন", 'renew_btn': "🎁 5 রেফারেল",
    },
    'en': {
        'welcome_user': "👋 <b>Welcome, {name}!</b>",
        'your_id': "🆔 <b>ID:</b> <code>{uid}</code>",
        'account': "💎 <b>Account:</b> {acc}",
        'limit': "📦 <b>Limit:</b> {lim}",
        'storage': "💾 <b>Storage:</b> {used}/{total} MB",
        'btn_upload': "📤 Upload File", 'btn_files': "📁 My Files",
        'btn_search': "🔍 Search", 'btn_fav': "⭐ Favorites",
        'btn_speed': "⚡ Speed", 'btn_stats': "📊 Stats",
        'btn_premium': "💎 Premium", 'btn_help': "ℹ️ Help",
        'btn_admin': "👑 Admin Panel", 'btn_youtube': "🎥 YouTube",
        'btn_main_ch': "📢 Main Channel", 'btn_backup_ch': "📢 Backup",
        'btn_contact': "💬 Contact", 'btn_main_menu': "🏠 Main Menu",
        'btn_back': "🔙 Back", 'btn_cancel': "❌ Cancel",
        'btn_run': "▶️ Run", 'btn_stop': "🛑 Stop",
        'btn_log': "📋 Output", 'btn_delete': "🗑️ Delete",
        'btn_info': "ℹ️ Info", 'btn_favorite': "⭐ Favorite",
        'btn_extract': "📦 Extract ZIP", 'btn_lang': "🌐 Language",
        'developed': "⚡ <b>Developed by</b>",
        'join_required': "🔒 <b>BOT STOPPED</b>",
        'join_msg': "Admin added new channel. Join all, then click ✅ I've Joined.",
        'join_channels': "📢 <b>Join:</b>",
        'join_after': "After joining, click ✅ I've Joined.",
        'btn_joined': "✅ I've Joined",
        'verified': "✅ Verified!", 'not_joined': "❌ You haven't joined!",
        'upload_ok': "✅ <b>UPLOADED!</b>",
        'only_files': "❌ Only .py, .js, .zip, requirements.txt",
        'limit_reached': "❌ Limit reached!", 'storage_full': "❌ 30 MB full!",
        'script_started': "✅ Started! (PID: {pid})",
        'script_stopped': "✅ Stopped!", 'already_running': "⚠️ Already running!",
        'no_files': "📭 No files!", 'search_prompt': "🔍 Send filename 👇",
        'banned': "🚫 Banned!", 'bot_locked': "🔒 Maintenance!",
        'help_title': "ℹ️ <b>HELP</b>", 'premium_title': "💎 <b>PREMIUM</b>",
        'trial_active': "🆓 <b>Trial:</b> {days} days left",
        'trial_expired': "⚠️ <b>Trial expired!</b>",
        'trial_expired_msg': "⚠️ <b>Your 2-day trial expired!</b>\n\n🎁 <b>2 Options:</b>\n1️⃣ 5 Referrals → 1 Month Free\n2️⃣ Buy Premium",
        'ref_info': "🎁 <b>Referral</b>\n\n👥 Referrals: <b>{count}/5</b>\n\n🔗 <code>{link}</code>\n\n5 referrals = 1 month free!",
        'ref_btn': "🎁 Referral Link", 'premium_btn': "💎 Buy Premium", 'renew_btn': "🎁 5 Referrals",
    }
}

def t(user_id, key, **kwargs):
    lang = user_languages.get(user_id, 'en')
    txt = TEXTS.get(lang, TEXTS['en']).get(key, TEXTS['en'].get(key, key))
    if kwargs:
        try:
            return txt.format(**kwargs)
        except Exception:
            return txt
    return txt

def get_language_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇮🇳 हिंदी", callback_data="set_lang:hi")],
        [InlineKeyboardButton(text="🇧🇩 বাংলা", callback_data="set_lang:bn")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="set_lang:en")],
    ])

def build_language_select_text():
    return "╔═══════════════════════╗\n    🌐 <b>SELECT LANGUAGE</b> 🌐\n    <b>भाषा चुनें / ভাষা নির্বাচন করুন</b>\n╚═══════════════════════╝\n\n👇 Choose your language"

def get_user_file_limit(user_id):
    if user_id == OWNER_ID:
        return OWNER_LIMIT
    if user_id in admin_ids:
        return ADMIN_LIMIT
    if user_id in user_subscriptions and user_subscriptions[user_id]['expiry'] > datetime.now():
        return SUBSCRIBED_USER_LIMIT
    return FREE_USER_LIMIT

def get_user_storage_limit_mb(user_id):
    if user_id == OWNER_ID or user_id in admin_ids:
        return float('inf')
    return FREE_USER_STORAGE_MB

def get_user_storage_used_mb(user_id):
    folder = UPLOAD_BOTS_DIR / str(user_id)
    if not folder.exists():
        return 0.0
    total = 0
    for f in folder.rglob('*'):
        if f.is_file():
            total += f.stat().st_size
    return total / (1024 * 1024)

def format_limit(limit):
    return "Unlimited ♾️" if limit == float('inf') else f"{limit} bots"

def is_premium(user_id):
    return user_id in user_subscriptions and user_subscriptions[user_id]['expiry'] > datetime.now()

def is_trial_active(user_id):
    if user_id in (OWNER_ID, ADMIN_ID, ADMIN_ID_2):
        return True
    if is_premium(user_id):
        return True
    if user_id in user_trial:
        days_passed = (datetime.now() - user_trial[user_id]).days
        return days_passed < FREE_TRIAL_DAYS
    return True

def get_trial_days_left(user_id):
    if user_id not in user_trial:
        return FREE_TRIAL_DAYS
    passed = (datetime.now() - user_trial[user_id]).days
    return max(0, FREE_TRIAL_DAYS - passed)

def is_trial_check(user_id):
    if user_id in (OWNER_ID, ADMIN_ID, ADMIN_ID_2):
        return True
    if is_premium(user_id):
        return True
    return is_trial_active(user_id)

def sanitize_log(content):
    content = re.sub(r'\x1b\[[0-9;]*m', '', content)
    content = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', content)
    return content

# ═══════════ DATABASE ═══════════
def init_db():
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS subscriptions (user_id INTEGER PRIMARY KEY, expiry TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS user_files (user_id INTEGER, file_name TEXT, file_type TEXT, upload_date TEXT, PRIMARY KEY (user_id, file_name))')
    c.execute('CREATE TABLE IF NOT EXISTS active_users (user_id INTEGER PRIMARY KEY, join_date TEXT, last_active TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS admins (user_id INTEGER PRIMARY KEY)')
    c.execute('CREATE TABLE IF NOT EXISTS banned_users (user_id INTEGER PRIMARY KEY, banned_date TEXT, reason TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS favorites (user_id INTEGER, file_name TEXT, PRIMARY KEY (user_id, file_name))')
    c.execute('CREATE TABLE IF NOT EXISTS bot_stats (stat_name TEXT PRIMARY KEY, stat_value INTEGER)')
    c.execute('CREATE TABLE IF NOT EXISTS required_channels (username TEXT PRIMARY KEY, url TEXT, title TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS user_languages (user_id INTEGER PRIMARY KEY, lang TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS user_trial (user_id INTEGER PRIMARY KEY, trial_start TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS user_referrals (user_id INTEGER PRIMARY KEY, ref_count INTEGER DEFAULT 0, ref_by INTEGER)')
    for aid in (OWNER_ID, ADMIN_ID, ADMIN_ID_2):
        c.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (aid,))
    for stat in ['total_uploads', 'total_downloads', 'total_runs']:
        c.execute('INSERT OR IGNORE INTO bot_stats (stat_name, stat_value) VALUES (?, 0)', (stat,))
    c.execute('SELECT COUNT(*) FROM required_channels')
    if c.fetchone()[0] == 0:
        c.execute('INSERT OR IGNORE INTO required_channels (username, url, title) VALUES (?, ?, ?)', ('@main_exodus', UPDATE_CHANNEL, 'Main Channel'))
        c.execute('INSERT OR IGNORE INTO required_channels (username, url, title) VALUES (?, ?, ?)', ('@DARKNYTEEXODUS_backup', BACKUP_CHANNEL, 'Backup Channel'))
    conn.commit()
    conn.close()

def load_data():
    global required_channels, FORCE_JOIN_MESSAGE
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    for uid, exp in c.execute('SELECT user_id, expiry FROM subscriptions').fetchall():
        try: user_subscriptions[uid] = {'expiry': datetime.fromisoformat(exp)}
        except: pass
    for uid, fn, ft in c.execute('SELECT user_id, file_name, file_type FROM user_files').fetchall():
        user_files.setdefault(uid, []).append((fn, ft))
    active_users.update(r[0] for r in c.execute('SELECT user_id FROM active_users').fetchall())
    admin_ids.update(r[0] for r in c.execute('SELECT user_id FROM admins').fetchall())
    banned_users.update(r[0] for r in c.execute('SELECT user_id FROM banned_users').fetchall())
    for uid, fn in c.execute('SELECT user_id, file_name FROM favorites').fetchall():
        user_favorites.setdefault(uid, []).append(fn)
    for k, v in c.execute('SELECT stat_name, stat_value FROM bot_stats').fetchall():
        bot_stats[k] = v
    required_channels = [{"username": r[0], "url": r[1], "title": r[2]} for r in c.execute('SELECT username, url, title FROM required_channels').fetchall()]
    row = c.execute('SELECT value FROM settings WHERE key = ?', ('force_join_message',)).fetchone()
    if row: FORCE_JOIN_MESSAGE = row[0]
    for uid, lang in c.execute('SELECT user_id, lang FROM user_languages').fetchall():
        user_languages[uid] = lang
    for uid, ts in c.execute('SELECT user_id, trial_start FROM user_trial').fetchall():
        try: user_trial[uid] = datetime.fromisoformat(ts)
        except: pass
    for uid, cnt, ref_by in c.execute('SELECT user_id, ref_count, ref_by FROM user_referrals').fetchall():
        user_referrals[uid] = cnt or 0
        if ref_by: user_ref_by[uid] = ref_by
    conn.close()

def save_setting(key, value):
    conn = sqlite3.connect(DATABASE_PATH); c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value))
    conn.commit(); conn.close()

def save_user_language(user_id, lang):
    user_languages[user_id] = lang
    conn = sqlite3.connect(DATABASE_PATH); c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO user_languages (user_id, lang) VALUES (?, ?)', (user_id, lang))
    conn.commit(); conn.close()

def save_trial_start(user_id, dt):
    user_trial[user_id] = dt
    conn = sqlite3.connect(DATABASE_PATH); c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO user_trial (user_id, trial_start) VALUES (?, ?)', (user_id, dt.isoformat()))
    conn.commit(); conn.close()

def save_referral(user_id, ref_count=None, ref_by=None):
    conn = sqlite3.connect(DATABASE_PATH); c = conn.cursor()
    current = user_referrals.get(user_id, 0)
    new_count = ref_count if ref_count is not None else current
    new_ref_by = ref_by if ref_by is not None else user_ref_by.get(user_id)
    c.execute('INSERT OR REPLACE INTO user_referrals (user_id, ref_count, ref_by) VALUES (?, ?, ?)', (user_id, new_count, new_ref_by))
    conn.commit(); conn.close()

def reload_channels():
    global required_channels
    conn = sqlite3.connect(DATABASE_PATH); c = conn.cursor()
    required_channels = [{"username": r[0], "url": r[1], "title": r[2]} for r in c.execute('SELECT username, url, title FROM required_channels').fetchall()]
    conn.close()

def kill_user_scripts(user_id):
    for key in [k for k in bot_scripts if k.startswith(f"{user_id}_")]:
        try:
            info = bot_scripts[key]
            if info.get('log_file') and not info['log_file'].closed: info['log_file'].close()
            p = psutil.Process(info['process'].pid)
            for child in p.children(recursive=True): child.terminate()
            p.terminate(); del bot_scripts[key]
        except: pass

init_db()
load_data()

# ═══════════ FORCE SUBSCRIBE ═══════════
async def is_subscribed_to(user_id, ch):
    if user_id in (OWNER_ID, ADMIN_ID, ADMIN_ID_2): return True
    try:
        member = await bot.get_chat_member(chat_id=ch, user_id=user_id)
        return member.status not in ('left', 'kicked')
    except Exception as e:
        logger.error(f"Sub check {ch}: {e}")
        return True

async def is_subscribed(user_id):
    if user_id in (OWNER_ID, ADMIN_ID, ADMIN_ID_2): return True
    for ch in required_channels:
        if not await is_subscribed_to(user_id, ch["username"]): return False
    return True

async def get_unjoined_channels(user_id):
    if user_id in (OWNER_ID, ADMIN_ID, ADMIN_ID_2): return []
    return [ch for ch in required_channels if not await is_subscribed_to(user_id, ch["username"])]

def get_join_keyboard(user_id, unjoined=None):
    if unjoined is None: unjoined = required_channels
    buttons = []
    for ch in unjoined:
        buttons.append([InlineKeyboardButton(text=f"📢 Join {ch['title']}", url=ch["url"], style="primary")])
    buttons.append([InlineKeyboardButton(text="🎥 YouTube", url=YOUTUBE_CHANNEL, style="danger")])
    buttons.append([InlineKeyboardButton(text=t(user_id, 'btn_joined'), callback_data="check_join", style="success")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def build_join_lock_text(user_id, unjoined):
    lines = ["╔═══════════════════════╗", f"    {t(user_id, 'join_required')}", "╚═══════════════════════╝", "", FORCE_JOIN_MESSAGE, "", t(user_id, 'join_channels')]
    for ch in unjoined: lines.append(f"• <a href='{ch['url']}'>{ch['title']}</a>")
    lines.append(""); lines.append(t(user_id, 'join_after'))
    return "\n".join(lines)

class ForceSubMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user = data.get("event_from_user")
        if user:
            state: FSMContext = data.get("state")
            cur_state = None
            if state:
                try: cur_state = await state.get_state()
                except: pass
            is_admin_flow = cur_state is not None and user.id in admin_ids
            is_join_cb = isinstance(event, types.CallbackQuery) and event.data == "check_join"
            is_lang_cb = isinstance(event, types.CallbackQuery) and event.data.startswith("set_lang:")
            if not is_join_cb and not is_lang_cb and not is_admin_flow and user.id not in (OWNER_ID, ADMIN_ID, ADMIN_ID_2):
                if not await is_subscribed(user.id):
                    unjoined = await get_unjoined_channels(user.id)
                    text = build_join_lock_text(user.id, unjoined)
                    if isinstance(event, types.Message):
                        await event.answer(text, reply_markup=get_join_keyboard(user.id, unjoined), parse_mode="HTML", disable_web_page_preview=True)
                    elif isinstance(event, types.CallbackQuery):
                        await event.answer("🔒 Join channels first!", show_alert=True)
                    return
        return await handler(event, data)

dp.message.outer_middleware(ForceSubMiddleware())
dp.callback_query.outer_middleware(ForceSubMiddleware())

# ═══════════ KEYBOARDS ═══════════
def get_main_keyboard(user_id):
    rows = [
        [InlineKeyboardButton(text=t(user_id, 'btn_main_ch'), url=UPDATE_CHANNEL, style="primary"),
         InlineKeyboardButton(text=t(user_id, 'btn_backup_ch'), url=BACKUP_CHANNEL, style="primary")],
        [InlineKeyboardButton(text=t(user_id, 'btn_upload'), callback_data="upload_file"),
         InlineKeyboardButton(text=t(user_id, 'btn_files'), callback_data="check_files")],
        [InlineKeyboardButton(text=t(user_id, 'btn_search'), callback_data="search_files"),
         InlineKeyboardButton(text=t(user_id, 'btn_fav'), callback_data="my_favorites")],
        [InlineKeyboardButton(text=t(user_id, 'btn_speed'), callback_data="bot_speed"),
         InlineKeyboardButton(text=t(user_id, 'btn_stats'), callback_data="statistics")],
        [InlineKeyboardButton(text=t(user_id, 'btn_premium'), callback_data="get_premium"),
         InlineKeyboardButton(text=t(user_id, 'btn_help'), callback_data="help_info")],
        [InlineKeyboardButton(text=t(user_id, 'btn_lang'), callback_data="change_language")],
        [InlineKeyboardButton(text=t(user_id, 'btn_youtube'), url=YOUTUBE_CHANNEL, style="danger")],
        [InlineKeyboardButton(text=t(user_id, 'btn_contact'), url=f"https://t.me/{YOUR_USERNAME.replace('@', '')}", style="success")],
    ]
    if user_id in admin_ids:
        rows.insert(5, [InlineKeyboardButton(text=t(user_id, 'btn_admin'), callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_admin_panel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏱️ Uptime", callback_data="admin_bot_uptime"),
         InlineKeyboardButton(text="👥 Users", callback_data="admin_total_users")],
        [InlineKeyboardButton(text="📁 Files", callback_data="admin_total_files"),
         InlineKeyboardButton(text="🚀 Running", callback_data="admin_running_scripts")],
        [InlineKeyboardButton(text="💎 Premium", callback_data="admin_premium_users"),
         InlineKeyboardButton(text="📊 Analytics", callback_data="admin_analytics")],
        [InlineKeyboardButton(text="⚙️ System", callback_data="admin_system_status")],
        [InlineKeyboardButton(text="📢 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="➕ Add Channel", callback_data="admin_add_channel")],
        [InlineKeyboardButton(text="📋 Channels", callback_data="admin_list_channels"),
         InlineKeyboardButton(text="❌ Remove Channel", callback_data="admin_remove_channel")],
        [InlineKeyboardButton(text="✏️ Edit Force Msg", callback_data="admin_edit_force_msg")],
        [InlineKeyboardButton(text="👑 Add Admin", callback_data="admin_add_admin_btn"),
         InlineKeyboardButton(text="➖ Remove Admin", callback_data="admin_remove_admin_btn")],
        [InlineKeyboardButton(text="🚫 Ban", callback_data="admin_ban_btn"),
         InlineKeyboardButton(text="✅ Unban", callback_data="admin_unban_btn")],
        [InlineKeyboardButton(text="💎 Add Premium", callback_data="admin_add_premium_btn")],
        [InlineKeyboardButton(text="🧹 Clean", callback_data="admin_clean_files"),
         InlineKeyboardButton(text="💾 Backup DB", callback_data="admin_backup_db")],
        [InlineKeyboardButton(text="📥 Import DB", callback_data="admin_import_db")],
        [InlineKeyboardButton(text="📝 Logs", callback_data="admin_view_logs"),
         InlineKeyboardButton(text="🔒 Lock", callback_data="lock_bot")],
        [InlineKeyboardButton(text="🔄 Restart", callback_data="admin_restart_bot")],
        [InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_to_main")]
    ])

def get_back_kb(cb="admin_panel"):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Back", callback_data=cb)]])

def build_welcome_text(user_id, full_name):
    limit = get_user_file_limit(user_id)
    acc = "Owner 👑" if user_id == OWNER_ID else "Admin 👑" if user_id in admin_ids else "Premium 💎" if is_premium(user_id) else "Free 🆓"
    used = get_user_storage_used_mb(user_id)
    total = get_user_storage_limit_mb(user_id)
    total_str = "∞" if total == float('inf') else f"{total}"
    trial_line = ""
    if user_id not in admin_ids and not is_premium(user_id):
        if is_trial_active(user_id):
            trial_line = f"\n{t(user_id, 'trial_active', days=get_trial_days_left(user_id))}"
        else:
            trial_line = f"\n{t(user_id, 'trial_expired')}"
    title = f"🚀 <b>{BRANDING_NAME}</b> 🚀\n⚡ <i>Script Runner Bot</i>"
    return f"╔═══════════════════════╗\n    {title}\n╚═══════════════════════╝\n\n{t(user_id, 'welcome_user', name=full_name)}\n\n{t(user_id, 'your_id', uid=user_id)}\n{t(user_id, 'account', acc=acc)}\n{t(user_id, 'limit', lim=format_limit(limit))}\n{t(user_id, 'storage', used=f'{used:.2f}', total=total_str)}{trial_line}\n\n━━━━━━━━━━━━━━━━━━━━\n📢 <b>Main:</b> {UPDATE_CHANNEL}\n📢 <b>Backup:</b> {BACKUP_CHANNEL}\n🎥 <b>YT:</b> {YOUTUBE_CHANNEL}\n\n{t(user_id, 'developed')} <a href=\"https://t.me/Exodus_OWN3R\">Exodus OWN3R</a>\n🔒 <b>Version:</b> 10.0"




# ═══════════ START ═══════════
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    if user_id in banned_users:
        await message.answer(t(user_id, 'banned'), parse_mode="HTML")
        return
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            referrer_id = int(args[1].replace("ref_", ""))
            if referrer_id != user_id and user_id not in user_ref_by and user_id not in active_users:
                user_ref_by[user_id] = referrer_id
                user_referrals[referrer_id] = user_referrals.get(referrer_id, 0) + 1
                save_referral(referrer_id, ref_count=user_referrals[referrer_id])
                save_referral(user_id, ref_count=0, ref_by=referrer_id)
                try:
                    await bot.send_message(referrer_id, f"🎉 <b>New Referral!</b>\n\nTotal: <b>{user_referrals[referrer_id]}/{REFERRALS_NEEDED}</b>", parse_mode="HTML")
                    if user_referrals[referrer_id] >= REFERRALS_NEEDED:
                        new_expiry = datetime.now() + timedelta(days=REFERRAL_REWARD_DAYS)
                        user_subscriptions[referrer_id] = {'expiry': new_expiry}
                        conn = sqlite3.connect(DATABASE_PATH); c = conn.cursor()
                        c.execute('INSERT OR REPLACE INTO subscriptions (user_id, expiry) VALUES (?, ?)', (referrer_id, new_expiry.isoformat()))
                        c.execute('UPDATE user_referrals SET ref_count = 0 WHERE user_id = ?', (referrer_id,))
                        conn.commit(); conn.close()
                        user_referrals[referrer_id] = 0
                        await bot.send_message(referrer_id, f"🎁 <b>CONGRATULATIONS!</b>\n\nYou earned <b>1 Month Premium</b> for 5 referrals!\n\nExpires: {new_expiry.strftime('%Y-%m-%d')}", parse_mode="HTML")
                except Exception as e:
                    logger.error(f"Ref notify: {e}")
        except Exception as e:
            logger.error(f"Ref parse: {e}")
    if user_id not in user_languages:
        await message.answer(build_language_select_text(), reply_markup=get_language_keyboard(), parse_mode="HTML")
        return
    if user_id not in user_trial and user_id not in admin_ids:
        save_trial_start(user_id, datetime.now())
    active_users.add(user_id)
    try:
        conn = sqlite3.connect(DATABASE_PATH); c = conn.cursor()
        now = datetime.now().isoformat()
        c.execute('INSERT OR REPLACE INTO active_users (user_id, join_date, last_active) VALUES (?, ?, ?)', (user_id, now, now))
        conn.commit(); conn.close()
    except Exception as e:
        logger.error(f"save user: {e}")
    if user_id not in admin_ids and not is_premium(user_id) and not is_trial_active(user_id):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t(user_id, 'renew_btn'), callback_data="my_referral")],
            [InlineKeyboardButton(text=t(user_id, 'premium_btn'), url=f"https://t.me/{YOUR_USERNAME.replace('@', '')}", style="success")],
        ])
        await message.answer(t(user_id, 'trial_expired_msg'), reply_markup=kb, parse_mode="HTML")
        return
    await message.answer(build_welcome_text(user_id, message.from_user.full_name), reply_markup=get_main_keyboard(user_id), parse_mode="HTML", disable_web_page_preview=True)

@dp.callback_query(F.data.startswith("set_lang:"))
async def callback_set_language(callback: types.CallbackQuery, state: FSMContext):
    lang = callback.data.split(":", 1)[1]
    if lang not in ('hi', 'bn', 'en'): lang = 'en'
    user_id = callback.from_user.id
    save_user_language(user_id, lang)
    active_users.add(user_id)
    if user_id not in user_trial and user_id not in admin_ids:
        save_trial_start(user_id, datetime.now())
    try:
        conn = sqlite3.connect(DATABASE_PATH); c = conn.cursor()
        now = datetime.now().isoformat()
        c.execute('INSERT OR REPLACE INTO active_users (user_id, join_date, last_active) VALUES (?, ?, ?)', (user_id, now, now))
        conn.commit(); conn.close()
    except: pass
    unjoined = await get_unjoined_channels(user_id)
    if unjoined:
        text = build_join_lock_text(user_id, unjoined)
        await callback.message.edit_text(text, reply_markup=get_join_keyboard(user_id, unjoined), parse_mode="HTML", disable_web_page_preview=True)
        await callback.answer("✅ Language set!")
        return
    if user_id not in admin_ids and not is_premium(user_id) and not is_trial_active(user_id):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t(user_id, 'renew_btn'), callback_data="my_referral")],
            [InlineKeyboardButton(text=t(user_id, 'premium_btn'), url=f"https://t.me/{YOUR_USERNAME.replace('@', '')}", style="success")],
        ])
        await callback.message.edit_text(t(user_id, 'trial_expired_msg'), reply_markup=kb, parse_mode="HTML")
        await callback.answer("✅ Language set!")
        return
    await callback.message.edit_text(build_welcome_text(user_id, callback.from_user.full_name), reply_markup=get_main_keyboard(user_id), parse_mode="HTML", disable_web_page_preview=True)
    await callback.answer("✅ Language set!")

@dp.callback_query(F.data == "change_language")
async def callback_change_language(callback: types.CallbackQuery):
    await callback.message.edit_text(build_language_select_text(), reply_markup=get_language_keyboard(), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "check_join")
async def callback_check_join(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    unjoined = await get_unjoined_channels(user_id)
    if not unjoined:
        await callback.answer(t(user_id, 'verified'), show_alert=True)
        await bot.send_message(user_id, build_welcome_text(user_id, callback.from_user.full_name), reply_markup=get_main_keyboard(user_id), parse_mode="HTML", disable_web_page_preview=True)
    else:
        text = build_join_lock_text(user_id, unjoined)
        await callback.message.edit_text(text, reply_markup=get_join_keyboard(user_id, unjoined), parse_mode="HTML", disable_web_page_preview=True)
        await callback.answer(t(user_id, 'not_joined'), show_alert=True)

@dp.callback_query(F.data == "back_to_main")
async def callback_back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    if user_id not in admin_ids and not is_premium(user_id) and not is_trial_active(user_id):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t(user_id, 'renew_btn'), callback_data="my_referral")],
            [InlineKeyboardButton(text=t(user_id, 'premium_btn'), url=f"https://t.me/{YOUR_USERNAME.replace('@', '')}", style="success")],
        ])
        await callback.message.edit_text(t(user_id, 'trial_expired_msg'), reply_markup=kb, parse_mode="HTML")
        await callback.answer()
        return
    await callback.message.edit_text(build_welcome_text(user_id, callback.from_user.full_name), reply_markup=get_main_keyboard(user_id), parse_mode="HTML", disable_web_page_preview=True)
    await callback.answer()

@dp.callback_query(F.data == "my_referral")
async def callback_my_referral(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    me = await bot.get_me()
    link = f"https://t.me/{me.username}?start=ref_{user_id}"
    count = user_referrals.get(user_id, 0)
    text = t(user_id, 'ref_info', count=count, link=link)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Share", url=f"https://t.me/share/url?url={link}&text=Join%20this%20bot%20hosting!", style="primary")],
        [InlineKeyboardButton(text=t(user_id, 'btn_back'), callback_data="back_to_main")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML", disable_web_page_preview=True)
    await callback.answer()

# ═══════════ UPLOAD ═══════════
@dp.callback_query(F.data == "upload_file")
async def callback_upload_file(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if bot_locked and user_id not in admin_ids:
        await callback.answer(t(user_id, 'bot_locked'), show_alert=True)
        return
    if not is_trial_check(user_id):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t(user_id, 'renew_btn'), callback_data="my_referral")],
            [InlineKeyboardButton(text=t(user_id, 'premium_btn'), url=f"https://t.me/{YOUR_USERNAME.replace('@', '')}", style="success")],
        ])
        await callback.message.edit_text(t(user_id, 'trial_expired_msg'), reply_markup=kb, parse_mode="HTML")
        await callback.answer()
        return
    current = len(user_files.get(user_id, []))
    limit = get_user_file_limit(user_id)
    used = get_user_storage_used_mb(user_id)
    total = get_user_storage_limit_mb(user_id)
    total_str = "∞" if total == float('inf') else f"{total}"
    text = f"╔═══════════════════════╗\n    {t(user_id, 'btn_upload')}\n╚═══════════════════════╝\n\n📊 <b>Files:</b> {current} / {format_limit(limit)}\n💾 <b>Storage:</b> {used:.2f} / {total_str} MB\n\n📝 <b>Supported:</b>\n🐍 .py • 🟨 .js • 📦 .zip • 📋 requirements.txt\n\n━━━━━━━━━━━━━━━━━━━━\nSend your file 👇"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t(user_id, 'btn_main_menu'), callback_data="back_to_main")]])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "check_files")
async def callback_check_files(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    files = user_files.get(user_id, [])
    if not files:
        text = f"╔═══════════════════════╗\n    {t(user_id, 'btn_files')}\n╚═══════════════════════╝\n\n{t(user_id, 'no_files')}\n\nUpload your first file 🚀"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t(user_id, 'btn_upload'), callback_data="upload_file")],
            [InlineKeyboardButton(text=t(user_id, 'btn_main_menu'), callback_data="back_to_main")]
        ])
    else:
        used = get_user_storage_used_mb(user_id)
        total = get_user_storage_limit_mb(user_id)
        total_str = "∞" if total == float('inf') else f"{total}"
        text = f"╔═══════════════════════╗\n    {t(user_id, 'btn_files')} ({len(files)})\n    💾 {used:.2f}/{total_str} MB\n╚═══════════════════════╝\n\n"
        buttons = []
        for i, (fn, ft) in enumerate(files, 1):
            icon = "🐍" if ft == "py" else "🟨" if ft == "js" else "📦" if ft == "zip" else "📋"
            text += f"{i}. {icon} <code>{escape(fn)}</code>\n"
            is_fav = fn in user_favorites.get(user_id, [])
            star = "⭐" if is_fav else "☆"
            buttons.append([InlineKeyboardButton(text=f"▶️ {fn[:15]}", callback_data=f"run_script:{fn}"), InlineKeyboardButton(text=f"{star}", callback_data=f"toggle_fav:{fn}")])
            buttons.append([InlineKeyboardButton(text=t(user_id, 'btn_info'), callback_data=f"file_info:{fn}"), InlineKeyboardButton(text=t(user_id, 'btn_delete'), callback_data=f"delete_file:{fn}")])
        buttons.append([InlineKeyboardButton(text=t(user_id, 'btn_main_menu'), callback_data="back_to_main")])
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data.startswith("toggle_fav:"))
async def callback_toggle_favorite(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    fn = callback.data.split(":", 1)[1]
    user_favorites.setdefault(user_id, [])
    try:
        conn = sqlite3.connect(DATABASE_PATH); c = conn.cursor()
        if fn in user_favorites[user_id]:
            user_favorites[user_id].remove(fn)
            c.execute('DELETE FROM favorites WHERE user_id = ? AND file_name = ?', (user_id, fn))
            await callback.answer("❌ Removed!", show_alert=True)
        else:
            user_favorites[user_id].append(fn)
            c.execute('INSERT OR IGNORE INTO favorites (user_id, file_name) VALUES (?, ?)', (user_id, fn))
            await callback.answer("⭐ Added!", show_alert=True)
        conn.commit(); conn.close()
        await callback_check_files(callback)
    except Exception as e:
        await callback.answer(f"❌ {str(e)}", show_alert=True)

@dp.callback_query(F.data == "my_favorites")
async def callback_my_favorites(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    favs = user_favorites.get(user_id, [])
    if not favs:
        text = f"╔═══════════════════════╗\n    ⭐ {t(user_id, 'btn_fav')}\n╚═══════════════════════╝\n\nNo favorites yet!"
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t(user_id, 'btn_main_menu'), callback_data="back_to_main")]])
    else:
        text = f"╔═══════════════════════╗\n    ⭐ {t(user_id, 'btn_fav')} ({len(favs)})\n╚═══════════════════════╝\n\n"
        buttons = []
        for i, fn in enumerate(favs, 1):
            text += f"{i}. ⭐ <code>{escape(fn)}</code>\n"
            buttons.append([InlineKeyboardButton(text=f"▶️ {fn[:15]}", callback_data=f"run_script:{fn}"), InlineKeyboardButton(text="❌", callback_data=f"toggle_fav:{fn}")])
        buttons.append([InlineKeyboardButton(text=t(user_id, 'btn_main_menu'), callback_data="back_to_main")])
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data.startswith("file_info:"))
async def callback_file_info(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    fn = callback.data.split(":", 1)[1]
    fp = UPLOAD_BOTS_DIR / str(user_id) / fn
    if not fp.exists():
        await callback.answer("❌ Not found!", show_alert=True)
        return
    size = fp.stat().st_size
    ext = fp.suffix
    mod = datetime.fromtimestamp(fp.stat().st_mtime)
    is_fav = fn in user_favorites.get(user_id, [])
    text = f"╔═══════════════════════╗\n    ℹ️ FILE INFO\n╚═══════════════════════╝\n\n📄 <code>{escape(fn)}</code>\n📦 {ext.upper()}\n💾 {size/1024:.2f} KB\n📅 {mod.strftime('%Y-%m-%d %H:%M')}\n⭐ {'Yes' if is_fav else 'No'}\n🔐 <code>{hashlib.md5(fp.read_bytes()).hexdigest()[:16]}...</code>"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(user_id, 'btn_run'), callback_data=f"run_script:{fn}"), InlineKeyboardButton(text=t(user_id, 'btn_delete'), callback_data=f"delete_file:{fn}")],
        [InlineKeyboardButton(text=t(user_id, 'btn_files'), callback_data="check_files"), InlineKeyboardButton(text=t(user_id, 'btn_main_menu'), callback_data="back_to_main")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

# ═══════════ DOCUMENT HANDLER (ONLY ONE) ═══════════
@dp.message(F.document)
async def handle_document(message: types.Message):
    user_id = message.from_user.id
    fn = message.document.file_name

    # ⚡ OWNER DB BYPASS
    if user_id == OWNER_ID and fn.endswith('.db'):
        temp_path = IROTECH_DIR / f"owner_import_{int(datetime.now().timestamp())}.db"
        try:
            status = await message.answer("⚙️ Importing DB (Owner)...")
            await bot.download(message.document, destination=temp_path)
            old_backup = BACKUP_DIR / f"before_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            if DATABASE_PATH.exists(): shutil.copy2(DATABASE_PATH, old_backup)
            shutil.copy2(temp_path, DATABASE_PATH)
            if temp_path.exists(): temp_path.unlink()
            await status.edit_text("✅ <b>DB Imported!</b>\n\n🔄 Restarting in 3 seconds...")
            await asyncio.sleep(3)
            os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception as e:
            logger.error(f"Owner import: {e}")
            await message.answer(f"❌ Import failed: {escape(str(e))}", parse_mode="HTML")
        return

    if user_id in banned_users:
        await message.answer(t(user_id, 'banned')); return
    if bot_locked and user_id not in admin_ids:
        await message.answer(t(user_id, 'bot_locked')); return
    if not is_trial_check(user_id):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t(user_id, 'renew_btn'), callback_data="my_referral")],
            [InlineKeyboardButton(text=t(user_id, 'premium_btn'), url=f"https://t.me/{YOUR_USERNAME.replace('@', '')}", style="success")],
        ])
        await message.answer(t(user_id, 'trial_expired_msg'), reply_markup=kb, parse_mode="HTML")
        return

    file_ext = os.path.splitext(fn)[1].lower()
    if file_ext not in ['.py', '.js', '.zip'] and fn.lower() != 'requirements.txt':
        await message.answer(t(user_id, 'only_files')); return

    current = len(user_files.get(user_id, []))
    limit = get_user_file_limit(user_id)
    if current >= limit:
        await message.answer(f"{t(user_id, 'limit_reached')} ({current}/{limit})"); return

    used = get_user_storage_used_mb(user_id)
    total_limit = get_user_storage_limit_mb(user_id)
    file_size_mb = message.document.file_size / (1024 * 1024)
    if total_limit != float('inf') and (used + file_size_mb) > total_limit:
        await message.answer(f"{t(user_id, 'storage_full')}\n\n💾 {used:.2f}/{total_limit} MB"); return

    user_folder = UPLOAD_BOTS_DIR / str(user_id)
    user_folder.mkdir(exist_ok=True)
    file_path = user_folder / fn
    try:
        size_kb = message.document.file_size / 1024
        status = await message.answer(f"📤 <b>Preparing...</b>\n📄 <code>{escape(fn)}</code>\n💾 {size_kb:.2f} KB", parse_mode="HTML")
        await bot.download(message.document, destination=file_path)
        existing = user_files.get(user_id, [])
        existing = [f for f in existing if f[0] != fn]
        ft = file_ext[1:] if file_ext else 'txt'
        existing.append((fn, ft))
        user_files[user_id] = existing
        conn = sqlite3.connect(DATABASE_PATH); c = conn.cursor()
        now = datetime.now().isoformat()
        c.execute('INSERT OR REPLACE INTO user_files (user_id, file_name, file_type, upload_date) VALUES (?, ?, ?, ?)', (user_id, fn, ft, now))
        c.execute('UPDATE bot_stats SET stat_value = stat_value + 1 WHERE stat_name = ?', ('total_uploads',))
        conn.commit(); conn.close()
        bot_stats['total_uploads'] = bot_stats.get('total_uploads', 0) + 1

        install_note = ""
        if fn.lower() == 'requirements.txt':
            try:
                await status.edit_text("⚙️ Installing requirements...")
                proc = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', str(file_path)], capture_output=True, text=True, timeout=300)
                install_note = "\n\n✅ Requirements installed!" if proc.returncode == 0 else "\n\n⚠️ Install warning"
            except Exception as e:
                install_note = f"\n\n⚠️ {escape(str(e)[:100])}"

        if file_ext == '.zip':
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=t(user_id, 'btn_extract'), callback_data=f"extract_zip:{fn}"), InlineKeyboardButton(text=t(user_id, 'btn_favorite'), callback_data=f"toggle_fav:{fn}")],
                [InlineKeyboardButton(text=t(user_id, 'btn_info'), callback_data=f"file_info:{fn}"), InlineKeyboardButton(text=t(user_id, 'btn_delete'), callback_data=f"delete_file:{fn}")],
                [InlineKeyboardButton(text=t(user_id, 'btn_files'), callback_data="check_files"), InlineKeyboardButton(text=t(user_id, 'btn_main_menu'), callback_data="back_to_main")]
            ])
        else:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=t(user_id, 'btn_run'), callback_data=f"run_script:{fn}"), InlineKeyboardButton(text=t(user_id, 'btn_favorite'), callback_data=f"toggle_fav:{fn}")],
                [InlineKeyboardButton(text=t(user_id, 'btn_info'), callback_data=f"file_info:{fn}"), InlineKeyboardButton(text=t(user_id, 'btn_delete'), callback_data=f"delete_file:{fn}")],
                [InlineKeyboardButton(text=t(user_id, 'btn_files'), callback_data="check_files"), InlineKeyboardButton(text=t(user_id, 'btn_main_menu'), callback_data="back_to_main")]
            ])

        used_now = get_user_storage_used_mb(user_id)
        total_str = "∞" if total_limit == float('inf') else f"{total_limit}"
        await status.edit_text(f"{t(user_id, 'upload_ok')}\n\n📄 <code>{escape(fn)}</code>\n📦 {ft.upper()}\n💾 {size_kb:.2f} KB\n📊 {len(user_files[user_id])} files\n💾 Storage: {used_now:.2f}/{total_str} MB{install_note}", reply_markup=kb, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Upload error: {e}")
        await message.answer(f"❌ Upload failed: {escape(str(e))}", parse_mode="HTML")

# ═══════════ RUN / STOP / LOG ═══════════
@dp.callback_query(F.data.startswith("run_script:"))
async def callback_run_script(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if not is_trial_check(user_id):
        await callback.answer("⚠️ Trial expired!", show_alert=True)
        return
    fn = callback.data.split(":", 1)[1]
    user_folder = UPLOAD_BOTS_DIR / str(user_id)
    fp = user_folder / fn
    if not fp.exists():
        await callback.answer("❌ File not found!", show_alert=True); return
    sk = f"{user_id}_{fn}"
    if sk in bot_scripts:
        await callback.answer(t(user_id, 'already_running'), show_alert=True); return
    fext = fp.suffix.lower()
    try:
        log_path = user_folder / f"{fp.stem}.log"
        log_file = open(log_path, 'w')
        if fext == '.py':
            process = subprocess.Popen([sys.executable, str(fp)], cwd=str(user_folder), stdout=log_file, stderr=log_file)
        elif fext == '.js':
            process = subprocess.Popen(['node', str(fp)], cwd=str(user_folder), stdout=log_file, stderr=log_file)
        else:
            log_file.close()
            await callback.answer("❌ Cannot run!", show_alert=True); return
        bot_scripts[sk] = {'process': process, 'file_name': fn, 'script_owner_id': user_id, 'start_time': datetime.now(), 'user_folder': str(user_folder), 'type': fext[1:], 'log_file': log_file}
        conn = sqlite3.connect(DATABASE_PATH); c = conn.cursor()
        c.execute('UPDATE bot_stats SET stat_value = stat_value + 1 WHERE stat_name = ?', ('total_runs',))
        conn.commit(); conn.close()
        bot_stats['total_runs'] = bot_stats.get('total_runs', 0) + 1
        await asyncio.sleep(4)
        if process.poll() is not None:
            try:
                if not log_file.closed: log_file.close()
            except: pass
            content = log_path.read_text(errors='replace') if log_path.exists() else ""
            content = sanitize_log(content)
            safe = escape(content[-1500:]) if content else "(empty)"
            await callback.message.answer(f"⚠️ <b>Crashed!</b>\n\nExit: <code>{process.returncode}</code>\n\n<pre>{safe}</pre>", parse_mode="HTML")
            if sk in bot_scripts: del bot_scripts[sk]
            return
        await callback.answer(t(user_id, 'script_started', pid=process.pid), show_alert=True)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t(user_id, 'btn_stop'), callback_data=f"stop_script:{sk}")],
            [InlineKeyboardButton(text=t(user_id, 'btn_log'), callback_data=f"view_log:{fn}")],
            [InlineKeyboardButton(text=t(user_id, 'btn_files'), callback_data="check_files"), InlineKeyboardButton(text=t(user_id, 'btn_main_menu'), callback_data="back_to_main")]
        ])
        await callback.message.edit_reply_markup(reply_markup=kb)
    except Exception as e:
        logger.error(f"Run: {e}")
        await callback.answer(f"❌ {escape(str(e))}", show_alert=True)

@dp.callback_query(F.data.startswith("view_log:"))
async def callback_view_log(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    fn = callback.data.split(":", 1)[1]
    log_path = UPLOAD_BOTS_DIR / str(user_id) / f"{Path(fn).stem}.log"
    if not log_path.exists():
        await callback.answer("❌ No log!", show_alert=True); return
    try:
        content = log_path.read_text(errors='replace').strip()
        status = "🟢 Running" if f"{user_id}_{fn}" in bot_scripts else "🔴 Stopped"
        if not content: content = "(No output)"
        elif len(content) > 3500: content = "...(truncated)...\n" + content[-3500:]
        content = sanitize_log(content)
        safe = escape(content)
        text = f"📋 <b>Output</b> — <code>{escape(fn)}</code>\n{status}\n\n<pre>{safe}</pre>"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Refresh", callback_data=f"view_log:{fn}")],
            [InlineKeyboardButton(text=t(user_id, 'btn_files'), callback_data="check_files")]
        ])
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
        await callback.answer()
    except Exception as e:
        await callback.answer(f"❌ {str(e)[:100]}", show_alert=True)

@dp.callback_query(F.data.startswith("stop_script:"))
async def callback_stop_script(callback: types.CallbackQuery):
    sk = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id
    if sk not in bot_scripts:
        await callback.answer("❌ Not running!", show_alert=True); return
    try:
        info = bot_scripts[sk]
        if info.get('log_file') and not info['log_file'].closed: info['log_file'].close()
        p = psutil.Process(info['process'].pid)
        for child in p.children(recursive=True): child.terminate()
        p.terminate()
        del bot_scripts[sk]
        await callback.answer(t(user_id, 'script_stopped'), show_alert=True)
        await callback_back_to_main(callback, None)
    except Exception as e:
        await callback.answer(f"❌ {str(e)}", show_alert=True)

@dp.callback_query(F.data.startswith("extract_zip:"))
async def callback_extract_zip(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    fn = callback.data.split(":", 1)[1]
    user_folder = UPLOAD_BOTS_DIR / str(user_id)
    zp = user_folder / fn
    if not zp.exists() or not zipfile.is_zipfile(zp):
        await callback.answer("❌ Invalid ZIP!", show_alert=True); return
    try:
        await callback.message.edit_text("📦 Extracting...", parse_mode="HTML")
        with zipfile.ZipFile(zp, 'r') as z:
            z.extractall(user_folder)
            all_files = z.namelist()
        conn = sqlite3.connect(DATABASE_PATH); c = conn.cursor()
        now = datetime.now().isoformat()
        registered = []
        for ef in all_files:
            if ef.endswith('/'): continue
            p = Path(ef)
            ext = p.suffix.lower()
            if ext in ['.py', '.js']:
                just = p.name
                src = user_folder / ef
                dst = user_folder / just
                if src.exists() and src != dst and not dst.exists(): src.rename(dst)
                user_files.setdefault(user_id, []).append((just, ext[1:]))
                c.execute('INSERT OR REPLACE INTO user_files (user_id, file_name, file_type, upload_date) VALUES (?, ?, ?, ?)', (user_id, just, ext[1:], now))
                registered.append(just)
        user_files[user_id] = [f for f in user_files.get(user_id, []) if f[0] != fn]
        c.execute('DELETE FROM user_files WHERE user_id = ? AND file_name = ?', (user_id, fn))
        c.execute('DELETE FROM favorites WHERE user_id = ? AND file_name = ?', (user_id, fn))
        conn.commit(); conn.close()
        if zp.exists(): zp.unlink()
        reg = "\n".join([f"• <code>{escape(f)}</code>" for f in registered[:10]]) or "<i>None</i>"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t(user_id, 'btn_files'), callback_data="check_files"), InlineKeyboardButton(text=t(user_id, 'btn_main_menu'), callback_data="back_to_main")]
        ])
        await callback.message.edit_text(f"✅ <b>EXTRACTED!</b>\n\n📦 <code>{escape(fn)}</code>\n✅ Registered: {len(registered)}\n\n{reg}", reply_markup=kb, parse_mode="HTML")
        await callback.answer("✅ Done!")
    except Exception as e:
        await callback.answer(f"❌ {escape(str(e))}", show_alert=True)

@dp.callback_query(F.data.startswith("delete_file:"))
async def callback_delete_file(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    fn = callback.data.split(":", 1)[1]
    fp = UPLOAD_BOTS_DIR / str(user_id) / fn
    try:
        if fp.exists(): fp.unlink()
        user_files[user_id] = [f for f in user_files.get(user_id, []) if f[0] != fn]
        if fn in user_favorites.get(user_id, []): user_favorites[user_id].remove(fn)
        conn = sqlite3.connect(DATABASE_PATH); c = conn.cursor()
        c.execute('DELETE FROM user_files WHERE user_id = ? AND file_name = ?', (user_id, fn))
        c.execute('DELETE FROM favorites WHERE user_id = ? AND file_name = ?', (user_id, fn))
        conn.commit(); conn.close()
        await callback.answer("✅ Deleted from VPS!", show_alert=True)
        await callback_check_files(callback)
    except Exception as e:
        await callback.answer(f"❌ {escape(str(e))}", show_alert=True)

# ═══════════ STATS / SPEED / SEARCH / HELP / PREMIUM ═══════════
@dp.callback_query(F.data == "statistics")
async def callback_statistics(callback: types.CallbackQuery):
    uid = callback.from_user.id
    limit = get_user_file_limit(uid)
    acc = "Owner 👑" if uid == OWNER_ID else "Admin 👑" if uid in admin_ids else "Premium 💎" if is_premium(uid) else "Free 🆓"
    used = get_user_storage_used_mb(uid)
    total = get_user_storage_limit_mb(uid)
    total_str = "∞" if total == float('inf') else f"{total}"
    text = f"📊 <b>STATS</b>\n\n👤 {callback.from_user.full_name}\n🆔 <code>{uid}</code>\n💎 {acc}\n\n📁 Files: {len(user_files.get(uid, []))} / {format_limit(limit)}\n💾 Storage: {used:.2f} / {total_str} MB\n⭐ Favs: {len(user_favorites.get(uid, []))}\n🚀 Running: {sum(1 for k in bot_scripts if k.startswith(f'{uid}_'))}"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t(uid, 'btn_main_menu'), callback_data="back_to_main")]])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "bot_speed")
async def callback_bot_speed(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    start = datetime.now()
    await callback.answer("⚡")
    ms = (datetime.now() - start).total_seconds() * 1000
    status = "🟢 Excellent" if ms < 100 else "🟡 Good" if ms < 300 else "🔴 Slow"
    text = f"⚡ <b>SPEED</b>\n\n{ms:.2f}ms\n{status}\nCPU: {psutil.cpu_percent()}%\nRAM: {psutil.virtual_memory().percent}%"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Retry", callback_data="bot_speed"), InlineKeyboardButton(text=t(user_id, 'btn_main_menu'), callback_data="back_to_main")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")

@dp.callback_query(F.data == "search_files")
async def callback_search_files(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(UserStates.waiting_search)
    user_id = callback.from_user.id
    files = user_files.get(user_id, [])
    text = f"🔍 <b>SEARCH</b>\n\n📊 Total: {len(files)}\n\n{t(user_id, 'search_prompt')}"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t(user_id, 'btn_cancel'), callback_data="back_to_main")]])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@dp.message(UserStates.waiting_search)
async def process_search(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    term = message.text.lower().strip()
    matches = [f for f in user_files.get(user_id, []) if term in f[0].lower()]
    if not matches:
        await message.answer(f"🔍 No files match <code>{escape(term)}</code>", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t(user_id, 'btn_main_menu'), callback_data="back_to_main")]]), parse_mode="HTML")
        return
    text = f"🔍 <b>Results ({len(matches)}):</b>\n\n"
    for fn, ft in matches:
        icon = "🐍" if ft == "py" else "🟨" if ft == "js" else "📦" if ft == "zip" else "📋"
        text += f"{icon} <code>{escape(fn)}</code>\n"
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t(user_id, 'btn_main_menu'), callback_data="back_to_main")]]), parse_mode="HTML")

@dp.callback_query(F.data == "help_info")
async def callback_help_info(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    text = f"ℹ️ <b>HELP</b>\n\n<b>How to use:</b>\n\n1️⃣ Upload: Click Upload → send main.py\n2️⃣ Send requirements.txt (auto-install)\n3️⃣ Run: My Files → ▶️ Run\n4️⃣ Stop: 🛑 Stop\n5️⃣ Log: 📋 View Output\n\n━━━━━━━━━━━━━━━━━━\n🎥 <b>Video Tutorial:</b>\n<a href='{HELP_VIDEO_LINK}'>Watch on YouTube</a>\n\n📢 <a href='{UPDATE_CHANNEL}'>Main Channel</a>\n📢 <a href='{BACKUP_CHANNEL}'>Backup Channel</a>\n\n💬 {YOUR_USERNAME}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎥 Watch Tutorial", url=HELP_VIDEO_LINK, style="danger")],
        [InlineKeyboardButton(text="🎁 Referral", callback_data="my_referral")],
        [InlineKeyboardButton(text=t(user_id, 'btn_main_menu'), callback_data="back_to_main")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML", disable_web_page_preview=True)
    await callback.answer()

@dp.callback_query(F.data == "get_premium")
async def callback_get_premium(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    text = f"💎 <b>PREMIUM</b>\n\n✨ <b>Benefits:</b>\n📦 {SUBSCRIBED_USER_LIMIT} bots (vs {FREE_USER_LIMIT})\n⚡ Priority Support\n🚀 Faster Response\n⭐ Premium Badge\n\n💰 <b>Pricing:</b>\n1 Month: $5\n3 Months: $12\n1 Year: $40\n\n🎁 <b>OR</b> — 5 Referrals = 1 Month FREE!"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Get Free (5 Refs)", callback_data="my_referral", style="primary")],
        [InlineKeyboardButton(text=t(user_id, 'btn_contact'), url=f"https://t.me/{YOUR_USERNAME.replace('@', '')}", style="success")],
        [InlineKeyboardButton(text=t(user_id, 'btn_main_menu'), callback_data="back_to_main")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

# ═══════════ ADMIN PANEL ═══════════
@dp.callback_query(F.data == "admin_panel")
async def callback_admin_panel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if callback.from_user.id not in admin_ids:
        await callback.answer("❌ Admin only!", show_alert=True); return
    await callback.message.edit_text("👑 <b>ADMIN PANEL</b>", reply_markup=get_admin_panel_keyboard(), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "admin_bot_uptime")
async def cb_uptime(callback: types.CallbackQuery):
    if callback.from_user.id not in admin_ids: return
    d = datetime.now() - BOT_START_TIME
    days, rem = d.days, d.seconds
    h, rem = divmod(rem, 3600); m, s = divmod(rem, 60)
    await callback.message.edit_text(f"⏱️ <b>UPTIME</b>\n\n{days}d {h}h {m}m {s}s\nStarted: {BOT_START_TIME.strftime('%d %b %Y %H:%M')}", reply_markup=get_back_kb(), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "admin_total_users")
async def cb_total_users(callback: types.CallbackQuery):
    if callback.from_user.id not in admin_ids: return
    lst = "\n".join([f"• <code>{u}</code>" for u in list(active_users)[:15]])
    await callback.message.edit_text(f"👥 <b>USERS</b>\n\nTotal: {len(active_users)}\nBanned: {len(banned_users)}\nRunning: {len(bot_scripts)}\n\n{lst}", reply_markup=get_back_kb(), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "admin_total_files")
async def cb_total_files(callback: types.CallbackQuery):
    if callback.from_user.id not in admin_ids: return
    total = sum(len(f) for f in user_files.values())
    py = sum(1 for files in user_files.values() for f in files if f[1] == 'py')
    js = sum(1 for files in user_files.values() for f in files if f[1] == 'js')
    zp = sum(1 for files in user_files.values() for f in files if f[1] == 'zip')
    await callback.message.edit_text(f"📁 <b>FILES</b>\n\nTotal: {total}\n🐍 Python: {py}\n🟨 JS: {js}\n📦 ZIP: {zp}", reply_markup=get_back_kb(), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "admin_running_scripts")
async def cb_running(callback: types.CallbackQuery):
    if callback.from_user.id not in admin_ids: return
    if not bot_scripts:
        await callback.message.edit_text("🚀 <b>RUNNING</b>\n\n💤 None", reply_markup=get_back_kb(), parse_mode="HTML")
    else:
        text = f"🚀 <b>RUNNING ({len(bot_scripts)})</b>\n\n"
        buttons = []
        for sk, info in bot_scripts.items():
            rt = (datetime.now() - info['start_time']).total_seconds()
            text += f"🔸 <code>{escape(info['file_name'])}</code>\n   PID: {info['process'].pid} | User: {info['script_owner_id']}\n   Runtime: {int(rt)}s\n\n"
            buttons.append([InlineKeyboardButton(text=f"🛑 Stop {info['file_name'][:15]}", callback_data=f"stop_script:{sk}")])
        buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="admin_panel")])
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "admin_premium_users")
async def cb_prem_users(callback: types.CallbackQuery):
    if callback.from_user.id not in admin_ids: return
    active = [(u, d) for u, d in user_subscriptions.items() if d['expiry'] > datetime.now()]
    text = "💎 <b>PREMIUM</b>\n\n" + ("\n".join([f"💎 <code>{u}</code> — {d['expiry'].strftime('%Y-%m-%d')}" for u, d in active]) if active else "None")
    await callback.message.edit_text(text, reply_markup=get_back_kb(), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "admin_analytics")
async def cb_analytics(callback: types.CallbackQuery):
    if callback.from_user.id not in admin_ids: return
    text = f"📊 <b>ANALYTICS</b>\n\n📤 Uploads: {bot_stats.get('total_uploads', 0)}\n▶️ Runs: {bot_stats.get('total_runs', 0)}\n👥 Users: {len(active_users)}\n📁 Files: {sum(len(f) for f in user_files.values())}\n🚀 Running: {len(bot_scripts)}\n💎 Premium: {len([u for u in user_subscriptions if user_subscriptions[u]['expiry'] > datetime.now()])}\n🚫 Banned: {len(banned_users)}\n🔒 Bot: {'Locked' if bot_locked else 'Active'}"
    await callback.message.edit_text(text, reply_markup=get_back_kb(), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "admin_system_status")
async def cb_sys(callback: types.CallbackQuery):
    if callback.from_user.id not in admin_ids: return
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    text = f"⚙️ <b>SYSTEM</b>\n\n💻 CPU: {cpu}%\n🧠 RAM: {mem.percent}%\n💾 DISK: {disk.percent}%\n\n🤖 Scripts: {len(bot_scripts)}"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔄 Refresh", callback_data="admin_system_status")], [InlineKeyboardButton(text="🔙 Back", callback_data="admin_panel")]])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

# ═══════════ ADMIN: CHANNELS ═══════════
@dp.callback_query(F.data == "admin_add_channel")
async def cb_add_ch(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in admin_ids: return
    await state.set_state(AdminStates.waiting_add_channel)
    text = "➕ <b>ADD CHANNEL</b>\n\n⚠️ Adding will STOP running bots for all users.\n\n<b>Send in 3 lines:</b>\n<code>@username\nhttps://t.me/username\nTitle</code>"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Cancel", callback_data="admin_panel")]])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@dp.message(AdminStates.waiting_add_channel)
async def proc_add_ch(message: types.Message, state: FSMContext):
    if message.from_user.id not in admin_ids: return
    await state.clear()
    lines = [l.strip() for l in message.text.splitlines() if l.strip()]
    if len(lines) < 3:
        await message.answer("❌ Need 3 lines", reply_markup=get_back_kb()); return
    username = lines[0] if lines[0].startswith('@') else '@' + lines[0]
    url = lines[1]; title = lines[2]
    conn = sqlite3.connect(DATABASE_PATH); c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO required_channels (username, url, title) VALUES (?, ?, ?)', (username, url, title))
    conn.commit(); conn.close()
    reload_channels()
    killed = 0
    for uid in list(active_users):
        if uid in admin_ids: continue
        before = len(bot_scripts); kill_user_scripts(uid); killed += before - len(bot_scripts)
    await message.answer(f"✅ Added: {title}\n🛑 Killed {killed} scripts\n\n⚠️ Broadcasting...", parse_mode="HTML")
    sent, failed = 0, 0
    for uid in list(active_users):
        if uid in admin_ids or uid in banned_users: continue
        try:
            jkb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=f"📢 Join {title}", url=url, style="primary")],
                [InlineKeyboardButton(text="🎥 YouTube", url=YOUTUBE_CHANNEL, style="danger")],
                [InlineKeyboardButton(text=t(uid, 'btn_joined'), callback_data="check_join", style="success")]
            ])
            msg = f"╔═══════════════════════╗\n    {t(uid, 'join_required')}\n╚═══════════════════════╝\n\n{t(uid, 'join_msg')}\n\n📢 <b>New Channel:</b> <a href='{url}'>{title}</a>\n\n⚠️ <b>Your running bots have been STOPPED.</b>\nJoin to restart."
            await bot.send_message(uid, msg, reply_markup=jkb, parse_mode="HTML", disable_web_page_preview=True)
            sent += 1; await asyncio.sleep(0.05)
        except: failed += 1
    await message.answer(f"📢 Broadcast!\n✅ Sent: {sent}\n❌ Failed: {failed}", reply_markup=get_back_kb(), parse_mode="HTML")

@dp.callback_query(F.data == "admin_list_channels")
async def cb_list_ch(callback: types.CallbackQuery):
    if callback.from_user.id not in admin_ids: return
    text = f"📋 <b>CHANNELS ({len(required_channels)})</b>\n\n"
    for i, ch in enumerate(required_channels, 1):
        text += f"{i}. <b>{ch['title']}</b>\n   {ch['username']}\n   {ch['url']}\n\n"
    await callback.message.edit_text(text, reply_markup=get_back_kb(), parse_mode="HTML", disable_web_page_preview=True)
    await callback.answer()

@dp.callback_query(F.data == "admin_remove_channel")
async def cb_rm_ch(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in admin_ids: return
    await state.set_state(AdminStates.waiting_remove_channel)
    text = "❌ <b>REMOVE CHANNEL</b>\n\n<b>Current:</b>\n\n"
    for i, ch in enumerate(required_channels, 1):
        text += f"{i}. {ch['title']} — <code>{ch['username']}</code>\n"
    text += "\nSend @username:"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Cancel", callback_data="admin_panel")]])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@dp.message(AdminStates.waiting_remove_channel)
async def proc_rm_ch(message: types.Message, state: FSMContext):
    if message.from_user.id not in admin_ids: return
    await state.clear()
    username = message.text.strip()
    if not username.startswith('@'): username = '@' + username
    conn = sqlite3.connect(DATABASE_PATH); c = conn.cursor()
    c.execute('DELETE FROM required_channels WHERE username = ?', (username,))
    conn.commit(); conn.close()
    reload_channels()
    await message.answer(f"✅ Removed: <code>{escape(username)}</code>", reply_markup=get_back_kb(), parse_mode="HTML")

@dp.callback_query(F.data == "admin_edit_force_msg")
async def cb_edit_msg(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in admin_ids: return
    await state.set_state(AdminStates.waiting_edit_msg)
    text = f"✏️ <b>EDIT FORCE MSG</b>\n\n<b>Current:</b>\n<i>{escape(FORCE_JOIN_MESSAGE[:300])}</i>\n\nSend new:"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Cancel", callback_data="admin_panel")]])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@dp.message(AdminStates.waiting_edit_msg)
async def proc_edit_msg(message: types.Message, state: FSMContext):
    global FORCE_JOIN_MESSAGE
    if message.from_user.id not in admin_ids: return
    await state.clear()
    FORCE_JOIN_MESSAGE = message.text.strip()
    save_setting('force_join_message', FORCE_JOIN_MESSAGE)
    await message.answer("✅ Updated!", reply_markup=get_back_kb())

# ═══════════ BROADCAST ═══════════
@dp.callback_query(F.data == "admin_broadcast")
async def cb_bc(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in admin_ids: return
    await state.set_state(AdminStates.waiting_broadcast)
    text = f"📢 <b>BROADCAST</b>\n\nRecipients: {len(active_users)}\n\nSend <b>text</b> OR <b>photo with caption</b> 👇"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Cancel", callback_data="admin_panel")]])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@dp.message(AdminStates.waiting_broadcast)
async def proc_bc(message: types.Message, state: FSMContext):
    if message.from_user.id not in admin_ids: return
    await state.clear()
    sent, failed = 0, 0
    status = await message.answer("📢 Broadcasting...")
    if message.photo:
        caption = message.caption or ""
        for uid in list(active_users):
            if uid in banned_users: continue
            try:
                await bot.send_photo(uid, message.photo[-1].file_id, caption=f"📢 <b>Announcement:</b>\n\n{caption}", parse_mode="HTML")
                sent += 1; await asyncio.sleep(0.05)
            except: failed += 1
    else:
        btext = message.text or ""
        for uid in list(active_users):
            if uid in banned_users: continue
            try:
                await bot.send_message(uid, f"📢 <b>Announcement:</b>\n\n{btext}", parse_mode="HTML")
                sent += 1; await asyncio.sleep(0.05)
            except: failed += 1
    await status.edit_text(f"✅ Done!\n\n✅ Sent: {sent}\n❌ Failed: {failed}", reply_markup=get_back_kb(), parse_mode="HTML")

# ═══════════ ADMIN MGMT ═══════════
@dp.callback_query(F.data == "admin_add_admin_btn")
async def cb_add_adm(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in admin_ids: return
    await state.set_state(AdminStates.waiting_add_admin)
    text = "👑 <b>ADD ADMIN</b>\n\nSend USER ID 👇"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Cancel", callback_data="admin_panel")]])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@dp.message(AdminStates.waiting_add_admin)
async def proc_add_adm(message: types.Message, state: FSMContext):
    if message.from_user.id not in admin_ids: return
    await state.clear()
    try:
        uid = int(message.text.strip())
        admin_ids.add(uid)
        conn = sqlite3.connect(DATABASE_PATH); c = conn.cursor()
        c.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (uid,))
        conn.commit(); conn.close()
        await message.answer(f"✅ Added admin: <code>{uid}</code>", reply_markup=get_back_kb(), parse_mode="HTML")
    except: await message.answer("❌ Invalid ID!", reply_markup=get_back_kb())

@dp.callback_query(F.data == "admin_remove_admin_btn")
async def cb_rm_adm(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != OWNER_ID:
        await callback.answer("❌ Owner only!", show_alert=True); return
    await state.set_state(AdminStates.waiting_remove_admin)
    text = f"➖ <b>REMOVE ADMIN</b>\n\nCurrent ({len(admin_ids)}):\n"
    for aid in admin_ids: text += f"👑 <code>{aid}</code>\n"
    text += "\nSend USER ID:"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Cancel", callback_data="admin_panel")]])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@dp.message(AdminStates.waiting_remove_admin)
async def proc_rm_adm(message: types.Message, state: FSMContext):
    if message.from_user.id != OWNER_ID: return
    await state.clear()
    try:
        uid = int(message.text.strip())
        if uid == OWNER_ID:
            await message.answer("❌ Cannot remove owner!", reply_markup=get_back_kb()); return
        admin_ids.discard(uid)
        conn = sqlite3.connect(DATABASE_PATH); c = conn.cursor()
        c.execute('DELETE FROM admins WHERE user_id = ?', (uid,))
        conn.commit(); conn.close()
        await message.answer(f"✅ Removed: <code>{uid}</code>", reply_markup=get_back_kb(), parse_mode="HTML")
    except: await message.answer("❌ Invalid ID!", reply_markup=get_back_kb())

# ═══════════ BAN / UNBAN ═══════════
@dp.callback_query(F.data == "admin_ban_btn")
async def cb_ban(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in admin_ids: return
    await state.set_state(AdminStates.waiting_ban)
    text = "🚫 <b>BAN USER</b>\n\nSend USER ID 👇"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Cancel", callback_data="admin_panel")]])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@dp.message(AdminStates.waiting_ban)
async def proc_ban(message: types.Message, state: FSMContext):
    if message.from_user.id not in admin_ids: return
    await state.clear()
    try:
        uid = int(message.text.strip())
        if uid in admin_ids:
            await message.answer("❌ Cannot ban admin!", reply_markup=get_back_kb()); return
        banned_users.add(uid)
        kill_user_scripts(uid)
        conn = sqlite3.connect(DATABASE_PATH); c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO banned_users (user_id, banned_date, reason) VALUES (?, ?, ?)', (uid, datetime.now().isoformat(), "By admin"))
        conn.commit(); conn.close()
        await message.answer(f"🚫 Banned: <code>{uid}</code>", reply_markup=get_back_kb(), parse_mode="HTML")
    except: await message.answer("❌ Invalid ID!", reply_markup=get_back_kb())

@dp.callback_query(F.data == "admin_unban_btn")
async def cb_unban(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in admin_ids: return
    await state.set_state(AdminStates.waiting_unban)
    text = f"✅ <b>UNBAN</b>\n\nBanned: {len(banned_users)}\n\nSend USER ID:"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Cancel", callback_data="admin_panel")]])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@dp.message(AdminStates.waiting_unban)
async def proc_unban(message: types.Message, state: FSMContext):
    if message.from_user.id not in admin_ids: return
    await state.clear()
    try:
        uid = int(message.text.strip())
        banned_users.discard(uid)
        conn = sqlite3.connect(DATABASE_PATH); c = conn.cursor()
        c.execute('DELETE FROM banned_users WHERE user_id = ?', (uid,))
        conn.commit(); conn.close()
        await message.answer(f"✅ Unbanned: <code>{uid}</code>", reply_markup=get_back_kb(), parse_mode="HTML")
    except: await message.answer("❌ Invalid ID!", reply_markup=get_back_kb())

# ═══════════ ADD PREMIUM ═══════════
@dp.callback_query(F.data == "admin_add_premium_btn")
async def cb_add_prem(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in admin_ids: return
    await state.set_state(AdminStates.waiting_premium)
    text = "💎 <b>ADD PREMIUM</b>\n\n<b>Send in 2 lines:</b>\n<code>USER_ID\nDAYS</code>"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Cancel", callback_data="admin_panel")]])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@dp.message(AdminStates.waiting_premium)
async def proc_prem(message: types.Message, state: FSMContext):
    if message.from_user.id not in admin_ids: return
    await state.clear()
    try:
        lines = message.text.splitlines()
        uid = int(lines[0].strip()); days = int(lines[1].strip())
        expiry = datetime.now() + timedelta(days=days)
        user_subscriptions[uid] = {'expiry': expiry}
        conn = sqlite3.connect(DATABASE_PATH); c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO subscriptions (user_id, expiry) VALUES (?, ?)', (uid, expiry.isoformat()))
        conn.commit(); conn.close()
        await message.answer(f"✅ Premium!\n\nUser: <code>{uid}</code>\nDays: {days}\nExpires: {expiry.strftime('%Y-%m-%d')}", reply_markup=get_back_kb(), parse_mode="HTML")
    except: await message.answer("❌ Format: USER_ID (newline) DAYS", reply_markup=get_back_kb())

# ═══════════ CLEAN / BACKUP / IMPORT / LOGS / LOCK / RESTART ═══════════
@dp.callback_query(F.data == "admin_clean_files")
async def cb_clean(callback: types.CallbackQuery):
    if callback.from_user.id not in admin_ids: return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑️ Files > 30 Days", callback_data="clean_old")],
        [InlineKeyboardButton(text="🚫 Banned Users' Files", callback_data="clean_banned")],
        [InlineKeyboardButton(text="🧹 .log Files", callback_data="clean_logs")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="admin_panel")]
    ])
    await callback.message.edit_text("🧹 <b>CLEAN</b>", reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "clean_old")
async def cb_clean_old(callback: types.CallbackQuery):
    if callback.from_user.id not in admin_ids: return
    cutoff = datetime.now() - timedelta(days=30)
    removed = 0
    for ud in UPLOAD_BOTS_DIR.iterdir():
        if not ud.is_dir(): continue
        for f in ud.iterdir():
            if f.is_file() and datetime.fromtimestamp(f.stat().st_mtime) < cutoff:
                f.unlink(); removed += 1
    await callback.answer(f"✅ Removed {removed} files!", show_alert=True)

@dp.callback_query(F.data == "clean_banned")
async def cb_clean_ban(callback: types.CallbackQuery):
    if callback.from_user.id not in admin_ids: return
    removed = 0
    for uid in list(banned_users):
        d = UPLOAD_BOTS_DIR / str(uid)
        if d.exists(): shutil.rmtree(d); removed += 1
    await callback.answer(f"✅ Removed {removed} folders!", show_alert=True)

@dp.callback_query(F.data == "clean_logs")
async def cb_clean_logs(callback: types.CallbackQuery):
    if callback.from_user.id not in admin_ids: return
    removed = 0
    for ud in UPLOAD_BOTS_DIR.iterdir():
        if ud.is_dir():
            for log in ud.glob("*.log"): log.unlink(); removed += 1
    await callback.answer(f"✅ Removed {removed} logs!", show_alert=True)

@dp.callback_query(F.data == "admin_backup_db")
async def cb_backup(callback: types.CallbackQuery):
    if callback.from_user.id not in admin_ids: return
    try:
        bp = BACKUP_DIR / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        conn = sqlite3.connect(DATABASE_PATH); bconn = sqlite3.connect(bp)
        conn.backup(bconn); bconn.close(); conn.close()
        await callback.message.answer_document(FSInputFile(bp), caption=f"💾 DB Backup\n{datetime.now().strftime('%Y-%m-%d %H:%M')}")
        bp.unlink()
        await callback.answer("✅ Backup sent!")
    except Exception as e:
        await callback.answer(f"❌ {str(e)}", show_alert=True)

@dp.callback_query(F.data == "admin_import_db")
async def cb_import(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != OWNER_ID:
        await callback.answer("❌ Owner only!", show_alert=True); return
    await state.set_state(AdminStates.waiting_import_db)
    text = "📥 <b>IMPORT DB (Owner)</b>\n\n⚠️ Will REPLACE current DB & uploads!\n\n<b>Send:</b>\n• <code>bot_data.db</code> direct\n• OR <code>.zip</code> with db + uploads/\n\nAuto-restart after import."
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Cancel", callback_data="admin_panel")]])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@dp.message(AdminStates.waiting_import_db, F.document)
async def proc_import(message: types.Message, state: FSMContext):
    if message.from_user.id != OWNER_ID:
        await state.clear(); return
    fn = message.document.file_name
    ext = os.path.splitext(fn)[1].lower()
    if ext not in ['.db', '.zip']:
        await message.answer("❌ Send .db or .zip only!", reply_markup=get_back_kb()); return
    await state.clear()
    temp = IROTECH_DIR / f"import_{int(datetime.now().timestamp())}{ext}"
    try:
        st = await message.answer("⚙️ Importing...")
        await bot.download(message.document, destination=temp)
        old = BACKUP_DIR / f"before_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        if DATABASE_PATH.exists(): shutil.copy2(DATABASE_PATH, old)
        if ext == '.db':
            shutil.copy2(temp, DATABASE_PATH)
        else:
            with zipfile.ZipFile(temp, 'r') as z: z.extractall(IROTECH_DIR)
            for f in IROTECH_DIR.rglob("*.db"):
                shutil.copy2(f, DATABASE_PATH); break
            for folder in IROTECH_DIR.rglob("upload_bots"):
                if folder.is_dir():
                    if UPLOAD_BOTS_DIR.exists(): shutil.rmtree(UPLOAD_BOTS_DIR)
                    shutil.copytree(folder, UPLOAD_BOTS_DIR); break
        if temp.exists(): temp.unlink()
        await st.edit_text("✅ <b>DB Imported!</b>\n\n🔄 Restarting...")
        await asyncio.sleep(3)
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as e:
        await message.answer(f"❌ {escape(str(e))}", parse_mode="HTML")

@dp.callback_query(F.data == "admin_view_logs")
async def cb_logs(callback: types.CallbackQuery):
    if callback.from_user.id not in admin_ids: return
    lf = list(IROTECH_DIR.rglob("*.log"))[:5]
    text = f"📝 <b>LOGS</b>\n\nFound: {len(lf)} files\n"
    for l in lf: text += f"• <code>{escape(l.name)}</code>\n"
    await callback.message.edit_text(text, reply_markup=get_back_kb(), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "lock_bot")
async def cb_lock(callback: types.CallbackQuery):
    global bot_locked
    if callback.from_user.id not in admin_ids:
        await callback.answer("❌ Admin only!", show_alert=True); return
    bot_locked = not bot_locked
    await callback.answer(f"{'🔒 Locked' if bot_locked else '🔓 Unlocked'}!", show_alert=True)
    await callback_admin_panel(callback, None)

@dp.callback_query(F.data == "admin_restart_bot")
async def cb_restart(callback: types.CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        await callback.answer("❌ Owner only!", show_alert=True); return
    await callback.answer("🔄 Restarting...", show_alert=True)
    try:
        for sk, info in list(bot_scripts.items()):
            try:
                if info.get('log_file') and not info['log_file'].closed: info['log_file'].close()
                p = psutil.Process(info['process'].pid)
                for c in p.children(recursive=True): c.terminate()
                p.terminate()
            except: pass
        bot_scripts.clear()
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as e:
        await callback.message.answer(f"❌ {escape(str(e))}", parse_mode="HTML")

# ═══════════ WEB SERVER ═══════════
async def web_server():
    app = web.Application()
    async def handle(request):
        return web.Response(text=f"🚀 {BRANDING_NAME} running!")
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 5000)
    await site.start()
    logger.info("🌐 Web on port 5000")

# ═══════════ MAIN ═══════════
async def main():
    logger.info(f"🚀 Starting {BRANDING_NAME}...")
    asyncio.create_task(web_server())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


