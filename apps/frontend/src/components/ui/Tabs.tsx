import React, { useState, createContext, useContext, useId } from 'react'

interface TabsContextValue {
    activeTab: string
    setActiveTab: (tab: string) => void
    variant: 'underline' | 'pills'
    idPrefix: string
}

const TabsContext = createContext<TabsContextValue | null>(null)

const useTabsContext = () => {
    const context = useContext(TabsContext)
    if (!context) {
        throw new Error('Tabs components must be used within a Tabs provider')
    }
    return context
}

// Root Tabs component
export interface TabsProps {
    defaultValue: string
    value?: string
    onValueChange?: (value: string) => void
    variant?: 'underline' | 'pills'
    className?: string
    children: React.ReactNode
}

export const Tabs: React.FC<TabsProps> = ({
    defaultValue,
    value,
    onValueChange,
    variant = 'underline',
    className = '',
    children,
}) => {
    const [internalValue, setInternalValue] = useState(defaultValue)
    const idPrefix = useId()

    const activeTab = value ?? internalValue
    const setActiveTab = (tab: string) => {
        setInternalValue(tab)
        onValueChange?.(tab)
    }

    return (
        <TabsContext.Provider value={{ activeTab, setActiveTab, variant, idPrefix }}>
            <div className={className}>{children}</div>
        </TabsContext.Provider>
    )
}

// TabsList - container for tab triggers
export interface TabsListProps {
    className?: string
    children: React.ReactNode
}

export const TabsList: React.FC<TabsListProps> = ({ className = '', children }) => {
    const { variant } = useTabsContext()

    const baseClasses = variant === 'underline'
        ? 'tabs flex border-b border-slate-200'
        : 'tabs-pills flex flex-wrap gap-2'

    return (
        <div role="tablist" className={`${baseClasses} ${className}`}>
            {children}
        </div>
    )
}

// TabTrigger - individual tab button
export interface TabTriggerProps {
    value: string
    disabled?: boolean
    className?: string
    children: React.ReactNode
    count?: number
}

export const TabTrigger: React.FC<TabTriggerProps> = ({
    value,
    disabled = false,
    className = '',
    children,
    count,
}) => {
    const { activeTab, setActiveTab, variant, idPrefix } = useTabsContext()
    const isActive = activeTab === value

    const handleClick = () => {
        if (!disabled) {
            setActiveTab(value)
        }
    }

    const baseClasses = variant === 'underline' ? 'tab' : 'tab-pill'

    return (
        <button
            role="tab"
            id={`${idPrefix}-tab-${value}`}
            aria-selected={isActive}
            aria-controls={`${idPrefix}-panel-${value}`}
            tabIndex={isActive ? 0 : -1}
            disabled={disabled}
            onClick={handleClick}
            className={`
        ${baseClasses}
        ${isActive ? 'active' : ''}
        ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
        ${className}
      `}
        >
            {children}
            {count !== undefined && (
                <span className={`ml-2 px-2 py-0.5 text-xs font-medium rounded-full ${isActive
                        ? variant === 'pills' ? 'bg-white/20' : 'bg-primary-100 text-primary-700'
                        : 'bg-slate-100 text-slate-600'
                    }`}>
                    {count}
                </span>
            )}
        </button>
    )
}

// TabContent - content panel for a tab
export interface TabContentProps {
    value: string
    className?: string
    children: React.ReactNode
    forceMount?: boolean
}

export const TabContent: React.FC<TabContentProps> = ({
    value,
    className = '',
    children,
    forceMount = false,
}) => {
    const { activeTab, idPrefix } = useTabsContext()
    const isActive = activeTab === value

    if (!isActive && !forceMount) return null

    return (
        <div
            role="tabpanel"
            id={`${idPrefix}-panel-${value}`}
            aria-labelledby={`${idPrefix}-tab-${value}`}
            hidden={!isActive}
            tabIndex={0}
            className={`focus:outline-none ${isActive ? 'animate-fade-in' : ''} ${className}`}
        >
            {children}
        </div>
    )
}

// Convenience component for simple tab lists with filter counts
export interface FilterTabsProps {
    tabs: { value: string; label: string; count?: number }[]
    value: string
    onChange: (value: string) => void
    variant?: 'underline' | 'pills'
    className?: string
}

export const FilterTabs: React.FC<FilterTabsProps> = ({
    tabs,
    value,
    onChange,
    variant = 'pills',
    className = '',
}) => {
    return (
        <Tabs value={value} onValueChange={onChange} defaultValue={value} variant={variant} className={className}>
            <TabsList>
                {tabs.map((tab) => (
                    <TabTrigger key={tab.value} value={tab.value} count={tab.count}>
                        {tab.label}
                    </TabTrigger>
                ))}
            </TabsList>
        </Tabs>
    )
}

export default Tabs
