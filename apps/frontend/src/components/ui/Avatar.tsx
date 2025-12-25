import React from 'react'

export interface AvatarProps extends React.HTMLAttributes<HTMLDivElement> {
    name: string
    src?: string
    size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
    variant?: 'circle' | 'rounded'
}

const Avatar = React.forwardRef<HTMLDivElement, AvatarProps>(
    (
        {
            name,
            src,
            size = 'md',
            variant = 'circle',
            className = '',
            ...props
        },
        ref
    ) => {
        const getInitials = (fullName: string): string => {
            const parts = fullName.trim().split(' ')
            if (parts.length >= 2) {
                return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
            }
            return fullName.substring(0, 2).toUpperCase()
        }

        const sizeClasses = {
            xs: 'avatar-xs',
            sm: 'avatar-sm',
            md: 'avatar-md',
            lg: 'avatar-lg',
            xl: 'avatar-xl',
        }

        const variantClasses = {
            circle: 'rounded-full',
            rounded: 'rounded-lg',
        }

        const classes = [
            'avatar',
            sizeClasses[size],
            variantClasses[variant],
            className,
        ]
            .filter(Boolean)
            .join(' ')

        if (src) {
            return (
                <div ref={ref} className={classes} {...props}>
                    <img
                        src={src}
                        alt={name}
                        className="w-full h-full object-cover rounded-inherit"
                        onError={(e) => {
                            // Hide image on error and show initials
                            (e.target as HTMLImageElement).style.display = 'none'
                        }}
                    />
                    <span className="absolute inset-0 flex items-center justify-center">
                        {getInitials(name)}
                    </span>
                </div>
            )
        }

        return (
            <div ref={ref} className={classes} {...props}>
                {getInitials(name)}
            </div>
        )
    }
)

Avatar.displayName = 'Avatar'

// Avatar group for showing multiple avatars
export const AvatarGroup: React.FC<{
    children: React.ReactNode
    max?: number
    size?: AvatarProps['size']
    className?: string
}> = ({ children, max = 4, size = 'md', className = '' }) => {
    const avatars = React.Children.toArray(children)
    const visibleAvatars = avatars.slice(0, max)
    const remainingCount = avatars.length - max

    return (
        <div className={`flex -space-x-2 ${className}`}>
            {visibleAvatars.map((avatar, index) => (
                <div key={index} className="relative ring-2 ring-white rounded-full">
                    {avatar}
                </div>
            ))}
            {remainingCount > 0 && (
                <div
                    className={`avatar ${size === 'md' ? 'avatar-md' : size === 'sm' ? 'avatar-sm' : 'avatar-md'} 
                     bg-slate-200 text-slate-600 ring-2 ring-white`}
                >
                    +{remainingCount}
                </div>
            )}
        </div>
    )
}

export default Avatar
