# DEBUG 模式群組限制繞過功能

## 📋 功能說明

為了方便開發和測試，我們添加了 `DEBUG` 環境變數來控制是否繞過 Telegram 群組 ID 的限制。

## 🔧 環境變數設定

在 `.env` 檔案中設定：

```bash
# Enable debug or not
DEBUG=True
```

- `DEBUG=True` - 啟用 DEBUG 模式，忽略群組 ID 限制
- `DEBUG=False` - 關閉 DEBUG 模式，恢復正常的群組限制（預設）

## 🎯 受影響的功能

### 1. **PVP 挑戰 (`/pvp` 指令)**

**正常模式（DEBUG=False）**：
- ❌ 私人聊天：`🚫 PVP 挑戰只能在群組中使用！`
- ❌ 非主群組：`🚫 PVP 挑戰只能在 Camp 大群中使用！`
- ✅ Camp 大群（-1002891865538）：可以使用

**DEBUG 模式（DEBUG=True）**：
- ❌ 私人聊天：`🚫 PVP 挑戰只能在群組中使用！`（仍然禁止）
- ✅ 任何群組：都可以使用 PVP 挑戰

### 2. **股票交易 (`/stock` 指令)**

**正常模式（DEBUG=False）**：
- ❌ Camp 大群：`🚫 不能在大群交易股票！`
- ✅ 其他群組：可以交易股票

**DEBUG 模式（DEBUG=True）**：
- ✅ 任何群組：都可以交易股票（包含 Camp 大群）

## 🔍 程式碼位置

### 1. PVP 挑戰限制
**檔案**: `bot/bot/handlers/commands.py`

```python
# 在 DEBUG 模式下忽略群組 ID 限制
if not DEBUG and update.message.chat_id != MAIN_GROUP:
    await update.message.reply_text("🚫 PVP 挑戰只能在 Camp 大群中使用！")
    return

# DEBUG 模式日誌
if DEBUG and update.message.chat_id != MAIN_GROUP:
    logger.info(f"🐛 DEBUG 模式：允許在非主群組 {update.message.chat_id} 中使用 PVP")
```

### 2. 股票交易限制
**檔案**: `bot/bot/handlers/conversation/stock.py`

```python
# 在 DEBUG 模式下忽略大群交易股票的限制
if not DEBUG and update.message.chat_id == MAIN_GROUP:
    await update.message.reply_text("🚫 不能在大群交易股票！")
    return ConversationHandler.END
```

## 📊 群組 ID 設定

**檔案**: `bot/bot/helper/chat_ids.py`

```python
MAIN_GROUP = -1002891865538  # Camp 大群

STUDENT_GROUPS = {
    "第一組": -1002811640813,
    "第二組": -1002818567445,
    # ... 其他小組群組
}
```

## 🐛 DEBUG 日誌

當 DEBUG 模式啟用時，會在日誌中顯示：

```
🐛 DEBUG 模式已啟用 - 將忽略群組 ID 限制
🐛 DEBUG 模式：允許在非主群組 -1234567890 中使用 PVP
```

## ⚠️ 安全注意事項

1. **生產環境務必設定 `DEBUG=False`**
2. **DEBUG 模式會繞過安全限制，僅供開發測試使用**
3. **部署前請確認環境變數設定正確**

## 🚀 使用情境

### 開發環境
```bash
DEBUG=True  # 允許在任何群組測試 PVP 和股票交易
```

### 測試環境
```bash
DEBUG=True  # 方便測試各種群組情境
```

### 生產環境
```bash
DEBUG=False  # 嚴格遵循群組限制規則
```

## 📝 測試檢查清單

- [ ] 在小組群組中測試 `/pvp` 指令（DEBUG=True 應該可用，DEBUG=False 應該被拒絕）
- [ ] 在 Camp 大群中測試 `/stock` 指令（DEBUG=True 應該可用，DEBUG=False 應該被拒絕）
- [ ] 確認私人聊天中 `/pvp` 仍然被拒絕（無論 DEBUG 設定）
- [ ] 檢查日誌中是否有正確的 DEBUG 模式提示

---

**建立日期**: 2025-01-21  
**最後更新**: 2025-01-21