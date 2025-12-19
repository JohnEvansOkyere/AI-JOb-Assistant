/**
 * Stat Card Component
 * Displays statistics with icons and trends
 */

import React from 'react'
import { clsx } from 'clsx'

interface StatCardProps {
  title: string
  value: string | number
  icon: React.ReactNode
  trend?: {
    value: number
    label: string
    positive?: boolean
  }
  className?: string
  onClick?: () => void
}

export function StatCard({ title, value, icon, trend, className, onClick }: StatCardProps) {
  return (
    <div
      className={clsx(
        'bg-white dark:bg-gray-800 rounded-xl shadow-sm dark:shadow-lg border border-gray-200 dark:border-gray-700 p-6 hover:shadow-md dark:hover:shadow-xl transition-shadow',
        onClick && 'cursor-pointer',
        className
      )}
      onClick={onClick}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">{title}</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{value}</p>
          {trend && (
            <div className="mt-2 flex items-center gap-1">
              <span
                className={clsx(
                  'text-xs font-medium',
                  trend.positive ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                )}
              >
                {trend.positive ? '↑' : '↓'} {Math.abs(trend.value)}%
              </span>
              <span className="text-xs text-gray-500 dark:text-gray-400">{trend.label}</span>
            </div>
          )}
        </div>
        <div className="ml-4 p-3 bg-primary-50 dark:bg-primary-900/30 rounded-lg text-primary-600 dark:text-primary-400">
          {icon}
        </div>
      </div>
    </div>
  )
}

