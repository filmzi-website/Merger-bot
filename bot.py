import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import handlers
from handlers.video_handler import VideoHandler
from handlers.audio_handler import AudioHandler
from handlers.subtitle_handler import SubtitleHandler
from handlers.admin_handler import AdminHandler
from handlers.broadcast_handler import BroadcastHandler
from database.database import Database
from config import Config

class MediaBot:
    def __init__(self):
        self.app = Client(
            "media_bot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            workers=50,
            sleep_threshold=10
        )
        
        # Initialize database
        self.db = Database()
        
        # Initialize handlers
        self.video_handler = VideoHandler(self.app, self.db)
        self.audio_handler = AudioHandler(self.app, self.db)
        self.subtitle_handler = SubtitleHandler(self.app, self.db)
        self.admin_handler = AdminHandler(self.app, self.db)
        self.broadcast_handler = BroadcastHandler(self.app, self.db)
        
        # User sessions for multi-file operations
        self.user_sessions = {}
        
    async def start(self):
        """Start the bot"""
        await self.db.connect()
        await self.app.start()
        logger.info("Bot started successfully!")
        
        # Send startup message to log channel
        try:
            await self.app.send_message(
                Config.LOG_CHANNEL,
                "🤖 **Bot Started Successfully!**\n\n"
                f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        except Exception as e:
            logger.error(f"Failed to send startup message: {e}")
        
        await asyncio.Event().wait()
        
    async def stop(self):
        """Stop the bot"""
        await self.app.stop()
        await self.db.close()
        logger.info("Bot stopped!")

# Initialize bot
bot = MediaBot()

# ============ START COMMAND ============
@bot.app.on_message(filters.command("start") & filters.private)
async def start_command(client, message: Message):
    user_id = message.from_user.id
    
    # Add user to database
    await bot.db.add_user(user_id, message.from_user.first_name)
    
    # Log to channel
    try:
        await client.send_message(
            Config.LOG_CHANNEL,
            f"👤 **New User Started Bot**\n\n"
            f"User: {message.from_user.mention}\n"
            f"ID: `{user_id}`\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
    except:
        pass
    
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎬 Merge Subtitle", callback_data="merge_sub"),
            InlineKeyboardButton("📤 Extract Subtitle", callback_data="extract_sub")
        ],
        [
            InlineKeyboardButton("🎵 Merge Audio", callback_data="merge_audio"),
            InlineKeyboardButton("🔇 Remove Audio", callback_data="remove_audio")
        ],
        [
            InlineKeyboardButton("📤 Extract Audio", callback_data="extract_audio")
        ],
        [
            InlineKeyboardButton("ℹ️ Help", callback_data="help"),
            InlineKeyboardButton("📊 Stats", callback_data="stats")
        ]
    ])
    
    await message.reply_text(
        f"👋 **Welcome {message.from_user.first_name}!**\n\n"
        "🎥 **Professional Media Processing Bot**\n\n"
        "**Features:**\n"
        "✅ Merge subtitles to video (SRT, ASS, VTT)\n"
        "✅ Extract subtitles from video\n"
        "✅ Merge audio to video\n"
        "✅ Extract audio from video\n"
        "✅ Remove audio from video\n"
        "✅ Support files up to 4GB\n"
        "✅ Batch processing support\n\n"
        "🚀 **Choose an option below to get started!**",
        reply_markup=buttons
    )

# ============ HELP COMMAND ============
@bot.app.on_message(filters.command("help") & filters.private)
async def help_command(client, message: Message):
    help_text = """
📖 **Bot Usage Guide**

**Merge Subtitle to Video:**
1. Click "Merge Subtitle" button
2. Send your video file
3. Send your subtitle file (SRT/ASS/VTT)
4. Bot will merge and send back

**Extract Subtitle from Video:**
1. Click "Extract Subtitle" button
2. Send your video file with subtitles
3. Choose subtitle format
4. Bot will extract and send

**Merge Audio to Video:**
1. Click "Merge Audio" button
2. Send your video file
3. Send your audio file
4. Bot will merge and send back

**Extract Audio from Video:**
1. Click "Extract Audio" button
2. Send your video file
3. Choose audio format (MP3/AAC/etc)
4. Bot will extract and send

**Remove Audio from Video:**
1. Click "Remove Audio" button
2. Send your video file
3. Bot will remove audio and send back

**Batch Processing:**
- Send multiple files for batch processing
- Use /cancel to stop current operation

**File Limits:**
- Maximum file size: 4GB
- Supported video formats: MP4, MKV, AVI, MOV, etc.
- Supported subtitle formats: SRT, ASS, VTT
- Supported audio formats: MP3, AAC, WAV, FLAC, etc.

**Commands:**
/start - Start the bot
/help - Show this help message
/stats - Show your statistics
/cancel - Cancel current operation
"""
    await message.reply_text(help_text)

# ============ STATS COMMAND ============
@bot.app.on_message(filters.command("stats") & filters.private)
async def stats_command(client, message: Message):
    user_id = message.from_user.id
    user_stats = await bot.db.get_user_stats(user_id)
    
    if user_stats:
        stats_text = f"""
📊 **Your Statistics**

👤 User: {message.from_user.mention}
🆔 User ID: `{user_id}`

**Usage Stats:**
🎬 Videos Processed: {user_stats.get('videos_processed', 0)}
📝 Subtitles Merged: {user_stats.get('subtitles_merged', 0)}
📤 Subtitles Extracted: {user_stats.get('subtitles_extracted', 0)}
🎵 Audio Merged: {user_stats.get('audio_merged', 0)}
📤 Audio Extracted: {user_stats.get('audio_extracted', 0)}
🔇 Audio Removed: {user_stats.get('audio_removed', 0)}

📅 Joined: {user_stats.get('joined_date', 'Unknown')}
"""
    else:
        stats_text = "No statistics available yet. Start using the bot!"
    
    await message.reply_text(stats_text)

# ============ CANCEL COMMAND ============
@bot.app.on_message(filters.command("cancel") & filters.private)
async def cancel_command(client, message: Message):
    user_id = message.from_user.id
    if user_id in bot.user_sessions:
        del bot.user_sessions[user_id]
        await message.reply_text("❌ Current operation cancelled!")
    else:
        await message.reply_text("No active operation to cancel.")

# ============ CALLBACK QUERY HANDLER ============
@bot.app.on_callback_query()
async def callback_handler(client, callback_query):
    data = callback_query.data
    user_id = callback_query.from_user.id
    
    if data == "help":
        await callback_query.message.edit_text(
            "📖 **Help Section**\n\n"
            "Use /help command for detailed usage guide.\n\n"
            "For support, contact admin.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="back_to_main")
            ]])
        )
    
    elif data == "stats":
        user_stats = await bot.db.get_user_stats(user_id)
        stats_text = f"""
📊 **Quick Stats**

🎬 Videos: {user_stats.get('videos_processed', 0)}
📝 Subtitles: {user_stats.get('subtitles_merged', 0)}
🎵 Audio: {user_stats.get('audio_merged', 0)}
"""
        await callback_query.answer(stats_text, show_alert=True)
    
    elif data == "merge_sub":
        bot.user_sessions[user_id] = {"action": "merge_subtitle", "step": 1}
        await callback_query.message.reply_text(
            "📤 **Merge Subtitle to Video**\n\n"
            "Please send your video file (up to 4GB)\n\n"
            "Use /cancel to stop this operation."
        )
        await callback_query.answer()
    
    elif data == "extract_sub":
        bot.user_sessions[user_id] = {"action": "extract_subtitle", "step": 1}
        await callback_query.message.reply_text(
            "📤 **Extract Subtitle from Video**\n\n"
            "Please send your video file\n\n"
            "Use /cancel to stop this operation."
        )
        await callback_query.answer()
    
    elif data == "merge_audio":
        bot.user_sessions[user_id] = {"action": "merge_audio", "step": 1}
        await callback_query.message.reply_text(
            "🎵 **Merge Audio to Video**\n\n"
            "Please send your video file (up to 4GB)\n\n"
            "Use /cancel to stop this operation."
        )
        await callback_query.answer()
    
    elif data == "extract_audio":
        bot.user_sessions[user_id] = {"action": "extract_audio", "step": 1}
        await callback_query.message.reply_text(
            "📤 **Extract Audio from Video**\n\n"
            "Please send your video file\n\n"
            "Use /cancel to stop this operation."
        )
        await callback_query.answer()
    
    elif data == "remove_audio":
        bot.user_sessions[user_id] = {"action": "remove_audio", "step": 1}
        await callback_query.message.reply_text(
            "🔇 **Remove Audio from Video**\n\n"
            "Please send your video file\n\n"
            "Use /cancel to stop this operation."
        )
        await callback_query.answer()
    
    elif data == "back_to_main":
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🎬 Merge Subtitle", callback_data="merge_sub"),
                InlineKeyboardButton("📤 Extract Subtitle", callback_data="extract_sub")
            ],
            [
                InlineKeyboardButton("🎵 Merge Audio", callback_data="merge_audio"),
                InlineKeyboardButton("🔇 Remove Audio", callback_data="remove_audio")
            ],
            [
                InlineKeyboardButton("📤 Extract Audio", callback_data="extract_audio")
            ],
            [
                InlineKeyboardButton("ℹ️ Help", callback_data="help"),
                InlineKeyboardButton("📊 Stats", callback_data="stats")
            ]
        ])
        
        await callback_query.message.edit_text(
            f"👋 **Welcome {callback_query.from_user.first_name}!**\n\n"
            "🎥 **Professional Media Processing Bot**\n\n"
            "🚀 **Choose an option below:**",
            reply_markup=buttons
        )
        await callback_query.answer()

# ============ DOCUMENT HANDLER ============
@bot.app.on_message(filters.document | filters.video)
async def document_handler(client, message: Message):
    user_id = message.from_user.id
    
    # Check if user has active session
    if user_id not in bot.user_sessions:
        await message.reply_text(
            "Please select an operation first using /start command."
        )
        return
    
    session = bot.user_sessions[user_id]
    action = session.get("action")
    
    # Route to appropriate handler
    if action == "merge_subtitle":
        await bot.subtitle_handler.handle_merge_subtitle(message, session)
    elif action == "extract_subtitle":
        await bot.subtitle_handler.handle_extract_subtitle(message, session)
    elif action == "merge_audio":
        await bot.audio_handler.handle_merge_audio(message, session)
    elif action == "extract_audio":
        await bot.audio_handler.handle_extract_audio(message, session)
    elif action == "remove_audio":
        await bot.audio_handler.handle_remove_audio(message, session)

if __name__ == "__main__":
    bot.app.run(bot.start())
