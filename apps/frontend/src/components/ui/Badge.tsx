import React from 'react'

export type BadgeVariant = 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'neutral'

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
    variant?: BadgeVariant
    size?: 'sm' | 'md'
    dot?: boolean
    children: React.ReactNode
}

const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
    (
        {
            variant = 'neutral',
            size = 'md',
            dot = false,
            className = '',
            children,
            ...props
        },
        ref
    ) => {
        const variantClasses = {
            primary: 'badge-primary',
            success: 'badge-success',
            warning: 'badge-warning',
            danger: 'badge-danger',
            info: 'badge-info',
            neutral: 'badge-neutral',
        }

        const sizeClasses = {
            sm: 'text-[10px] px-2 py-0.5',
            md: 'text-xs px-2.5 py-0.5',
        }

        const classes = [
            'badge',
            variantClasses[variant],
            sizeClasses[size],
            dot && 'badge-dot',
            className,
        ]
            .filter(Boolean)
            .join(' ')

        return (
            <span ref={ref} className={classes} {...props}>
                {children}
            </span>
        )
    }
)

Badge.displayName = 'Badge'

// Convenience components for common status badges
export const StatusBadge: React.FC<{
    status: 'Beklemede' | 'Onaylandi' | 'Reddedildi' | string
    className?: string
}> = ({ status, className }) => {
    const variantMap: Record<string, BadgeVariant> = {
        'Beklemede': 'warning',
        'Onaylandi': 'success',
        'Reddedildi': 'danger',
    }

    const labelMap: Record<string, string> = {
        'Beklemede': 'Beklemede',
        'Onaylandi': 'Onaylandı',
        'Reddedildi': 'Reddedildi',
    }

    return (
        <Badge
            variant={variantMap[status] || 'neutral'}
            dot
            className={className}
        >
            {labelMap[status] || status}
        </Badge>
    )
}

export const AttendanceBadge: React.FC<{
    status: 'Normal' | 'Izinli' | 'Devamsiz' | string | null
    className?: string
}> = ({ status, className }) => {
    const variantMap: Record<string, BadgeVariant> = {
        'Normal': 'success',
        'Izinli': 'info',
        'Devamsiz': 'danger',
    }

    const labelMap: Record<string, string> = {
        'Normal': 'Normal',
        'Izinli': 'İzinli',
        'Devamsiz': 'Devamsız',
    }

    if (!status) {
        return <Badge variant="neutral" className={className}>—</Badge>
    }

    return (
        <Badge
            variant={variantMap[status] || 'neutral'}
            className={className}
        >
            {labelMap[status] || status}
        </Badge>
    )
}

export const PriorityBadge: React.FC<{
    priority: 'Dusuk' | 'Normal' | 'Yuksek' | string
    className?: string
}> = ({ priority, className }) => {
    const variantMap: Record<string, BadgeVariant> = {
        'Dusuk': 'neutral',
        'Normal': 'warning',
        'Yuksek': 'danger',
    }

    const labelMap: Record<string, string> = {
        'Dusuk': 'Düşük',
        'Normal': 'Normal',
        'Yuksek': 'Yüksek',
    }

    return (
        <Badge
            variant={variantMap[priority] || 'neutral'}
            size="sm"
            className={className}
        >
            {labelMap[priority] || priority}
        </Badge>
    )
}

export default Badge
