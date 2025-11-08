import asyncio
from pyrogram import filters
from pyrogram.types import Message
from config import Config
import logging

logger = logging.getLogger(__name__)

class BroadcastHandler:
    def __init__(self, app, db):
        self.app = app
        self.db = db
        self.broadcast_sessions = {}
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup broadcast command handlers"""
        
        @self.app.on_message(filters.command("broadcast") & filters.user(Config.ADMIN_IDS))
        async def start_broadcast(client, message: Message):
            """Start broadcast session"""
            user_id = message.from_user.id
            
            if len(message.command) > 1:
                # Direct broadcast with text
                broadcast_text = message.text.split(None, 1)[1]
                await self._execute_broadcast(client, message, broadcast_text)
            else:
                # Start broadcast session
                self.broadcast_sessions[user_id] = True
                await message.reply_text(
                    "📢 **Broadcast Mode Activated**\n\n"
                    "Send me the message you want to broadcast to all users.\n\n"
                    "You can send:\n"
                    "• Text messages\n"
                    "• Photos with captions\n"
                    "• Videos with captions\n"
                    "• Documents\n\n"
                    "Use /cancel to stop broadcast mode."
                )
        
        @self.app.on_message(filters.user(Config.ADMIN_IDS) & filters.private)
        async def handle_broadcast_message(client, message: Message):
            """Handle broadcast message"""
            user_id = message.from_user.id
            
            # Check if user is in broadcast session
            if user_id not in self.broadcast_sessions:
                return
            
            # Remove session
            del self.broadcast_sessions[user_id]
            
            # Get message content
            if message.text and message.text.startswith("/"):
                return  # Ignore commands
            
            # Confirm broadcast
            await message.reply_text(
                "⚠️ **Confirm Broadcast**\n\n"
                "Are you sure you want to send this message to all users?\n\n"
                "Reply with /confirm to proceed or /cancel to abort."
            )
            
            # Store message for confirmation
            self.broadcast_sessions[f"{user_id}_pending"] = message
        
        @self.app.on_message(filters.command("confirm") & filters.user(Config.ADMIN_IDS))
        async def confirm_broadcast(client, message: Message):
            """Confirm and execute broadcast"""
            user_id = message.from_user.id
            pending_key = f"{user_id}_pending"
            
            if pending_key not in self.broadcast_sessions:
                await message.reply_text("❌ No pending broadcast found!")
                return
            
            broadcast_message = self.broadcast_sessions[pending_key]
            del self.broadcast_sessions[pending_key]
            
            # Execute broadcast
            await self._execute_broadcast_message(client, message, broadcast_message)
    
    async def _execute_broadcast(self, client, admin_message: Message, broadcast_text: str):
        """Execute text broadcast"""
        status_msg = await admin_message.reply_text("📡 Starting broadcast...")
        
        users = await self.db.get_all_users()
        total_users = len(users)
        success_count = 0
        failed_count = 0
        
        await status_msg.edit_text(
            f"📡 **Broadcasting...**\n\n"
            f"Total Users: {total_users}\n"
            f"Progress: 0/{total_users}"
        )
        
        for i, user in enumerate(users, 1):
            try:
                user_id = user.get("user_id")
                
                # Skip banned users
                if user.get("is_banned", False):
                    failed_count += 1
                    continue
                
                # Send message
                await client.send_message(
                    chat_id=user_id,
                    text=f"📢 **Broadcast Message**\n\n{broadcast_text}"
                )
                
                success_count += 1
                
                # Update progress every 10 users
                if i % 10 == 0:
                    await status_msg.edit_text(
                        f"📡 **Broadcasting...**\n\n"
                        f"Total Users: {total_users}\n"
                        f"Progress: {i}/{total_users}\n"
                        f"✅ Success: {success_count}\n"
                        f"❌ Failed: {failed_count}"
                    )
                
                # Small delay to avoid flood
                await asyncio.sleep(0.05)
            
            except Exception as e:
                logger.error(f"Broadcast error for user {user.get('user_id')}: {e}")
                failed_count += 1
        
        # Final status
        await status_msg.edit_text(
            f"✅ **Broadcast Completed!**\n\n"
            f"Total Users: {total_users}\n"
            f"✅ Success: {success_count}\n"
            f"❌ Failed: {failed_count}"
        )
        
        # Save broadcast record
        await self.db.save_broadcast(broadcast_text, success_count, failed_count)
        
        # Log to channel
        try:
            await client.send_message(
                Config.LOG_CHANNEL,
                f"📢 **Broadcast Completed**\n\n"
                f"Sent by: {admin_message.from_user.mention}\n"
                f"Total: {total_users}\n"
                f"✅ Success: {success_count}\n"
                f"❌ Failed: {failed_count}\n\n"
                f"**Message:**\n{broadcast_text}"
            )
        except:
            pass
    
    async def _execute_broadcast_message(self, client, admin_message: Message, broadcast_msg: Message):
        """Execute broadcast with media message"""
        status_msg = await admin_message.reply_text("📡 Starting broadcast...")
        
        users = await self.db.get_all_users()
        total_users = len(users)
        success_count = 0
        failed_count = 0
        
        await status_msg.edit_text(
            f"📡 **Broadcasting...**\n\n"
            f"Total Users: {total_users}\n"
            f"Progress: 0/{total_users}"
        )
        
        for i, user in enumerate(users, 1):
            try:
                user_id = user.get("user_id")
                
                # Skip banned users
                if user.get("is_banned", False):
                    failed_count += 1
                    continue
                
                # Copy message to user
                await broadcast_msg.copy(chat_id=user_id)
                
                success_count += 1
                
                # Update progress every 10 users
                if i % 10 == 0:
                    await status_msg.edit_text(
                        f"📡 **Broadcasting...**\n\n"
                        f"Total Users: {total_users}\n"
                        f"Progress: {i}/{total_users}\n"
                        f"✅ Success: {success_count}\n"
                        f"❌ Failed: {failed_count}"
                    )
                
                # Small delay to avoid flood
                await asyncio.sleep(0.05)
            
            except Exception as e:
                logger.error(f"Broadcast error for user {user.get('user_id')}: {e}")
                failed_count += 1
        
        # Final status
        await status_msg.edit_text(
            f"✅ **Broadcast Completed!**\n\n"
            f"Total Users: {total_users}\n"
            f"✅ Success: {success_count}\n"
            f"❌ Failed: {failed_count}"
        )
        
        # Save broadcast record
        message_text = broadcast_msg.text or broadcast_msg.caption or "Media message"
        await self.db.save_broadcast(message_text, success_count, failed_count)
        
        # Log to channel
        try:
            await client.send_message(
                Config.LOG_CHANNEL,
                f"📢 **Broadcast Completed**\n\n"
                f"Sent by: {admin_message.from_user.mention}\n"
                f"Total: {total_users}\n"
                f"✅ Success: {success_count}\n"
                f"❌ Failed: {failed_count}"
            )
        except:
            pass
