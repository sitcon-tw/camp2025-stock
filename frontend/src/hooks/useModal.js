import { useState } from "react";

const useModal = (defaultOpen = false) => {
    const [isOpen, setIsOpen] = useState(defaultOpen);
    const [isClosing, setIsClosing] = useState(false);

    const openModal = () => {
        setIsOpen(true);
        setIsClosing(false);
    };

    const closeModal = () => {
        setIsClosing(true);
        setTimeout(() => {
            setIsOpen(false);
            setIsClosing(false);
        }, 200);
    };

    const toggleModal = () => {
        if (isOpen) {
            closeModal();
        } else {
            openModal();
        }
    };

    return {
        isOpen,
        isClosing,
        openModal,
        closeModal,
        toggleModal,
    };
};

export default useModal;
