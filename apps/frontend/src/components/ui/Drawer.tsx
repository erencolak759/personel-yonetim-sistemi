import React, { useEffect, useRef, useCallback } from 'react'
import { X } from 'lucide-react'
import { createPortal } from 'react-dom'

export interface DrawerProps {
    isOpen: boolean
    onClose: () => void
    title?: string
    description?: string
    size?: 'sm' | 'md' | 'lg' | 'xl'
    position?: 'left' | 'right'
    children: React.ReactNode
    footer?: React.ReactNode
    closeOnBackdrop?: boolean
    closeOnEscape?: boolean
    showCloseButton?: boolean
    className?: string
}

const Drawer: React.FC<DrawerProps> = ({
    isOpen,
    onClose,
    title,
    description,
    size = 'md',
    position = 'right',
    children,
    footer,
    closeOnBackdrop = true,
    closeOnEscape = true,
    showCloseButton = true,
    className = '',
}) => {
    const drawerRef = useRef<HTMLDivElement>(null)
    const previousActiveElement = useRef<HTMLElement | null>(null)

    // Keyboard handling
    const handleKeyDown = useCallback(
        (e: KeyboardEvent) => {
            if (e.key === 'Escape' && closeOnEscape) {
                onClose()
                return
            }

            if (e.key === 'Tab' && drawerRef.current) {
                const focusableElements = drawerRef.current.querySelectorAll(
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

            setTimeout(() => {
                const focusableElement = drawerRef.current?.querySelector(
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
    }

    const positionClasses = {
        left: 'left-0 animate-slide-in-left',
        right: 'right-0 animate-slide-in-right',
    }

    const drawerContent = (
        <div className="fixed inset-0 z-50">
            {/* Backdrop */}
            <div
                className="fixed inset-0 bg-black/50 backdrop-blur-sm animate-fade-in"
                onClick={closeOnBackdrop ? onClose : undefined}
                aria-hidden="true"
            />

            {/* Drawer */}
            <div
                ref={drawerRef}
                role="dialog"
                aria-modal="true"
                aria-labelledby={title ? 'drawer-title' : undefined}
                aria-describedby={description ? 'drawer-description' : undefined}
                className={`
          fixed top-0 h-full w-full ${sizeClasses[size]}
          bg-white shadow-2xl
          flex flex-col
          ${positionClasses[position]}
          ${className}
        `}
            >
                {/* Header */}
                <div className="flex items-start justify-between p-6 border-b border-slate-200 shrink-0">
                    <div>
                        {title && (
                            <h2 id="drawer-title" className="text-lg font-semibold text-slate-900">
                                {title}
                            </h2>
                        )}
                        {description && (
                            <p id="drawer-description" className="text-sm text-slate-500 mt-1">
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

                {/* Body */}
                <div className="flex-1 overflow-y-auto p-6">{children}</div>

                {/* Footer */}
                {footer && (
                    <div className="flex items-center justify-end gap-3 p-6 border-t border-slate-200 bg-slate-50/50 shrink-0">
                        {footer}
                    </div>
                )}
            </div>
        </div>
    )

    return createPortal(drawerContent, document.body)
}

export default Drawer
