# 啟動重構後的應用程式
# 用於測試重構版本

import uvicorn
import asyncio
import sys
import os

# 添加目前路徑到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def check_dependencies():
    """檢查依賴是否正確安裝"""
    try:
        print("🔍 檢查重構後的依賴...")
        
        # 測試基本導入
        from app.main_refactored import app
        from app.core.config_refactored import config
        
        print("✅ 主應用程式導入成功")
        
        # 測試領域層
        from app.domain.entities import User, Stock
        from app.domain.services import UserDomainService
        print("✅ 領域層導入成功")
        
        # 測試應用層
        from app.application.services import UserApplicationService
        from app.application.dependencies import get_service_container
        print("✅ 應用層導入成功")
        
        # 測試基礎設施層
        from app.infrastructure.mongodb_repositories import MongoUserRepository
        print("✅ 基礎設施層導入成功")
        
        print("🎉 所有依賴檢查通過！")
        return True
        
    except ImportError as e:
        print(f"❌ 導入錯誤: {e}")
        print("💡 請檢查 Python 路徑和模組結構")
        return False
    except Exception as e:
        print(f"❌ 其他錯誤: {e}")
        return False

def main():
    """主函數"""
    print("🚀 啟動重構版本測試...")
    
    # 同步檢查依賴
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        dependencies_ok = loop.run_until_complete(check_dependencies())
        loop.close()
        
        if not dependencies_ok:
            print("💥 依賴檢查失敗，無法啟動應用程式")
            return
        
        print("📡 啟動重構後的 FastAPI 應用程式...")
        print("🌐 應用程式將在 http://localhost:8000 運行")
        print("📚 API 文件: http://localhost:8000/docs")
        print("🏗️  架構資訊: http://localhost:8000/api/architecture")
        print("❤️  健康檢查: http://localhost:8000/api/health")
        
        # 啟動應用程式
        uvicorn.run(
            "app.main_refactored:app",
            host="0.0.0.0",
            port=8000,
            reload=True,  # 開發模式下啟用hot reload
            log_level="info"
        )
        
    except KeyboardInterrupt:
        print("\n👋 應用程式已停止")
    except Exception as e:
        print(f"💥 啟動失敗: {e}")

if __name__ == "__main__":
    main()