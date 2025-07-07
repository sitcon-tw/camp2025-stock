import { PERMISSIONS } from "@/contexts/PermissionContext";
import useModal from "@/hooks/useModal";
import {
    createAnnouncement,
    deleteAnnouncement,
    getAnnouncementsAdmin,
} from "@/lib/api";
import { Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { Modal } from "../ui";
import { PermissionButton } from "./PermissionGuard";

/**
 * 公告管理組件 - 包含發布公告和管理公告功能
 */
export const AnnouncementManagement = ({ token }) => {
    const [activeTab, setActiveTab] = useState("manage");
    const [announcements, setAnnouncements] = useState([]);
    const [loading, setLoading] = useState(false);
    const [notification, setNotification] = useState({
        show: false,
        message: "",
        type: "info",
    });

    // 分頁和過濾狀態
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage] = useState(5); // 每頁顯示5個公告
    const [showDeleted, setShowDeleted] = useState(false);

    // 發布公告相關狀態
    const createModal = useModal();
    const [publishForm, setPublishForm] = useState({
        title: "",
        message: "",
        broadcast: true,
    });
    const [publishLoading, setPublishLoading] = useState(false);

    // 編輯公告相關狀態
    const editModal = useModal();
    const [editForm, setEditForm] = useState({
        id: "",
        title: "",
        message: "",
        broadcast: true,
    });
    const [editLoading, setEditLoading] = useState(false);

    // 刪除確認模態框
    const deleteModal = useModal();
    const [deleteTarget, setDeleteTarget] = useState(null);
    const [deleteLoading, setDeleteLoading] = useState(false);

    useEffect(() => {
        fetchAnnouncements();
    }, [token]);

    // 顯示通知
    const showNotification = (message, type = "info") => {
        setNotification({ show: true, message, type });
        setTimeout(
            () =>
                setNotification({
                    show: false,
                    message: "",
                    type: "info",
                }),
            3000,
        );
    };

    // 過濾公告
    const filteredAnnouncements = announcements.filter((announcement) => {
        if (showDeleted) {
            return announcement.is_deleted; // 只顯示已刪除的
        } else {
            return !announcement.is_deleted; // 只顯示未刪除的
        }
    });

    // 分頁邏輯
    const totalPages = Math.ceil(filteredAnnouncements.length / itemsPerPage);
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const currentAnnouncements = filteredAnnouncements.slice(startIndex, endIndex);

    // 重置分頁當過濾條件改變
    const handleFilterChange = (deleted) => {
        setShowDeleted(deleted);
        setCurrentPage(1);
    };

    // 獲取公告列表
    const fetchAnnouncements = async () => {
        try {
            setLoading(true);
            const response = await getAnnouncementsAdmin(token);

            setAnnouncements(response || []);
        } catch (error) {
            showNotification(
                `獲取公告列表失敗: ${error.message}`,
                "error",
            );
            setAnnouncements([]);
        } finally {
            setLoading(false);
        }
    };

    // 發布公告
    const handlePublishAnnouncement = async () => {
        if (
            !publishForm.title.trim() ||
            !publishForm.message.trim()
        ) {
            showNotification("請填寫公告標題和內容", "error");
            return;
        }

        try {
            setPublishLoading(true);
            await createAnnouncement(
                token,
                publishForm.title,
                publishForm.message,
                publishForm.broadcast,
            );
            showNotification("公告已成功發布", "success");
            setPublishForm({
                title: "",
                message: "",
                broadcast: true,
            });
            createModal.closeModal();
            fetchAnnouncements(); // 重新獲取公告列表
        } catch (error) {
            showNotification(
                `發布公告失敗: ${error.message}`,
                "error",
            );
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
            showNotification(
                "功能開發中：編輯公告 API 尚未實作",
                "info",
            );
            editModal.closeModal();
        } catch (error) {
            showNotification(
                `編輯公告失敗: ${error.message}`,
                "error",
            );
        } finally {
            setEditLoading(false);
        }
    };

    // 刪除公告
    const handleDeleteAnnouncement = async () => {
        if (!deleteTarget) return;

        try {
            setDeleteLoading(true);
            const response = await deleteAnnouncement(token, deleteTarget._id);
            showNotification(response.message || "公告已標記為已刪除", "success");
            deleteModal.closeModal();
            setDeleteTarget(null);
            fetchAnnouncements(); // 重新獲取公告列表
        } catch (error) {
            showNotification(
                `刪除公告失敗: ${error.message}`,
                "error",
            );
        } finally {
            setDeleteLoading(false);
        }
    };

    // 打開編輯模態框
    const openEditModal = (announcement) => {
        setEditForm({
            id: announcement.id,
            title: announcement.title,
            message: announcement.message,
            broadcast: announcement.broadcast !== false,
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
            return new Date(dateString).toLocaleString("zh-TW", {
                year: "numeric",
                month: "2-digit",
                day: "2-digit",
                hour: "2-digit",
                minute: "2-digit",
            });
        } catch {
            return "日期格式錯誤";
        }
    };

    return (
        <div className="space-y-6">
            {/* 通知提示 */}
            {notification.show && (
                <div
                    className={`rounded-lg border p-4 ${
                        notification.type === "success"
                            ? "border-green-500/30 bg-green-600/20 text-green-400"
                            : notification.type === "error"
                              ? "border-red-500/30 bg-red-600/20 text-red-400"
                              : "border-blue-500/30 bg-blue-600/20 text-blue-400"
                    }`}
                >
                    {notification.message}
                </div>
            )}

            {/* 標題和操作按鈕 */}
            <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-[#92cbf4]">
                    公告管理
                </h2>
                <div className="flex space-x-3">
                    <PermissionButton
                        requiredPermission={
                            PERMISSIONS.CREATE_ANNOUNCEMENT
                        }
                        token={token}
                        onClick={createModal.openModal}
                        className="flex items-center space-x-2 rounded bg-[#469FD2] px-4 py-2 text-white hover:bg-[#5BAEE3]"
                    >
                        <span>發佈新公告</span>
                    </PermissionButton>
                </div>
            </div>

            {/* 過濾控制 */}
            <div className="flex items-center justify-between rounded-lg border border-[#294565] bg-[#1A325F] p-4">
                <div className="flex items-center space-x-4">
                    <span className="text-sm font-medium text-[#7BC2E6]">顯示：</span>
                    <div className="flex space-x-2">
                        <button
                            onClick={() => handleFilterChange(false)}
                            className={`rounded px-3 py-1 text-sm transition-colors ${
                                !showDeleted
                                    ? "bg-blue-500 text-white"
                                    : "bg-[#294565] text-[#7BC2E6] hover:bg-[#3A5578]"
                            }`}
                        >
                            有效公告
                        </button>
                        <button
                            onClick={() => handleFilterChange(true)}
                            className={`rounded px-3 py-1 text-sm transition-colors ${
                                showDeleted
                                    ? "bg-red-500 text-white"
                                    : "bg-[#294565] text-[#7BC2E6] hover:bg-[#3A5578]"
                            }`}
                        >
                            已刪除公告
                        </button>
                    </div>
                </div>
                <div className="text-sm text-[#557797]">
                    共 {filteredAnnouncements.length} 個公告
                </div>
            </div>

            {/* 公告列表 */}
            <div className="rounded-lg border border-[#294565] bg-[#1A325F]">
                <div className="p-6">
                    {loading ? (
                        <div className="flex items-center justify-center p-8">
                            <div className="text-lg text-[#7BC2E6]">
                                載入中...
                            </div>
                        </div>
                    ) : currentAnnouncements.length === 0 ? (
                        <div className="p-8 text-center">
                            <div className="mb-2 text-lg text-[#7BC2E6]">
                                📝 {showDeleted ? "暫無已刪除公告" : "暫無有效公告"}
                            </div>
                            <div className="text-sm text-[#557797]">
                                {showDeleted 
                                    ? "沒有找到已刪除的公告" 
                                    : "點擊上方「發布公告」按鈕來創建第一個公告"
                                }
                            </div>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            {currentAnnouncements.map((announcement) => (
                                <div
                                    key={announcement._id}
                                    className={`rounded-lg border p-4 ${
                                        announcement.is_deleted
                                            ? "border-red-500/30 bg-red-900/20 opacity-75"
                                            : "border-[#294565] bg-[#0f203e]"
                                    }`}
                                >
                                    <div className="flex items-start justify-between">
                                        <div className="flex-1">
                                            <div className="mb-2 flex items-center space-x-2">
                                                <h4 className={`text-lg font-semibold ${
                                                    announcement.is_deleted
                                                        ? "text-red-400 line-through"
                                                        : "text-[#92cbf4]"
                                                }`}>
                                                    {announcement.title}
                                                </h4>
                                                {announcement.is_deleted && (
                                                    <span className="rounded bg-red-600/30 px-2 py-1 text-xs text-red-400">
                                                        已刪除
                                                    </span>
                                                )}
                                            </div>
                                            <p className={`mb-3 leading-relaxed ${
                                                announcement.is_deleted
                                                    ? "text-red-300/70 line-through"
                                                    : "text-[#7BC2E6]"
                                            }`}>
                                                {announcement.message}
                                            </p>
                                            <div className="flex items-center space-x-4 text-sm text-[#557797]">
                                                <span>
                                                    {formatDate(
                                                        announcement.created_at,
                                                    )}
                                                </span>
                                                {announcement.broadcast && (
                                                    <span className="rounded bg-blue-600/20 px-2 py-1 text-xs text-blue-400">
                                                        Telegram 廣播
                                                    </span>
                                                )}
                                                {announcement.is_deleted && announcement.deleted_at && (
                                                    <span className="rounded bg-red-600/20 px-2 py-1 text-xs text-red-400">
                                                        刪除於 {formatDate(announcement.deleted_at)}
                                                    </span>
                                                )}
                                            </div>
                                        </div>

                                        <div className="ml-4 flex space-x-2">
                                            {!announcement.is_deleted && (
                                                <PermissionButton
                                                    requiredPermission={
                                                        PERMISSIONS.CREATE_ANNOUNCEMENT
                                                    }
                                                    token={token}
                                                    onClick={() =>
                                                        openDeleteModal(
                                                            announcement,
                                                        )
                                                    }
                                                    className="text-gray-600 transition-colors hover:text-red-500"
                                                >
                                                    <Trash2 className="h-5 w-5" />
                                                </PermissionButton>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* 分頁控制 */}
                {totalPages > 1 && (
                    <div className="flex items-center justify-between border-t border-[#294565] p-4">
                        <div className="text-sm text-[#557797]">
                            第 {startIndex + 1} - {Math.min(endIndex, filteredAnnouncements.length)} 項，
                            共 {filteredAnnouncements.length} 項
                        </div>
                        <div className="flex items-center space-x-2">
                            <button
                                onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                                disabled={currentPage === 1}
                                className="rounded bg-[#294565] px-3 py-1 text-sm text-[#7BC2E6] hover:bg-[#3A5578] disabled:cursor-not-allowed disabled:opacity-50"
                            >
                                上一頁
                            </button>
                            <div className="flex items-center space-x-1">
                                {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                                    <button
                                        key={page}
                                        onClick={() => setCurrentPage(page)}
                                        className={`rounded px-3 py-1 text-sm transition-colors ${
                                            currentPage === page
                                                ? "bg-blue-500 text-white"
                                                : "bg-[#294565] text-[#7BC2E6] hover:bg-[#3A5578]"
                                        }`}
                                    >
                                        {page}
                                    </button>
                                ))}
                            </div>
                            <button
                                onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                                disabled={currentPage === totalPages}
                                className="rounded bg-[#294565] px-3 py-1 text-sm text-[#7BC2E6] hover:bg-[#3A5578] disabled:cursor-not-allowed disabled:opacity-50"
                            >
                                下一頁
                            </button>
                        </div>
                    </div>
                )}
            </div>

            {/* 發布公告模態框 */}
            <Modal
                isOpen={createModal.isOpen}
                onClose={createModal.closeModal}
                title="發布新公告"
                size="lg"
            >
                <div className="space-y-4">
                    <div>
                        <label className="mb-2 block text-sm font-medium text-[#7BC2E6]">
                            公告標題
                        </label>
                        <input
                            type="text"
                            value={publishForm.title}
                            onChange={(e) =>
                                setPublishForm({
                                    ...publishForm,
                                    title: e.target.value,
                                })
                            }
                            className="w-full rounded border border-[#294565] bg-[#0f203e] px-3 py-2 text-[#92cbf4] focus:border-[#469FD2] focus:outline-none"
                            placeholder="請輸入公告標題"
                        />
                    </div>

                    <div>
                        <label className="mb-2 block text-sm font-medium text-[#7BC2E6]">
                            公告內容
                        </label>
                        <textarea
                            value={publishForm.message}
                            onChange={(e) =>
                                setPublishForm({
                                    ...publishForm,
                                    message: e.target.value,
                                })
                            }
                            rows={5}
                            className="w-full resize-none rounded border border-[#294565] bg-[#0f203e] px-3 py-2 text-[#92cbf4] focus:border-[#469FD2] focus:outline-none"
                            placeholder="請輸入公告內容"
                        />
                    </div>

                    <div>
                        <label className="flex items-center space-x-2">
                            <input
                                type="checkbox"
                                checked={publishForm.broadcast}
                                onChange={(e) =>
                                    setPublishForm({
                                        ...publishForm,
                                        broadcast: e.target.checked,
                                    })
                                }
                                className="rounded border-[#294565] bg-[#0f203e] text-[#469FD2]"
                            />
                            <span className="text-[#7BC2E6]">
                                同時發送到 Telegram Bot
                            </span>
                        </label>
                    </div>
                </div>

                <div className="mt-6 flex justify-end space-x-3">
                    <button
                        onClick={createModal.closeModal}
                        className="rounded bg-[#294565] px-4 py-2 text-[#7BC2E6] hover:bg-[#3A5578]"
                    >
                        取消
                    </button>
                    <button
                        onClick={handlePublishAnnouncement}
                        disabled={
                            publishLoading ||
                            !publishForm.title.trim() ||
                            !publishForm.message.trim()
                        }
                        className="rounded bg-[#469FD2] px-4 py-2 text-white hover:bg-[#5BAEE3] disabled:cursor-not-allowed disabled:opacity-50"
                    >
                        {publishLoading ? "發布中..." : "發布公告"}
                    </button>
                </div>
            </Modal>

            {/* 刪除確認模態框 */}
            <Modal
                isOpen={deleteModal.isOpen}
                onClose={deleteModal.closeModal}
                title="確認刪除公告？"
                size="md"
            >
                {deleteTarget && (
                    <div className="mb-6">
                        <p className="mb-2 text-[#7BC2E6]">
                            確定要標記以下公告為已刪除嗎？
                        </p>
                        <div className="rounded border border-[#294565] bg-[#0f203e] p-3">
                            <div className="font-medium text-[#92cbf4]">
                                {deleteTarget.title}
                            </div>
                            <div className="mt-1 line-clamp-2 text-sm text-[#7BC2E6]">
                                {deleteTarget.message}
                            </div>
                        </div>
                        <p className="mt-3 text-sm text-yellow-400">
                            ⚠️ 公告將被標記為已刪除，但仍會保留在系統中
                        </p>
                    </div>
                )}

                <div className="flex justify-end space-x-3">
                    <button
                        onClick={deleteModal.closeModal}
                        className="rounded bg-[#294565] px-4 py-2 text-[#7BC2E6] hover:bg-[#3A5578]"
                    >
                        取消
                    </button>
                    <button
                        onClick={handleDeleteAnnouncement}
                        disabled={deleteLoading}
                        className="rounded bg-red-600 px-4 py-2 text-white hover:bg-red-700 disabled:cursor-not-allowed! disabled:opacity-50"
                    >
                        {deleteLoading ? "標記中..." : "確認標記為已刪除"}
                    </button>
                </div>
            </Modal>
        </div>
    );
};

export default AnnouncementManagement;
