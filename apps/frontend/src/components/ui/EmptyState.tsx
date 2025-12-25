import React from 'react'
import { LucideIcon } from 'lucide-react'
import Button from './Button'

export interface EmptyStateProps {
    icon?: LucideIcon
    title: string
    description?: string
    action?: {
        label: string
        onClick: () => void
        icon?: LucideIcon
    }
    className?: string
}

const EmptyState: React.FC<EmptyStateProps> = ({
    icon: Icon,
    title,
    description,
    action,
    className = '',
}) => {
    return (
        <div className={`empty-state ${className}`}>
            {Icon && <Icon className="empty-state-icon" strokeWidth={1.5} />}
            <h3 className="empty-state-title">{title}</h3>
            {description && <p className="empty-state-description">{description}</p>}
            {action && (
                <div className="mt-6">
                    <Button
                        variant="primary"
                        leftIcon={action.icon}
                        onClick={action.onClick}
                    >
                        {action.label}
                    </Button>
                </div>
            )}
        </div>
    )
}

export default EmptyState
