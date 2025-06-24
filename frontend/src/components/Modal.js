"use client";

import { useEffect } from "react";
import { twMerge } from "tailwind-merge";

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
    // 處理 ESC
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

    if (!isOpen) return null;

    // Modal 尺寸
    const sizeClasses = {
        sm: "max-w-sm",
        md: "max-w-md", 
        lg: "max-w-lg",
        xl: "max-w-xl",
        "2xl": "max-w-2xl",
        "3xl": "max-w-3xl",
        full: "max-w-full mx-4"
    };

    const handleOverlayClick = (e) => {
        if (closeOnOverlayClick && e.target === e.currentTarget) {
            onClose();
        }
    };

    return (
        <>
            {/* Modal 遮罩 */}
            <div
                className={twMerge(
                    "fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm",
                    isClosing
                        ? "animate-modal-close-bg"
                        : "animate-modal-open-bg",
                )}
                onClick={handleOverlayClick}
            >
                {/* Modal 內容 */}
                <div
                    className={twMerge(
                        "w-full rounded-xl bg-[#1A325F] p-6 shadow-2xl",
                        sizeClasses[size],
                        isClosing
                            ? "animate-modal-close"
                            : "animate-modal-open",
                        className
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
                                    className="text-xl font-bold text-[#AFE1F5] hover:text-[#7BC2E6] transition-colors"
                                    aria-label="關閉"
                                >
                                    ×
                                </button>
                            )}
                        </div>
                    )}

                    {/* Modal內容 */}
                    <div className={title || showCloseButton ? "" : "mt-0"}>
                        {children}
                    </div>
                </div>
            </div>

            <style jsx global>{`
                @keyframes modal-open {
                    from {
                        opacity: 0;
                        transform: scale(0.95);
                    }
                    to {
                        opacity: 1;
                        transform: scale(1);
                    }
                }

                @keyframes modal-close {
                    from {
                        opacity: 1;
                        transform: scale(1);
                    }
                    to {
                        opacity: 0;
                        transform: scale(0.95);
                    }
                }

                @keyframes modal-open-bg {
                    from {
                        opacity: 0;
                        backdrop-filter: blur(0px);
                    }
                    to {
                        opacity: 1;
                        backdrop-filter: blur(4px);
                    }
                }

                @keyframes modal-close-bg {
                    from {
                        opacity: 1;
                        backdrop-filter: blur(4px);
                    }
                    to {
                        opacity: 0;
                        backdrop-filter: blur(0px);
                    }
                }

                .animate-modal-open {
                    animation: modal-open 0.2s ease-out;
                }

                .animate-modal-close {
                    animation: modal-close 0.2s ease-in;
                }

                .animate-modal-open-bg {
                    animation: modal-open-bg 0.2s ease-out;
                }

                .animate-modal-close-bg {
                    animation: modal-close-bg 0.2s ease-in;
                }
            `}</style>
        </>
    );
};

export default Modal;