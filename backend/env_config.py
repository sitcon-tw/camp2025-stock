#!/usr/bin/env python3
"""環境變數配置檢查工具"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv


def check_env_config():
    """檢查環境變數配置"""
    print("檢查環境變數配置...")
    
    env_path = Path(__file__).parent / '.env'
    if not env_path.exists():
        print("錯誤: .env 文件不存在，請先執行 --generate 產生範例文件")
        return False
    
    load_dotenv(env_path)
    
    # 必要的環境變數
    required_vars = [
        'MONGO_URI',
        'DATABASE_NAME', 
        'JWT_SECRET',
        'ADMIN_PASSWORD'
    ]
    
    all_good = True
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            print(f"錯誤: {var} 未設定")
            all_good = False
        else:
            # 隱藏敏感資訊
            if var in ['JWT_SECRET', 'ADMIN_PASSWORD']:
                display = f"{'*' * (len(value) - 4)}{value[-4:]}" if len(value) > 4 else "****"
            else:
                display = value
            print(f"成功: {var} = {display}")
    
    if all_good:
        print("環境變數配置完成")
        return True
    else:
        print("請修正上述問題")
        return False


def generate_sample_env():
    """產生範例 .env 文件"""
    content = """# MongoDB 連線 URI
MONGO_URI=mongodb://localhost:27017

# MongoDB 資料庫名稱
DATABASE_NAME=sitcon_camp_2025

# Telegram 機器人 Token
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Telegram Webhook Secret
WEBHOOK_SECRET=your_webhook_secret_here

# JWT Secret Key
JWT_SECRET=your_super_secret_jwt_key_here

# JWT Token 過期時間（分鐘）
JWT_EXPIRE_MINUTES=1440

# 管理員密碼
ADMIN_PASSWORD=your_admin_password_here

# 內部使用 API Key
INTERNAL_API_KEY=your_internal_api_key_here

# CORS 允許來源
ALLOWED_HOSTS=*

# 環境設定
ENVIRONMENT=development
DEBUG=True
"""
    
    sample_path = Path(__file__).parent / '.env.example'
    with open(sample_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"範例配置文件已產生: {sample_path}")
    print("請複製範例為 .env 並填入實際值")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--generate":
        generate_sample_env()
    else:
        success = check_env_config()
        if not success:
            print("提示: 執行 'python env_config.py --generate' 產生範例配置文件")
            sys.exit(1)
        else:
            print("準備就緒，執行 'python main.py' 啟動服務")