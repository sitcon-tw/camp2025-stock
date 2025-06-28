import { useState, useCallback } from "react";

const useModal = (defaultOpen = false) => {
    const [isOpen, setIsOpen] = useState(defaultOpen);
    const [isClosing, setIsClosing] = useState(false);

    const openModal = useCallback(() => {
        setIsClosing(false);
        setIsOpen(true);
    }, []);

    const closeModal = useCallback(() => {
        if (!isClosing && isOpen) {
            setIsClosing(true);

            setTimeout(() => {
                setIsOpen(false);
                setIsClosing(false);
            }, 200);
        }
    }, [isClosing, isOpen]);

    const toggleModal = useCallback(() => {
        if (isOpen) {
            closeModal();
        } else {
            openModal();
        }
    }, [isOpen, closeModal, openModal]);

    return {
        isOpen,
        isClosing,
        openModal,
        closeModal,
        toggleModal,
    };
};

export default useModal;
