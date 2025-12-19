/**
 * Card Component
 * Reusable card container component
 */

import React from 'react'
import { clsx } from 'clsx'

interface CardProps {
  children: React.ReactNode
  className?: string
  title?: string
  footer?: React.ReactNode
}

export function Card({ children, className, title, footer }: CardProps) {
  return (
    <div className={clsx('bg-white dark:bg-gray-800 rounded-lg shadow-md dark:shadow-lg p-6 border border-gray-200 dark:border-gray-700', className)}>
      {title && (
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">{title}</h3>
      )}
      <div className="text-gray-700 dark:text-gray-300">{children}</div>
      {footer && (
        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">{footer}</div>
      )}
    </div>
  )
}

