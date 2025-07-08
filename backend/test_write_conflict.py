#!/usr/bin/env python3
"""
高併發測試腳本 - 用於測試 WriteConflict 錯誤的重試機制
"""

import asyncio
import aiohttp
import time
import json
from concurrent.futures import ThreadPoolExecutor
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 配置
BASE_URL = "http://localhost:8000"
CONCURRENT_USERS = 50  # 同時併發用戶數
ORDERS_PER_USER = 10   # 每個用戶下的訂單數
TRANSFER_AMOUNT = 10   # 轉帳金額

class LoadTester:
    def __init__(self):
        self.session = None
        self.success_count = 0
        self.error_count = 0
        self.write_conflict_count = 0
        self.results = []
        
    async def create_session(self):
        """創建 HTTP 會話"""
        self.session = aiohttp.ClientSession()
        
    async def close_session(self):
        """關閉 HTTP 會話"""
        if self.session:
            await self.session.close()
            
    async def simulate_user_trading(self, user_id: int):
        """模擬用戶交易"""
        user_token = f"test_token_{user_id}"
        
        # 模擬市價單交易
        for i in range(ORDERS_PER_USER):
            try:
                start_time = time.time()
                
                # 模擬市價買單
                order_data = {
                    "side": "buy",
                    "quantity": 1,
                    "order_type": "market"
                }
                
                async with self.session.post(
                    f"{BASE_URL}/api/web/stock/order",
                    json=order_data,
                    headers={"Authorization": f"Bearer {user_token}"}
                ) as response:
                    result = await response.json()
                    end_time = time.time()
                    
                    if response.status == 200:
                        self.success_count += 1
                        logger.info(f"用戶 {user_id} 訂單 {i+1} 成功，耗時 {end_time - start_time:.3f}s")
                    else:
                        self.error_count += 1
                        if "WriteConflict" in str(result):
                            self.write_conflict_count += 1
                            logger.warning(f"用戶 {user_id} 訂單 {i+1} WriteConflict: {result}")
                        else:
                            logger.error(f"用戶 {user_id} 訂單 {i+1} 失敗: {result}")
                    
                    self.results.append({
                        "user_id": user_id,
                        "order_id": i+1,
                        "success": response.status == 200,
                        "response_time": end_time - start_time,
                        "error": result if response.status != 200 else None
                    })
                    
            except Exception as e:
                self.error_count += 1
                logger.error(f"用戶 {user_id} 訂單 {i+1} 異常: {e}")
                
            # 短暫延遲避免過度衝突
            await asyncio.sleep(0.1)
            
    async def simulate_concurrent_transfers(self):
        """模擬併發轉帳"""
        logger.info("開始併發轉帳測試...")
        
        tasks = []
        for user_id in range(CONCURRENT_USERS):
            task = asyncio.create_task(self.simulate_user_transfer(user_id))
            tasks.append(task)
            
        await asyncio.gather(*tasks)
        
    async def simulate_user_transfer(self, user_id: int):
        """模擬用戶轉帳"""
        user_token = f"test_token_{user_id}"
        to_user = f"user_{(user_id + 1) % CONCURRENT_USERS}"
        
        try:
            start_time = time.time()
            
            transfer_data = {
                "to_username": to_user,
                "amount": TRANSFER_AMOUNT,
                "note": f"測試轉帳 from user_{user_id}"
            }
            
            async with self.session.post(
                f"{BASE_URL}/api/web/transfer",
                json=transfer_data,
                headers={"Authorization": f"Bearer {user_token}"}
            ) as response:
                result = await response.json()
                end_time = time.time()
                
                if response.status == 200:
                    self.success_count += 1
                    logger.info(f"用戶 {user_id} 轉帳成功，耗時 {end_time - start_time:.3f}s")
                else:
                    self.error_count += 1
                    if "WriteConflict" in str(result):
                        self.write_conflict_count += 1
                        logger.warning(f"用戶 {user_id} 轉帳 WriteConflict: {result}")
                    else:
                        logger.error(f"用戶 {user_id} 轉帳失敗: {result}")
                
        except Exception as e:
            self.error_count += 1
            logger.error(f"用戶 {user_id} 轉帳異常: {e}")
            
    async def run_concurrent_trading_test(self):
        """運行併發交易測試"""
        logger.info(f"開始併發交易測試 - {CONCURRENT_USERS} 用戶，每人 {ORDERS_PER_USER} 訂單")
        
        await self.create_session()
        
        try:
            start_time = time.time()
            
            # 創建所有用戶的任務
            tasks = []
            for user_id in range(CONCURRENT_USERS):
                task = asyncio.create_task(self.simulate_user_trading(user_id))
                tasks.append(task)
            
            # 等待所有任務完成
            await asyncio.gather(*tasks)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # 統計結果
            logger.info("=== 測試結果統計 ===")
            logger.info(f"總測試時間: {total_time:.2f}s")
            logger.info(f"成功請求: {self.success_count}")
            logger.info(f"失敗請求: {self.error_count}")
            logger.info(f"WriteConflict 錯誤: {self.write_conflict_count}")
            logger.info(f"成功率: {self.success_count/(self.success_count + self.error_count)*100:.1f}%")
            logger.info(f"平均響應時間: {sum(r['response_time'] for r in self.results)/len(self.results):.3f}s")
            
        finally:
            await self.close_session()
            
    async def run_mixed_load_test(self):
        """運行混合負載測試（交易 + 轉帳）"""
        logger.info("開始混合負載測試...")
        
        await self.create_session()
        
        try:
            start_time = time.time()
            
            # 同時運行交易和轉帳
            trading_task = asyncio.create_task(self.run_concurrent_trading_test())
            transfer_task = asyncio.create_task(self.simulate_concurrent_transfers())
            
            await asyncio.gather(trading_task, transfer_task)
            
            end_time = time.time()
            logger.info(f"混合負載測試完成，總耗時: {end_time - start_time:.2f}s")
            
        finally:
            await self.close_session()

async def main():
    """主函數"""
    tester = LoadTester()
    
    print("選擇測試類型:")
    print("1. 併發交易測試")
    print("2. 併發轉帳測試")
    print("3. 混合負載測試")
    
    choice = input("請選擇 (1-3): ").strip()
    
    if choice == "1":
        await tester.run_concurrent_trading_test()
    elif choice == "2":
        await tester.simulate_concurrent_transfers()
    elif choice == "3":
        await tester.run_mixed_load_test()
    else:
        logger.error("無效選擇")

if __name__ == "__main__":
    asyncio.run(main())