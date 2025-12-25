import React, { useState, useMemo } from 'react'
import { ChevronUp, ChevronDown, ChevronsUpDown, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react'
import Button from './Button'
import { SkeletonTableRow } from './Skeleton'
import EmptyState from './EmptyState'

export type SortDirection = 'asc' | 'desc' | null

export interface Column<T> {
    key: string
    header: string
    sortable?: boolean
    width?: string | number
    minWidth?: string | number
    align?: 'left' | 'center' | 'right'
    className?: string
    render?: (value: any, row: T, index: number) => React.ReactNode
    accessor?: (row: T) => any
}

export interface TableProps<T> {
    data: T[]
    columns: Column<T>[]
    keyExtractor: (row: T, index: number) => string | number
    isLoading?: boolean
    emptyState?: {
        title: string
        description?: string
        action?: {
            label: string
            onClick: () => void
        }
    }
    // Sorting
    sortable?: boolean
    defaultSortKey?: string
    defaultSortDirection?: SortDirection
    onSort?: (key: string, direction: SortDirection) => void
    // Pagination
    pagination?: {
        page: number
        pageSize: number
        total: number
        onPageChange: (page: number) => void
        onPageSizeChange?: (size: number) => void
        pageSizeOptions?: number[]
    }
    // Styling
    compact?: boolean
    striped?: boolean
    hoverable?: boolean
    stickyHeader?: boolean
    className?: string
    // Row actions
    onRowClick?: (row: T, index: number) => void
}

function Table<T>({
    data,
    columns,
    keyExtractor,
    isLoading = false,
    emptyState,
    sortable = true,
    defaultSortKey,
    defaultSortDirection = null,
    onSort,
    pagination,
    compact = false,
    striped = false,
    hoverable = true,
    stickyHeader = false,
    className = '',
    onRowClick,
}: TableProps<T>) {
    const [sortKey, setSortKey] = useState<string | null>(defaultSortKey || null)
    const [sortDirection, setSortDirection] = useState<SortDirection>(defaultSortDirection)

    const handleSort = (key: string) => {
        const column = columns.find(c => c.key === key)
        if (!column?.sortable && !sortable) return

        let newDirection: SortDirection
        if (sortKey !== key) {
            newDirection = 'asc'
        } else if (sortDirection === 'asc') {
            newDirection = 'desc'
        } else if (sortDirection === 'desc') {
            newDirection = null
        } else {
            newDirection = 'asc'
        }

        setSortKey(key)
        setSortDirection(newDirection)
        onSort?.(key, newDirection)
    }

    // Client-side sorting if no onSort handler provided
    const sortedData = useMemo(() => {
        if (onSort || !sortKey || !sortDirection) return data

        const column = columns.find(c => c.key === sortKey)
        if (!column) return data

        return [...data].sort((a, b) => {
            const aValue = column.accessor ? column.accessor(a) : (a as any)[sortKey]
            const bValue = column.accessor ? column.accessor(b) : (b as any)[sortKey]

            if (aValue === bValue) return 0
            if (aValue == null) return 1
            if (bValue == null) return -1

            const comparison = aValue < bValue ? -1 : 1
            return sortDirection === 'asc' ? comparison : -comparison
        })
    }, [data, sortKey, sortDirection, columns, onSort])

    const getCellValue = (row: T, column: Column<T>, index: number) => {
        const value = column.accessor ? column.accessor(row) : (row as any)[column.key]
        if (column.render) {
            return column.render(value, row, index)
        }
        return value ?? '—'
    }

    const renderSortIcon = (column: Column<T>) => {
        if (!column.sortable && !sortable) return null

        if (sortKey !== column.key) {
            return <ChevronsUpDown size={14} className="text-slate-300" />
        }

        if (sortDirection === 'asc') {
            return <ChevronUp size={14} className="text-primary-600" />
        }
        if (sortDirection === 'desc') {
            return <ChevronDown size={14} className="text-primary-600" />
        }
        return <ChevronsUpDown size={14} className="text-slate-300" />
    }

    const rowHeight = compact ? 'py-2.5' : 'py-4'
    const headerHeight = compact ? 'py-2.5' : 'py-3.5'

    return (
        <div className={`card overflow-hidden ${className}`}>
            <div className="table-container overflow-x-auto">
                <table className="table w-full">
                    <thead className={`bg-slate-50 border-b border-slate-200 ${stickyHeader ? 'table-sticky' : ''}`}>
                        <tr>
                            {columns.map((column) => (
                                <th
                                    key={column.key}
                                    className={`
                    ${headerHeight} px-4 text-xs font-semibold text-slate-500 uppercase tracking-wider
                    ${column.align === 'center' ? 'text-center' : column.align === 'right' ? 'text-right' : 'text-left'}
                    ${(column.sortable || sortable) ? 'cursor-pointer select-none hover:bg-slate-100 transition-colors' : ''}
                    ${column.className || ''}
                  `}
                                    style={{
                                        width: column.width,
                                        minWidth: column.minWidth
                                    }}
                                    onClick={() => (column.sortable !== false && sortable) || column.sortable ? handleSort(column.key) : undefined}
                                >
                                    <div className={`flex items-center gap-1 ${column.align === 'right' ? 'justify-end' : column.align === 'center' ? 'justify-center' : ''}`}>
                                        {column.header}
                                        {(column.sortable !== false && sortable) || column.sortable ? renderSortIcon(column) : null}
                                    </div>
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody className={`divide-y divide-slate-100 ${striped ? 'divide-slate-200' : ''}`}>
                        {isLoading ? (
                            // Skeleton loading rows
                            Array.from({ length: pagination?.pageSize || 5 }).map((_, idx) => (
                                <SkeletonTableRow key={idx} columns={columns.length} />
                            ))
                        ) : sortedData.length === 0 ? (
                            // Empty state
                            <tr>
                                <td colSpan={columns.length} className="p-0">
                                    <EmptyState
                                        title={emptyState?.title || 'Veri bulunamadı'}
                                        description={emptyState?.description}
                                        action={emptyState?.action}
                                        className="py-16"
                                    />
                                </td>
                            </tr>
                        ) : (
                            // Data rows
                            sortedData.map((row, rowIndex) => (
                                <tr
                                    key={keyExtractor(row, rowIndex)}
                                    className={`
                    transition-colors
                    ${hoverable ? 'hover:bg-slate-50' : ''}
                    ${striped && rowIndex % 2 === 1 ? 'bg-slate-50/50' : ''}
                    ${onRowClick ? 'cursor-pointer' : ''}
                  `}
                                    onClick={() => onRowClick?.(row, rowIndex)}
                                >
                                    {columns.map((column) => (
                                        <td
                                            key={column.key}
                                            className={`
                        ${rowHeight} px-4 text-sm text-slate-700
                        ${column.align === 'center' ? 'text-center' : column.align === 'right' ? 'text-right' : 'text-left'}
                        ${column.className || ''}
                      `}
                                        >
                                            {getCellValue(row, column, rowIndex)}
                                        </td>
                                    ))}
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* Pagination */}
            {pagination && !isLoading && sortedData.length > 0 && (
                <TablePagination {...pagination} />
            )}
        </div>
    )
}

interface TablePaginationProps {
    page: number
    pageSize: number
    total: number
    onPageChange: (page: number) => void
    onPageSizeChange?: (size: number) => void
    pageSizeOptions?: number[]
}

function TablePagination({
    page,
    pageSize,
    total,
    onPageChange,
    onPageSizeChange,
    pageSizeOptions = [10, 25, 50, 100],
}: TablePaginationProps) {
    const totalPages = Math.ceil(total / pageSize)
    const startItem = (page - 1) * pageSize + 1
    const endItem = Math.min(page * pageSize, total)

    const canGoPrevious = page > 1
    const canGoNext = page < totalPages

    // Generate page numbers to show
    const getPageNumbers = () => {
        const pages: (number | 'ellipsis')[] = []
        const showPages = 5

        if (totalPages <= showPages + 2) {
            // Show all pages
            for (let i = 1; i <= totalPages; i++) {
                pages.push(i)
            }
        } else {
            // Always show first page
            pages.push(1)

            if (page <= 3) {
                // Near start
                for (let i = 2; i <= Math.min(showPages, totalPages - 1); i++) {
                    pages.push(i)
                }
                if (totalPages > showPages) {
                    pages.push('ellipsis')
                }
            } else if (page >= totalPages - 2) {
                // Near end
                pages.push('ellipsis')
                for (let i = Math.max(totalPages - showPages + 1, 2); i < totalPages; i++) {
                    pages.push(i)
                }
            } else {
                // In middle
                pages.push('ellipsis')
                for (let i = page - 1; i <= page + 1; i++) {
                    pages.push(i)
                }
                pages.push('ellipsis')
            }

            // Always show last page
            if (!pages.includes(totalPages)) {
                pages.push(totalPages)
            }
        }

        return pages
    }

    return (
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 px-4 py-3 border-t border-slate-200 bg-slate-50/50">
            {/* Left: Page size + info */}
            <div className="flex items-center gap-4 text-sm text-slate-600">
                {onPageSizeChange && (
                    <div className="flex items-center gap-2">
                        <span>Sayfa başına:</span>
                        <select
                            value={pageSize}
                            onChange={(e) => onPageSizeChange(Number(e.target.value))}
                            className="h-8 px-2 pr-8 text-sm border border-slate-300 rounded-md bg-white focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                        >
                            {pageSizeOptions.map((size) => (
                                <option key={size} value={size}>
                                    {size}
                                </option>
                            ))}
                        </select>
                    </div>
                )}
                <span>
                    {startItem}–{endItem} / {total} kayıt
                </span>
            </div>

            {/* Right: Page navigation */}
            <div className="flex items-center gap-1">
                <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onPageChange(1)}
                    disabled={!canGoPrevious}
                    isIconOnly
                    aria-label="First page"
                >
                    <ChevronsLeft size={16} />
                </Button>
                <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onPageChange(page - 1)}
                    disabled={!canGoPrevious}
                    isIconOnly
                    aria-label="Previous page"
                >
                    <ChevronLeft size={16} />
                </Button>

                <div className="flex items-center gap-1 mx-1">
                    {getPageNumbers().map((pageNum, idx) =>
                        pageNum === 'ellipsis' ? (
                            <span key={`ellipsis-${idx}`} className="px-2 text-slate-400">
                                ...
                            </span>
                        ) : (
                            <button
                                key={pageNum}
                                onClick={() => onPageChange(pageNum)}
                                className={`
                  min-w-[32px] h-8 px-2 text-sm font-medium rounded-md transition-colors
                  ${pageNum === page
                                        ? 'bg-primary-600 text-white'
                                        : 'text-slate-600 hover:bg-slate-100'
                                    }
                `}
                            >
                                {pageNum}
                            </button>
                        )
                    )}
                </div>

                <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onPageChange(page + 1)}
                    disabled={!canGoNext}
                    isIconOnly
                    aria-label="Next page"
                >
                    <ChevronRight size={16} />
                </Button>
                <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onPageChange(totalPages)}
                    disabled={!canGoNext}
                    isIconOnly
                    aria-label="Last page"
                >
                    <ChevronsRight size={16} />
                </Button>
            </div>
        </div>
    )
}

export { TablePagination }
export default Table
