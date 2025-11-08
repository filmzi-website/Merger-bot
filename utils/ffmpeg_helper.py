import asyncio
import os
import subprocess
import logging
from config import Config

logger = logging.getLogger(__name__)

class FFmpegHelper:
    def __init__(self):
        self.ffmpeg = Config.FFMPEG_PATH
        self.ffprobe = Config.FFPROBE_PATH
    
    async def merge_subtitle(self, video_path: str, subtitle_path: str, output_path: str, status_msg=None):
        """Merge subtitle to video"""
        try:
            # Build FFmpeg command
            cmd = [
                self.ffmpeg,
                '-i', video_path,
                '-i', subtitle_path,
                '-c:v', 'copy',
                '-c:a', 'copy',
                '-c:s', 'mov_text',
                '-map', '0:v',
                '-map', '0:a?',
                '-map', '1:s',
                '-metadata:s:s:0', 'language=eng',
                '-y',
                output_path
            ]
            
            logger.info(f"Executing: {' '.join(cmd)}")
            
            # Run FFmpeg
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info("Subtitle merged successfully")
                return True
            else:
                logger.error(f"FFmpeg error: {stderr.decode()}")
                if status_msg:
                    await status_msg.edit_text(f"❌ Error: {stderr.decode()[:200]}")
                return False
        
        except Exception as e:
            logger.error(f"Error merging subtitle: {e}")
            if status_msg:
                await status_msg.edit_text(f"❌ Error: {str(e)}")
            return False
    
    async def extract_subtitle(self, video_path: str, output_path: str):
        """Extract subtitle from video"""
        try:
            cmd = [
                self.ffmpeg,
                '-i', video_path,
                '-map', '0:s:0',
                '-y',
                output_path
            ]
            
            logger.info(f"Executing: {' '.join(cmd)}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info("Subtitle extracted successfully")
                return True
            else:
                logger.error(f"FFmpeg error: {stderr.decode()}")
                return False
        
        except Exception as e:
            logger.error(f"Error extracting subtitle: {e}")
            return False
    
    async def has_subtitles(self, video_path: str):
        """Check if video has subtitles"""
        try:
            cmd = [
                self.ffprobe,
                '-v', 'error',
                '-select_streams', 's',
                '-show_entries', 'stream=index',
                '-of', 'csv=p=0',
                video_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            return len(stdout.decode().strip()) > 0
        
        except Exception as e:
            logger.error(f"Error checking subtitles: {e}")
            return False
    
    async def merge_audio(self, video_path: str, audio_path: str, output_path: str, status_msg=None):
        """Merge audio to video"""
        try:
            cmd = [
                self.ffmpeg,
                '-i', video_path,
                '-i', audio_path,
                '-c:v', 'copy',
                '-map', '0:v',
                '-map', '1:a',
                '-shortest',
                '-y',
                output_path
            ]
            
            logger.info(f"Executing: {' '.join(cmd)}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info("Audio merged successfully")
                return True
            else:
                logger.error(f"FFmpeg error: {stderr.decode()}")
                if status_msg:
                    await status_msg.edit_text(f"❌ Error: {stderr.decode()[:200]}")
                return False
        
        except Exception as e:
            logger.error(f"Error merging audio: {e}")
            if status_msg:
                await status_msg.edit_text(f"❌ Error: {str(e)}")
            return False
    
    async def extract_audio(self, video_path: str, output_path: str):
        """Extract audio from video"""
        try:
            cmd = [
                self.ffmpeg,
                '-i', video_path,
                '-vn',
                '-acodec', 'libmp3lame',
                '-q:a', '2',
                '-y',
                output_path
            ]
            
            logger.info(f"Executing: {' '.join(cmd)}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info("Audio extracted successfully")
                return True
            else:
                logger.error(f"FFmpeg error: {stderr.decode()}")
                return False
        
        except Exception as e:
            logger.error(f"Error extracting audio: {e}")
            return False
    
    async def remove_audio(self, video_path: str, output_path: str, status_msg=None):
        """Remove audio from video"""
        try:
            cmd = [
                self.ffmpeg,
                '-i', video_path,
                '-c:v', 'copy',
                '-an',
                '-y',
                output_path
            ]
            
            logger.info(f"Executing: {' '.join(cmd)}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info("Audio removed successfully")
                return True
            else:
                logger.error(f"FFmpeg error: {stderr.decode()}")
                if status_msg:
                    await status_msg.edit_text(f"❌ Error: {stderr.decode()[:200]}")
                return False
        
        except Exception as e:
            logger.error(f"Error removing audio: {e}")
            if status_msg:
                await status_msg.edit_text(f"❌ Error: {str(e)}")
            return False
    
    async def get_video_info(self, video_path: str):
        """Get video information"""
        try:
            cmd = [
                self.ffprobe,
                '-v', 'error',
                '-show_entries', 'format=duration,size',
                '-of', 'default=noprint_wrappers=1',
                video_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                info = {}
                for line in stdout.decode().split('\n'):
                    if '=' in line:
                        key, value = line.split('=')
                        info[key] = value
                return info
            else:
                return None
        
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            return None
