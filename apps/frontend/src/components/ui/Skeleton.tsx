import React from 'react'

interface SkeletonProps {
    className?: string
    variant?: 'text' | 'circular' | 'rectangular'
    width?: string | number
    height?: string | number
    lines?: number
}

const Skeleton: React.FC<SkeletonProps> = ({
    className = '',
    variant = 'rectangular',
    width,
    height,
    lines = 1,
}) => {
    const baseClass = 'animate-pulse bg-slate-200'

    const variantClasses = {
        text: 'rounded h-4',
        circular: 'rounded-full',
        rectangular: 'rounded-lg',
    }

    const style: React.CSSProperties = {
        width: width || '100%',
        height: variant === 'text' ? (height || '1rem') : (height || '100%'),
    }

    if (variant === 'text' && lines > 1) {
        return (
            <div className={`space-y-2 ${className}`}>
                {Array.from({ length: lines }).map((_, idx) => (
                    <div
                        key={idx}
                        className={`${baseClass} ${variantClasses.text}`}
                        style={{
                            ...style,
                            width: idx === lines - 1 ? '75%' : '100%',
                        }}
                    />
                ))}
            </div>
        )
    }

    return (
        <div
            className={`${baseClass} ${variantClasses[variant]} ${className}`}
            style={style}
        />
    )
}

// Pre-built skeleton patterns
export const SkeletonCard: React.FC<{ className?: string }> = ({ className = '' }) => (
    <div className={`card p-6 ${className}`}>
        <div className="flex items-center gap-4 mb-4">
            <Skeleton variant="circular" width={48} height={48} />
            <div className="flex-1">
                <Skeleton variant="text" width="60%" className="mb-2" />
                <Skeleton variant="text" width="40%" />
            </div>
        </div>
        <Skeleton variant="text" lines={3} />
    </div>
)

export const SkeletonTableRow: React.FC<{ columns?: number; className?: string }> = ({
    columns = 5,
    className = '',
}) => (
    <tr className={className}>
        {Array.from({ length: columns }).map((_, idx) => (
            <td key={idx} className="py-4 px-4">
                <Skeleton variant="text" width={idx === 0 ? '80%' : '60%'} />
            </td>
        ))}
    </tr>
)

export const SkeletonTable: React.FC<{
    rows?: number
    columns?: number
    className?: string
}> = ({ rows = 5, columns = 5, className = '' }) => (
    <div className={`card overflow-hidden ${className}`}>
        <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                    {Array.from({ length: columns }).map((_, idx) => (
                        <th key={idx} className="py-3.5 px-4">
                            <Skeleton variant="text" width="70%" />
                        </th>
                    ))}
                </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
                {Array.from({ length: rows }).map((_, idx) => (
                    <SkeletonTableRow key={idx} columns={columns} />
                ))}
            </tbody>
        </table>
    </div>
)

export const SkeletonStatCard: React.FC<{ className?: string }> = ({ className = '' }) => (
    <div className={`card p-6 ${className}`}>
        <div className="flex items-start justify-between">
            <div className="flex-1">
                <Skeleton variant="text" width="50%" className="mb-2" />
                <Skeleton variant="rectangular" width="70%" height={32} className="mb-3" />
                <Skeleton variant="text" width="40%" />
            </div>
            <Skeleton variant="rectangular" width={48} height={48} className="rounded-xl" />
        </div>
    </div>
)

export default Skeleton
