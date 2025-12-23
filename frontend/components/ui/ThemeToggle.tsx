/**
 * Theme Toggle Component
 * Button to switch between light and dark mode
 */

'use client'

import { useState, useEffect } from 'react'
import { Moon, Sun } from 'lucide-react'
import { useTheme } from '@/hooks/useTheme'
import { Button } from './Button'

interface ThemeToggleProps {
  variant?: 'button' | 'icon'
  className?: string
}

export function ThemeToggle({ variant = 'icon', className = '' }: ThemeToggleProps) {
  const [mounted, setMounted] = useState(false)
  
  useEffect(() => {
    setMounted(true)
  }, [])

  // During SSR, return a placeholder to avoid hydration mismatch
  // Use suppressHydrationWarning since this component intentionally differs between server/client
  // and browser extensions may modify the DOM
  if (!mounted) {
    return (
      <button
        className={`p-2 rounded-lg ${className}`}
        aria-label="Theme toggle"
        disabled
        suppressHydrationWarning
      >
        <Moon className="w-5 h-5 text-gray-400" suppressHydrationWarning />
      </button>
    )
  }

  // Safe to call useTheme after mounted check
  const { theme, toggleTheme } = useTheme()

  if (variant === 'icon') {
    return (
      <button
        onClick={toggleTheme}
        className={`p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors ${className}`}
        aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
        title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
      >
        {theme === 'light' ? (
          <Moon className="w-5 h-5 text-gray-700 dark:text-gray-300" />
        ) : (
          <Sun className="w-5 h-5 text-gray-700 dark:text-gray-300" />
        )}
      </button>
    )
  }

  return (
    <Button
      variant="outline"
      onClick={toggleTheme}
      className={className}
      aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
    >
      {theme === 'light' ? (
        <>
          <Moon className="w-4 h-4 mr-2" />
          Dark Mode
        </>
      ) : (
        <>
          <Sun className="w-4 h-4 mr-2" />
          Light Mode
        </>
      )}
    </Button>
  )
}

