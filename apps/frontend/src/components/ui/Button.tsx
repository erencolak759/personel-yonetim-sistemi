import React from 'react'
import { LucideIcon } from 'lucide-react'

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger' | 'success' | 'warning'
    size?: 'xs' | 'sm' | 'md' | 'lg'
    leftIcon?: LucideIcon
    rightIcon?: LucideIcon
    isLoading?: boolean
    isIconOnly?: boolean
    children?: React.ReactNode
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
    (
        {
            variant = 'primary',
            size = 'md',
            leftIcon: LeftIcon,
            rightIcon: RightIcon,
            isLoading = false,
            isIconOnly = false,
            children,
            className = '',
            disabled,
            ...props
        },
        ref
    ) => {
        const baseClasses = 'btn'

        const variantClasses = {
            primary: 'btn-primary',
            secondary: 'btn-secondary',
            outline: 'btn-outline',
            ghost: 'btn-ghost',
            danger: 'btn-danger',
            success: 'btn-success',
            warning: 'btn-warning',
        }

        const sizeClasses = {
            xs: 'btn-xs',
            sm: 'btn-sm',
            md: 'btn-md',
            lg: 'btn-lg',
        }

        const iconSize = {
            xs: 14,
            sm: 16,
            md: 18,
            lg: 20,
        }

        const classes = [
            baseClasses,
            variantClasses[variant],
            sizeClasses[size],
            isIconOnly && 'btn-icon',
            className,
        ]
            .filter(Boolean)
            .join(' ')

        return (
            <button
                ref={ref}
                className={classes}
                disabled={disabled || isLoading}
                {...props}
            >
                {isLoading ? (
                    <svg
                        className="animate-spin"
                        width={iconSize[size]}
                        height={iconSize[size]}
                        viewBox="0 0 24 24"
                        fill="none"
                    >
                        <circle
                            className="opacity-25"
                            cx="12"
                            cy="12"
                            r="10"
                            stroke="currentColor"
                            strokeWidth="4"
                        />
                        <path
                            className="opacity-75"
                            fill="currentColor"
                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                        />
                    </svg>
                ) : LeftIcon ? (
                    <LeftIcon size={iconSize[size]} />
                ) : null}

                {!isIconOnly && children}

                {!isLoading && RightIcon && <RightIcon size={iconSize[size]} />}
            </button>
        )
    }
)

Button.displayName = 'Button'

export default Button
