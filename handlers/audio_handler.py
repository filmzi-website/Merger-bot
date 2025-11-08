import os
import time
from pyrogram.types import Message
from utils.ffmpeg_helper import FFmpegHelper
from utils.file_helper import FileHelper
from config import Config
import logging

logger = logging.getLogger(__name__)

class AudioHandler:
    def __init__(self, app, db):
        self.app = app
        self.db = db
        self.ffmpeg = FFmpegHelper()
        self.file_helper = FileHelper()
    
    async def handle_merge_audio(self, message: Message, session: dict):
        """Handle audio merging process"""
        user_id = message.from_user.id
        step = session.get("step", 1)
        
        try:
            if step == 1:
                # Receiving video file
                if not (message.video or message.document):
                    await message.reply_text("❌ Please send a valid video file!")
                    return
                
                file_size = message.video.file_size if message.video else message.document.file_size
                if file_size > Config.MAX_FILE_SIZE:
                    await message.reply_text(
                        f"❌ File size exceeds 4GB limit!\n"
                        f"Your file: {self.file_helper.format_size(file_size)}"
                    )
                    return
                
                status_msg = await message.reply_text("⏬ Downloading video file...")
                
                video_path = await self.file_helper.download_file(
                    self.app, message, status_msg
                )
                
                if not video_path:
                    await status_msg.edit_text("❌ Failed to download video!")
                    return
                
                session["step"] = 2
                session["video_path"] = video_path
                session["video_size"] = file_size
                
                await status_msg.edit_text(
                    "✅ Video downloaded successfully!\n\n"
                    "🎵 Now send your audio file"
                )
            
            elif step == 2:
                # Receiving audio file
                if not (message.audio or message.document):
                    await message.reply_text("❌ Please send a valid audio file!")
                    return
                
                status_msg = await message.reply_text("⏬ Downloading audio file...")
                
                audio_path = await self.file_helper.download_file(
                    self.app, message, status_msg
                )
                
                if not audio_path:
                    await status_msg.edit_text("❌ Failed to download audio!")
                    return
                
                await status_msg.edit_text("🔄 Merging audio to video...\nThis may take a while...")
                
                video_path = session.get("video_path")
                output_path = video_path.rsplit(".", 1)[0] + "_audio_merged.mp4"
                
                success = await self.ffmpeg.merge_audio(
                    video_path, audio_path, output_path, status_msg
                )
                
                if success and os.path.exists(output_path):
                    await status_msg.edit_text("📤 Uploading merged video...")
                    
                    try:
                        await self.app.send_video(
                            chat_id=user_id,
                            video=output_path,
                            caption="✅ **Audio merged successfully!**\n\n"
                                    f"📁 File size: {self.file_helper.format_size(os.path.getsize(output_path))}\n"
                                    f"⚡ Processed by @YourBotUsername",
                            progress=self.file_helper.upload_progress,
                            progress_args=(status_msg, time.time())
                        )
                        
                        await self.db.increment_stat(user_id, "videos_processed")
                        await self.db.increment_stat(user_id, "audio_merged")
                        await self.db.update_size_processed(user_id, session.get("video_size", 0))
                        
                        await status_msg.edit_text("✅ Video uploaded successfully!")
                        
                        try:
                            await self.app.send_message(
                                Config.LOG_CHANNEL,
                                f"✅ **Audio Merged**\n\n"
                                f"User: {message.from_user.mention}\n"
                                f"ID: `{user_id}`\n"
                                f"Size: {self.file_helper.format_size(session.get('video_size', 0))}"
                            )
                        except:
                            pass
                    
                    except Exception as e:
                        logger.error(f"Upload error: {e}")
                        await status_msg.edit_text(f"❌ Upload failed: {str(e)}")
                    
                    self.file_helper.cleanup_files([video_path, audio_path, output_path])
                else:
                    await status_msg.edit_text("❌ Failed to merge audio!")
                    self.file_helper.cleanup_files([video_path, audio_path])
                
                if user_id in self.app.user_sessions:
                    del self.app.user_sessions[user_id]
        
        except Exception as e:
            logger.error(f"Error in merge audio: {e}")
            await message.reply_text(f"❌ An error occurred: {str(e)}")
            if "video_path" in session:
                self.file_helper.cleanup_files([session.get("video_path")])
            if user_id in self.app.user_sessions:
                del self.app.user_sessions[user_id]
    
    async def handle_extract_audio(self, message: Message, session: dict):
        """Handle audio extraction process"""
        user_id = message.from_user.id
        
        try:
            if not (message.video or message.document):
                await message.reply_text("❌ Please send a valid video file!")
                return
            
            status_msg = await message.reply_text("⏬ Downloading video file...")
            
            video_path = await self.file_helper.download_file(
                self.app, message, status_msg
            )
            
            if not video_path:
                await status_msg.edit_text("❌ Failed to download video!")
                return
            
            await status_msg.edit_text("🎵 Extracting audio...")
            
            audio_path = video_path.rsplit(".", 1)[0] + ".mp3"
            success = await self.ffmpeg.extract_audio(video_path, audio_path)
            
            if success and os.path.exists(audio_path):
                try:
                    await self.app.send_audio(
                        chat_id=user_id,
                        audio=audio_path,
                        caption="✅ **Audio extracted successfully!**\n\n"
                                "⚡ Processed by @YourBotUsername"
                    )
                    
                    await self.db.increment_stat(user_id, "audio_extracted")
                    
                    await status_msg.edit_text("✅ Audio uploaded successfully!")
                    
                    try:
                        await self.app.send_message(
                            Config.LOG_CHANNEL,
                            f"✅ **Audio Extracted**\n\n"
                            f"User: {message.from_user.mention}\n"
                            f"ID: `{user_id}`"
                        )
                    except:
                        pass
                
                except Exception as e:
                    logger.error(f"Upload error: {e}")
                    await status_msg.edit_text(f"❌ Upload failed: {str(e)}")
                
                self.file_helper.cleanup_files([video_path, audio_path])
            else:
                await status_msg.edit_text("❌ Failed to extract audio!")
                self.file_helper.cleanup_files([video_path])
            
            if user_id in self.app.user_sessions:
                del self.app.user_sessions[user_id]
        
        except Exception as e:
            logger.error(f"Error in extract audio: {e}")
            await message.reply_text(f"❌ An error occurred: {str(e)}")
            if user_id in self.app.user_sessions:
                del self.app.user_sessions[user_id]
    
    async def handle_remove_audio(self, message: Message, session: dict):
        """Handle audio removal process"""
        user_id = message.from_user.id
        
        try:
            if not (message.video or message.document):
                await message.reply_text("❌ Please send a valid video file!")
                return
            
            file_size = message.video.file_size if message.video else message.document.file_size
            
            status_msg = await message.reply_text("⏬ Downloading video file...")
            
            video_path = await self.file_helper.download_file(
                self.app, message, status_msg
            )
            
            if not video_path:
                await status_msg.edit_text("❌ Failed to download video!")
                return
            
            await status_msg.edit_text("🔇 Removing audio from video...")
            
            output_path = video_path.rsplit(".", 1)[0] + "_no_audio.mp4"
            success = await self.ffmpeg.remove_audio(video_path, output_path, status_msg)
            
            if success and os.path.exists(output_path):
                await status_msg.edit_text("📤 Uploading video...")
                
                try:
                    await self.app.send_video(
                        chat_id=user_id,
                        video=output_path,
                        caption="✅ **Audio removed successfully!**\n\n"
                                f"📁 File size: {self.file_helper.format_size(os.path.getsize(output_path))}\n"
                                f"⚡ Processed by @YourBotUsername",
                        progress=self.file_helper.upload_progress,
                        progress_args=(status_msg, time.time())
                    )
                    
                    await self.db.increment_stat(user_id, "videos_processed")
                    await self.db.increment_stat(user_id, "audio_removed")
                    await self.db.update_size_processed(user_id, file_size)
                    
                    await status_msg.edit_text("✅ Video uploaded successfully!")
                    
                    try:
                        await self.app.send_message(
                            Config.LOG_CHANNEL,
                            f"✅ **Audio Removed**\n\n"
                            f"User: {message.from_user.mention}\n"
                            f"ID: `{user_id}`\n"
                            f"Size: {self.file_helper.format_size(file_size)}"
                        )
                    except:
                        pass
                
                except Exception as e:
                    logger.error(f"Upload error: {e}")
                    await status_msg.edit_text(f"❌ Upload failed: {str(e)}")
                
                self.file_helper.cleanup_files([video_path, output_path])
            else:
                await status_msg.edit_text("❌ Failed to remove audio!")
                self.file_helper.cleanup_files([video_path])
            
            if user_id in self.app.user_sessions:
                del self.app.user_sessions[user_id]
        
        except Exception as e:
            logger.error(f"Error in remove audio: {e}")
            await message.reply_text(f"❌ An error occurred: {str(e)}")
            if user_id in self.app.user_sessions:
                del self.app.user_sessions[user_id]
