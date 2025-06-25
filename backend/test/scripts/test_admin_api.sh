#!/bin/bash
# 管理員 API 測試腳本

BASE_URL="http://localhost:8000"
ADMIN_PASSWORD="admin123"  # 請替換為您的實際密碼

echo "🔒 測試管理員 API 權限"
echo "=============================="

# 1. 測試未授權存取（應該失敗）
echo "1. 測試未授權存取管理員 API..."
curl -X GET "$BASE_URL/api/admin/user" \
  -H "Content-Type: application/json" \
  -w "\nHTTP Status: %{http_code}\n\n"

# 2. 管理員登入取得 Token
echo "2. 管理員登入..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/admin/login" \
  -H "Content-Type: application/json" \
  -d "{\"password\": \"$ADMIN_PASSWORD\"}")

echo "登入回應: $LOGIN_RESPONSE"

# 提取 Token
TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ 登入失敗，無法取得 Token"
    exit 1
fi

echo "✅ 登入成功，Token: ${TOKEN:0:20}..."
echo ""

# 3. 使用 Token 測試各個管理員 API
echo "3. 測試管理員 API 端點..."

# 查詢使用者資產
echo "3.1 查詢所有使用者資產："
curl -X GET "$BASE_URL/api/admin/user" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -w "\nHTTP Status: %{http_code}\n\n"

# 查詢特定使用者
echo "3.2 查詢特定使用者（小明）："
curl -X GET "$BASE_URL/api/admin/user?user=小明" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -w "\nHTTP Status: %{http_code}\n\n"

# 給予點數
echo "3.3 給使用者點數："
curl -X POST "$BASE_URL/api/admin/users/give-points" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "測試使用者",
    "type": "user",
    "amount": 100
  }' \
  -w "\nHTTP Status: %{http_code}\n\n"

# 發布公告
echo "3.4 發布公告："
curl -X POST "$BASE_URL/api/admin/announcement" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "測試公告",
    "message": "這是一個測試公告",
    "broadcast": true
  }' \
  -w "\nHTTP Status: %{http_code}\n\n"

# 更新市場時間
echo "3.5 更新市場時間："
curl -X POST "$BASE_URL/api/admin/market/update" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "openTime": [
      {
        "start": 1640995200,
        "end": 1641002400
      }
    ]
  }' \
  -w "\nHTTP Status: %{http_code}\n\n"

# 設定漲跌限制
echo "3.6 設定漲跌限制："
curl -X POST "$BASE_URL/api/admin/market/set-limit" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "limitPercent": 15.0
  }' \
  -w "\nHTTP Status: %{http_code}\n\n"

# 取得公告列表
echo "3.7 取得公告列表："
curl -X GET "$BASE_URL/api/admin/announcements" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -w "\nHTTP Status: %{http_code}\n\n"

# 取得系統統計
echo "3.8 取得系統統計："
curl -X GET "$BASE_URL/api/admin/stats" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -w "\nHTTP Status: %{http_code}\n\n"

echo "✅ 管理員 API 測試完成！"
