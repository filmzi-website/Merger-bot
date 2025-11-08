# database.py - MongoDB Database Handler

from pymongo import MongoClient, ASCENDING, DESCENDING
from datetime import datetime, timedelta
import logging
from config import *

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, mongodb_uri, database_name):
        """Initialize MongoDB connection"""
        try:
            self.client = MongoClient(mongodb_uri)
            self.db = self.client[database_name]
            
            # Collections
            self.users = self.db.users
            self.operations = self.db.operations
            self.stats = self.db.stats
            
            # Create indexes
            self.create_indexes()
            logger.info("✅ Database connected successfully")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise
    
    def create_indexes(self):
        """Create database indexes for better performance"""
        self.users.create_index([("user_id", ASCENDING)], unique=True)
        self.operations.create_index([("user_id", ASCENDING), ("timestamp", DESCENDING)])
        self.operations.create_index([("timestamp", DESCENDING)])
    
    # ========== USER MANAGEMENT ==========
    
    def add_user(self, user_id, username=None, first_name=None, last_name=None):
        """Add new user to database"""
        try:
            user_data = {
                "user_id": user_id,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "join_date": datetime.now(),
                "last_active": datetime.now(),
                "total_operations": 0,
                "is_premium": False,
                "is_banned": False,
                "language": "en"
            }
            self.users.insert_one(user_data)
            logger.info(f"✅ New user added: {user_id}")
            return user_data
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            return None
    
    def get_user(self, user_id):
        """Get user from database"""
        return self.users.find_one({"user_id": user_id})
    
    def update_user_activity(self, user_id):
        """Update user's last activity"""
        self.users.update_one(
            {"user_id": user_id},
            {"$set": {"last_active": datetime.now()}}
        )
    
    def get_or_create_user(self, user_id, username=None, first_name=None, last_name=None):
        """Get user or create if doesn't exist"""
        user = self.get_user(user_id)
        if not user:
            user = self.add_user(user_id, username, first_name, last_name)
        else:
            self.update_user_activity(user_id)
        return user
    
    def set_premium(self, user_id, is_premium=True):
        """Set user premium status"""
        self.users.update_one(
            {"user_id": user_id},
            {"$set": {"is_premium": is_premium}}
        )
        logger.info(f"🌟 Premium status updated: {user_id} = {is_premium}")
    
    def ban_user(self, user_id, banned=True):
        """Ban or unban user"""
        self.users.update_one(
            {"user_id": user_id},
            {"$set": {"is_banned": banned}}
        )
        logger.info(f"🚫 Ban status updated: {user_id} = {banned}")
    
    def is_user_banned(self, user_id):
        """Check if user is banned"""
        user = self.get_user(user_id)
        return user.get("is_banned", False) if user else False
    
    # ========== OPERATIONS TRACKING ==========
    
    def add_operation(self, user_id, operation_type, file_size=0, processing_time=0, success=True, error_message=None):
        """Record an operation"""
        try:
            operation_data = {
                "user_id": user_id,
                "operation_type": operation_type,
                "timestamp": datetime.now(),
                "file_size": file_size,
                "processing_time": processing_time,
                "success": success,
                "error_message": error_message
            }
            self.operations.insert_one(operation_data)
            
            # Update user total operations
            if success:
                self.users.update_one(
                    {"user_id": user_id},
                    {"$inc": {"total_operations": 1}}
                )
            
            logger.info(f"📝 Operation logged: {operation_type} by {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding operation: {e}")
            return False
    
    def get_user_operations_today(self, user_id):
        """Get user's operations count for today"""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        count = self.operations.count_documents({
            "user_id": user_id,
            "timestamp": {"$gte": today_start},
            "success": True
        })
        return count
    
    def get_user_operations_history(self, user_id, limit=10):
        """Get user's operation history"""
        return list(self.operations.find(
            {"user_id": user_id}
        ).sort("timestamp", DESCENDING).limit(limit))
    
    def can_user_operate(self, user_id):
        """Check if user can perform operation (rate limiting)"""
        user = self.get_user(user_id)
        if not user:
            return False, "User not found"
        
        if user.get("is_banned", False):
            return False, "You are banned from using this bot"
        
        operations_today = self.get_user_operations_today(user_id)
        limit = PREMIUM_USER_DAILY_LIMIT if user.get("is_premium", False) else FREE_USER_DAILY_LIMIT
        
        if operations_today >= limit:
            return False, f"Daily limit reached ({limit} operations/day)"
        
        return True, "OK"
    
    # ========== STATISTICS ==========
    
    def get_bot_stats(self):
        """Get overall bot statistics"""
        total_users = self.users.count_documents({})
        total_operations = self.operations.count_documents({"success": True})
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_operations = self.operations.count_documents({
            "timestamp": {"$gte": today_start},
            "success": True
        })
        premium_users = self.users.count_documents({"is_premium": True})
        
        return {
            "total_users": total_users,
            "total_operations": total_operations,
            "today_operations": today_operations,
            "premium_users": premium_users
        }
    
    def get_all_users(self):
        """Get all users"""
        return list(self.users.find({}))
    
    def get_all_user_ids(self):
        """Get all user IDs"""
        return [user["user_id"] for user in self.users.find({}, {"user_id": 1})]
