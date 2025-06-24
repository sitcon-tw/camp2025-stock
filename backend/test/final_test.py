#!/usr/bin/env python3
"""
SITCON Camp 2025 學員啟用與交易模擬腳本 (含股票交易)

功能：
1. 自動檢查市場開放狀態，可選擇自動開啟市場
2. 啟用所有學員（通過給予初始點數）
3. 模擬隨機的點數轉帳交易
4. 模擬隨機的股票買賣交易
5. IPO股票發行和購買測試
6. 查詢投資組合和市場狀態
7. 完整資料庫重置功能

需要安裝的套件：
pip install requests

使用方法：
python final_test.py

注意事項：
- 腳本會自動檢查市場是否開放，如果關閉會詢問是否開啟
- 提供完整的交易系統測試，包括IPO和使用者間交易
- 包含資料庫重置功能，請謹慎使用
"""

import requests
import json
import random
import time
import threading
import concurrent.futures
from typing import List, Dict, Optional, Tuple
import sys
from datetime import datetime
from collections import defaultdict
import queue

# API 設定
BASE_URL = "http://localhost:8000"  # 請根據實際情況修改
ADMIN_PASSWORD = "admin123"
BOT_TOKEN = "neverGonnaGiveYouUp"

# 學員資料（從您提供的JSON文件）
STUDENTS_DATA = [
    {"id": 6179851991, "name": "毛哥EM", "team": "第一組"},
    {"id": 1681526140, "name": "KoukeNeko", "team": "第一組測試更新"},
    {"id": 2189572562, "name": "Wolf", "team": "第一組"},
    {"id": 6027605121, "name": "Denny Huang", "team": "第一組"},
    {"id": 7345251950, "name": "Leo Lee", "team": "第一組"},
    {"id": 4262256661, "name": "康 康", "team": "第一組"},
    {"id": 5836830293, "name": "Sky Hong", "team": "第一組"},
    {"id": 4847225996, "name": "皮蛋", "team": "第一組"},
    {"id": 3000259327, "name": "Zhuyuan", "team": "第二組"},
    {"id": 2933649958, "name": "Mina", "team": "第二組"},
    {"id": 5293586656, "name": "qian🐾", "team": "第二組"},
    {"id": 9164694505, "name": "邱 子洺", "team": "第二組"},
    {"id": 8449838999, "name": "OsGa", "team": "第二組"},
    {"id": 9609223894, "name": "Yorukot", "team": "第二組"},
    {"id": 6889818510, "name": "Ya", "team": "第二組"},
    {"id": 9283937785, "name": "末 夜", "team": "第二組"},
    {"id": 1287779434, "name": "魚 章", "team": "第三組"},
    {"id": 7649822961, "name": "Terry Chung", "team": "第三組"},
    {"id": 1666353438, "name": "Hex Zeng", "team": "第三組"},
    {"id": 9443699832, "name": "yimang", "team": "第三組"},
    {"id": 8450934833, "name": "🍊 橘子", "team": ""},
    {"id": 9207866388, "name": "曾 兆翌", "team": "第三組"},
    {"id": 2221857365, "name": "Ben Chueh", "team": "第三組"},
    {"id": 4301530116, "name": "ffting", "team": "第三組"},
    {"id": 2024083999, "name": "阿 六", "team": "第五組"},
    {"id": 4034849899, "name": "Windless", "team": "第五組"},
    {"id": 6117747728, "name": "W", "team": "第五組"},
    {"id": 3683764508, "name": "EHDW Pan", "team": "第五組"},
    {"id": 3027783575, "name": "開根號", "team": "第五組"},
    {"id": 6840016852, "name": "Fearnot", "team": "第五組"},
    {"id": 3793321529, "name": "Yuto", "team": "第五組"},
    {"id": 3048374304, "name": "Limu S", "team": "第五組"},
    {"id": 9099883062, "name": "Poren Chiang", "team": "第四組"},
    {"id": 2179555812, "name": "Hao Cheng Yang", "team": "第四組"},
    {"id": 2100155397, "name": "Hans", "team": "第四組"},
    {"id": 5247487669, "name": "Panda Wu", "team": "第四組"},
    {"id": 1864321953, "name": "qiqi _77", "team": "第四組"},
    {"id": 1526124507, "name": "Alvin Chen", "team": "第四組"},
    {"id": 2449263859, "name": "AC", "team": "第四組"},
    {"id": 7171752714, "name": "Kevinowo", "team": "第四組"},
    {"id": 6615396167, "name": "cheng", "team": "第六組"},
    {"id": 8695899481, "name": "kyle chen", "team": "第六組"},
    {"id": 2092802196, "name": "Hugo Wang", "team": "第六組"},
    {"id": 8065456402, "name": "Lindy", "team": "第六組"},
    {"id": 4182490650, "name": "Helena L.", "team": "第六組"},
    {"id": 6859268520, "name": "滷味 LowV", "team": "第六組"},
    {"id": 4767432557, "name": "crab", "team": "第六組"},
    {"id": 1940625703, "name": ":D 阿玉騎士", "team": "第六組"},
    {"id": 9649065380, "name": "OnCloud", "team": "第七組"},
    {"id": 6941268369, "name": "T. 庭", "team": "第七組"},
    {"id": 1440402751, "name": "Kiki Yang", "team": "第七組"},
    {"id": 4836647852, "name": "KY", "team": "第七組"},
    {"id": 4230397197, "name": "拾弎", "team": "第七組"},
    {"id": 5627985223, "name": "椰 花", "team": "第七組"},
    {"id": 6879681869, "name": "Sam Liu", "team": "第七組"},
    {"id": 5270449810, "name": "Yuru", "team": "第七組"},
    {"id": 6249238790, "name": "Kang Kason", "team": "第八組"},
    {"id": 7160192821, "name": "Sean Wei", "team": "第八組"},
    {"id": 9111529055, "name": "Leaf Tseng", "team": "第八組"},
    {"id": 7270129811, "name": "Arnoldsky", "team": "第八組"},
    {"id": 9638449803, "name": "Ricky Lu", "team": "第八組"},
    {"id": 4247512694, "name": "nelsonGX", "team": "第八組"},
    {"id": 2048973433, "name": "咪路", "team": "第八組"},
    {"id": 2732641150, "name": "Andrew Kuo", "team": "第八組"},
    {"id": 3085998690, "name": "AK", "team": "第九組"},
    {"id": 4068012480, "name": "Jasmine Kao", "team": "第九組"},
    {"id": 5554687314, "name": "pU yUeh", "team": "第九組"},
    {"id": 2501542103, "name": "小婕", "team": "第九組"},
    {"id": 5104840283, "name": "小", "team": "第九組"},
    {"id": 2478489903, "name": "xiunG 翔", "team": "第九組"},
    {"id": 6994583294, "name": "x翔", "team": "第九組"},
    {"id": 8117668223, "name": "Yuan' OR 1=1; -- #", "team": "第九組"},
    {"id": 9804697237, "name": "henry heute", "team": "第十組"},
    {"id": 7373939096, "name": "hh", "team": "第十組"},
    {"id": 9453611846, "name": "Tony2100", "team": "第十組"},
    {"id": 2254757472, "name": "Camel", "team": "第十組"},
    {"id": 2941650133, "name": "小徐", "team": "第十組"},
    {"id": 3298232482, "name": "小", "team": "第十組"},
    {"id": 4483416927, "name": "Xin Qi", "team": "第十組"},
    {"id": 1731762105, "name": "SITCON Camp 2025 行政好夥伴", "team": "第十組"},
    {"id": 3536132809, "name": "S行", "team": "第十組"}
]

class CampTradingSimulator:
    """SITCON Camp 2025 交易模擬器 (含股票交易)"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url.rstrip('/')
        self.admin_token: Optional[str] = None
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
        
        # 執行緒安全的交易統計
        self.stats_lock = threading.Lock()
        self.stats = {
            'point_transfers': {'success': 0, 'failed': 0},
            'stock_trades': {'success': 0, 'failed': 0},
            'total_points_transferred': 0,
            'total_stocks_traded': 0
        }
        
        # 多執行緒相關
        self.active_threads = 0
        self.thread_results = queue.Queue()
        self.thread_lock = threading.Lock()
    
    def log(self, message: str, level: str = "INFO"):
        """記錄日誌"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        thread_id = threading.current_thread().name
        print(f"[{timestamp}] [{level}] [{thread_id}] {message}")
    
    def update_stats(self, stat_type: str, operation: str, amount: int = 0):
        """執行緒安全的統計更新"""
        with self.stats_lock:
            if stat_type == 'point_transfer':
                self.stats['point_transfers'][operation] += 1
                if operation == 'success':
                    self.stats['total_points_transferred'] += amount
            elif stat_type == 'stock_trade':
                self.stats['stock_trades'][operation] += 1
                if operation == 'success':
                    self.stats['total_stocks_traded'] += amount
    
    def admin_login(self) -> bool:
        """管理員登入"""
        try:
            self.log("正在進行管理員登入...")
            response = self.session.post(
                f"{self.base_url}/api/admin/login",
                json={"password": ADMIN_PASSWORD}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("token")
                self.log("管理員登入成功")
                return True
            else:
                self.log(f"管理員登入失敗: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"管理員登入異常: {e}", "ERROR")
            return False
    
    def reset_ipo_for_testing(self, initial_shares: int = 1000, initial_price: int = 20) -> bool:
        """重置IPO狀態以便測試"""
        try:
            self.log(f"🔄 重置IPO狀態: {initial_shares} 股 @ {initial_price} 點/股")
            
            if not self.admin_token:
                self.log("請先登入管理員", "ERROR")
                return False
            
            response = self.session.post(
                f"{self.base_url}/api/admin/ipo/reset",
                headers=self.get_admin_headers(),
                params={"initial_shares": initial_shares, "initial_price": initial_price}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    self.log(f"✅ IPO重置成功: {data.get('message')}")
                    return True
                else:
                    self.log(f"❌ IPO重置失敗: {data.get('message', '未知錯誤')}", "ERROR")
                    return False
            else:
                self.log(f"❌ IPO重置請求失敗: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"IPO重置異常: {e}", "ERROR")
            return False
    
    def reset_all_data(self) -> bool:
        """重置所有資料"""
        try:
            self.log("🔄 重置所有資料庫資料...")
            
            if not self.admin_token:
                self.log("請先登入管理員", "ERROR")
                return False
            
            response = self.session.post(
                f"{self.base_url}/api/admin/reset/alldata",
                headers=self.get_admin_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    self.log(f"✅ 資料重置成功: {data.get('message')}")
                    self.log(f"📊 刪除記錄數: {data.get('deletedDocuments', 0)}")
                    self.log(f"🔧 重新初始化設定: IPO {data.get('initializedConfigs', {}).get('ipo', {})}")
                    return True
                else:
                    self.log(f"❌ 資料重置失敗: {data.get('message', '未知錯誤')}", "ERROR")
                    return False
            else:
                self.log(f"❌ 資料重置請求失敗: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"資料重置異常: {e}", "ERROR")
            return False
    
    def check_and_ensure_market_open(self) -> bool:
        """檢查並確保市場開放交易"""
        try:
            self.log("🔍 檢查市場開放狀態...")
            
            # 檢查目前市場狀態
            market_response = self.session.get(f"{self.base_url}/api/status")
            if market_response.status_code != 200:
                self.log(f"❌ 無法查詢市場狀態: {market_response.status_code}", "ERROR")
                return False
            
            market_data = market_response.json()
            is_open = market_data.get("isOpen", False)
            current_time = market_data.get("currentTime", "unknown")
            
            if is_open:
                self.log("✅ 市場目前開放交易")
                return True
            
            self.log("⚠️ 市場目前關閉")
            self.log(f"   目前時間: {current_time}")
            
            # 詢問是否要開放市場
            open_market = input("是否要開放市場進行測試？ (Y/n): ").strip().lower()
            if open_market in ['', 'y', 'yes']:
                return self.open_market_for_testing()
            else:
                self.log("❌ 市場未開放，無法進行交易測試", "WARNING")
                return False
                
        except Exception as e:
            self.log(f"檢查市場狀態異常: {e}", "ERROR")
            return False
    
    def open_market_for_testing(self) -> bool:
        """開放市場進行測試"""
        try:
            from datetime import datetime, timezone, timedelta
            
            self.log("🔓 正在開放市場...")
            
            if not self.admin_token:
                self.log("請先登入管理員", "ERROR")
                return False
            
            # 設定市場開放時間為現在起24小時
            current_time = datetime.now(timezone.utc)
            start_time = int((current_time - timedelta(hours=1)).timestamp())  # 1小時前開始
            end_time = int((current_time + timedelta(hours=24)).timestamp())   # 24小時後結束
            
            response = self.session.post(
                f"{self.base_url}/api/admin/market/update",
                headers=self.get_admin_headers(),
                json={
                    "openTime": [
                        {
                            "start": start_time,
                            "end": end_time
                        }
                    ]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok", False):
                    self.log("✅ 市場已開放，交易時間: 現在 ~ 24小時後")
                    return True
                else:
                    self.log(f"❌ 開放市場失敗: {data.get('message', '未知錯誤')}", "ERROR")
                    return False
            else:
                self.log(f"❌ 開放市場請求失敗: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"開放市場異常: {e}", "ERROR")
            return False
    
    def get_admin_headers(self) -> Dict[str, str]:
        """取得管理員API請求標頭"""
        if not self.admin_token:
            raise ValueError("未登入管理員，請先呼叫 admin_login()")
        
        return {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.admin_token}'
        }
    
    def get_bot_headers(self) -> Dict[str, str]:
        """取得BOT API請求標頭"""
        return {
            'Content-Type': 'application/json',
            'token': BOT_TOKEN
        }
    
    # ========== 市場狀態查詢 ==========
    
    def get_market_status(self) -> Tuple[bool, int]:
        """
        取得市場狀態和目前股價
        
        Returns:
            Tuple[bool, int]: (是否開放交易, 目前股價)
        """
        try:
            # 檢查市場狀態
            market_response = self.session.get(f"{self.base_url}/api/status")
            is_open = True  # 預設開放
            if market_response.status_code == 200:
                market_data = market_response.json()
                is_open = market_data.get("isOpen", True)
            
            # 取得目前股價
            price_response = self.session.get(f"{self.base_url}/api/price/current")
            current_price = 20  # 預設價格
            if price_response.status_code == 200:
                price_data = price_response.json()
                current_price = price_data.get("price", 20)
            
            return is_open, current_price
            
        except Exception as e:
            self.log(f"查詢市場狀態異常: {e}", "WARNING")
            return True, 20  # 預設開放，價格20
    
    def show_market_info(self) -> None:
        """顯示市場資訊"""
        try:
            self.log("📈 正在查詢市場資訊...")
            
            # 市場狀態
            is_open, current_price = self.get_market_status()
            status_text = "🟢 開放中" if is_open else "🔴 已關閉"
            self.log(f"   市場狀態: {status_text}")
            self.log(f"   目前股價: {current_price} 元")
            
            # IPO狀態
            ipo_response = self.session.get(f"{self.base_url}/api/ipo/status")
            if ipo_response.status_code == 200:
                ipo_status = ipo_response.json()
                self.log(f"   IPO狀態: {ipo_status.get('sharesRemaining', 0)} / {ipo_status.get('initialShares', 0)} 股剩餘")
                self.log(f"   IPO價格: {ipo_status.get('initialPrice', 20)} 元/股")
            
            # 價格摘要
            summary_response = self.session.get(f"{self.base_url}/api/price/summary")
            if summary_response.status_code == 200:
                summary = summary_response.json()
                self.log(f"   開盤價: {summary.get('open', 20)} 元")
                self.log(f"   最高價: {summary.get('high', 20)} 元")
                self.log(f"   最低價: {summary.get('low', 20)} 元")
                self.log(f"   成交量: {summary.get('volume', 0)} 股")
                self.log(f"   漲跌: {summary.get('change', '+0')} ({summary.get('changePercent', '+0.0%')})")
            
            # 最近成交
            trades_response = self.session.get(f"{self.base_url}/api/price/trades?limit=3")
            if trades_response.status_code == 200:
                trades = trades_response.json()
                if trades:
                    self.log("   最近成交:")
                    for trade in trades[:3]:
                        self.log(f"     {trade.get('price', 0)} 元 x {trade.get('quantity', 0)} 股")
                        
        except Exception as e:
            self.log(f"顯示市場資訊異常: {e}", "WARNING")
    
    # ========== 學員啟用 ==========
    
    def enable_all_students(self, initial_points: int = 1000) -> bool:
        """
        啟用所有學員（通過給予初始點數）
        
        Args:
            initial_points: 初始點數
            
        Returns:
            bool: 是否成功
        """
        try:
            self.log(f"開始啟用所有學員，每人給予 {initial_points} 點數...")
            
            if not self.admin_token:
                self.log("請先登入管理員", "ERROR")
                return False
            
            success_count = 0
            failed_count = 0
            
            for student in STUDENTS_DATA:
                try:
                    # 給每個學員點數（這樣可以確保他們在系統中且有點數）
                    response = self.session.post(
                        f"{self.base_url}/api/admin/users/give-points",
                        headers=self.get_admin_headers(),
                        json={
                            "username": str(student["id"]),  # 使用ID作為username
                            "type": "user",
                            "amount": initial_points
                        }
                    )
                    
                    if response.status_code == 200:
                        success_count += 1
                        self.log(f"✓ 啟用學員: {student['name']} (ID: {student['id']}) - {student['team']}")
                    else:
                        failed_count += 1
                        self.log(f"✗ 啟用失敗: {student['name']} - {response.text}", "WARNING")
                    
                    # 避免過於頻繁的請求
                    # time.sleep(0.1)
                    
                except Exception as e:
                    failed_count += 1
                    self.log(f"✗ 啟用異常: {student['name']} - {e}", "ERROR")
            
            self.log(f"學員啟用完成: 成功 {success_count} 人，失敗 {failed_count} 人")
            return failed_count == 0
            
        except Exception as e:
            self.log(f"啟用學員過程異常: {e}", "ERROR")
            return False

    def simulate_initial_stock_distribution(self, max_stocks_per_person: int = 10) -> bool:
        """
        模擬初始股票發行 - 讓部分學員購買初始股票
        
        Args:
            max_stocks_per_person: 每人最多購買股數
            
        Returns:
            bool: 是否成功
        """
        try:
            self.log(f"🏭 開始模擬初始股票發行...")
            
            # 先檢查IPO狀態
            ipo_response = self.session.get(f"{self.base_url}/api/ipo/status")
            if ipo_response.status_code == 200:
                ipo_status = ipo_response.json()
                shares_available = ipo_status.get('sharesRemaining', 0)
                ipo_price = ipo_status.get('initialPrice', 20)
                self.log(f"   IPO庫存: {shares_available} 股")
                self.log(f"   IPO價格: {ipo_price} 點/股")
                
                if shares_available <= 0:
                    self.log("   ⚠️ IPO庫存已售完，無法從系統購買", "WARNING")
                    return False
            else:
                self.log("   ⚠️ 無法查詢IPO狀態", "WARNING")
                return False
            
            active_students = self.get_active_students()
            
            # 選擇40-60%的學員參與IPO購買
            buyers_ratio = random.uniform(0.4, 0.6)
            num_buyers = int(len(active_students) * buyers_ratio)
            buyers = random.sample(active_students, num_buyers)
            
            success_count = 0
            total_stocks_issued = 0
            ipo_purchases = 0
            market_purchases = 0
            
            self.log(f"   選擇 {num_buyers} 位學員參與IPO ({buyers_ratio:.1%})")
            self.log(f"   每人限購: {max_stocks_per_person} 股")
            
            for i, buyer in enumerate(buyers):
                try:
                    # 隨機購買1-max_stocks_per_person股
                    buy_quantity = random.randint(1, max_stocks_per_person)
                    
                    # 使用市價單從系統IPO購買股票
                    response = self.session.post(
                        f"{self.base_url}/api/bot/stock/order",
                        headers=self.get_bot_headers(),
                        json={
                            "from_user": str(buyer["id"]),
                            "order_type": "market",
                            "side": "buy",
                            "quantity": buy_quantity
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("success", False):
                            success_count += 1
                            total_stocks_issued += buy_quantity
                            executed_price = data.get("executed_price", ipo_price)
                            message = data.get("message", "")
                            order_id = data.get("order_id", "N/A")
                            
                            # 判斷是否為IPO購買
                            if "IPO申購" in message or executed_price == ipo_price:
                                ipo_purchases += 1
                                purchase_type = "🏭IPO"
                            else:
                                market_purchases += 1
                                purchase_type = "📈市價"
                                
                            self.log(f"💰 {buyer['name']} {purchase_type}購買 {buy_quantity} 股 @ {executed_price}元 ✅立即成交")
                            
                        else:
                            self.log(f"❌ {buyer['name']} 購買失敗: {data.get('message', '未知錯誤')}", "WARNING")
                    else:
                        self.log(f"❌ {buyer['name']} 購買請求失敗: {response.status_code}", "WARNING")
                    
                    # 每10筆交易檢查一次IPO狀態
                    if (i + 1) % 10 == 0:
                        ipo_check = self.session.get(f"{self.base_url}/api/ipo/status")
                        if ipo_check.status_code == 200:
                            current_ipo = ipo_check.json()
                            remaining = current_ipo.get('sharesRemaining', 0)
                            self.log(f"   📊 進度檢查 ({i+1}/{num_buyers}): IPO剩餘 {remaining} 股")
                    
                    time.sleep(0.1)  # 避免過於頻繁
                    
                except Exception as e:
                    self.log(f"❌ {buyer['name']} 購買異常: {e}", "ERROR")
            
            self.log(f"📈 初始股票發行完成:")
            self.log(f"   參與購買: {success_count}/{len(buyers)} 人")
            self.log(f"   IPO購買: {ipo_purchases} 筆")
            self.log(f"   市價購買: {market_purchases} 筆")
            self.log(f"   發行總量: {total_stocks_issued} 股")
            
            # 檢查最終IPO狀態
            final_ipo = self.session.get(f"{self.base_url}/api/ipo/status")
            if final_ipo.status_code == 200:
                final_status = final_ipo.json()
                remaining = final_status.get('sharesRemaining', 0)
                self.log(f"   🏭 IPO最終狀態: {remaining} 股剩餘")
            
            # 檢查成交情況
            self.check_recent_trades()
            
            return success_count > 0
            
        except Exception as e:
            self.log(f"初始股票發行異常: {e}", "ERROR")
            return False
    
    # ========== 點數轉帳模擬 ==========
    
    def get_active_students(self) -> List[Dict]:
        """取得活躍學員列表（用於交易模擬）"""
        # 過濾掉未分組的學員
        active_students = [
            student for student in STUDENTS_DATA 
            if student.get("team") and student["team"].strip()
        ]
        return active_students
    
    def simulate_random_transfer(self, min_amount: int = 10, max_amount: int = 200) -> bool:
        """
        模擬一次隨機轉帳
        
        Args:
            min_amount: 最小轉帳金額
            max_amount: 最大轉帳金額
            
        Returns:
            bool: 是否成功
        """
        try:
            active_students = self.get_active_students()
            
            if len(active_students) < 2:
                self.log("活躍學員數量不足，無法進行轉帳", "WARNING")
                return False
            
            # 隨機選擇轉帳雙方
            sender, receiver = random.sample(active_students, 2)
            amount = random.randint(min_amount, max_amount)
            
            # 產生隨機備註
            notes = [
                "感謝幫忙！",
                "請你喝飲料",
                "借一下點數",
                "團隊合作獎勵",
                "活動獎金",
                "小小心意",
                "Thanks!",
                "辛苦了！",
                "加油！",
                "買零食錢"
            ]
            note = random.choice(notes)
            
            # 進行轉帳
            response = self.session.post(
                f"{self.base_url}/api/bot/transfer",
                headers=self.get_bot_headers(),
                json={
                    "from_user": str(sender["id"]),
                    "to_username": str(receiver["id"]),
                    "amount": amount,
                    "note": note
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success", False):
                    fee = data.get("fee", 0)
                    self.update_stats('point_transfer', 'success', amount)
                    self.log(f"💰 轉帳成功: {sender['name']} → {receiver['name']} "
                           f"{amount} 點 (手續費: {fee}) 備註: {note}")
                    return True
                else:
                    self.update_stats('point_transfer', 'failed')
                    self.log(f"💸 轉帳失敗: {sender['name']} → {receiver['name']} "
                           f"{amount} 點 - {data.get('message', '未知錯誤')}", "WARNING")
                    return False
            else:
                self.update_stats('point_transfer', 'failed')
                self.log(f"💸 轉帳請求失敗: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.update_stats('point_transfer', 'failed')
            self.log(f"轉帳模擬異常: {e}", "ERROR")
            return False
    
    # ========== 股票交易模擬 ==========
    
    def simulate_smart_stock_trade(self) -> bool:
        """
        模擬智能股票交易（會檢查學員持股狀況）
        
        Returns:
            bool: 是否成功
        """
        try:
            active_students = self.get_active_students()
            
            if not active_students:
                self.log("沒有活躍學員可進行股票交易", "WARNING")
                return False
            
            # 檢查市場狀態
            is_open, current_price = self.get_market_status()
            if not is_open:
                self.log("市場未開放，無法進行股票交易", "WARNING")
                return False
            
            # 隨機選擇交易者
            trader = random.choice(active_students)
            
            # 查詢該學員的投資組合來決定買賣方向
            portfolio = self.get_student_portfolio(str(trader["id"]))
            if not portfolio:
                self.log(f"無法查詢 {trader['name']} 的投資組合", "WARNING")
                return False
            
            points = portfolio.get("points", 0)
            stocks = portfolio.get("stocks", 0)
            
            # 智能決定買賣方向
            if stocks > 0 and points > 0:
                # 有股票也有點數，隨機選擇
                side = random.choice(["buy", "sell"])
            elif stocks > 0:
                # 只有股票，選擇賣出
                side = "sell"
            elif points >= current_price:
                # 只有點數且足夠買股票，選擇買入
                side = "buy"
            else:
                # 點數不足買股票，跳過此次交易
                self.log(f"⏭️ {trader['name']} 點數不足購買股票 ({points} < {current_price})，跳過交易", "INFO")
                return False
            
            # 調整訂單類型比例，更多限價單創造價格變動（40%市價單，60%限價單）
            order_type = "market" if random.random() < 0.4 else "limit"
            
            # 根據買賣方向和持股情況決定交易數量
            if side == "buy":
                # 買入：根據點數決定最大可買數量
                max_buyable = min(50, points // current_price) if order_type == "market" else 50
                if max_buyable <= 0:
                    self.log(f"⏭️ {trader['name']} 點數不足購買股票，跳過交易", "INFO")
                    return False
                quantity = random.randint(1, max_buyable)
            else:
                # 賣出：根據持股決定最大可賣數量
                if stocks <= 0:
                    self.log(f"⏭️ {trader['name']} 無股票可賣，跳過交易", "INFO")
                    return False
                quantity = random.randint(1, min(stocks, 50))
            
            # 構建訂單
            order_data = {
                "from_user": str(trader["id"]),
                "order_type": order_type,
                "side": side,
                "quantity": quantity
            }
            
            # 如果是限價單，設定價格 - 增大價格變動幅度（目前價格±20-40%）
            if order_type == "limit":
                # 更大的價格變動範圍：±20-40%
                price_variation = random.uniform(-0.4, 0.4)
                
                # 買單傾向於出更高價，賣單傾向於要更高價，增加成交機會但也增加價格波動
                if side == "buy":
                    # 買單：80%機率出高價搶購，20%機率出低價等待
                    if random.random() < 0.8:
                        price_variation = abs(price_variation) * 0.8  # 出高價但不要太誇張
                    else:
                        price_variation = -abs(price_variation)  # 出低價等待
                else:
                    # 賣單：70%機率要高價，30%機率割肉賣出
                    if random.random() < 0.7:
                        price_variation = abs(price_variation)  # 要高價
                    else:
                        price_variation = -abs(price_variation) * 0.5  # 割肉但不要太過分
                
                limit_price = max(1, int(current_price * (1 + price_variation)))
                order_data["price"] = limit_price
                price_text = f" @ {limit_price}元"
            else:
                price_text = " (市價)"
            
            # 提交訂單
            response = self.session.post(
                f"{self.base_url}/api/bot/stock/order",
                headers=self.get_bot_headers(),
                json=order_data
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success", False):
                    self.update_stats('stock_trade', 'success', quantity)
                    
                    action = "買入" if side == "buy" else "賣出"
                    order_id = data.get("order_id", "N/A")
                    executed_price = data.get("executed_price")
                    
                    if executed_price:
                        self.log(f"📈 股票交易成功: {trader['name']} {action} {quantity} 股{price_text} "
                               f"(成交價: {executed_price}元, 訂單ID: {order_id[:8]}...)")
                    else:
                        self.log(f"📋 限價單已提交: {trader['name']} {action} {quantity} 股{price_text} "
                               f"(訂單ID: {order_id[:8]}...)")
                    return True
                else:
                    self.update_stats('stock_trade', 'failed')
                    self.log(f"📉 股票交易失敗: {trader['name']} - {data.get('message', '未知錯誤')}", "WARNING")
                    return False
            else:
                self.update_stats('stock_trade', 'failed')
                self.log(f"📉 股票交易請求失敗: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.update_stats('stock_trade', 'failed')
            self.log(f"股票交易模擬異常: {e}", "ERROR")
            return False

    def check_recent_trades(self, limit: int = 10) -> None:
        """檢查最近成交記錄"""
        try:
            self.log("🔍 檢查最近成交記錄...")
            
            # 檢查成交記錄
            trades_response = self.session.get(f"{self.base_url}/api/price/trades?limit={limit}")
            if trades_response.status_code == 200:
                trades = trades_response.json()
                self.log(f"   最近成交記錄數: {len(trades)} 筆")
                
                if trades:
                    for i, trade in enumerate(trades[:5]):  # 只顯示前5筆
                        self.log(f"   #{i+1}: {trade.get('price', 'N/A')} 元 x {trade.get('quantity', 0)} 股 "
                               f"({trade.get('timestamp', 'N/A')})")
                else:
                    self.log("   ⚠️ 沒有找到成交記錄")
            else:
                self.log(f"   ❌ 查詢成交記錄失敗: {trades_response.status_code}")
            
            # 檢查歷史價格
            history_response = self.session.get(f"{self.base_url}/api/price/history?hours=1")
            if history_response.status_code == 200:
                history = history_response.json()
                self.log(f"   過去1小時價格記錄: {len(history)} 筆")
                
                if history:
                    latest = history[-1] if history else {}
                    self.log(f"   最新價格記錄: {latest.get('price', 'N/A')} 元 "
                           f"({latest.get('timestamp', 'N/A')})")
                else:
                    self.log("   ⚠️ 沒有找到價格歷史記錄")
            else:
                self.log(f"   ❌ 查詢價格歷史失敗: {history_response.status_code}")
                
        except Exception as e:
            self.log(f"檢查成交記錄異常: {e}", "WARNING")

    def check_pending_orders(self) -> None:
        """檢查待成交訂單"""
        try:
            self.log("🔍 檢查五檔報價和待成交訂單...")
            
            # 檢查五檔報價
            depth_response = self.session.get(f"{self.base_url}/api/price/depth")
            if depth_response.status_code == 200:
                depth = depth_response.json()
                buy_orders = depth.get("buy", [])
                sell_orders = depth.get("sell", [])
                
                self.log(f"   買方掛單: {len(buy_orders)} 檔")
                for i, order in enumerate(buy_orders[:3]):
                    self.log(f"     買{i+1}: {order.get('price', 'N/A')} 元 x {order.get('quantity', 0)} 股")
                
                self.log(f"   賣方掛單: {len(sell_orders)} 檔")
                for i, order in enumerate(sell_orders[:3]):
                    self.log(f"     賣{i+1}: {order.get('price', 'N/A')} 元 x {order.get('quantity', 0)} 股")
                    
                if not buy_orders and not sell_orders:
                    self.log("   ⚠️ 沒有掛單，這可能解釋為什麼沒有成交")
                    
            else:
                self.log(f"   ❌ 查詢五檔報價失敗: {depth_response.status_code}")
                
        except Exception as e:
            self.log(f"檢查掛單異常: {e}", "WARNING")

    def create_manual_trades(self) -> None:
        """手動建立一些對向交易來測試撮合"""
        try:
            self.log("🧪 建立測試對向交易...")
            
            active_students = self.get_active_students()
            if len(active_students) < 2:
                self.log("學員數量不足", "WARNING")
                return
            
            # 選擇兩個學員
            buyer, seller = random.sample(active_students, 2)
            current_price = 20  # 使用固定價格
            
            # 先讓賣方下賣單
            sell_response = self.session.post(
                f"{self.base_url}/api/bot/stock/order",
                headers=self.get_bot_headers(),
                json={
                    "from_user": str(seller["id"]),
                    "order_type": "limit",
                    "side": "sell",
                    "quantity": 1,
                    "price": current_price
                }
            )
            
            if sell_response.status_code == 200:
                sell_data = sell_response.json()
                if sell_data.get("success"):
                    self.log(f"📋 {seller['name']} 掛賣單: 1股 @ {current_price}元")
                    
                    # time.sleep(1)  # 等待1秒
                    
                    # 再讓買方下買單（價格稍高以確保成交）
                    buy_response = self.session.post(
                        f"{self.base_url}/api/bot/stock/order",
                        headers=self.get_bot_headers(),
                        json={
                            "from_user": str(buyer["id"]),
                            "order_type": "limit",
                            "side": "buy",
                            "quantity": 1,
                            "price": current_price
                        }
                    )
                    
                    if buy_response.status_code == 200:
                        buy_data = buy_response.json()
                        if buy_data.get("success"):
                            self.log(f"📋 {buyer['name']} 掛買單: 1股 @ {current_price}元")
                            
                            # time.sleep(2)  # 等待撮合
                            self.check_recent_trades(5)
                        else:
                            self.log(f"買單失敗: {buy_data.get('message')}", "WARNING")
                    else:
                        self.log(f"買單請求失敗: {buy_response.status_code}", "WARNING")
                else:
                    self.log(f"賣單失敗: {sell_data.get('message')}", "WARNING")
            else:
                self.log(f"賣單請求失敗: {sell_response.status_code}", "WARNING")
                
        except Exception as e:
            self.log(f"手動交易測試異常: {e}", "ERROR")
    
    def get_student_portfolio(self, student_id: str) -> Optional[Dict]:
        """查詢指定學員的投資組合"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/bot/portfolio",
                headers=self.get_bot_headers(),
                json={"from_user": student_id}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.log(f"查詢學員 {student_id} 投資組合失敗: {response.status_code} - {response.text}", "WARNING")
                return None
            
        except Exception as e:
            self.log(f"查詢學員 {student_id} 投資組合異常: {e}", "WARNING")
            return None

    def get_random_portfolio(self) -> Optional[Dict]:
        """隨機查詢一個學員的投資組合"""
        try:
            active_students = self.get_active_students()
            if not active_students:
                return None
            
            student = random.choice(active_students)
            
            response = self.session.post(
                f"{self.base_url}/api/bot/portfolio",
                headers=self.get_bot_headers(),
                json={"from_user": str(student["id"])}
            )
            
            if response.status_code == 200:
                portfolio = response.json()
                portfolio["student_name"] = student["name"]
                return portfolio
            
        except Exception as e:
            self.log(f"查詢投資組合異常: {e}", "WARNING")
        
        return None
    
    # ========== 多執行緒交易模擬 ==========
    
    def worker_thread(self, thread_id: int, transactions_per_thread: int, 
                     stock_ratio: float, delay_range: tuple) -> Dict:
        """單一工作執行緒的交易邏輯"""
        thread_stats = {
            'point_transfers': {'success': 0, 'failed': 0},
            'stock_trades': {'success': 0, 'failed': 0},
            'total_points_transferred': 0,
            'total_stocks_traded': 0,
            'thread_id': thread_id
        }
        
        try:
            # 每個執行緒需要自己的 session 來避免衝突
            thread_session = requests.Session()
            thread_session.headers.update({
                'Content-Type': 'application/json'
            })
            original_session = self.session
            self.session = thread_session
            
            for i in range(transactions_per_thread):
                try:
                    # 隨機決定交易類型
                    is_stock_trade = random.random() < stock_ratio
                    
                    if is_stock_trade:
                        success = self.simulate_smart_stock_trade()
                        if success:
                            thread_stats['stock_trades']['success'] += 1
                        else:
                            thread_stats['stock_trades']['failed'] += 1
                    else:
                        success = self.simulate_random_transfer()
                        if success:
                            thread_stats['point_transfers']['success'] += 1
                        else:
                            thread_stats['point_transfers']['failed'] += 1
                    
                    # 隨機延遲
                    if i < transactions_per_thread - 1:
                        delay = random.uniform(delay_range[0], delay_range[1])
                        time.sleep(delay)
                        
                except Exception as e:
                    self.log(f"執行緒 {thread_id} 交易 {i+1} 異常: {e}", "ERROR")
            
            # 恢復原來的 session
            self.session = original_session
            
        except Exception as e:
            self.log(f"執行緒 {thread_id} 異常: {e}", "ERROR")
            # 恢復原來的 session
            self.session = original_session
        
        return thread_stats
    
    def simulate_concurrent_trading(self, total_transactions: int = 100, 
                                  num_threads: int = 5,
                                  stock_ratio: float = 0.4, 
                                  delay_range: tuple = (0.5, 2.0)) -> None:
        """
        多執行緒混合交易模擬（模擬多使用者同時交易）
        
        Args:
            total_transactions: 總交易次數
            num_threads: 執行緒數量（模擬同時在線使用者數）
            stock_ratio: 股票交易比例 (0.0-1.0)
            delay_range: 每次交易間的延遲時間範圍（秒）
        """
        try:
            self.log(f"🚀 開始多執行緒交易模擬...")
            self.log(f"總交易次數: {total_transactions} 筆")
            self.log(f"執行緒數量: {num_threads} 個 (模擬 {num_threads} 個同時在線使用者)")
            self.log(f"股票交易比例: {stock_ratio:.1%}，點數轉帳比例: {1-stock_ratio:.1%}")
            
            # 顯示市場資訊
            self.show_market_info()
            
            # 計算每個執行緒的交易數量
            transactions_per_thread = total_transactions // num_threads
            remaining_transactions = total_transactions % num_threads
            
            self.log(f"每個執行緒處理: {transactions_per_thread} 筆交易")
            if remaining_transactions > 0:
                self.log(f"額外分配: {remaining_transactions} 筆交易給前 {remaining_transactions} 個執行緒")
            
            # 重置統計
            with self.stats_lock:
                self.stats = {
                    'point_transfers': {'success': 0, 'failed': 0},
                    'stock_trades': {'success': 0, 'failed': 0},
                    'total_points_transferred': 0,
                    'total_stocks_traded': 0
                }
            
            start_time = time.time()
            
            # 使用 ThreadPoolExecutor 管理執行緒
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
                # 提交所有工作
                futures = []
                for i in range(num_threads):
                    # 前面的執行緒處理額外的交易
                    thread_transactions = transactions_per_thread + (1 if i < remaining_transactions else 0)
                    future = executor.submit(
                        self.worker_thread, 
                        i + 1, 
                        thread_transactions, 
                        stock_ratio, 
                        delay_range
                    )
                    futures.append(future)
                
                # 等待所有執行緒完成並收集結果
                thread_results = []
                for i, future in enumerate(concurrent.futures.as_completed(futures)):
                    try:
                        result = future.result()
                        thread_results.append(result)
                        self.log(f"✅ 執行緒 {result['thread_id']} 完成")
                    except Exception as e:
                        self.log(f"❌ 執行緒異常: {e}", "ERROR")
            
            end_time = time.time()
            duration = end_time - start_time
            
            self.log(f"🎉 多執行緒交易模擬完成！執行時間: {duration:.2f} 秒")
            
            # 顯示詳細統計
            self.show_concurrent_trading_summary(thread_results, duration)
            
        except KeyboardInterrupt:
            self.log("多執行緒交易模擬被使用者中斷", "WARNING")
        except Exception as e:
            self.log(f"多執行緒交易模擬異常: {e}", "ERROR")
    
    def show_concurrent_trading_summary(self, thread_results: List[Dict], duration: float):
        """顯示多執行緒交易統計摘要"""
        self.log("📊 多執行緒交易統計摘要:")
        
        # 匯總所有執行緒的結果
        total_point_success = sum(r['point_transfers']['success'] for r in thread_results)
        total_point_failed = sum(r['point_transfers']['failed'] for r in thread_results)
        total_stock_success = sum(r['stock_trades']['success'] for r in thread_results)
        total_stock_failed = sum(r['stock_trades']['failed'] for r in thread_results)
        
        self.log(f"   執行緒數量: {len(thread_results)} 個")
        self.log(f"   總執行時間: {duration:.2f} 秒")
        self.log(f"   平均TPS: {(total_point_success + total_point_failed + total_stock_success + total_stock_failed) / duration:.2f} 筆/秒")
        
        self.log(f"   點數轉帳: 成功 {total_point_success} 筆，失敗 {total_point_failed} 筆")
        self.log(f"   股票交易: 成功 {total_stock_success} 筆，失敗 {total_stock_failed} 筆")
        
        total_success = total_point_success + total_stock_success
        total_failed = total_point_failed + total_stock_failed
        total_transactions = total_success + total_failed
        
        if total_transactions > 0:
            success_rate = (total_success / total_transactions) * 100
            self.log(f"   總成功率: {success_rate:.1f}% ({total_success}/{total_transactions})")
        
        # 顯示各執行緒詳細統計
        self.log("   各執行緒統計:")
        for result in sorted(thread_results, key=lambda x: x['thread_id']):
            tid = result['thread_id']
            pt_s = result['point_transfers']['success']
            pt_f = result['point_transfers']['failed']
            st_s = result['stock_trades']['success']
            st_f = result['stock_trades']['failed']
            self.log(f"     執行緒{tid}: 轉帳({pt_s}✓/{pt_f}✗) 股票({st_s}✓/{st_f}✗)")
        
        # 顯示目前市場狀態
        self.log("📈 交易後市場狀態:")
        self.show_market_info()
    
    # ========== 混合交易模擬 ==========
    
    def simulate_mixed_trading(self, total_transactions: int = 100, 
                             stock_ratio: float = 0.4, 
                             delay_range: tuple = (1, 5)) -> None:
        """
        模擬混合交易（點數轉帳 + 股票交易）
        
        Args:
            total_transactions: 總交易次數
            stock_ratio: 股票交易比例 (0.0-1.0)
            delay_range: 每次交易間的延遲時間範圍（秒）
        """
        try:
            self.log(f"開始模擬 {total_transactions} 筆混合交易...")
            self.log(f"股票交易比例: {stock_ratio:.1%}，點數轉帳比例: {1-stock_ratio:.1%}")
            
            # 顯示市場資訊
            self.show_market_info()
            
            for i in range(1, total_transactions + 1):
                # 隨機決定交易類型
                is_stock_trade = random.random() < stock_ratio
                
                if is_stock_trade:
                    self.log(f"進行第 {i}/{total_transactions} 筆交易 [股票]")
                    success = self.simulate_smart_stock_trade()
                else:
                    self.log(f"進行第 {i}/{total_transactions} 筆交易 [轉帳]")
                    success = self.simulate_random_transfer()
                
                # 每10筆交易後顯示一次投資組合
                if i % 10 == 0:
                    portfolio = self.get_random_portfolio()
                    if portfolio:
                        self.log(f"💼 {portfolio['student_name']} 的投資組合: "
                               f"點數 {portfolio.get('points', 0)}, "
                               f"持股 {portfolio.get('stocks', 0)} 股 "
                               f"(總價值 {portfolio.get('totalValue', 0)} 點)")
                
                # 隨機延遲
                if i < total_transactions:
                    delay = random.uniform(delay_range[0], delay_range[1])
                    # time.sleep(delay)
            
            self.show_trading_summary()
            
        except KeyboardInterrupt:
            self.log("交易模擬被使用者中斷", "WARNING")
            self.show_trading_summary()
        except Exception as e:
            self.log(f"交易模擬異常: {e}", "ERROR")
    
    def show_trading_summary(self) -> None:
        """顯示交易統計摘要"""
        self.log("📊 交易統計摘要:")
        self.log(f"   點數轉帳: 成功 {self.stats['point_transfers']['success']} 筆，"
               f"失敗 {self.stats['point_transfers']['failed']} 筆")
        self.log(f"   股票交易: 成功 {self.stats['stock_trades']['success']} 筆，"
               f"失敗 {self.stats['stock_trades']['failed']} 筆")
        self.log(f"   總轉帳點數: {self.stats['total_points_transferred']} 點")
        self.log(f"   總交易股數: {self.stats['total_stocks_traded']} 股")
        
        total_success = (self.stats['point_transfers']['success'] + 
                        self.stats['stock_trades']['success'])
        total_failed = (self.stats['point_transfers']['failed'] + 
                       self.stats['stock_trades']['failed'])
        total_transactions = total_success + total_failed
        
        if total_transactions > 0:
            success_rate = (total_success / total_transactions) * 100
            self.log(f"   總成功率: {success_rate:.1f}% ({total_success}/{total_transactions})")
    
    # ========== 系統統計 ==========
    
    def get_system_stats(self) -> None:
        """查看系統統計"""
        try:
            self.log("正在取得系統統計資訊...")
            
            if not self.admin_token:
                self.log("請先登入管理員", "ERROR")
                return
            
            response = self.session.get(
                f"{self.base_url}/api/admin/stats",
                headers=self.get_admin_headers()
            )
            
            if response.status_code == 200:
                stats = response.json()
                self.log("📊 系統統計資訊:")
                self.log(f"   總使用者數: {stats.get('total_users', 0)}")
                self.log(f"   總群組數: {stats.get('total_groups', 0)}")
                self.log(f"   總點數: {stats.get('total_points', 0)}")
                self.log(f"   總股票數(單位:股): {stats.get('total_stocks', 0)}")
                self.log(f"   總交易次數: {stats.get('total_trades', 0)}")
                
                # 額外顯示市場資訊
                self.show_market_info()
            else:
                self.log(f"取得統計資訊失敗: {response.status_code} - {response.text}", "ERROR")
                
        except Exception as e:
            self.log(f"取得統計資訊異常: {e}", "ERROR")
    
    # ========== 快速測試功能 ==========
    
    def quick_market_test(self) -> None:
        """快速市場測試 - 少量交易來測試系統"""
        self.log("🚀 開始快速市場測試...")
        
        # 顯示目前市場狀態
        self.show_market_info()
        
        # 進行5筆隨機交易
        self.log("進行 5 筆測試交易...")
        for i in range(5):
            if i % 2 == 0:
                self.simulate_smart_stock_trade()
            else:
                self.simulate_random_transfer()
            time.sleep(1)
        
        # 顯示投資組合樣本
        portfolio = self.get_random_portfolio()
        if portfolio:
            self.log(f"💼 隨機投資組合樣本 ({portfolio['student_name']}):")
            self.log(f"   點數: {portfolio.get('points', 0)}")
            self.log(f"   持股: {portfolio.get('stocks', 0)} 股")
            self.log(f"   股票價值: {portfolio.get('stockValue', 0)} 點")
            self.log(f"   總價值: {portfolio.get('totalValue', 0)} 點")
        
        self.show_trading_summary()
        self.log("✅ 快速市場測試完成")


def main():
    """主程式"""
    print("🏫 SITCON Camp 2025 學員啟用與交易模擬腳本 (含股票交易)")
    print("=" * 60)
    
    # 初始化模擬器
    simulator = CampTradingSimulator()
    
    # 檢查API連線
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ API 連線失敗: {response.status_code}")
            sys.exit(1)
        print("✅ API 連線正常")
    except Exception as e:
        print(f"❌ 無法連接到 API: {e}")
        print(f"請確認後端服務已啟動，並檢查 BASE_URL: {BASE_URL}")
        sys.exit(1)
    
    # 管理員登入
    if not simulator.admin_login():
        print("❌ 管理員登入失敗，程式結束")
        sys.exit(1)
    
    # 檢查並確保市場開放
    print("\n🏪 檢查市場狀態...")
    if not simulator.check_and_ensure_market_open():
        print("❌ 市場未開放且無法開啟，程式結束")
        sys.exit(1)
    
    # 詢問使用者要執行的操作
    print("\n請選擇要執行的操作:")
    print("1. 啟用所有學員 (給予初始點數)")
    print("2. 進行點數轉帳模擬")
    print("3. 進行股票交易模擬 (含初始發行)")
    print("4. 進行混合交易模擬 (轉帳 + 股票)")
    print("5. 🚀 多執行緒混合交易模擬 (模擬多使用者同時交易)")
    print("6. 啟用學員 + 股票發行 + 混合交易 (完整流程)")
    print("7. 查看系統統計和市場狀態")
    print("8. 快速市場測試")
    print("9. 深度調試 - 檢查成交和撮合機制")
    print("10. 重置IPO狀態")
    print("11. 重置所有資料")
    print("12. 退出")
    
    while True:
        try:
            choice = input("\n請輸入選項 (1-12): ").strip()
            
            if choice == "1":
                initial_points = input("請輸入初始點數 (預設 1000): ").strip()
                initial_points = int(initial_points) if initial_points.isdigit() else 1000
                simulator.enable_all_students(initial_points)
                break
                
            elif choice == "2":
                num_transactions = input("請輸入轉帳次數 (預設 20): ").strip()
                num_transactions = int(num_transactions) if num_transactions.isdigit() else 20
                
                print(f"\n🚀 開始進行 {num_transactions} 筆點數轉帳...")
                for i in range(num_transactions):
                    print(f"進行第 {i+1}/{num_transactions} 筆轉帳")
                    simulator.simulate_random_transfer()
                    # time.sleep(random.uniform(1, 3))
                simulator.show_trading_summary()
                break
                
            elif choice == "3":
                num_transactions = input("請輸入股票交易次數 (預設 20): ").strip()
                num_transactions = int(num_transactions) if num_transactions.isdigit() else 20
                
                print(f"\n📈 開始進行 {num_transactions} 筆股票交易...")
                simulator.show_market_info()
                
                # 先進行初始股票發行
                print("\n🏭 先進行初始股票發行...")
                simulator.simulate_initial_stock_distribution()
                print("\n等待 3 秒後開始股票交易...")
                
                
                for i in range(num_transactions):
                    print(f"進行第 {i+1}/{num_transactions} 筆股票交易")
                    simulator.simulate_smart_stock_trade()
                    # time.sleep(random.uniform(1, 3))
                simulator.show_trading_summary()
                break
                
            elif choice == "4":
                num_transactions = input("請輸入總交易次數 (預設 50): ").strip()
                num_transactions = int(num_transactions) if num_transactions.isdigit() else 50
                
                stock_ratio = input("請輸入股票交易比例 0-100% (預設 40): ").strip()
                if stock_ratio.isdigit():
                    stock_ratio = min(100, max(0, int(stock_ratio))) / 100
                else:
                    stock_ratio = 0.4
                
                simulator.simulate_mixed_trading(num_transactions, stock_ratio)
                break
                
            elif choice == "5":
                # 多執行緒混合交易模擬
                num_transactions = input("請輸入總交易次數 (預設 100): ").strip()
                num_transactions = int(num_transactions) if num_transactions.isdigit() else 100
                
                num_threads = input("請輸入執行緒數量 (預設 5): ").strip()
                num_threads = int(num_threads) if num_threads.isdigit() and int(num_threads) > 0 else 5
                num_threads = min(num_threads, 20)  # 限制最多20個執行緒
                
                stock_ratio = input("請輸入股票交易比例 0-100% (預設 40): ").strip()
                if stock_ratio.isdigit():
                    stock_ratio = min(100, max(0, int(stock_ratio))) / 100
                else:
                    stock_ratio = 0.4
                
                delay_range_input = input("請輸入交易延遲範圍 (秒, 格式: min,max, 預設 0.5,2.0): ").strip()
                try:
                    if delay_range_input and ',' in delay_range_input:
                        min_delay, max_delay = map(float, delay_range_input.split(','))
                        delay_range = (min_delay, max_delay)
                    else:
                        delay_range = (0.5, 2.0)
                except:
                    delay_range = (0.5, 2.0)
                
                print(f"\n🚀 啟動多執行緒交易模擬...")
                print(f"   總交易次數: {num_transactions}")
                print(f"   執行緒數量: {num_threads} (模擬 {num_threads} 個同時在線使用者)")
                print(f"   股票交易比例: {stock_ratio:.1%}")
                print(f"   交易延遲: {delay_range[0]}-{delay_range[1]} 秒")
                
                simulator.simulate_concurrent_trading(num_transactions, num_threads, stock_ratio, delay_range)
                break
                
            elif choice == "6":
                # 完整流程
                initial_points = input("請輸入初始點數 (預設 1000): ").strip()
                initial_points = int(initial_points) if initial_points.isdigit() else 1000
                
                num_transactions = input("請輸入總交易次數 (預設 50): ").strip()
                num_transactions = int(num_transactions) if num_transactions.isdigit() else 50
                
                stock_ratio = input("請輸入股票交易比例 0-100% (預設 40): ").strip()
                if stock_ratio.isdigit():
                    stock_ratio = min(100, max(0, int(stock_ratio))) / 100
                else:
                    stock_ratio = 0.4
                
                print("\n🚀 開始執行完整流程...")
                
                # 1. 啟用學員
                if simulator.enable_all_students(initial_points):
                    print("\n✅ 學員啟用完成，等待 3 秒後進行初始股票發行...")
                    
                    
                    # 2. 初始股票發行
                    simulator.simulate_initial_stock_distribution()
                    print("\n等待 3 秒後開始交易模擬...")
                    
                    
                    # 3. 混合交易模擬
                    simulator.simulate_mixed_trading(num_transactions, stock_ratio)
                else:
                    print("\n❌ 學員啟用過程中出現錯誤，是否繼續交易模擬？")
                    continue_choice = input("繼續? (y/N): ").strip().lower()
                    if continue_choice == 'y':
                        # 即使啟用失敗，也先進行股票發行再交易
                        simulator.simulate_initial_stock_distribution()
                        
                        simulator.simulate_mixed_trading(num_transactions, stock_ratio)
                break
                
            elif choice == "7":
                simulator.get_system_stats()
                break
                
            elif choice == "8":
                simulator.quick_market_test()
                break
                
            elif choice == "9":
                print("\n🔍 深度調試模式")
                print("正在檢查系統狀態...")
                
                # 檢查市場資訊
                simulator.show_market_info()
                
                # 檢查成交記錄
                simulator.check_recent_trades(20)
                
                # 檢查掛單情況
                simulator.check_pending_orders()
                
                # 詢問是否進行測試交易
                test_choice = input("\n是否進行測試對向交易? (y/N): ").strip().lower()
                if test_choice == 'y':
                    simulator.create_manual_trades()
                
                break
                
            elif choice == "10":
                # 重置IPO狀態
                initial_shares = input("請輸入IPO初始股數 (預設 1000): ").strip()
                initial_shares = int(initial_shares) if initial_shares.isdigit() else 1000
                
                initial_price = input("請輸入IPO初始價格 (預設 20): ").strip()
                initial_price = int(initial_price) if initial_price.isdigit() else 20
                
                if simulator.reset_ipo_for_testing(initial_shares, initial_price):
                    print("✅ IPO狀態已重置")
                    simulator.show_market_info()
                else:
                    print("❌ IPO重置失敗")
                break
                
            elif choice == "11":
                # 重置所有資料
                confirm = input("⚠️ 這將刪除所有資料，確定要繼續嗎？ (y/N): ").strip().lower()
                if confirm == 'y':
                    if simulator.reset_all_data():
                        print("✅ 所有資料已重置")
                        simulator.show_market_info()
                    else:
                        print("❌ 資料重置失敗")
                else:
                    print("❌ 操作已取消")
                break
                
            elif choice == "12":
                print("👋 程式結束")
                sys.exit(0)
                
            else:
                print("❌ 無效選項，請重新輸入")
                
        except ValueError:
            print("❌ 請輸入有效的數字")
        except KeyboardInterrupt:
            print("\n👋 程式被使用者中斷")
            sys.exit(0)
    
    # 最後顯示統計
    print("\n" + "=" * 60)
    simulator.get_system_stats()
    print("🎉 腳本執行完成！")


if __name__ == "__main__":
    main()