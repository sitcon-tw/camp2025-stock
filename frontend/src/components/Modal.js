"use client";

import { useEffect } from "react";
import { twMerge } from "tailwind-merge";
import "./Modal.css";

const Modal = ({
    isOpen,
    onClose,
    title,
    children,
    size = "md",
    closeOnOverlayClick = true,
    showCloseButton = true,
    className = "",
    isClosing = false,
}) => {
    // ESC 鍵
    useEffect(() => {
        const handleEsc = (e) => {
            if (e.key === "Escape" && isOpen) {
                onClose();
            }
        };

        if (isOpen) {
            document.addEventListener("keydown", handleEsc);
            document.body.style.overflow = "hidden";
        }

        return () => {
            document.removeEventListener("keydown", handleEsc);
            document.body.style.overflow = "unset";
        };
    }, [isOpen, onClose]);

    // 只有在未開啟且未關閉中時才隱藏 Modal
    if (!isOpen && !isClosing) return null;

    // Modal 尺寸
    const sizeClasses = {
        sm: "max-w-sm",
        md: "max-w-md",
        lg: "max-w-lg",
        xl: "max-w-xl",
        "2xl": "max-w-2xl",
        "3xl": "max-w-3xl",
        full: "max-w-full mx-4",
    };

    const handleOverlayClick = (e) => {
        if (closeOnOverlayClick && e.target === e.currentTarget) {
            onClose();
        }
    };

    return (
        <>
            <div
                className={twMerge(
                    "fixed inset-0 z-50 flex items-center justify-center p-4",
                    isClosing
                        ? "animate-modal-close-bg"
                        : "animate-modal-open-bg",
                )}
                onClick={handleOverlayClick}
                style={{
                    backgroundColor: 'rgba(0, 0, 0, 0.5)',
                    backdropFilter: 'blur(4px)',
                    WebkitBackdropFilter: 'blur(4px)',
                }}
            >
                {/* Modal 內容 */}
                <div
                    className={twMerge(
                        "w-full rounded-xl bg-[#1A325F] p-6 shadow-2xl",
                        sizeClasses[size],
                        isClosing
                            ? "animate-modal-close"
                            : "animate-modal-open",
                        className,
                    )}
                    onClick={(e) => e.stopPropagation()}
                >
                    {/* Modal 標題 */}
                    {(title || showCloseButton) && (
                        <div className="mb-4 flex items-center justify-between">
                            {title && (
                                <h2 className="text-xl font-bold text-[#AFE1F5]">
                                    {title}
                                </h2>
                            )}
                            {showCloseButton && (
                                <button
                                    onClick={onClose}
                                    className="text-xl font-bold text-[#AFE1F5] transition-colors hover:text-[#7BC2E6]"
                                    aria-label="關閉"
                                >
                                    ×
                                </button>
                            )}
                        </div>
                    )}

                    {/* Modal內容 */}
                    <div
                        className={
                            title || showCloseButton ? "" : "mt-0"
                        }
                    >
                        {children}
                    </div>
                </div>
            </div>
        </>
    );
};

export default Modal;
