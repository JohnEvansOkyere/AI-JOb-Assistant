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
    <div className={clsx('bg-white rounded-lg shadow-md p-6', className)}>
      {title && (
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      )}
      <div>{children}</div>
      {footer && (
        <div className="mt-4 pt-4 border-t border-gray-200">{footer}</div>
      )}
    </div>
  )
}

