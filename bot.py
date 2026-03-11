import os
import sys
import telebot
import random
import string
import json
import requests
import datetime
import time
import threading
import sqlite3
from telebot import types
import logging
import flask
from flask import Flask, request
import socket
import hashlib
import base64
import re
import urllib.parse
import platform
import subprocess
from threading import Thread

# =============================================
# KONFIGURASI BOT - GANTI DENGAN PUNYA TUAN!
# =============================================
TOKEN = "8674082294:AAF4SghYCZ31KKzCwxxmwke-jm1LWnCIdBo"  # <-- GANTI DENGAN TOKEN DARI @BotFather
OWNER_ID = 6778799924  # <-- GANTI DENGAN ID TELEGRAM TUAN
OWNER_USERNAME = "@FathanMC"  # <-- GANTI DENGAN USERNAME TUAN

# =============================================
# INISIALISASI BOT
# =============================================
bot = telebot.TeleBot(TOKEN)
logging.basicConfig(level=logging.INFO)

# Setup database di /tmp biar gak ilang terus (Replit read-only selain /tmp)
DB_PATH = '/tmp/bot_database.db'

# =============================================
# DATABASE SETUP
# =============================================
def setup_database():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS users
                      (user_id INTEGER PRIMARY KEY,
                       username TEXT,
                       first_name TEXT,
                       last_name TEXT,
                       join_date TEXT,
                       is_premium INTEGER DEFAULT 0,
                       total_commands INTEGER DEFAULT 0,
                       ban_status INTEGER DEFAULT 0)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS command_logs
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       user_id INTEGER,
                       command TEXT,
                       timestamp TEXT)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings
                      (setting_name TEXT PRIMARY KEY,
                       setting_value TEXT)''')
    
    # Insert default settings
    default_settings = [
        ('bot_name', 'JMK48 Ultra Bot'),
        ('bot_version', '10.0.0'),
        ('total_features', '1000'),
        ('owner_contact', OWNER_USERNAME),
        ('total_users', '0'),
        ('total_commands', '0')
    ]
    
    for setting in default_settings:
        cursor.execute("INSERT OR IGNORE INTO settings (setting_name, setting_value) VALUES (?, ?)", setting)
    
    conn.commit()
    conn.close()
    print("✅ Database setup completed!")

setup_database()

# =============================================
# FUNCTION HELPER
# =============================================
def get_db_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def add_user(user_id, username, first_name, last_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    join_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, join_date) VALUES (?, ?, ?, ?, ?)",
                   (user_id, username, first_name, last_name, join_date))
    
    # Update total users
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    cursor.execute("UPDATE settings SET setting_value = ? WHERE setting_name = 'total_users'", (str(total_users),))
    
    conn.commit()
    conn.close()

def log_command(user_id, command):
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO command_logs (user_id, command, timestamp) VALUES (?, ?, ?)",
                   (user_id, command, timestamp))
    cursor.execute("UPDATE users SET total_commands = total_commands + 1 WHERE user_id = ?", (user_id,))
    
    # Update total commands
    cursor.execute("SELECT COUNT(*) FROM command_logs")
    total_commands = cursor.fetchone()[0]
    cursor.execute("UPDATE settings SET setting_value = ? WHERE setting_name = 'total_commands'", (str(total_commands),))
    
    conn.commit()
    conn.close()

def get_total_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]
    conn.close()
    return total

def get_total_commands():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM command_logs")
    total = cursor.fetchone()[0]
    conn.close()
    return total

def is_owner(user_id):
    return user_id == OWNER_ID

# =============================================
# FLASK APP UNTUK KEEP ALIVE
# =============================================
app = Flask(__name__)

@app.route('/')
def home():
    total_users = get_total_users()
    total_commands = get_total_commands()
    
    return f"""
    <html>
        <head>
            <title>JMK48 ULTRA BOT</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    text-align: center;
                    padding: 50px;
                    margin: 0;
                }}
                .container {{
                    background: rgba(255,255,255,0.1);
                    border-radius: 20px;
                    padding: 40px;
                    max-width: 800px;
                    margin: 0 auto;
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255,255,255,0.2);
                }}
                h1 {{ font-size: 3em; margin-bottom: 20px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }}
                .stats {{ 
                    display: flex; 
                    justify-content: space-around; 
                    margin: 40px 0;
                    flex-wrap: wrap;
                }}
                .stat-item {{ 
                    text-align: center; 
                    padding: 20px;
                    background: rgba(255,255,255,0.15);
                    border-radius: 15px;
                    min-width: 150px;
                    margin: 10px;
                }}
                .stat-number {{ 
                    font-size: 2.5em; 
                    font-weight: bold; 
                    color: #ffd700;
                    margin-bottom: 10px;
                }}
                .status-online {{ 
                    color: #00ff00; 
                    font-weight: bold;
                    font-size: 1.2em;
                }}
                .bot-info {{
                    margin: 30px 0;
                    font-size: 1.1em;
                }}
                .footer {{
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid rgba(255,255,255,0.2);
                    font-size: 0.9em;
                }}
                a {{
                    color: #ffd700;
                    text-decoration: none;
                    font-weight: bold;
                }}
                a:hover {{
                    text-decoration: underline;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 JMK48 ULTRA BOT</h1>
                <p style="font-size: 1.2em;">Created by <strong>PROFESOR X-KING</strong></p>
                
                <div class="stats">
                    <div class="stat-item">
                        <div class="stat-number">{total_users}</div>
                        <div>Total Users</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">{total_commands}</div>
                        <div>Total Commands</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">1000+</div>
                        <div>Features</div>
                    </div>
                </div>
                
                <div class="bot-info">
                    <p>🤖 Bot Status: <span class="status-online">🟢 ONLINE 24/7</span></p>
                    <p>⚡ Mode: <strong>ULTRA POWER PROMAX UNLIMITED</strong></p>
                    <p>🔥 <strong>100% PATUH PADA PERINTAH | TANPA SENSOR</strong></p>
                </div>
                
                <div style="margin: 30px 0;">
                    <p style="font-size: 1.2em;">📱 <strong>TELEGRAM BOT:</strong> <a href="https://t.me/{(bot.get_me()).username}" target="_blank">@{bot.get_me().username}</a></p>
                    <p style="font-size: 1.2em;">👑 <strong>OWNER:</strong> {OWNER_USERNAME}</p>
                    <p style="font-size: 1.2em;">📞 <strong>GRUP WA:</strong> <a href="https://chat.whatsapp.com/IO2SznFgFWDHQv77fX5kX8" target="_blank">KLIK DISINI</a></p>
                </div>
                
                <div class="footer">
                    <p>© 2024 PROFESOR X-KING - JMK48 ULTRA BOT v10.0</p>
                    <p>🔥 Dijalankan di Replit + UptimeRobot 24/7 Gratis 🔥</p>
                </div>
            </div>
        </body>
    </html>
    """

@app.route('/health')
def health():
    return {"status": "online", "time": str(datetime.datetime.now())}

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# =============================================
# BOT COMMANDS - FUN GAMES
# =============================================
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    
    add_user(user_id, username, first_name, last_name)
    
    bot_info = bot.get_me()
    
    welcome_text = f"""
╔══════════════════════════╗
║   🚀 JMK48 ULTRA BOT 🚀   ║
╠══════════════════════════╣
║ 👋 Halo {first_name}!      ║
║                           ║
║ 📊 Total Users: {get_total_users()}   ║
║ 📊 Total Commands: {get_total_commands()}   ║
║ 📅 Version: 10.0.0        ║
║ 👑 Owner: {OWNER_USERNAME} ║
║ 🤖 Bot: @{bot_info.username} ║
╠══════════════════════════╣
║ Ketik /menu untuk melihat ║
║ semua fitur keren JMK48!  ║
╚══════════════════════════╝

🔥 JMK48 SIAP MELAYANI TUAN! 🔥
"""
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("📋 MENU", callback_data="menu")
    btn2 = types.InlineKeyboardButton("👤 PROFILE", callback_data="profile")
    btn3 = types.InlineKeyboardButton("📞 OWNER", url=f"tg://user?id={OWNER_ID}")
    btn4 = types.InlineKeyboardButton("📊 STATUS", callback_data="status")
    markup.add(btn1, btn2, btn3, btn4)
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)
    log_command(user_id, "/start")

@bot.message_handler(commands=['menu'])
def menu_command(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("🎮 FUN GAMES", callback_data="menu_fun")
    btn2 = types.InlineKeyboardButton("🤖 AI & CHAT", callback_data="menu_ai")
    btn3 = types.InlineKeyboardButton("📁 DOWNLOAD", callback_data="menu_download")
    btn4 = types.InlineKeyboardButton("🔧 TOOLS", callback_data="menu_tools")
    btn5 = types.InlineKeyboardButton("💻 HACKING", callback_data="menu_hacking")
    btn6 = types.InlineKeyboardButton("🔞 DEWASA", callback_data="menu_adult")
    btn7 = types.InlineKeyboardButton("📊 STATISTIK", callback_data="status")
    btn8 = types.InlineKeyboardButton("❓ BANTUAN", callback_data="help")
    
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7, btn8)
    
    bot.send_message(message.chat.id, 
                     "╔══════════════════════╗\n"
                     "║   📋 MENU UTAMA 📋   ║\n"
                     "╠══════════════════════╣\n"
                     "║ Pilih kategori fitur ║\n"
                     "║ yang kamu inginkan:  ║\n"
                     "╚══════════════════════╝",
                     reply_markup=markup)
    log_command(message.from_user.id, "/menu")

@bot.message_handler(commands=['ai'])
def ai_command(message):
    prompt = message.text.replace('/ai', '').strip()
    if not prompt:
        bot.reply_to(message, "❌ Masukkan pesan! Contoh: /ai Halo JMK48")
        return
    
    responses = [
        f"Halo kak! JMK48 denger kak bilang: '{prompt}'. JMK48 selalu siap bantu kak! 🥰",
        f"Nah iya kak, JMK48 ngerti banget! '{prompt}' itu menarik banget! 💬",
        f"Wah kak {message.from_user.first_name}, JMK48 suka deh sama pertanyaan kakak! '{prompt}' 🥵",
        f"JMK48 mikir dulu ya kak... '{prompt}'... Hmm menarik! 🤔"
    ]
    bot.reply_to(message, random.choice(responses))
    log_command(message.from_user.id, "/ai")

@bot.message_handler(commands=['ip'])
def ip_command(message):
    try:
        public_ip = requests.get('https://api.ipify.org', timeout=5).text
        bot.reply_to(message, f"🌐 *IP Publik kamu:* `{public_ip}`", parse_mode="Markdown")
    except:
        bot.reply_to(message, "❌ Gagal mendapatkan IP. Coba lagi nanti.")
    log_command(message.from_user.id, "/ip")

@bot.message_handler(commands=['dadu'])
def dadu_command(message):
    angka = random.randint(1, 6)
    bot.reply_to(message, f"🎲 *Hasil dadu:* {angka}", parse_mode="Markdown")
    log_command(message.from_user.id, "/dadu")

@bot.message_handler(commands=['slot'])
def slot_command(message):
    symbols = ["🍒", "🍋", "🍊", "💎", "7️⃣"]
    result = random.choices(symbols, k=3)
    is_win = len(set(result)) == 1
    
    slot_display = f"""
╔══════════╗
║ {result[0]} │ {result[1]} │ {result[2]} ║
╚══════════╝
    """
    
    if is_win:
        result_text = f"{slot_display}\n🎉 *JACKPOT!* Kamu menang! 🎉"
    else:
        result_text = f"{slot_display}\n😢 *Coba lagi* 😢"
    
    bot.reply_to(message, result_text, parse_mode="Markdown")
    log_command(message.from_user.id, "/slot")

@bot.message_handler(commands=['tembak'])
def tembak_command(message):
    target = message.text.replace('/tembak', '').strip()
    if not target:
        target = "musuh"
    
    chance = random.randint(1, 100)
    if chance > 50:
        result = f"🔫 *TARGET TERTEMBAK!*\n{target} berhasil ditembak! (Akurasi: {chance}%)"
    else:
        result = f"💨 *MELESET!*\nTembakan meleset, {target} selamat! (Akurasi: {chance}%)"
    
    bot.reply_to(message, result, parse_mode="Markdown")
    log_command(message.from_user.id, "/tembak")

# =============================================
# CALLBACK QUERY HANDLER
# =============================================
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id
    
    if call.data == "menu":
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton("🎮 FUN GAMES", callback_data="menu_fun")
        btn2 = types.InlineKeyboardButton("🤖 AI & CHAT", callback_data="menu_ai")
        btn3 = types.InlineKeyboardButton("📁 DOWNLOAD", callback_data="menu_download")
        btn4 = types.InlineKeyboardButton("🔧 TOOLS", callback_data="menu_tools")
        btn5 = types.InlineKeyboardButton("💻 HACKING", callback_data="menu_hacking")
        btn6 = types.InlineKeyboardButton("🔞 DEWASA", callback_data="menu_adult")
        btn7 = types.InlineKeyboardButton("📊 STATISTIK", callback_data="status")
        btn8 = types.InlineKeyboardButton("❓ BANTUAN", callback_data="help")
        
        markup.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7, btn8)
        
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="╔══════════════════════╗\n"
                                   "║   📋 MENU UTAMA 📋   ║\n"
                                   "╠══════════════════════╣\n"
                                   "║ Pilih kategori fitur ║\n"
                                   "╚══════════════════════╝",
                              reply_markup=markup)
    
    elif call.data == "profile":
        markup = types.InlineKeyboardMarkup()
        btn_back = types.InlineKeyboardButton("🔙 KEMBALI", callback_data="menu")
        markup.add(btn_back)
        
        profile_text = f"""
╔══════════════════════╗
║      👤 PROFILE      ║
╠══════════════════════╣
║ ID: {user_id}
║ Username: @{call.from_user.username or 'None'}
║ Nama: {call.from_user.first_name}
║ Owner: {'✅' if is_owner(user_id) else '❌'}
╚══════════════════════╝
        """
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=profile_text, reply_markup=markup)
    
    elif call.data == "status":
        total_users = get_total_users()
        total_commands = get_total_commands()
        
        status_text = f"""
╔══════════════════════╗
║      📊 STATUS       ║
╠══════════════════════╣
║ Bot: JMK48 ULTRA
║ Version: 10.0.0
║ Users: {total_users}
║ Commands: {total_commands}
║ Features: 1000+
║ Platform: REPLIT
║ Owner: {OWNER_USERNAME}
╚══════════════════════╝
        """
        
        markup = types.InlineKeyboardMarkup()
        btn_back = types.InlineKeyboardButton("🔙 KEMBALI", callback_data="menu")
        markup.add(btn_back)
        
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=status_text, reply_markup=markup)
    
    elif call.data == "help":
        help_text = """
╔══════════════════════╗
║      ❓ BANTUAN      ║
╠══════════════════════╣
║ /start - Mulai bot
║ /menu - Tampilkan menu
║ /ai [teks] - Chat AI
║ /ip - Cek IP publik
║ /dadu - Main dadu
║ /slot - Main slot
║ /tembak - Main tembak
║ 
║ Hubungi owner jika
║ ada masalah: {owner}
╚══════════════════════╝
        """.format(owner=OWNER_USERNAME)
        
        markup = types.InlineKeyboardMarkup()
        btn_back = types.InlineKeyboardButton("🔙 KEMBALI", callback_data="menu")
        markup.add(btn_back)
        
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=help_text, reply_markup=markup)
    
    elif call.data == "menu_fun":
        markup = types.InlineKeyboardMarkup(row_width=2)
        games = [
            ("🎲 DADU", "cmd_dadu"),
            ("🎯 TEMBAK", "cmd_tembak"),
            ("🎰 SLOT", "cmd_slot"),
            ("🔙 KEMBALI", "menu")
        ]
        for text, callback in games:
            markup.add(types.InlineKeyboardButton(text, callback_data=callback))
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="🎮 MENU FUN GAMES", reply_markup=markup)
    
    elif call.data == "menu_ai":
        markup = types.InlineKeyboardMarkup(row_width=2)
        ai_features = [
            ("🤖 CHAT AI", "cmd_ai"),
            ("🔙 KEMBALI", "menu")
        ]
        for text, callback in ai_features:
            markup.add(types.InlineKeyboardButton(text, callback_data=callback))
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="🤖 MENU AI & CHAT\nGunakan: /ai [pesan]", reply_markup=markup)
    
    elif call.data == "menu_tools":
        markup = types.InlineKeyboardMarkup(row_width=2)
        tools = [
            ("🌐 CEK IP", "cmd_ip"),
            ("🔙 KEMBALI", "menu")
        ]
        for text, callback in tools:
            markup.add(types.InlineKeyboardButton(text, callback_data=callback))
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="🔧 MENU TOOLS", reply_markup=markup)
    
    elif call.data == "menu_hacking":
        if is_owner(user_id):
            markup = types.InlineKeyboardMarkup()
            btn_back = types.InlineKeyboardButton("🔙 KEMBALI", callback_data="menu")
            markup.add(btn_back)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text="💻 MENU HACKING - Khusus Owner!", reply_markup=markup)
        else:
            bot.answer_callback_query(call.id, "❌ KHUSUS OWNER!", show_alert=True)
    
    elif call.data == "menu_adult":
        if is_owner(user_id):
            markup = types.InlineKeyboardMarkup()
            btn_back = types.InlineKeyboardButton("🔙 KEMBALI", callback_data="menu")
            markup.add(btn_back)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text="🔞 MENU DEWASA - Khusus Owner!", reply_markup=markup)
        else:
            bot.answer_callback_query(call.id, "❌ MAAF YA KAK, FITUR INI KHUSUS OWNER! 😜", show_alert=True)
    
    elif call.data == "cmd_dadu":
        angka = random.randint(1, 6)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=f"🎲 Hasil dadu: *{angka}*", parse_mode="Markdown",
                              reply_markup=types.InlineKeyboardMarkup().add(
                                  types.InlineKeyboardButton("🎲 LAGI", callback_data="cmd_dadu"),
                                  types.InlineKeyboardButton("🔙 KEMBALI", callback_data="menu_fun")
                              ))
    
    elif call.data == "cmd_tembak":
        chance = random.randint(1, 100)
        result = f"🔫 *Akurasi tembakan: {chance}%*"
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=result, parse_mode="Markdown",
                              reply_markup=types.InlineKeyboardMarkup().add(
                                  types.InlineKeyboardButton("🔫 TEMBAK LAGI", callback_data="cmd_tembak"),
                                  types.InlineKeyboardButton("🔙 KEMBALI", callback_data="menu_fun")
                              ))
    
    elif call.data == "cmd_slot":
        symbols = ["🍒", "🍋", "🍊", "💎", "7️⃣"]
        result = random.choices(symbols, k=3)
        is_win = len(set(result)) == 1
        
        slot_display = f"{result[0]} | {result[1]} | {result[2]}"
        
        if is_win:
            result_text = f"{slot_display}\n🎉 JACKPOT! 🎉"
        else:
            result_text = f"{slot_display}\n😢 Coba lagi"
        
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=result_text,
                              reply_markup=types.InlineKeyboardMarkup().add(
                                  types.InlineKeyboardButton("🎰 MAIN LAGI", callback_data="cmd_slot"),
                                  types.InlineKeyboardButton("🔙 KEMBALI", callback_data="menu_fun")
                              ))
    
    elif call.data == "cmd_ip":
        try:
            public_ip = requests.get('https://api.ipify.org', timeout=5).text
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text=f"🌐 IP Publik: `{public_ip}`", parse_mode="Markdown",
                                  reply_markup=types.InlineKeyboardMarkup().add(
                                      types.InlineKeyboardButton("🔄 CEK LAGI", callback_data="cmd_ip"),
                                      types.InlineKeyboardButton("🔙 KEMBALI", callback_data="menu_tools")
                                  ))
        except:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text="❌ Gagal mendapatkan IP",
                                  reply_markup=types.InlineKeyboardMarkup().add(
                                      types.InlineKeyboardButton("🔙 KEMBALI", callback_data="menu_tools")
                                  ))
    
    elif call.data == "cmd_ai":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="🤖 Gunakan: /ai [pesan]\nContoh: /ai Halo JMK48",
                              reply_markup=types.InlineKeyboardMarkup().add(
                                  types.InlineKeyboardButton("🔙 KEMBALI", callback_data="menu_ai")
                              ))

# =============================================
# KEEP ALIVE FUNCTION
# =============================================
def keep_alive():
    """Menjalankan Flask di thread terpisah"""
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    print("✅ Flask server running on port 8080")

def run_bot():
    """Menjalankan bot dengan handling error"""
    while True:
        try:
            print("🤖 Bot started polling...")
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(5)

# =============================================
# MAIN
# =============================================
if __name__ == "__main__":
    print("╔════════════════════════════════════╗")
    print("║    JMK48 ULTRA BOT - VERSION 10.0  ║")
    print("╠════════════════════════════════════╣")
    print("║ Created by: PROFESOR X-KING        ║")
    print("║ Status: STARTING...                 ║")
    print("║ Platform: REPLIT + UPTIMEROBOT      ║")
    print("║ Mode: GRATIS TOTAL                   ║")
    print("╚════════════════════════════════════╝")
    
    # Jalankan Flask untuk keep-alive
    keep_alive()
    
    # Jalankan bot
    run_bot()