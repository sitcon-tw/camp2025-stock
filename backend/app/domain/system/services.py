# 系統領域服務
# 負責債務管理和學生管理的業務邏輯

from __future__ import annotations
from typing import Optional, List
from bson import ObjectId
from datetime import datetime
import logging

from .entities import Student, UserDebt
from .repositories import StudentRepository, UserDebtRepository
from ..common.exceptions import DomainException

logger = logging.getLogger(__name__)


class DebtDomainService:
    """債務管理領域服務"""
    
    def __init__(self, debt_repository: UserDebtRepository):
        self.debt_repository = debt_repository
    
    async def calculate_user_total_debt(self, user_id: ObjectId) -> int:
        """
        計算使用者總債務
        領域邏輯：債務總額 = 所有 active 狀態債務的總和
        """
        try:
            active_debts = await self.debt_repository.find_by_user_and_status(user_id, "active")
            total_debt = sum(debt.amount for debt in active_debts)
            
            logger.debug(f"Calculated total debt for user {user_id}: {total_debt}")
            return total_debt
            
        except Exception as e:
            logger.error(f"Failed to calculate total debt for user {user_id}: {e}")
            raise DomainException(f"計算債務總額失敗: {str(e)}")
    
    async def create_debt(self, user_id: ObjectId, amount: int, reason: str, created_by: ObjectId) -> UserDebt:
        """
        建立新債務
        領域邏輯：債務金額必須大於 0，並記錄建立原因
        """
        if amount <= 0:
            raise DomainException("債務金額必須大於 0")
        
        if not reason.strip():
            raise DomainException("必須提供債務原因")
        
        debt = UserDebt(
            user_id=user_id,
            amount=amount,
            reason=reason,
            status="active",
            created_by=created_by,
            created_at=datetime.utcnow()
        )
        
        return await self.debt_repository.save(debt)
    
    async def resolve_debt(self, debt_id: ObjectId, resolved_by: ObjectId) -> bool:
        """
        解決債務
        領域邏輯：只有 active 狀態的債務可以被解決
        """
        debt = await self.debt_repository.find_by_id(debt_id)
        if not debt:
            raise DomainException("債務不存在")
        
        if debt.status != "active":
            raise DomainException("只有 active 狀態的債務可以被解決")
        
        debt.status = "resolved"
        debt.resolved_by = resolved_by
        debt.resolved_at = datetime.utcnow()
        
        await self.debt_repository.update(debt)
        logger.info(f"Debt {debt_id} resolved by {resolved_by}")
        return True
    
    async def get_user_active_debts(self, user_id: ObjectId) -> List[UserDebt]:
        """取得使用者所有 active 狀態的債務"""
        return await self.debt_repository.find_by_user_and_status(user_id, "active")
    
    async def get_user_debt_history(self, user_id: ObjectId) -> List[UserDebt]:
        """取得使用者完整債務歷史"""
        return await self.debt_repository.find_by_user_id(user_id)


class StudentDomainService:
    """學生管理領域服務"""
    
    def __init__(self, student_repository: StudentRepository):
        self.student_repository = student_repository
    
    async def register_student(self, student_id: str, name: str, team: str, telegram_id: Optional[int] = None) -> Student:
        """
        註冊新學生
        領域邏輯：學生 ID 必須唯一，姓名和隊伍不能為空
        """
        if not student_id.strip():
            raise DomainException("學生 ID 不能為空")
        
        if not name.strip():
            raise DomainException("學生姓名不能為空")
        
        if not team.strip():
            raise DomainException("隊伍名稱不能為空")
        
        # 檢查學生 ID 是否已存在
        existing_student = await self.student_repository.find_by_student_id(student_id)
        if existing_student:
            raise DomainException("學生 ID 已存在")
        
        student = Student(
            student_id=student_id,
            name=name,
            team=team,
            telegram_id=telegram_id,
            enabled=True,
            created_at=datetime.utcnow()
        )
        
        return await self.student_repository.save(student)
    
    async def enable_student(self, student_id: str) -> bool:
        """啟用學生帳號"""
        student = await self.student_repository.find_by_student_id(student_id)
        if not student:
            raise DomainException("學生不存在")
        
        if student.enabled:
            return True  # 已經啟用
        
        student.enabled = True
        student.updated_at = datetime.utcnow()
        
        await self.student_repository.update(student)
        logger.info(f"Student {student_id} enabled")
        return True
    
    async def disable_student(self, student_id: str) -> bool:
        """停用學生帳號"""
        student = await self.student_repository.find_by_student_id(student_id)
        if not student:
            raise DomainException("學生不存在")
        
        if not student.enabled:
            return True  # 已經停用
        
        student.enabled = False
        student.updated_at = datetime.utcnow()
        
        await self.student_repository.update(student)
        logger.info(f"Student {student_id} disabled")
        return True
    
    async def update_student_telegram(self, student_id: str, telegram_id: int) -> bool:
        """更新學生的 Telegram ID"""
        student = await self.student_repository.find_by_student_id(student_id)
        if not student:
            raise DomainException("學生不存在")
        
        student.telegram_id = telegram_id
        student.updated_at = datetime.utcnow()
        
        await self.student_repository.update(student)
        logger.info(f"Updated Telegram ID for student {student_id}")
        return True
    
    async def get_students_by_team(self, team: str) -> List[Student]:
        """取得指定隊伍的所有學生"""
        return await self.student_repository.find_by_team(team)
    
    async def get_all_teams(self) -> List[str]:
        """取得所有隊伍名稱"""
        students = await self.student_repository.find_all()
        teams = set(student.team for student in students if student.team)
        return sorted(list(teams))