/**
 * Interview utility functions
 * Helper functions for interview links and ticket codes
 */

/**
 * Generate a generic interview entry link (for sharing with multiple candidates)
 * @param jobId - Optional job ID to create a job-specific link
 * @returns Full URL to the interview entry page
 */
export function getInterviewLink(jobId?: string): string {
  if (typeof window === 'undefined') {
    // Server-side: use environment variable or default
    const baseUrl = process.env.NEXT_PUBLIC_FRONTEND_URL || process.env.NEXT_PUBLIC_VERCEL_URL || 'http://localhost:3000'
    if (jobId) {
      return `${baseUrl}/interview/job/${encodeURIComponent(jobId)}`
    }
    return `${baseUrl}/interview`
  }
  // Client-side: use current origin
  if (jobId) {
    return `${window.location.origin}/interview/job/${encodeURIComponent(jobId)}`
  }
  return `${window.location.origin}/interview`
}

/**
 * Generate a direct interview link for a specific ticket code (for individual sharing)
 * @param ticketCode - The interview ticket code
 * @returns Full URL to the interview page with ticket code
 */
export function getDirectInterviewLink(ticketCode: string): string {
  if (typeof window === 'undefined') {
    const baseUrl = process.env.NEXT_PUBLIC_FRONTEND_URL || process.env.NEXT_PUBLIC_VERCEL_URL || 'http://localhost:3000'
    return `${baseUrl}/interview/${encodeURIComponent(ticketCode)}`
  }
  return `${window.location.origin}/interview/${encodeURIComponent(ticketCode)}`
}

/**
 * Copy text to clipboard with user feedback
 * @param text - Text to copy
 * @returns Promise that resolves when copy is complete
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch (err) {
    // Fallback for older browsers
    const textArea = document.createElement('textarea')
    textArea.value = text
    textArea.style.position = 'fixed'
    textArea.style.opacity = '0'
    document.body.appendChild(textArea)
    textArea.select()
    try {
      document.execCommand('copy')
      document.body.removeChild(textArea)
      return true
    } catch (fallbackErr) {
      document.body.removeChild(textArea)
      return false
    }
  }
}

