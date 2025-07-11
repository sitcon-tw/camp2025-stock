from fastapi import APIRouter, Query
from app.core.database import get_database, Collections
from app.schemas.public import ErrorResponse
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/community", tags=["Community APIs - 社群攤位功能"])


@router.post(
    "/verify",
    responses={
        400: {"model": ErrorResponse, "description": "請求參數錯誤"},
        401: {"model": ErrorResponse, "description": "密碼錯誤"},
        500: {"model": ErrorResponse, "description": "伺服器內部錯誤"}
    },
    summary="社群密碼驗證",
    description="驗證密碼並自動檢測對應的社群"
)
async def verify_community_password(
    password: str = Query(..., description="社群密碼")
):
    """
    社群密碼驗證（自動檢測社群）
    
    Args:
        password: 社群密碼
        
    Returns:
        dict: 驗證結果，包含：
        - success: 是否驗證成功
        - community: 社群名稱（驗證成功時）
        - message: 錯誤訊息（驗證失敗時）
    """
    try:
        # 社群密碼配置
        COMMUNITY_PASSWORDS = {
            "SITCON 學生計算機年會": "Tiger9@Vault!Mo0n#42*",
            "OCF 開放文化基金會": "Ocean^CultuR3$Rise!888",
            "Ubuntu 台灣社群": "Ubun2u!Taipei@2025^Rocks",
            "MozTW 社群": "MozTw$Fox_@42Jade*Fire",
            "COSCUP 開源人年會": "COde*0p3n#Sun5et!UP22",
            "Taiwan Security Club": "S3curE@Tree!^Night_CLUB99",
            "SCoML 學生機器學習社群": "M@chin3Zebra_Learn#504*",
            "綠洲計畫 LZGH": "0@si5^L!ght$Grow*Green88",
            "PyCon TW": "PyTh0n#Conf!Luv2TW@2025"
        }
        
        # 尋找密碼對應的社群
        for community_name, community_password in COMMUNITY_PASSWORDS.items():
            if community_password == password:
                return {
                    "success": True,
                    "community": community_name,
                    "message": "驗證成功"
                }
        
        # 密碼不對應任何社群
        return {
            "success": False,
            "message": "密碼錯誤或不存在對應的社群"
        }
        
    except Exception as e:
        logger.error(f"Community password verification failed: {e}")
        return {
            "success": False,
            "message": "驗證過程發生錯誤"
        }


@router.post(
    "/give-points",
    responses={
        400: {"model": ErrorResponse, "description": "請求參數錯誤"},
        401: {"model": ErrorResponse, "description": "社群密碼錯誤"},
        404: {"model": ErrorResponse, "description": "找不到學員"},
        500: {"model": ErrorResponse, "description": "伺服器內部錯誤"}
    },
    summary="社群攤位發放點數",
    description="社群攤位給學員發放點數"
)
async def community_give_points(
    community_password: str = Query(..., description="社群密碼"),
    student_username: str = Query(..., description="學員用戶名"),
    points: int = Query(..., description="發放點數", ge=1, le=1000),
    note: str = Query("社群攤位獎勵", description="備註"),
    create_if_not_exists: bool = Query(False, description="如果學員不存在是否創建")
):
    """
    社群攤位發放點數
    
    Args:
        community_password: 社群密碼
        student_username: 學員用戶名
        points: 發放點數
        note: 備註
        create_if_not_exists: 如果學員不存在是否創建
        
    Returns:
        dict: 發放結果
    """
    try:
        # 社群密碼配置
        COMMUNITY_PASSWORDS = {
            "SITCON 學生計算機年會": "Tiger9@Vault!Mo0n#42*",
            "OCF 開放文化基金會": "Ocean^CultuR3$Rise!888",
            "Ubuntu 台灣社群": "Ubun2u!Taipei@2025^Rocks",
            "MozTW 社群": "MozTw$Fox_@42Jade*Fire",
            "COSCUP 開源人年會": "COde*0p3n#Sun5et!UP22",
            "Taiwan Security Club": "S3curE@Tree!^Night_CLUB99",
            "SCoML 學生機器學習社群": "M@chin3Zebra_Learn#504*",
            "綠洲計畫 LZGH": "0@si5^L!ght$Grow*Green88",
            "PyCon TW": "PyTh0n#Conf!Luv2TW@2025"
        }
        
        # 驗證社群密碼
        community_name = None
        for name, password in COMMUNITY_PASSWORDS.items():
            if password == community_password:
                community_name = name
                break
        
        if not community_name:
            return {
                "success": False,
                "message": "社群密碼錯誤"
            }
        
        db = get_database()
        
        # 查找學員 (可能是telegram_id或username)
        user = None
        
        # 首先嘗試作為telegram_id查找
        try:
            telegram_id = int(student_username)
            logger.info(f"嘗試用telegram_id查找: {telegram_id}")
            user = await db[Collections.USERS].find_one({
                "telegram_id": telegram_id
            })
            if user:
                logger.info(f"通過telegram_id找到用戶: {user.get('username', 'unknown')}")
        except ValueError:
            logger.info(f"無法轉換為數字，嘗試用username查找: {student_username}")
        
        # 如果沒找到，嘗試作為字符串格式的telegram_id
        if not user:
            logger.info(f"嘗試用字符串格式的telegram_id查找: {student_username}")
            user = await db[Collections.USERS].find_one({
                "telegram_id": student_username
            })
            if user:
                logger.info(f"通過字符串telegram_id找到用戶: {user.get('username', 'unknown')}")
        
        # 最後嘗試作為username查找
        if not user:
            logger.info(f"嘗試用username查找: {student_username}")
            user = await db[Collections.USERS].find_one({
                "username": student_username
            })
            if user:
                logger.info(f"通過username找到用戶: {user.get('username', 'unknown')}")
        
        if not user:
            if create_if_not_exists:
                # 創建新學員
                try:
                    telegram_id = int(student_username)
                    user = {
                        "telegram_id": telegram_id,
                        "username": f"user_{telegram_id}",
                        "points": 0,
                        "stocks": 0,
                        "created_at": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc)
                    }
                    result = await db[Collections.USERS].insert_one(user)
                    user["_id"] = result.inserted_id
                    logger.info(f"創建新學員: {user['username']} (ID: {telegram_id})")
                except ValueError:
                    return {
                        "success": False,
                        "message": f"無法創建學員，學員ID必須是數字: {student_username}"
                    }
            else:
                return {
                    "success": False,
                    "message": f"找不到學員: {student_username}",
                    "tip": "可以加上參數 create_if_not_exists=true 來自動創建學員"
                }
        
        # 發放點數
        now = datetime.now(timezone.utc)
        
        # 更新學員點數
        result = await db[Collections.USERS].update_one(
            {"_id": user["_id"]},
            {
                "$inc": {"points": points},
                "$set": {"updated_at": now}
            }
        )
        
        if result.modified_count == 0:
            return {
                "success": False,
                "message": "更新學員點數失敗"
            }
        
        # 獲取更新後的餘額
        updated_user = await db[Collections.USERS].find_one({"_id": user["_id"]})
        balance_after = updated_user.get("points", 0) if updated_user else 0
        
        # 記錄點數歷史
        point_record = {
            "user_id": user["_id"],  # 使用 ObjectId 以保持與查詢邏輯一致
            "username": student_username,
            "amount": points,
            "balance_after": balance_after,  # 使用實際更新後的餘額
            "type": "community_reward",
            "note": f"{note} (來自 {community_name})",
            "source": "community_booth",
            "community": community_name,
            "created_at": now
        }
        
        await db[Collections.POINT_LOGS].insert_one(point_record)
        
        logger.info(f"社群 {community_name} 給學員 {student_username} 發放了 {points} 點數")
        
        return {
            "success": True,
            "message": f"成功給 {student_username} 發放 {points} 點數",
            "student": student_username,
            "points": points,
            "new_balance": user["points"] + points,
            "community": community_name
        }
        
    except Exception as e:
        logger.error(f"社群發放點數失敗: {e}")
        return {
            "success": False,
            "message": "發放點數時發生錯誤"
        }