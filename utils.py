# utils.py - Utility Functions

import os
import shutil
import asyncio
from datetime import datetime
from config import *
import logging

logger = logging.getLogger(__name__)

def setup_directories():
    """Create necessary directories"""
    os.makedirs(DOWNLOAD_PATH, exist_ok=True)
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    logger.info("✅ Directories created")

def get_user_dir(user_id):
    """Get user-specific directory"""
    user_dir = os.path.join(DOWNLOAD_PATH, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    return user_dir

def cleanup_user_files(user_id):
    """Clean up user files"""
    user_dir = get_user_dir(user_id)
    if os.path.exists(user_dir):
        shutil.rmtree(user_dir)
    os.makedirs(user_dir, exist_ok=True)
    logger.info(f"🗑️ Cleaned up files for user {user_id}")

def format_file_size(size_bytes):
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def format_duration(seconds):
    """Format seconds to human readable duration"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"

def is_admin(user_id):
    """Check if user is admin"""
    return user_id in ADMIN_IDS

def get_file_extension(filename):
    """Get file extension"""
    return os.path.splitext(filename)[1].lower()

def is_video_file(filename):
    """Check if file is video"""
    return get_file_extension(filename) in VIDEO_FORMATS

def is_audio_file(filename):
    """Check if file is audio"""
    return get_file_extension(filename) in AUDIO_FORMATS

def is_subtitle_file(filename):
    """Check if file is subtitle"""
    return get_file_extension(filename) in SUBTITLE_FORMATS

async def run_ffmpeg_command(cmd, timeout=3600):
    """Run FFmpeg command asynchronously"""
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout
        )
        
        return process.returncode, stdout.decode(), stderr.decode()
    except asyncio.TimeoutError:
        logger.error("FFmpeg command timed out")
        return -1, "", "Timeout"
    except Exception as e:
        logger.error(f"FFmpeg error: {e}")
        return -1, "", str(e)

def escape_path(path):
    """Escape special characters in file path for FFmpeg"""
    return path.replace("'", "'\\''")

def generate_output_filename(user_id, operation, extension=".mp4"):
    """Generate unique output filename"""
    timestamp = int(datetime.now().timestamp())
    return f"{operation}_{user_id}_{timestamp}{extension}"
