import { useState, useEffect } from "react";
import Modal from "./Modal";
import useModal from "@/hooks/useModal";
import { createAnnouncement, getAnnouncementsAdmin, deleteAnnouncement } from "@/lib/api";
import { PERMISSIONS } from "@/contexts/PermissionContext";
import { PermissionButton } from "./PermissionGuard";

/**
 * 公告管理組件 - 包含發布公告和管理公告功能
 */
export const AnnouncementManagement = ({ token, permissions }) => {
    const [activeTab, setActiveTab] = useState("manage");
    const [announcements, setAnnouncements] = useState([]);
    const [loading, setLoading] = useState(false);
    const [notification, setNotification] = useState({ show: false, message: "", type: "info" });
    
    // 發布公告相關狀態
    const createModal = useModal();
    const [publishForm, setPublishForm] = useState({ title: "", message: "", broadcast: true });
    const [publishLoading, setPublishLoading] = useState(false);
    
    // 編輯公告相關狀態
    const editModal = useModal();
    const [editForm, setEditForm] = useState({ id: "", title: "", message: "", broadcast: true });
    const [editLoading, setEditLoading] = useState(false);
    
    // 刪除確認模態框
    const deleteModal = useModal();
    const [deleteTarget, setDeleteTarget] = useState(null);
    
    useEffect(() => {
        fetchAnnouncements();
    }, [token]);
    
    // 顯示通知
    const showNotification = (message, type = "info") => {
        setNotification({ show: true, message, type });
        setTimeout(() => setNotification({ show: false, message: "", type: "info" }), 3000);
    };
    
    // 獲取公告列表
    const fetchAnnouncements = async () => {
        try {
            setLoading(true);
            const response = await getAnnouncementsAdmin(token);
            setAnnouncements(response.announcements || []);
        } catch (error) {
            showNotification(`獲取公告列表失敗: ${error.message}`, 'error');
            setAnnouncements([]);
        } finally {
            setLoading(false);
        }
    };
    
    // 發布公告
    const handlePublishAnnouncement = async () => {
        if (!publishForm.title.trim() || !publishForm.message.trim()) {
            showNotification("請填寫公告標題和內容", "error");
            return;
        }
        
        try {
            setPublishLoading(true);
            await createAnnouncement(token, publishForm.title, publishForm.message, publishForm.broadcast);
            showNotification('公告已成功發布', 'success');
            setPublishForm({ title: "", message: "", broadcast: true });
            createModal.closeModal();
            fetchAnnouncements(); // 重新獲取公告列表
        } catch (error) {
            showNotification(`發布公告失敗: ${error.message}`, 'error');
        } finally {
            setPublishLoading(false);
        }
    };
    
    // 編輯公告
    const handleEditAnnouncement = async () => {
        if (!editForm.title.trim() || !editForm.message.trim()) {
            showNotification("請填寫公告標題和內容", "error");
            return;
        }
        
        try {
            setEditLoading(true);
            // 注意：這裡需要後端支援編輯公告的 API
            // await updateAnnouncement(token, editForm.id, editForm.title, editForm.message, editForm.broadcast);
            showNotification('功能開發中：編輯公告 API 尚未實作', 'info');
            editModal.closeModal();
        } catch (error) {
            showNotification(`編輯公告失敗: ${error.message}`, 'error');
        } finally {
            setEditLoading(false);
        }
    };
    
    // 刪除公告
    const handleDeleteAnnouncement = async () => {
        if (!deleteTarget) return;
        
        try {
            await deleteAnnouncement(token, deleteTarget.id);
            showNotification('公告已成功刪除', 'success');
            deleteModal.closeModal();
            setDeleteTarget(null);
            fetchAnnouncements(); // 重新獲取公告列表
        } catch (error) {
            showNotification(`刪除公告失敗: ${error.message}`, 'error');
        }
    };
    
    // 打開編輯模態框
    const openEditModal = (announcement) => {
        setEditForm({
            id: announcement.id,
            title: announcement.title,
            message: announcement.message,
            broadcast: announcement.broadcast !== false
        });
        editModal.openModal();
    };
    
    // 打開刪除確認模態框
    const openDeleteModal = (announcement) => {
        setDeleteTarget(announcement);
        deleteModal.openModal();
    };
    
    // 格式化日期
    const formatDate = (dateString) => {
        if (!dateString) return "未知時間";
        try {
            return new Date(dateString).toLocaleString('zh-TW', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch {
            return "日期格式錯誤";
        }
    };
    
    return (
        <div className="space-y-6">
            {/* 通知提示 */}
            {notification.show && (
                <div className={`p-4 rounded-lg border ${
                    notification.type === 'success' ? 'bg-green-600/20 border-green-500/30 text-green-400' :
                    notification.type === 'error' ? 'bg-red-600/20 border-red-500/30 text-red-400' :
                    'bg-blue-600/20 border-blue-500/30 text-blue-400'
                }`}>
                    {notification.message}
                </div>
            )}
            
            {/* 標題和操作按鈕 */}
            <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold text-[#92cbf4]">📢 公告管理</h2>
                <div className="flex space-x-3">
                    <PermissionButton
                        permission={PERMISSIONS.CREATE_ANNOUNCEMENT}
                        userPermissions={permissions}
                        onClick={createModal.openModal}
                        className="bg-[#469FD2] text-white px-4 py-2 rounded hover:bg-[#5BAEE3] flex items-center space-x-2"
                    >
                        <span>📝</span>
                        <span>發布公告</span>
                    </PermissionButton>
                    <button
                        onClick={fetchAnnouncements}
                        className="bg-[#294565] text-[#92cbf4] px-4 py-2 rounded hover:bg-[#3A5578] flex items-center space-x-2"
                    >
                        <span>🔄</span>
                        <span>重新整理</span>
                    </button>
                </div>
            </div>
            
            {/* 公告列表 */}
            <div className="bg-[#1A325F] rounded-lg border border-[#294565]">
                <div className="p-6">
                    <h3 className="text-lg font-semibold text-[#92cbf4] mb-4">📋 公告列表</h3>
                    
                    {loading ? (
                        <div className="flex items-center justify-center p-8">
                            <div className="text-lg text-[#7BC2E6]">載入中...</div>
                        </div>
                    ) : announcements.length === 0 ? (
                        <div className="text-center p-8">
                            <div className="text-[#7BC2E6] text-lg mb-2">📝 暫無公告</div>
                            <div className="text-[#557797] text-sm">點擊上方「發布公告」按鈕來創建第一個公告</div>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            {announcements.map((announcement) => (
                                <div key={announcement.id} className="bg-[#0f203e] border border-[#294565] rounded-lg p-4">
                                    <div className="flex justify-between items-start">
                                        <div className="flex-1">
                                            <h4 className="text-[#92cbf4] font-semibold text-lg mb-2">
                                                {announcement.title}
                                            </h4>
                                            <p className="text-[#7BC2E6] mb-3 leading-relaxed">
                                                {announcement.message}
                                            </p>
                                            <div className="flex items-center space-x-4 text-sm text-[#557797]">
                                                <span>📅 {formatDate(announcement.created_at)}</span>
                                                {announcement.broadcast && (
                                                    <span className="bg-blue-600/20 text-blue-400 px-2 py-1 rounded text-xs">
                                                        📢 已廣播
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                        
                                        <div className="flex space-x-2 ml-4">
                                            <PermissionButton
                                                permission={PERMISSIONS.CREATE_ANNOUNCEMENT}
                                                userPermissions={permissions}
                                                onClick={() => openEditModal(announcement)}
                                                className="bg-[#469FD2] text-white px-3 py-1 rounded text-sm hover:bg-[#5BAEE3]"
                                            >
                                                編輯
                                            </PermissionButton>
                                            <PermissionButton
                                                permission={PERMISSIONS.CREATE_ANNOUNCEMENT}
                                                userPermissions={permissions}
                                                onClick={() => openDeleteModal(announcement)}
                                                className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700"
                                            >
                                                刪除
                                            </PermissionButton>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
            
            {/* 發布公告模態框 */}
            <Modal
                isOpen={createModal.isOpen}
                onClose={createModal.closeModal}
                size="lg"
            >
                <div className="bg-[#1A325F] border border-[#294565] rounded-lg p-6">
                    <h3 className="text-xl font-bold text-[#92cbf4] mb-4">📝 發布新公告</h3>
                    
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-[#7BC2E6] mb-2">
                                公告標題 *
                            </label>
                            <input
                                type="text"
                                value={publishForm.title}
                                onChange={(e) => setPublishForm({ ...publishForm, title: e.target.value })}
                                className="w-full bg-[#0f203e] border border-[#294565] rounded px-3 py-2 text-[#92cbf4] focus:outline-none focus:border-[#469FD2]"
                                placeholder="請輸入公告標題"
                            />
                        </div>
                        
                        <div>
                            <label className="block text-sm font-medium text-[#7BC2E6] mb-2">
                                公告內容 *
                            </label>
                            <textarea
                                value={publishForm.message}
                                onChange={(e) => setPublishForm({ ...publishForm, message: e.target.value })}
                                rows={5}
                                className="w-full bg-[#0f203e] border border-[#294565] rounded px-3 py-2 text-[#92cbf4] focus:outline-none focus:border-[#469FD2] resize-none"
                                placeholder="請輸入公告內容"
                            />
                        </div>
                        
                        <div>
                            <label className="flex items-center space-x-2">
                                <input
                                    type="checkbox"
                                    checked={publishForm.broadcast}
                                    onChange={(e) => setPublishForm({ ...publishForm, broadcast: e.target.checked })}
                                    className="rounded border-[#294565] bg-[#0f203e] text-[#469FD2]"
                                />
                                <span className="text-[#7BC2E6]">同時發送到 Telegram Bot</span>
                            </label>
                        </div>
                    </div>
                    
                    <div className="flex justify-end space-x-3 mt-6">
                        <button
                            onClick={createModal.closeModal}
                            className="px-4 py-2 text-[#7BC2E6] bg-[#294565] rounded hover:bg-[#3A5578]"
                        >
                            取消
                        </button>
                        <button
                            onClick={handlePublishAnnouncement}
                            disabled={publishLoading || !publishForm.title.trim() || !publishForm.message.trim()}
                            className="px-4 py-2 bg-[#469FD2] text-white rounded hover:bg-[#5BAEE3] disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {publishLoading ? "發布中..." : "發布公告"}
                        </button>
                    </div>
                </div>
            </Modal>
            
            {/* 編輯公告模態框 */}
            <Modal
                isOpen={editModal.isOpen}
                onClose={editModal.closeModal}
                size="lg"
            >
                <div className="bg-[#1A325F] border border-[#294565] rounded-lg p-6">
                    <h3 className="text-xl font-bold text-[#92cbf4] mb-4">✏️ 編輯公告</h3>
                    
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-[#7BC2E6] mb-2">
                                公告標題 *
                            </label>
                            <input
                                type="text"
                                value={editForm.title}
                                onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
                                className="w-full bg-[#0f203e] border border-[#294565] rounded px-3 py-2 text-[#92cbf4] focus:outline-none focus:border-[#469FD2]"
                                placeholder="請輸入公告標題"
                            />
                        </div>
                        
                        <div>
                            <label className="block text-sm font-medium text-[#7BC2E6] mb-2">
                                公告內容 *
                            </label>
                            <textarea
                                value={editForm.message}
                                onChange={(e) => setEditForm({ ...editForm, message: e.target.value })}
                                rows={5}
                                className="w-full bg-[#0f203e] border border-[#294565] rounded px-3 py-2 text-[#92cbf4] focus:outline-none focus:border-[#469FD2] resize-none"
                                placeholder="請輸入公告內容"
                            />
                        </div>
                        
                        <div>
                            <label className="flex items-center space-x-2">
                                <input
                                    type="checkbox"
                                    checked={editForm.broadcast}
                                    onChange={(e) => setEditForm({ ...editForm, broadcast: e.target.checked })}
                                    className="rounded border-[#294565] bg-[#0f203e] text-[#469FD2]"
                                />
                                <span className="text-[#7BC2E6]">同時發送到 Telegram Bot</span>
                            </label>
                        </div>
                    </div>
                    
                    <div className="flex justify-end space-x-3 mt-6">
                        <button
                            onClick={editModal.closeModal}
                            className="px-4 py-2 text-[#7BC2E6] bg-[#294565] rounded hover:bg-[#3A5578]"
                        >
                            取消
                        </button>
                        <button
                            onClick={handleEditAnnouncement}
                            disabled={editLoading || !editForm.title.trim() || !editForm.message.trim()}
                            className="px-4 py-2 bg-[#469FD2] text-white rounded hover:bg-[#5BAEE3] disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {editLoading ? "更新中..." : "更新公告"}
                        </button>
                    </div>
                </div>
            </Modal>
            
            {/* 刪除確認模態框 */}
            <Modal
                isOpen={deleteModal.isOpen}
                onClose={deleteModal.closeModal}
                size="md"
            >
                <div className="bg-[#1A325F] border border-[#294565] rounded-lg p-6">
                    <h3 className="text-xl font-bold text-red-400 mb-4">🗑️ 確認刪除</h3>
                    
                    {deleteTarget && (
                        <div className="mb-6">
                            <p className="text-[#7BC2E6] mb-2">確定要刪除以下公告嗎？</p>
                            <div className="bg-[#0f203e] border border-[#294565] rounded p-3">
                                <div className="text-[#92cbf4] font-medium">{deleteTarget.title}</div>
                                <div className="text-[#7BC2E6] text-sm mt-1 line-clamp-2">
                                    {deleteTarget.message}
                                </div>
                            </div>
                            <p className="text-red-400 text-sm mt-3">⚠️ 此操作無法撤銷</p>
                        </div>
                    )}
                    
                    <div className="flex justify-end space-x-3">
                        <button
                            onClick={deleteModal.closeModal}
                            className="px-4 py-2 text-[#7BC2E6] bg-[#294565] rounded hover:bg-[#3A5578]"
                        >
                            取消
                        </button>
                        <button
                            onClick={handleDeleteAnnouncement}
                            className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                        >
                            確認刪除
                        </button>
                    </div>
                </div>
            </Modal>
        </div>
    );
};

export default AnnouncementManagement;