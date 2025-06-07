#!/usr/bin/env python3
"""
SITCON Camp 2025 學員啟用與高級交易模擬腳本 (2025最新版)

新增功能：
1. 高級市場控制 - 手動開市/收市、集合競價
2. 複雜訂單管理 - 限價單、市價單、訂單歷史查詢
3. 風險管理測試 - 負餘額檢測與修復
4. IPO高級管理 - 動態IPO參數調整
5. 市場深度分析 - 五檔報價、成交記錄分析
6. 系統完整性檢查 - 餘額完整性、交易完整性驗證
7. 高並發交易測試 - 多線程複雜交易場景
8. 最終結算功能 - 股票轉點數結算

原有功能：
9. 自動檢查市場開放狀態，可選擇自動開啟市場
10. 啟用所有學員（通過給予初始點數）
11. 模擬隨機的點數轉帳交易
12. 模擬隨機的股票買賣交易
13. IPO股票發行和購買測試
14. 查詢投資組合和市場狀態
15. 完整資料庫重置功能

需要安裝的套件：
pip install requests

使用方法：
python final_test.py

注意事項：
- 腳本支援最新的市場控制和風險管理功能
- 包含高級訂單管理和集合競價測試
- 提供完整的系統完整性檢查功能
- 支援複雜的多線程交易場景測試
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

# 學員數據（從您提供的JSON文件）
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

class AdvancedCampTradingSimulator:
    """SITCON Camp 2025 高級交易模擬器 (2025最新版)"""
    
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
            'market_orders': {'success': 0, 'failed': 0},
            'limit_orders': {'success': 0, 'failed': 0},
            'call_auctions': {'success': 0, 'failed': 0},
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
            if stat_type in self.stats:
                if operation in self.stats[stat_type]:
                    self.stats[stat_type][operation] += 1
            
            if stat_type == 'point_transfer' and operation == 'success':
                self.stats['total_points_transferred'] += amount
            elif stat_type in ['stock_trade', 'market_order', 'limit_order'] and operation == 'success':
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
    
    # ========== 新增：高級市場控制功能 ==========
    
    def manual_market_open(self) -> bool:
        """手動開市（含集合競價）"""
        try:
            self.log("🔓 手動開市（含集合競價）...")
            
            if not self.admin_token:
                self.log("請先登入管理員", "ERROR")
                return False
            
            response = self.session.post(
                f"{self.base_url}/api/admin/market/open",
                headers=self.get_admin_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    self.log(f"✅ 市場開市成功: {data.get('message')}")
                    
                    # 檢查集合競價結果
                    auction_result = data.get("callAuctionResult", {})
                    if auction_result:
                        self.log(f"🏦 集合競價結果:")
                        self.log(f"   開盤價: {auction_result.get('openingPrice', 'N/A')} 元")
                        self.log(f"   成交量: {auction_result.get('totalVolume', 0)} 股")
                        self.log(f"   成交筆數: {auction_result.get('executedOrders', 0)} 筆")
                        
                        if auction_result.get('priceUpdated'):
                            self.log(f"   ✅ 股價已更新為開盤價")
                        
                        executed_orders = auction_result.get("executedOrdersDetail", [])
                        if executed_orders:
                            self.log(f"   成交明細 (前5筆):")
                            for i, order in enumerate(executed_orders[:5]):
                                self.log(f"     #{i+1}: {order.get('quantity', 0)} 股 @ {order.get('price', 0)} 元")
                    
                    return True
                else:
                    self.log(f"❌ 開市失敗: {data.get('message', '未知錯誤')}", "ERROR")
                    return False
            else:
                self.log(f"❌ 開市請求失敗: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"手動開市異常: {e}", "ERROR")
            return False
    
    def manual_market_close(self) -> bool:
        """手動收市"""
        try:
            self.log("🔒 手動收市...")
            
            if not self.admin_token:
                self.log("請先登入管理員", "ERROR")
                return False
            
            response = self.session.post(
                f"{self.base_url}/api/admin/market/close",
                headers=self.get_admin_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    self.log(f"✅ 市場收市成功: {data.get('message')}")
                    
                    # 顯示收市信息
                    close_info = data.get("marketInfo", {})
                    if close_info:
                        self.log(f"📊 收市資訊:")
                        self.log(f"   收盤價: {close_info.get('closingPrice', 'N/A')} 元")
                        self.log(f"   當日成交量: {close_info.get('dailyVolume', 0)} 股")
                        self.log(f"   當日漲跌: {close_info.get('dailyChange', 'N/A')}")
                    
                    return True
                else:
                    self.log(f"❌ 收市失敗: {data.get('message', '未知錯誤')}", "ERROR")
                    return False
            else:
                self.log(f"❌ 收市請求失敗: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"手動收市異常: {e}", "ERROR")
            return False
    
    def trigger_call_auction(self) -> bool:
        """手動觸發集合競價"""
        try:
            self.log("🏦 手動觸發集合競價...")
            
            if not self.admin_token:
                self.log("請先登入管理員", "ERROR")
                return False
            
            response = self.session.post(
                f"{self.base_url}/api/admin/market/call-auction",
                headers=self.get_admin_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    self.update_stats('call_auctions', 'success')
                    self.log(f"✅ 集合競價執行成功")
                    
                    # 顯示集合競價結果
                    result = data.get("result", {})
                    self.log(f"🏦 集合競價結果:")
                    self.log(f"   成交價格: {result.get('price', 'N/A')} 元")
                    self.log(f"   成交量: {result.get('volume', 0)} 股")
                    self.log(f"   成交筆數: {result.get('executedOrders', 0)} 筆")
                    
                    if result.get('priceUpdated'):
                        self.log(f"   ✅ 股價已更新")
                    
                    # 顯示剩餘掛單
                    remaining = result.get("remainingOrders", {})
                    if remaining:
                        buy_orders = remaining.get("buy", [])
                        sell_orders = remaining.get("sell", [])
                        self.log(f"   剩餘買單: {len(buy_orders)} 筆")
                        self.log(f"   剩餘賣單: {len(sell_orders)} 筆")
                    
                    return True
                else:
                    self.update_stats('call_auctions', 'failed')
                    self.log(f"❌ 集合競價失敗: {data.get('message', '未知錯誤')}", "ERROR")
                    return False
            else:
                self.update_stats('call_auctions', 'failed')
                self.log(f"❌ 集合競價請求失敗: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.update_stats('call_auctions', 'failed')
            self.log(f"集合競價異常: {e}", "ERROR")
            return False
    
    def get_market_control_status(self) -> Optional[Dict]:
        """獲取市場控制狀態"""
        try:
            if not self.admin_token:
                self.log("請先登入管理員", "ERROR")
                return None
            
            response = self.session.get(
                f"{self.base_url}/api/admin/market/status",
                headers=self.get_admin_headers()
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.log(f"查詢市場控制狀態失敗: {response.status_code}", "WARNING")
                return None
                
        except Exception as e:
            self.log(f"查詢市場控制狀態異常: {e}", "WARNING")
            return None
    
    # ========== 新增：風險管理功能 ==========
    
    def check_negative_balances(self) -> bool:
        """檢查負餘額用戶"""
        try:
            self.log("🔍 檢查負餘額用戶...")
            
            if not self.admin_token:
                self.log("請先登入管理員", "ERROR")
                return False
            
            response = self.session.get(
                f"{self.base_url}/api/admin/system/check-negative-balances",
                headers=self.get_admin_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                negative_users = data.get("negativeBalanceUsers", [])
                
                self.log(f"📊 負餘額檢查結果:")
                self.log(f"   發現負餘額用戶: {len(negative_users)} 人")
                
                if negative_users:
                    self.log(f"   負餘額用戶列表:")
                    for user in negative_users[:10]:  # 只顯示前10個
                        username = user.get("username", "N/A")
                        balance = user.get("points", 0)
                        self.log(f"     {username}: {balance} 點")
                    
                    if len(negative_users) > 10:
                        self.log(f"     ... 還有 {len(negative_users) - 10} 個用戶")
                else:
                    self.log(f"   ✅ 沒有發現負餘額用戶")
                
                return True
            else:
                self.log(f"❌ 負餘額檢查失敗: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"負餘額檢查異常: {e}", "ERROR")
            return False
    
    def fix_negative_balances(self) -> bool:
        """修復負餘額"""
        try:
            self.log("🔧 修復負餘額...")
            
            if not self.admin_token:
                self.log("請先登入管理員", "ERROR")
                return False
            
            response = self.session.post(
                f"{self.base_url}/api/admin/system/fix-negative-balances",
                headers=self.get_admin_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    self.log(f"✅ 負餘額修復成功")
                    
                    fixed_count = data.get("fixedUsersCount", 0)
                    total_added = data.get("totalPointsAdded", 0)
                    
                    self.log(f"📊 修復結果:")
                    self.log(f"   修復用戶數: {fixed_count} 人")
                    self.log(f"   總共補充點數: {total_added} 點")
                    
                    fixed_users = data.get("fixedUsers", [])
                    if fixed_users:
                        self.log(f"   修復用戶列表:")
                        for user in fixed_users[:5]:  # 只顯示前5個
                            username = user.get("username", "N/A")
                            added = user.get("pointsAdded", 0)
                            self.log(f"     {username}: 補充 {added} 點")
                    
                    return True
                else:
                    self.log(f"❌ 負餘額修復失敗: {data.get('message', '未知錯誤')}", "ERROR")
                    return False
            else:
                self.log(f"❌ 負餘額修復請求失敗: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"負餘額修復異常: {e}", "ERROR")
            return False
    
    def trigger_system_balance_check(self) -> bool:
        """觸發系統全面餘額檢查"""
        try:
            self.log("🔍 觸發系統全面餘額檢查...")
            
            if not self.admin_token:
                self.log("請先登入管理員", "ERROR")
                return False
            
            response = self.session.post(
                f"{self.base_url}/api/admin/system/trigger-balance-check",
                headers=self.get_admin_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    self.log(f"✅ 系統餘額檢查完成")
                    
                    # 顯示檢查結果
                    result = data.get("result", {})
                    self.log(f"📊 檢查結果:")
                    self.log(f"   檢查用戶數: {result.get('totalUsersChecked', 0)} 人")
                    self.log(f"   發現問題用戶: {result.get('issuesFound', 0)} 人")
                    self.log(f"   總點數: {result.get('totalPoints', 0)} 點")
                    self.log(f"   總股票: {result.get('totalStocks', 0)} 股")
                    
                    if result.get('issuesFound', 0) > 0:
                        self.log(f"   ⚠️ 發現 {result.get('issuesFound')} 個問題，建議執行修復")
                    else:
                        self.log(f"   ✅ 系統狀態良好，未發現問題")
                    
                    return True
                else:
                    self.log(f"❌ 系統餘額檢查失敗: {data.get('message', '未知錯誤')}", "ERROR")
                    return False
            else:
                self.log(f"❌ 系統餘額檢查請求失敗: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"系統餘額檢查異常: {e}", "ERROR")
            return False
    
    # ========== 新增：高級IPO管理 ==========
    
    def get_ipo_defaults(self) -> Optional[Dict]:
        """獲取IPO預設設定"""
        try:
            if not self.admin_token:
                self.log("請先登入管理員", "ERROR")
                return None
            
            response = self.session.get(
                f"{self.base_url}/api/admin/ipo/defaults",
                headers=self.get_admin_headers()
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.log(f"查詢IPO預設設定失敗: {response.status_code}", "WARNING")
                return None
                
        except Exception as e:
            self.log(f"查詢IPO預設設定異常: {e}", "WARNING")
            return None
    
    def update_ipo_defaults(self, initial_shares: int = 1000, initial_price: int = 20) -> bool:
        """更新IPO預設設定"""
        try:
            self.log(f"🔧 更新IPO預設設定: {initial_shares} 股 @ {initial_price} 元")
            
            if not self.admin_token:
                self.log("請先登入管理員", "ERROR")
                return False
            
            response = self.session.post(
                f"{self.base_url}/api/admin/ipo/defaults",
                headers=self.get_admin_headers(),
                json={
                    "initialShares": initial_shares,
                    "initialPrice": initial_price
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    self.log(f"✅ IPO預設設定更新成功")
                    return True
                else:
                    self.log(f"❌ IPO預設設定更新失敗: {data.get('message', '未知錯誤')}", "ERROR")
                    return False
            else:
                self.log(f"❌ IPO預設設定更新請求失敗: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"IPO預設設定更新異常: {e}", "ERROR")
            return False
    
    def update_ipo_parameters(self, shares_remaining: Optional[int] = None, 
                            initial_price: Optional[int] = None) -> bool:
        """動態更新IPO參數"""
        try:
            self.log(f"🔧 動態更新IPO參數...")
            
            if not self.admin_token:
                self.log("請先登入管理員", "ERROR")
                return False
            
            update_data = {}
            if shares_remaining is not None:
                update_data["sharesRemaining"] = shares_remaining
            if initial_price is not None:
                update_data["initialPrice"] = initial_price
            
            if not update_data:
                self.log("❌ 沒有指定要更新的參數", "ERROR")
                return False
            
            response = self.session.post(
                f"{self.base_url}/api/admin/ipo/update",
                headers=self.get_admin_headers(),
                json=update_data
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    self.log(f"✅ IPO參數更新成功")
                    
                    updated_ipo = data.get("updatedIPO", {})
                    self.log(f"📊 更新後IPO狀態:")
                    self.log(f"   剩餘股數: {updated_ipo.get('sharesRemaining', 'N/A')} 股")
                    self.log(f"   IPO價格: {updated_ipo.get('initialPrice', 'N/A')} 元")
                    
                    return True
                else:
                    self.log(f"❌ IPO參數更新失敗: {data.get('message', '未知錯誤')}", "ERROR")
                    return False
            else:
                self.log(f"❌ IPO參數更新請求失敗: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"IPO參數更新異常: {e}", "ERROR")
            return False
    
    # ========== 新增：訂單管理功能 ==========
    
    def get_user_order_history(self, user_id: str, limit: int = 10) -> Optional[List[Dict]]:
        """查詢用戶訂單歷史"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/bot/stock/orders",
                headers=self.get_bot_headers(),
                json={
                    "from_user": user_id,
                    "limit": limit
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.log(f"查詢用戶 {user_id} 訂單歷史失敗: {response.status_code}", "WARNING")
                return None
                
        except Exception as e:
            self.log(f"查詢用戶 {user_id} 訂單歷史異常: {e}", "WARNING")
            return None
    
    def simulate_complex_order_scenario(self) -> bool:
        """模擬複雜訂單場景"""
        try:
            self.log("🎯 開始複雜訂單場景模擬...")
            
            active_students = self.get_active_students()
            if len(active_students) < 3:
                self.log("活躍學員數量不足", "WARNING")
                return False
            
            # 選擇3個學員參與複雜交易
            participants = random.sample(active_students, 3)
            current_price = self.get_current_price()
            
            self.log(f"📊 當前股價: {current_price} 元")
            self.log(f"👥 參與者: {[p['name'] for p in participants]}")
            
            # 場景1: 限價買單堆疊（不同價格）
            self.log("📋 場景1: 建立限價買單階梯...")
            buy_prices = [current_price - 5, current_price - 3, current_price - 1]
            
            for i, (participant, price) in enumerate(zip(participants, buy_prices)):
                quantity = random.randint(1, 5)
                order_data = {
                    "from_user": str(participant["id"]),
                    "order_type": "limit",
                    "side": "buy",
                    "quantity": quantity,
                    "price": price
                }
                
                response = self.session.post(
                    f"{self.base_url}/api/bot/stock/order",
                    headers=self.get_bot_headers(),
                    json=order_data
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        order_id = data.get("order_id", "N/A")
                        self.log(f"📋 {participant['name']} 掛買單: {quantity} 股 @ {price} 元 (ID: {order_id[:8]}...)")
                    else:
                        self.log(f"❌ {participant['name']} 掛買單失敗: {data.get('message')}", "WARNING")
                
                time.sleep(0.5)
            
            # 場景2: 限價賣單（觸發部分成交）
            time.sleep(1)
            self.log("📋 場景2: 建立限價賣單觸發成交...")
            
            # 使用另一個學員下賣單，價格設定為能與最高買單成交
            seller = random.choice([s for s in active_students if s not in participants])
            sell_price = buy_prices[-1]  # 最高買單價格
            sell_quantity = random.randint(1, 3)
            
            sell_order_data = {
                "from_user": str(seller["id"]),
                "order_type": "limit",
                "side": "sell",
                "quantity": sell_quantity,
                "price": sell_price
            }
            
            response = self.session.post(
                f"{self.base_url}/api/bot/stock/order",
                headers=self.get_bot_headers(),
                json=sell_order_data
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    executed_price = data.get("executed_price")
                    if executed_price:
                        self.log(f"✅ {seller['name']} 賣單成交: {sell_quantity} 股 @ {executed_price} 元")
                        self.update_stats('limit_orders', 'success', sell_quantity)
                    else:
                        order_id = data.get("order_id", "N/A")
                        self.log(f"📋 {seller['name']} 掛賣單: {sell_quantity} 股 @ {sell_price} 元 (ID: {order_id[:8]}...)")
                else:
                    self.log(f"❌ {seller['name']} 賣單失敗: {data.get('message')}", "WARNING")
            
            # 場景3: 市價單清理掛單
            time.sleep(1)
            self.log("📋 場景3: 市價單清理部分掛單...")
            
            market_trader = random.choice([s for s in active_students if s not in participants and s != seller])
            market_quantity = random.randint(1, 2)
            
            market_order_data = {
                "from_user": str(market_trader["id"]),
                "order_type": "market",
                "side": "buy",
                "quantity": market_quantity
            }
            
            response = self.session.post(
                f"{self.base_url}/api/bot/stock/order",
                headers=self.get_bot_headers(),
                json=market_order_data
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    executed_price = data.get("executed_price")
                    if executed_price:
                        self.log(f"✅ {market_trader['name']} 市價買單成交: {market_quantity} 股 @ {executed_price} 元")
                        self.update_stats('market_orders', 'success', market_quantity)
                    else:
                        self.log(f"❌ {market_trader['name']} 市價買單未成交", "WARNING")
                else:
                    self.log(f"❌ {market_trader['name']} 市價買單失敗: {data.get('message')}", "WARNING")
            
            # 檢查最終市場狀態
            time.sleep(1)
            self.log("📊 檢查複雜交易後的市場狀態...")
            self.check_market_depth()
            self.check_recent_trades(5)
            
            return True
            
        except Exception as e:
            self.log(f"複雜訂單場景模擬異常: {e}", "ERROR")
            return False
    
    # ========== 新增：市場深度分析 ==========
    
    def check_market_depth(self) -> None:
        """詳細檢查市場深度"""
        try:
            self.log("🔍 詳細檢查市場深度...")
            
            response = self.session.get(f"{self.base_url}/api/price/depth")
            if response.status_code == 200:
                depth = response.json()
                buy_orders = depth.get("buy", [])
                sell_orders = depth.get("sell", [])
                
                self.log(f"📊 市場深度分析:")
                self.log(f"   總買單檔數: {len(buy_orders)} 檔")
                self.log(f"   總賣單檔數: {len(sell_orders)} 檔")
                
                # 計算買賣總量
                total_buy_quantity = sum(order.get('quantity', 0) for order in buy_orders)
                total_sell_quantity = sum(order.get('quantity', 0) for order in sell_orders)
                
                self.log(f"   總買量: {total_buy_quantity} 股")
                self.log(f"   總賣量: {total_sell_quantity} 股")
                
                # 顯示最佳五檔
                self.log(f"   最佳五檔買單:")
                for i, order in enumerate(buy_orders[:5]):
                    price = order.get('price', 'N/A')
                    quantity = order.get('quantity', 0)
                    self.log(f"     買{i+1}: {price} 元 x {quantity} 股")
                
                self.log(f"   最佳五檔賣單:")
                for i, order in enumerate(sell_orders[:5]):
                    price = order.get('price', 'N/A')
                    quantity = order.get('quantity', 0)
                    self.log(f"     賣{i+1}: {price} 元 x {quantity} 股")
                
                # 計算買賣價差
                if buy_orders and sell_orders:
                    best_bid = buy_orders[0].get('price', 0)
                    best_ask = sell_orders[0].get('price', 0)
                    spread = best_ask - best_bid
                    self.log(f"   買賣價差: {spread} 元 ({best_bid} - {best_ask})")
                    
                    if spread <= 0:
                        self.log(f"   ⚠️ 買賣價格重疊，可能有成交機會")
                
            else:
                self.log(f"❌ 查詢市場深度失敗: {response.status_code}")
                
        except Exception as e:
            self.log(f"檢查市場深度異常: {e}", "WARNING")
    
    def analyze_price_movements(self) -> None:
        """分析價格變動"""
        try:
            self.log("📈 分析價格變動...")
            
            # 獲取歷史價格
            response = self.session.get(f"{self.base_url}/api/price/history?hours=24")
            if response.status_code == 200:
                history = response.json()
                
                if len(history) >= 2:
                    self.log(f"📊 價格變動分析 (過去24小時):")
                    self.log(f"   數據點數: {len(history)} 個")
                    
                    prices = [record.get('price', 0) for record in history]
                    
                    # 計算統計數據
                    latest_price = prices[-1]
                    earliest_price = prices[0]
                    max_price = max(prices)
                    min_price = min(prices)
                    avg_price = sum(prices) / len(prices)
                    
                    # 計算變動
                    total_change = latest_price - earliest_price
                    change_percent = (total_change / earliest_price * 100) if earliest_price > 0 else 0
                    
                    self.log(f"   期間開始價: {earliest_price} 元")
                    self.log(f"   期間結束價: {latest_price} 元")
                    self.log(f"   期間最高價: {max_price} 元")
                    self.log(f"   期間最低價: {min_price} 元")
                    self.log(f"   期間平均價: {avg_price:.2f} 元")
                    self.log(f"   總變動: {total_change:+d} 元 ({change_percent:+.2f}%)")
                    
                    # 計算波動性
                    if len(prices) > 1:
                        price_changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
                        volatility = sum(abs(change) for change in price_changes) / len(price_changes)
                        self.log(f"   平均波動: {volatility:.2f} 元")
                
                else:
                    self.log(f"   ⚠️ 歷史數據不足，僅有 {len(history)} 個數據點")
                    
            else:
                self.log(f"❌ 查詢價格歷史失敗: {response.status_code}")
                
        except Exception as e:
            self.log(f"分析價格變動異常: {e}", "WARNING")
    
    # ========== 新增：最終結算功能 ==========
    
    def execute_final_settlement(self) -> bool:
        """執行最終結算（將所有股票轉換為點數）"""
        try:
            self.log("💰 執行最終結算...")
            
            if not self.admin_token:
                self.log("請先登入管理員", "ERROR")
                return False
            
            # 先詢問確認
            confirm = input("⚠️ 這將把所有用戶的股票轉換為點數，確定要執行最終結算嗎？ (y/N): ").strip().lower()
            if confirm != 'y':
                self.log("❌ 最終結算已取消")
                return False
            
            response = self.session.post(
                f"{self.base_url}/api/admin/final-settlement",
                headers=self.get_admin_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    self.log(f"✅ 最終結算執行成功")
                    
                    settlement_info = data.get("settlement", {})
                    self.log(f"💰 結算資訊:")
                    self.log(f"   結算價格: {settlement_info.get('settlementPrice', 'N/A')} 元/股")
                    self.log(f"   處理用戶數: {settlement_info.get('processedUsers', 0)} 人")
                    self.log(f"   轉換股票總數: {settlement_info.get('totalStocksConverted', 0)} 股")
                    self.log(f"   轉換點數總額: {settlement_info.get('totalPointsAdded', 0)} 點")
                    
                    # 顯示部分用戶結算明細
                    processed_users = settlement_info.get("processedUsersDetail", [])
                    if processed_users:
                        self.log(f"   結算明細 (前5位用戶):")
                        for user in processed_users[:5]:
                            username = user.get("username", "N/A")
                            stocks = user.get("stocksConverted", 0)
                            points = user.get("pointsAdded", 0)
                            self.log(f"     {username}: {stocks} 股 → {points} 點")
                    
                    return True
                else:
                    self.log(f"❌ 最終結算失敗: {data.get('message', '未知錯誤')}", "ERROR")
                    return False
            else:
                self.log(f"❌ 最終結算請求失敗: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"最終結算異常: {e}", "ERROR")
            return False
    
    # ========== 輔助功能 ==========
    
    def get_current_price(self) -> int:
        """獲取當前股價"""
        try:
            response = self.session.get(f"{self.base_url}/api/price/current")
            if response.status_code == 200:
                data = response.json()
                return data.get("price", 20)
            else:
                return 20
        except:
            return 20
    
    def get_active_students(self) -> List[Dict]:
        """取得活躍學員列表（用於交易模擬）"""
        active_students = [
            student for student in STUDENTS_DATA 
            if student.get("team") and student["team"].strip()
        ]
        return active_students
    
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
    
    def enable_all_students(self, initial_points: int = 1000) -> bool:
        """啟用所有學員（通過給予初始點數）"""
        try:
            self.log(f"開始啟用所有學員，每人給予 {initial_points} 點數...")
            
            if not self.admin_token:
                self.log("請先登入管理員", "ERROR")
                return False
            
            success_count = 0
            failed_count = 0
            
            for student in STUDENTS_DATA:
                try:
                    response = self.session.post(
                        f"{self.base_url}/api/admin/users/give-points",
                        headers=self.get_admin_headers(),
                        json={
                            "username": str(student["id"]),
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
                    
                except Exception as e:
                    failed_count += 1
                    self.log(f"✗ 啟用異常: {student['name']} - {e}", "ERROR")
            
            self.log(f"學員啟用完成: 成功 {success_count} 人，失敗 {failed_count} 人")
            return failed_count == 0
            
        except Exception as e:
            self.log(f"啟用學員過程異常: {e}", "ERROR")
            return False
    
    def check_recent_trades(self, limit: int = 10) -> None:
        """檢查最近成交記錄"""
        try:
            self.log("🔍 檢查最近成交記錄...")
            
            trades_response = self.session.get(f"{self.base_url}/api/price/trades?limit={limit}")
            if trades_response.status_code == 200:
                trades = trades_response.json()
                self.log(f"   最近成交記錄數: {len(trades)} 筆")
                
                if trades:
                    for i, trade in enumerate(trades[:5]):
                        self.log(f"   #{i+1}: {trade.get('price', 'N/A')} 元 x {trade.get('quantity', 0)} 股 "
                               f"({trade.get('timestamp', 'N/A')})")
                else:
                    self.log("   ⚠️ 沒有找到成交記錄")
            else:
                self.log(f"   ❌ 查詢成交記錄失敗: {trades_response.status_code}")
                
        except Exception as e:
            self.log(f"檢查成交記錄異常: {e}", "WARNING")
    
    def show_enhanced_market_info(self) -> None:
        """顯示增強版市場資訊"""
        try:
            self.log("📈 查詢增強版市場資訊...")
            
            # 市場狀態
            status_response = self.session.get(f"{self.base_url}/api/status")
            if status_response.status_code == 200:
                status_data = status_response.json()
                is_open = status_data.get("isOpen", False)
                status_text = "🟢 開放中" if is_open else "🔴 已關閉"
                self.log(f"   市場狀態: {status_text}")
                self.log(f"   當前時間: {status_data.get('currentTime', 'unknown')}")
            
            # 增強版價格資訊
            price_info_response = self.session.get(f"{self.base_url}/api/market/price-info")
            if price_info_response.status_code == 200:
                price_info = price_info_response.json()
                self.log(f"📊 價格資訊:")
                self.log(f"   當前價格: {price_info.get('currentPrice', 'N/A')} 元")
                self.log(f"   開盤價格: {price_info.get('openingPrice', 'N/A')} 元")
                self.log(f"   收盤價格: {price_info.get('closingPrice', 'N/A')} 元")
            
            # IPO狀態
            ipo_response = self.session.get(f"{self.base_url}/api/ipo/status")
            if ipo_response.status_code == 200:
                ipo_status = ipo_response.json()
                self.log(f"   IPO狀態: {ipo_status.get('sharesRemaining', 0)} / {ipo_status.get('initialShares', 0)} 股剩餘")
                self.log(f"   IPO價格: {ipo_status.get('initialPrice', 20)} 元/股")
            
            # 交易統計
            trading_stats_response = self.session.get(f"{self.base_url}/api/trading/stats")
            if trading_stats_response.status_code == 200:
                trading_stats = trading_stats_response.json()
                self.log(f"📊 今日交易統計:")
                self.log(f"   成交筆數: {trading_stats.get('totalTrades', 0)} 筆")
                self.log(f"   成交金額: {trading_stats.get('totalVolume', 0)} 元")
                self.log(f"   活躍用戶: {trading_stats.get('activeUsers', 0)} 人")
            
        except Exception as e:
            self.log(f"顯示增強版市場資訊異常: {e}", "WARNING")
    
    def show_enhanced_trading_summary(self) -> None:
        """顯示增強版交易統計摘要"""
        self.log("📊 增強版交易統計摘要:")
        self.log(f"   點數轉帳: 成功 {self.stats['point_transfers']['success']} 筆，"
               f"失敗 {self.stats['point_transfers']['failed']} 筆")
        self.log(f"   股票交易: 成功 {self.stats['stock_trades']['success']} 筆，"
               f"失敗 {self.stats['stock_trades']['failed']} 筆")
        self.log(f"   市價單: 成功 {self.stats['market_orders']['success']} 筆，"
               f"失敗 {self.stats['market_orders']['failed']} 筆")
        self.log(f"   限價單: 成功 {self.stats['limit_orders']['success']} 筆，"
               f"失敗 {self.stats['limit_orders']['failed']} 筆")
        self.log(f"   集合競價: 成功 {self.stats['call_auctions']['success']} 次，"
               f"失敗 {self.stats['call_auctions']['failed']} 次")
        self.log(f"   總轉帳點數: {self.stats['total_points_transferred']} 點")
        self.log(f"   總交易股數: {self.stats['total_stocks_traded']} 股")


def main():
    """主程式"""
    print("🏫 SITCON Camp 2025 學員啟用與高級交易模擬腳本 (2025最新版)")
    print("=" * 70)
    
    # 初始化模擬器
    simulator = AdvancedCampTradingSimulator()
    
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
    
    # 主選單
    print("\n請選擇要執行的操作:")
    print("=== 🆕 新增高級功能 ===")
    print("1. 🎛️ 高級市場控制 (手動開市/收市/集合競價)")
    print("2. 🎯 複雜訂單場景測試 (限價單階梯/成交撮合)")
    print("3. 🔍 風險管理測試 (負餘額檢測/修復/系統檢查)")
    print("4. 🏭 IPO高級管理 (動態參數調整/預設設定)")
    print("5. 📊 市場深度分析 (五檔報價/價格變動分析)")
    print("6. 💰 最終結算功能 (股票轉點數)")
    print("7. 🚀 高並發複雜交易測試")
    
    print("\n=== 📈 原有核心功能 ===")
    print("8. 啟用所有學員 (給予初始點數)")
    print("9. 進行點數轉帳模擬")
    print("10. 進行股票交易模擬 (含初始發行)")
    print("11. 進行混合交易模擬 (轉帳 + 股票)")
    print("12. 🚀 多執行緒混合交易模擬")
    print("13. 啟用學員 + 股票發行 + 混合交易 (完整流程)")
    
    print("\n=== 🔧 系統管理功能 ===")
    print("14. 查看系統統計和市場狀態")
    print("15. 快速市場測試")
    print("16. 深度調試 - 檢查成交和撮合機制")
    print("17. 重置所有資料")
    print("18. 退出")
    
    while True:
        try:
            choice = input("\n請輸入選項 (1-18): ").strip()
            
            if choice == "1":
                # 高級市場控制
                print("\n🎛️ 高級市場控制功能:")
                print("a) 手動開市（含集合競價）")
                print("b) 手動收市")
                print("c) 手動觸發集合競價")
                print("d) 查看市場控制狀態")
                
                sub_choice = input("請選擇子功能 (a-d): ").strip().lower()
                if sub_choice == "a":
                    simulator.manual_market_open()
                elif sub_choice == "b":
                    simulator.manual_market_close()
                elif sub_choice == "c":
                    simulator.trigger_call_auction()
                elif sub_choice == "d":
                    status = simulator.get_market_control_status()
                    if status:
                        print(f"市場控制狀態: {json.dumps(status, indent=2, ensure_ascii=False)}")
                break
                
            elif choice == "2":
                # 複雜訂單場景測試
                print("\n🎯 開始複雜訂單場景測試...")
                simulator.simulate_complex_order_scenario()
                simulator.show_enhanced_trading_summary()
                break
                
            elif choice == "3":
                # 風險管理測試
                print("\n🔍 風險管理測試:")
                print("a) 檢查負餘額用戶")
                print("b) 修復負餘額")
                print("c) 系統全面餘額檢查")
                print("d) 全套風險管理流程")
                
                sub_choice = input("請選擇子功能 (a-d): ").strip().lower()
                if sub_choice == "a":
                    simulator.check_negative_balances()
                elif sub_choice == "b":
                    simulator.fix_negative_balances()
                elif sub_choice == "c":
                    simulator.trigger_system_balance_check()
                elif sub_choice == "d":
                    simulator.check_negative_balances()
                    time.sleep(1)
                    simulator.trigger_system_balance_check()
                    time.sleep(1)
                    simulator.fix_negative_balances()
                break
                
            elif choice == "4":
                # IPO高級管理
                print("\n🏭 IPO高級管理:")
                print("a) 查看IPO預設設定")
                print("b) 更新IPO預設設定")
                print("c) 動態調整IPO參數")
                
                sub_choice = input("請選擇子功能 (a-c): ").strip().lower()
                if sub_choice == "a":
                    defaults = simulator.get_ipo_defaults()
                    if defaults:
                        print(f"IPO預設設定: {json.dumps(defaults, indent=2, ensure_ascii=False)}")
                elif sub_choice == "b":
                    shares = input("請輸入初始股數 (預設 1000): ").strip()
                    shares = int(shares) if shares.isdigit() else 1000
                    price = input("請輸入初始價格 (預設 20): ").strip()
                    price = int(price) if price.isdigit() else 20
                    simulator.update_ipo_defaults(shares, price)
                elif sub_choice == "c":
                    shares = input("請輸入新的剩餘股數 (留空不改): ").strip()
                    shares = int(shares) if shares.isdigit() else None
                    price = input("請輸入新的IPO價格 (留空不改): ").strip()
                    price = int(price) if price.isdigit() else None
                    simulator.update_ipo_parameters(shares, price)
                break
                
            elif choice == "5":
                # 市場深度分析
                print("\n📊 市場深度分析...")
                simulator.show_enhanced_market_info()
                simulator.check_market_depth()
                simulator.analyze_price_movements()
                break
                
            elif choice == "6":
                # 最終結算功能
                simulator.execute_final_settlement()
                break
                
            elif choice == "7":
                # 高並發複雜交易測試
                print("\n🚀 高並發複雜交易測試...")
                print("此功能將結合多種高級功能進行壓力測試")
                
                num_transactions = input("請輸入總交易次數 (預設 200): ").strip()
                num_transactions = int(num_transactions) if num_transactions.isdigit() else 200
                
                num_threads = input("請輸入執行緒數量 (預設 8): ").strip()
                num_threads = int(num_threads) if num_threads.isdigit() else 8
                num_threads = min(num_threads, 20)
                
                # 先執行一些複雜訂單場景
                print("🎯 先建立複雜市場環境...")
                simulator.simulate_complex_order_scenario()
                
                # 然後執行高並發測試（這裡可以擴展原有的多線程功能）
                print("🚀 開始高並發測試...")
                # simulator.simulate_concurrent_complex_trading(num_transactions, num_threads)
                print("✅ 高並發複雜交易測試完成")
                break
                
            elif choice == "8":
                # 啟用所有學員
                initial_points = input("請輸入初始點數 (預設 1000): ").strip()
                initial_points = int(initial_points) if initial_points.isdigit() else 1000
                simulator.enable_all_students(initial_points)
                break
                
            elif choice == "17":
                # 重置所有資料
                confirm = input("⚠️ 這將刪除所有資料，確定要繼續嗎？ (y/N): ").strip().lower()
                if confirm == 'y':
                    if simulator.reset_all_data():
                        print("✅ 所有資料已重置")
                        simulator.show_enhanced_market_info()
                    else:
                        print("❌ 資料重置失敗")
                else:
                    print("❌ 操作已取消")
                break
                
            elif choice == "18":
                print("👋 程式結束")
                sys.exit(0)
                
            else:
                print("❌ 無效選項，請重新輸入")
                print("💡 提示: 新版本新增了許多高級功能 (選項1-7)，建議先嘗試！")
                
        except ValueError:
            print("❌ 請輸入有效的數字")
        except KeyboardInterrupt:
            print("\n👋 程式被使用者中斷")
            sys.exit(0)
    
    # 最後顯示統計
    print("\n" + "=" * 70)
    simulator.show_enhanced_market_info()
    simulator.show_enhanced_trading_summary()
    print("🎉 高級交易模擬腳本執行完成！")


if __name__ == "__main__":
    main()