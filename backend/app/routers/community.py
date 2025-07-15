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
    description="社群攤位給學員發放固定1000點數"
)
async def community_give_points(
    community_password: str = Query(..., description="社群密碼"),
    student_username: str = Query(..., description="學員使用者名"),
    note: str = Query("社群攤位獎勵", description="備註"),
    create_if_not_exists: bool = Query(False, description="如果學員不存在是否創建")
):
    """
    社群攤位發放點數 (固定1000點)
    
    Args:
        community_password: 社群密碼
        student_username: 學員使用者名
        note: 備註
        create_if_not_exists: 如果學員不存在是否創建
        
    Returns:
        dict: 發放結果
    """
    try:
        # 固定發放點數
        points = 1000
        
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
                logger.info(f"通過telegram_id找到使用者: {user.get('username', 'unknown')}")
        except ValueError:
            logger.info(f"無法轉換為數字，嘗試用username查找: {student_username}")
        
        # 如果沒找到，嘗試作為字符串格式的telegram_id
        if not user:
            logger.info(f"嘗試用字符串格式的telegram_id查找: {student_username}")
            user = await db[Collections.USERS].find_one({
                "telegram_id": student_username
            })
            if user:
                logger.info(f"通過字符串telegram_id找到使用者: {user.get('username', 'unknown')}")
        
        # 最後嘗試作為username查找
        if not user:
            logger.info(f"嘗試用username查找: {student_username}")
            user = await db[Collections.USERS].find_one({
                "username": student_username
            })
            if user:
                logger.info(f"通過username找到使用者: {user.get('username', 'unknown')}")
        
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
        
        # 檢查是否已經發放過點數（重複檢查）
        existing_log = await db[Collections.POINT_LOGS].find_one({
            "username": student_username,
            "type": "community_reward",
            "community": community_name
        })
        
        if existing_log:
            # 找到重複發放記錄
            existing_time = existing_log.get("created_at")
            time_str = existing_time.strftime("%Y/%m/%d %H:%M") if existing_time else "未知時間"
            return {
                "success": False,
                "message": f"該學員已於 {time_str} 領取過 {community_name} 的點數獎勵",
                "already_given": True,
                "previous_amount": existing_log.get("amount", 0),
                "previous_time": existing_time.isoformat() if existing_time else None
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
            "student": user.get("username", student_username),  # 返回實際使用者名而不是 telegram_id
            "student_display_name": user.get("username", user.get("name", student_username)),
            "student_photo_url": user.get("photo_url"),
            "student_team": user.get("team"),
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


@router.get(
    "/student-info",
    responses={
        200: {"description": "學員資訊獲取成功"},
        400: {"description": "請求參數錯誤"},
        401: {"description": "社群密碼錯誤"},
        404: {"description": "學員不存在"},
        500: {"description": "伺服器內部錯誤"}
    },
    summary="獲取學員資訊",
    description="社群攤位獲取學員的基本資訊，包括顯示名稱、頭像和隊伍"
)
async def get_student_info(
    community_password: str = Query(..., description="社群密碼"),
    student_username: str = Query(..., description="學員使用者名或 telegram_id")
):
    """
    社群攤位獲取學員資訊
    
    Args:
        community_password: 社群密碼
        student_username: 學員使用者名或 telegram_id
    
    Returns:
        學員的基本資訊，包括顯示名稱、頭像URL和隊伍
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
            logger.warning(f"無效的社群密碼嘗試")
            return {
                "success": False,
                "message": "無效的社群密碼"
            }
        
        db = get_database()
        
        # 查找學員 (與發放點數邏輯相同)
        user = None
        
        # 首先嘗試作為telegram_id查找
        try:
            telegram_id = int(student_username)
            logger.info(f"嘗試用telegram_id查找學員資訊: {telegram_id}")
            user = await db[Collections.USERS].find_one({
                "telegram_id": telegram_id
            })
            if user:
                logger.info(f"通過telegram_id找到學員: {user.get('username', 'unknown')}")
        except ValueError:
            logger.info(f"無法轉換為數字，嘗試用username查找學員: {student_username}")
        
        # 如果沒找到，嘗試作為字符串格式的telegram_id
        if not user:
            logger.info(f"嘗試用字符串格式的telegram_id查找學員: {student_username}")
            user = await db[Collections.USERS].find_one({
                "telegram_id": student_username
            })
            if user:
                logger.info(f"通過字符串telegram_id找到學員: {user.get('username', 'unknown')}")
        
        # 最後嘗試作為username查找
        if not user:
            logger.info(f"嘗試用username查找學員: {student_username}")
            user = await db[Collections.USERS].find_one({
                "username": student_username
            })
            if user:
                logger.info(f"通過username找到學員: {user.get('username', 'unknown')}")
        
        if not user:
            logger.warning(f"找不到學員: {student_username}")
            return {
                "success": False,
                "message": "找不到該學員"
            }
        
        logger.info(f"社群 {community_name} 查詢學員 {student_username} 的資訊")
        
        return {
            "success": True,
            "student_id": student_username,
            "student_display_name": user.get("username", user.get("name", student_username)),
            "student_photo_url": user.get("photo_url"),
            "student_team": user.get("team"),
            "student_points": user.get("points", 0),
            "community": community_name
        }
        
    except Exception as e:
        logger.error(f"獲取學員資訊失敗: {e}")
        return {
            "success": False,
            "message": "獲取學員資訊時發生錯誤"
        }


@router.get(
    "/check-student-reward",
    responses={
        200: {"description": "檢查成功"},
        400: {"description": "請求參數錯誤"},
        401: {"description": "社群密碼錯誤"},
        404: {"description": "找不到學員"},
        500: {"description": "伺服器內部錯誤"}
    },
    summary="檢查學員是否已領取社群獎勵",
    description="檢查特定學員是否已經領取過本社群的點數獎勵"
)
async def check_student_reward(
    community_password: str = Query(..., description="社群密碼"),
    student_username: str = Query(..., description="學員使用者名或 telegram_id")
):
    """
    檢查學員是否已領取社群獎勵
    
    Args:
        community_password: 社群密碼
        student_username: 學員使用者名或 telegram_id
    
    Returns:
        檢查結果，包含是否已領取和相關資訊
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
                "message": "無效的社群密碼"
            }
        
        db = get_database()
        
        # 檢查是否已經發放過點數
        existing_log = await db[Collections.POINT_LOGS].find_one({
            "username": student_username,
            "type": "community_reward",
            "community": community_name
        })
        
        if existing_log:
            # 找到重複發放記錄
            existing_time = existing_log.get("created_at")
            time_str = existing_time.strftime("%Y/%m/%d %H:%M") if existing_time else "未知時間"
            return {
                "success": True,
                "already_given": True,
                "message": f"該學員已於 {time_str} 領取過 {community_name} 的點數獎勵",
                "previous_amount": existing_log.get("amount", 0),
                "previous_time": existing_time.isoformat() if existing_time else None,
                "community": community_name
            }
        else:
            # 未領取過
            return {
                "success": True,
                "already_given": False,
                "message": "該學員尚未領取過獎勵",
                "community": community_name
            }
        
    except Exception as e:
        logger.error(f"檢查學員獎勵狀態失敗: {e}")
        return {
            "success": False,
            "message": "檢查獎勵狀態時發生錯誤"
        }


@router.get(
    "/giving-logs",
    responses={
        200: {"description": "社群發放紀錄獲取成功"},
        400: {"description": "請求參數錯誤"},
        401: {"description": "社群密碼錯誤"},
        500: {"description": "伺服器內部錯誤"}
    },
    summary="獲取社群發放紀錄",
    description="社群攤位獲取本社群的點數發放紀錄"
)
async def get_community_giving_logs(
    community_password: str = Query(..., description="社群密碼"),
    limit: int = Query(50, description="返回紀錄數量", ge=1, le=500)
):
    """
    社群攤位獲取發放紀錄
    
    Args:
        community_password: 社群密碼
        limit: 返回紀錄數量 (1-500，預設50)
    
    Returns:
        本社群的點數發放紀錄列表
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
            logger.warning(f"無效的社群密碼嘗試")
            return {
                "success": False,
                "message": "無效的社群密碼"
            }
        
        db = get_database()
        
        # 查詢本社群的發放紀錄
        logs_cursor = db[Collections.POINT_LOGS].find({
            "type": "community_reward",
            "community": community_name
        }).sort("created_at", -1).limit(limit)
        
        logs = await logs_cursor.to_list(length=None)
        
        # 格式化返回資料，包含學員顯示名稱
        formatted_logs = []
        for log in logs:
            student_username = log.get("username")
            
            # 嘗試獲取學員的顯示名稱
            student_display_name = student_username
            try:
                # 查找學員資料
                user = None
                # 首先嘗試作為telegram_id查找
                try:
                    telegram_id = int(student_username)
                    user = await db[Collections.USERS].find_one({"telegram_id": telegram_id})
                except ValueError:
                    pass
                
                # 如果沒找到，嘗試作為字符串格式的telegram_id
                if not user:
                    user = await db[Collections.USERS].find_one({"telegram_id": student_username})
                
                # 最後嘗試作為username查找
                if not user:
                    user = await db[Collections.USERS].find_one({"username": student_username})
                
                if user:
                    student_display_name = user.get("username", user.get("name", student_username))
                    
            except Exception as e:
                logger.warning(f"獲取學員 {student_username} 顯示名稱失敗: {e}")
            
            formatted_logs.append({
                "id": str(log.get("_id")),
                "student_username": student_username,  # 原始 telegram_id
                "student_display_name": student_display_name,  # 可辨識的顯示名稱
                "amount": log.get("amount"),
                "balance_after": log.get("balance_after"),
                "note": log.get("note"),
                "created_at": log.get("created_at").isoformat() if log.get("created_at") else None,
                "timestamp": log.get("created_at")
            })
        
        logger.info(f"社群 {community_name} 查詢發放紀錄，共 {len(formatted_logs)} 筆")
        
        return {
            "success": True,
            "community": community_name,
            "logs": formatted_logs,
            "total_count": len(formatted_logs)
        }
        
    except Exception as e:
        logger.error(f"獲取社群發放紀錄失敗: {e}")
        return {
            "success": False,
            "message": "獲取發放紀錄時發生錯誤"
        }


@router.delete(
    "/clear-logs",
    responses={
        200: {"description": "社群發放紀錄清除成功"},
        400: {"description": "請求參數錯誤"},
        401: {"description": "社群密碼錯誤"},
        500: {"description": "伺服器內部錯誤"}
    },
    summary="清除社群發放紀錄（開發測試用）",
    description="清除本社群的所有點數發放紀錄，僅供開發測試使用"
)
async def clear_community_giving_logs(
    community_password: str = Query(..., description="社群密碼")
):
    """
    清除社群發放紀錄（開發測試用）
    
    Args:
        community_password: 社群密碼
        
    Returns:
        清除結果
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
            logger.warning(f"無效的社群密碼嘗試")
            return {
                "success": False,
                "message": "無效的社群密碼"
            }
        
        db = get_database()
        
        # 刪除本社群的所有發放紀錄
        result = await db[Collections.POINT_LOGS].delete_many({
            "type": "community_reward",
            "community": community_name
        })
        
        logger.info(f"社群 {community_name} 清除了 {result.deleted_count} 筆發放紀錄（開發測試）")
        
        return {
            "success": True,
            "message": f"已清除 {result.deleted_count} 筆發放紀錄",
            "deleted_count": result.deleted_count,
            "community": community_name
        }
        
    except Exception as e:
        logger.error(f"清除社群發放紀錄失敗: {e}")
        return {
            "success": False,
            "message": "清除發放紀錄時發生錯誤"
        }