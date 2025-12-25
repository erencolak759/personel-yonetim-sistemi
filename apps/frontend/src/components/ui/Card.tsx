import React from 'react'

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
    variant?: 'default' | 'elevated' | 'outlined'
    padding?: 'none' | 'sm' | 'md' | 'lg'
    hoverable?: boolean
    children: React.ReactNode
}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
    (
        {
            variant = 'default',
            padding = 'md',
            hoverable = false,
            className = '',
            children,
            ...props
        },
        ref
    ) => {
        const variantClasses = {
            default: 'card',
            elevated: 'card shadow-md',
            outlined: 'bg-white rounded-xl border-2 border-slate-200',
        }

        const paddingClasses = {
            none: '',
            sm: 'p-4',
            md: 'p-6',
            lg: 'p-8',
        }

        const classes = [
            variantClasses[variant],
            paddingClasses[padding],
            hoverable && 'card-hover cursor-pointer',
            className,
        ]
            .filter(Boolean)
            .join(' ')

        return (
            <div ref={ref} className={classes} {...props}>
                {children}
            </div>
        )
    }
)

Card.displayName = 'Card'

// Card sub-components for structured layouts
export const CardHeader: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
    className = '',
    children,
    ...props
}) => (
    <div className={`flex items-center justify-between mb-4 ${className}`} {...props}>
        {children}
    </div>
)

export const CardTitle: React.FC<React.HTMLAttributes<HTMLHeadingElement>> = ({
    className = '',
    children,
    ...props
}) => (
    <h3 className={`text-lg font-semibold text-slate-900 ${className}`} {...props}>
        {children}
    </h3>
)

export const CardDescription: React.FC<React.HTMLAttributes<HTMLParagraphElement>> = ({
    className = '',
    children,
    ...props
}) => (
    <p className={`text-sm text-slate-500 ${className}`} {...props}>
        {children}
    </p>
)

export const CardContent: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
    className = '',
    children,
    ...props
}) => (
    <div className={className} {...props}>
        {children}
    </div>
)

export const CardFooter: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
    className = '',
    children,
    ...props
}) => (
    <div className={`flex items-center justify-end gap-3 pt-4 mt-4 border-t border-slate-200 ${className}`} {...props}>
        {children}
    </div>
)

export default Card
