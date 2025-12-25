import React from 'react'

export interface SelectOption {
    value: string | number
    label: string
    disabled?: boolean
}

export interface SelectProps extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, 'size'> {
    label?: string
    error?: string
    helperText?: string
    options: SelectOption[]
    placeholder?: string
    selectSize?: 'sm' | 'md' | 'lg'
    fullWidth?: boolean
}

const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
    (
        {
            label,
            error,
            helperText,
            options,
            placeholder = 'Seçiniz...',
            selectSize = 'md',
            fullWidth = true,
            className = '',
            id,
            ...props
        },
        ref
    ) => {
        const selectId = id || `select-${Math.random().toString(36).substr(2, 9)}`

        const sizeClasses = {
            sm: 'h-8 text-sm',
            md: 'h-10 text-sm',
            lg: 'h-12 text-base',
        }

        const selectClasses = [
            'select',
            sizeClasses[selectSize],
            error && 'border-error-500 focus:border-error-500 focus:ring-error-500/20',
            className,
        ]
            .filter(Boolean)
            .join(' ')

        const wrapperClasses = fullWidth ? 'w-full' : ''

        return (
            <div className={wrapperClasses}>
                {label && (
                    <label htmlFor={selectId} className="label">
                        {label}
                    </label>
                )}
                <select
                    ref={ref}
                    id={selectId}
                    className={selectClasses}
                    aria-invalid={error ? 'true' : 'false'}
                    aria-describedby={error ? `${selectId}-error` : helperText ? `${selectId}-helper` : undefined}
                    {...props}
                >
                    {placeholder && (
                        <option value="" disabled>
                            {placeholder}
                        </option>
                    )}
                    {options.map((option) => (
                        <option
                            key={option.value}
                            value={option.value}
                            disabled={option.disabled}
                        >
                            {option.label}
                        </option>
                    ))}
                </select>
                {error && (
                    <p id={`${selectId}-error`} className="error-text" role="alert">
                        {error}
                    </p>
                )}
                {helperText && !error && (
                    <p id={`${selectId}-helper`} className="helper-text">
                        {helperText}
                    </p>
                )}
            </div>
        )
    }
)

Select.displayName = 'Select'

export default Select
