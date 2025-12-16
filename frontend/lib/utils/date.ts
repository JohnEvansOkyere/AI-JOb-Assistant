/**
 * Date formatting utilities
 * Ensures consistent date formatting between server and client to avoid hydration mismatches
 */

/**
 * Format a date string to a consistent format (YYYY-MM-DD)
 * This ensures server and client render the same string
 */
export function formatDate(dateString: string): string {
  const date = new Date(dateString)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

/**
 * Format a date string to a readable format (e.g., "January 15, 2024")
 * Uses explicit locale and options to ensure consistency
 */
export function formatDateReadable(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

/**
 * Format a date string to a short format (e.g., "Jan 15, 2024")
 */
export function formatDateShort(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

