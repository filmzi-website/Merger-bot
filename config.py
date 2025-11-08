# FILE 1: config.py
# Save this as: config.py

import os
from dotenv import load_dotenv

load_dotenv()

# ========== BOT CREDENTIALS ==========
BOT_TOKEN = os.getenv('BOT_TOKEN', '')
API_ID = int(os.getenv('API_ID', '0'))
API_HASH = os.getenv('API_HASH', '')

# ========== ADMIN SETTINGS ==========
ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]
LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL_ID', '0'))

# ========== MONGODB SETTINGS ==========
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'telegram_media_bot')

# ========== FILE SETTINGS ==========
DOWNLOAD_PATH = "./downloads"
OUTPUT_PATH = "./output"
MAX_FILE_SIZE = 4 * 1024 * 1024 * 1024  # 4GB

# ========== SUPPORTED FORMATS ==========
VIDEO_FORMATS = ['.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv', '.wmv', '.m4v']
AUDIO_FORMATS = ['.mp3', '.aac', '.wav', '.m4a', '.ogg', '.flac', '.wma', '.opus']
SUBTITLE_FORMATS = ['.srt', '.ass', '.vtt', '.sub', '.ssa']

# ========== FEATURE FLAGS ==========
ENABLE_STATS = True
ENABLE_USER_LIMITS = True
FREE_USER_DAILY_LIMIT = 5
PREMIUM_USER_DAILY_LIMIT = 50

# ========== MESSAGES ==========
WELCOME_MESSAGE = """
🎬 <b>Professional Media Processor Bot v3.0</b>

<b>✨ Complete Features:</b>
📝 Merge subtitles to video
📤 Extract subtitles from video
🎵 Extract audio from video
🔇 Remove audio from video
🎶 Merge audio to video
🔄 Replace audio in video

<b>📊 Your Stats:</b>
Operations today: {operations_today}/{daily_limit}
Total operations: {total_operations}
Member since: {join_date}

Choose an operation below! 👇
"""
