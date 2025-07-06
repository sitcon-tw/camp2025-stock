from __future__ import annotations
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_database, Collections
from datetime import datetime, timezone
from typing import List
import logging

logger = logging.getLogger(__name__)

def get_student_service() -> StudentService:
    """StudentService 的依賴注入函數"""
    return StudentService()

class StudentService:
    """學生服務 - 負責處理學生管理相關功能"""
    
    def __init__(self, db: AsyncIOMotorDatabase = None):
        if db is None:
            self.db = get_database()
        else:
            self.db = db
    
    async def create_student(self, student_id: str, username: str) -> bool:
        """
        建立新學員
        
        Args:
            student_id: 學員ID（唯一不變的識別碼）
            username: 學員姓名
            
        Returns:
            bool: 是否建立成功
        """
        try:
            # 檢查是否已存在
            existing_student = await self.db[Collections.USERS].find_one({
                "id": student_id
            })
            if existing_student:
                logger.warning(f"Student with id {student_id} already exists")
                return False
            
            # 建立學員記錄
            student_doc = {
                "id": student_id,
                "name": username,
                "team": None,  # 等待後續更新
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            
            result = await self.db[Collections.USERS].insert_one(student_doc)
            
            if result.inserted_id:
                logger.info(f"Student created successfully: {student_id} - {username}")
                return True
            else:
                logger.error(f"Failed to create student: {student_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating student {student_id}: {e}")
            return False
    
    async def update_students(self, student_data: List[dict]) -> dict:
        """
        批量更新學員資料（支援新增學員，enabled 預設 false）
        
        Args:
            student_data: 學員資料列表，包含 id, name, team
            
        Returns:
            dict: 更新結果和學生列表
        """
        try:
            updated_count = 0
            created_count = 0
            errors = []
            
            # 批量更新學員資料
            for student in student_data:
                try:
                    result = await self.db[Collections.USERS].update_one(
                        {"id": student["id"]},
                        {
                            "$set": {
                                "name": student["name"],
                                "team": student["team"],
                                "updated_at": datetime.now(timezone.utc)
                            },
                            "$setOnInsert": {
                                "enabled": False,  # 新學員預設未啟用
                                "points": 100,     # 初始點數
                                "stock_amount": 10,  # 10 股
                                "created_at": datetime.now(timezone.utc)
                            }
                        },
                        upsert=True  # 允許建立新記錄
                    )
                    
                    if result.matched_count > 0:
                        updated_count += 1
                        logger.info(f"Updated student: {student['id']} - {student['name']} - {student['team']}")
                    elif result.upserted_id:
                        created_count += 1
                        logger.info(f"Created student: {student['id']} - {student['name']} - {student['team']}")
                        
                        # 為新學員初始化股票持有記錄，給予5股初始股票
                        await self.db[Collections.STOCKS].insert_one({
                            "user_id": result.upserted_id,
                            "stock_amount": 10, # 10 股
                            "updated_at": datetime.now(timezone.utc)
                        })
                        
                except Exception as e:
                    error_msg = f"Error updating student {student['id']}: {e}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            # 獲取更新後的學生列表（只包含有 id 欄位的學員）
            students_cursor = self.db[Collections.USERS].find(
                {"id": {"$exists": True}},  # 只查詢有 id 欄位的文件
                {
                    "_id": 0,
                    "id": 1,
                    "name": 1,
                    "team": 1,
                    "enabled": 1
                }
            )
            
            students = []
            async for student in students_cursor:
                students.append({
                    "id": student.get("id", ""),
                    "name": student.get("name", ""),
                    "team": student.get("team", ""),
                    "enabled": student.get("enabled", False)
                })
            
            # 準備回應訊息
            message = f"成功更新 {updated_count} 位學員"
            if created_count > 0:
                message += f"，新增 {created_count} 位學員"
            if errors:
                message += f"，{len(errors)} 個錯誤"
            
            return {
                "success": True,
                "message": message,
                "students": students,
                "updated_count": updated_count,
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Error in batch update students: {e}")
            return {
                "success": False,
                "message": f"批量更新使用者狀態失敗: {str(e)}",
                "students": [],
                "updated_count": 0,
                "errors": [str(e)]
            }
    
    async def activate_student(self, student_id: str, telegram_id: str, telegram_nickname: str) -> dict:
        """
        啟用學員帳號（只需 ID 存在即可）
        
        Args:
            student_id: 學員 ID（驗證碼）
            telegram_id: Telegram ID
            telegram_nickname: Telegram 暱稱
            
        Returns:
            dict: 啟用結果
        """
        try:
            # 查找學員是否存在
            student = await self.db[Collections.USERS].find_one({
                "id": student_id
            })
            
            if not student:
                return {
                    "ok": False,
                    "message": "noexist"
                }
            
            # 檢查是否已經啟用
            if student.get("enabled", False):
                return {
                    "ok": False,
                    "message": f"already_activated"
                }
            
            # 啟用學員帳號
            result = await self.db[Collections.USERS].update_one(
                {"id": student_id},
                {
                    "$set": {
                        "enabled": True,
                        "telegram_id": telegram_id,
                        "telegram_nickname": telegram_nickname,
                        "activated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Student activated: {student_id} - {student.get('name', 'Unknown')}")
                return {
                    "ok": True,
                    "message": f"success:{student.get('name', student_id)}"
                }
            else:
                return {
                    "ok": False,
                    "message": "error"
                }
                
        except Exception as e:
            logger.error(f"Error activating student {student_id}: {e}")
            return {
                "ok": False,
                "message": f"啟用失敗: {str(e)}"
            }
    
    async def get_student_status(self, student_id: str) -> dict:
        """
        查詢學員狀態
        
        Args:
            student_id: 學員 ID
            
        Returns:
            dict: 學員狀態資訊
        """
        try:
            # 查找學員
            student = await self.db[Collections.USERS].find_one({
                "id": student_id
            })
            
            if not student:
                return {
                    "ok": False,
                    "message": f"學員 ID '{student_id}' 不存在"
                }
            
            return {
                "ok": True,
                "message": "查詢成功",
                "id": student.get("id"),
                "name": student.get("name"),
                "enabled": student.get("enabled", False),
                "team": student.get("team")
            }
                
        except Exception as e:
            logger.error(f"Error getting student status {student_id}: {e}")
            return {
                "ok": False,
                "message": f"查詢學員資料失敗: {str(e)}"
            }
    
    async def get_student_info(self, student_id: str) -> dict:
        """
        查詢學員詳細資訊
        
        Args:
            student_id: 學員 ID
            
        Returns:
            dict: 學員詳細資訊
        """
        try:
            # 查找學員
            student = await self.db[Collections.USERS].find_one({
                "id": student_id
            })
            
            if not student:
                raise HTTPException(
                    status_code=404,
                    detail=f"學員 ID '{student_id}' 不存在"
                )
            
            return {
                "id": student.get("id"),
                "name": student.get("name"),
                "team": student.get("team"),
                "enabled": student.get("enabled", False)
            }
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting student info {student_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"查詢學員資訊失敗: {str(e)}"
            )