import React, { useEffect, useRef, useCallback } from 'react'
import { X } from 'lucide-react'
import { createPortal } from 'react-dom'
import Button from './Button'

export interface ModalProps {
    isOpen: boolean
    onClose: () => void
    title?: string
    description?: string
    size?: 'sm' | 'md' | 'lg' | 'xl' | 'full'
    children: React.ReactNode
    footer?: React.ReactNode
    closeOnBackdrop?: boolean
    closeOnEscape?: boolean
    showCloseButton?: boolean
    className?: string
}

const Modal: React.FC<ModalProps> = ({
    isOpen,
    onClose,
    title,
    description,
    size = 'md',
    children,
    footer,
    closeOnBackdrop = true,
    closeOnEscape = true,
    showCloseButton = true,
    className = '',
}) => {
    const modalRef = useRef<HTMLDivElement>(null)
    const previousActiveElement = useRef<HTMLElement | null>(null)

    // Trap focus inside modal
    const handleKeyDown = useCallback(
        (e: KeyboardEvent) => {
            if (e.key === 'Escape' && closeOnEscape) {
                onClose()
                return
            }

            if (e.key === 'Tab' && modalRef.current) {
                const focusableElements = modalRef.current.querySelectorAll(
                    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
                )
                const firstElement = focusableElements[0] as HTMLElement
                const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement

                if (e.shiftKey && document.activeElement === firstElement) {
                    e.preventDefault()
                    lastElement?.focus()
                } else if (!e.shiftKey && document.activeElement === lastElement) {
                    e.preventDefault()
                    firstElement?.focus()
                }
            }
        },
        [closeOnEscape, onClose]
    )

    useEffect(() => {
        if (isOpen) {
            previousActiveElement.current = document.activeElement as HTMLElement
            document.body.style.overflow = 'hidden'
            document.addEventListener('keydown', handleKeyDown)

            // Focus first focusable element
            setTimeout(() => {
                const focusableElement = modalRef.current?.querySelector(
                    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
                ) as HTMLElement
                focusableElement?.focus()
            }, 0)
        }

        return () => {
            document.body.style.overflow = ''
            document.removeEventListener('keydown', handleKeyDown)
            previousActiveElement.current?.focus()
        }
    }, [isOpen, handleKeyDown])

    if (!isOpen) return null

    const sizeClasses = {
        sm: 'max-w-sm',
        md: 'max-w-md',
        lg: 'max-w-lg',
        xl: 'max-w-xl',
        full: 'max-w-4xl',
    }

    const modalContent = (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            {/* Backdrop */}
            <div
                className="overlay animate-fade-in"
                onClick={closeOnBackdrop ? onClose : undefined}
                aria-hidden="true"
            />

            {/* Modal */}
            <div
                ref={modalRef}
                role="dialog"
                aria-modal="true"
                aria-labelledby={title ? 'modal-title' : undefined}
                aria-describedby={description ? 'modal-description' : undefined}
                className={`
          relative bg-white rounded-2xl shadow-2xl w-full ${sizeClasses[size]}
          max-h-[90vh] overflow-hidden flex flex-col
          animate-scale-in
          ${className}
        `}
            >
                {/* Header */}
                {(title || showCloseButton) && (
                    <div className="modal-header flex items-start justify-between p-6 border-b border-slate-200">
                        <div>
                            {title && (
                                <h2 id="modal-title" className="text-lg font-semibold text-slate-900">
                                    {title}
                                </h2>
                            )}
                            {description && (
                                <p id="modal-description" className="text-sm text-slate-500 mt-1">
                                    {description}
                                </p>
                            )}
                        </div>
                        {showCloseButton && (
                            <button
                                onClick={onClose}
                                className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors -mr-1.5 -mt-1.5"
                                aria-label="Close"
                            >
                                <X size={20} />
                            </button>
                        )}
                    </div>
                )}

                {/* Body */}
                <div className="modal-body p-6 overflow-y-auto flex-1">{children}</div>

                {/* Footer */}
                {footer && (
                    <div className="modal-footer flex items-center justify-end gap-3 p-6 border-t border-slate-200 bg-slate-50/50">
                        {footer}
                    </div>
                )}
            </div>
        </div>
    )

    return createPortal(modalContent, document.body)
}

// Convenience component for confirmation dialogs
export interface ConfirmModalProps {
    isOpen: boolean
    onClose: () => void
    onConfirm: () => void
    title: string
    message: string
    confirmLabel?: string
    cancelLabel?: string
    variant?: 'danger' | 'warning' | 'primary'
    isLoading?: boolean
}

export const ConfirmModal: React.FC<ConfirmModalProps> = ({
    isOpen,
    onClose,
    onConfirm,
    title,
    message,
    confirmLabel = 'Onayla',
    cancelLabel = 'İptal',
    variant = 'danger',
    isLoading = false,
}) => {
    const buttonVariant = variant === 'danger' ? 'danger' : variant === 'warning' ? 'warning' : 'primary'

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title={title}
            size="sm"
            footer={
                <>
                    <Button variant="secondary" onClick={onClose} disabled={isLoading}>
                        {cancelLabel}
                    </Button>
                    <Button variant={buttonVariant} onClick={onConfirm} isLoading={isLoading}>
                        {confirmLabel}
                    </Button>
                </>
            }
        >
            <p className="text-slate-600">{message}</p>
        </Modal>
    )
}

export default Modal
