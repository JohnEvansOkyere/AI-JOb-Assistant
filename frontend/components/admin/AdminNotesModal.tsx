/**
 * Admin Notes Modal
 * Modal for editing admin notes for an organization
 */

'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { apiClient } from '@/lib/api/client'
import { X } from 'lucide-react'

interface AdminNotesModalProps {
  isOpen: boolean
  onClose: () => void
  orgName: string
  currentNotes?: string
  onSuccess: () => void
}

export function AdminNotesModal({
  isOpen,
  onClose,
  orgName,
  currentNotes = '',
  onSuccess
}: AdminNotesModalProps) {
  const [notes, setNotes] = useState(currentNotes)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (isOpen) {
      setNotes(currentNotes || '')
    }
  }, [isOpen, currentNotes])

  if (!isOpen) return null

  const handleSubmit = async () => {
    setLoading(true)
    setError(null)

    try {
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }

      const response = await apiClient.put(
        `/admin/organizations/${encodeURIComponent(orgName)}/admin-notes`,
        { admin_notes: notes }
      )

      if (response.success) {
        onSuccess()
        onClose()
      } else {
        throw new Error(response.message || 'Failed to update admin notes')
      }
    } catch (err: any) {
      setError(err.message || 'Failed to update admin notes')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" 
      onClick={(e) => {
        // Only close if clicking the backdrop, not the modal content
        if (e.target === e.currentTarget) {
          onClose()
        }
      }}
    >
      <Card className="w-full max-w-2xl mx-4" onClick={(e) => e.stopPropagation()}>
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900">Admin Notes</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="mb-4">
            <p className="text-sm text-gray-600 mb-4">
              Organization: <span className="font-semibold">{orgName}</span>
            </p>
            <p className="text-xs text-gray-500 mb-2">Internal notes visible only to admins</p>

            <label className="block text-sm font-medium text-gray-700 mb-2">
              Notes
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white text-gray-900 min-h-[200px]"
              placeholder="Add internal notes about this organization..."
              disabled={loading}
            />
            <p className="text-xs text-gray-500 mt-1">
              {notes.length} characters
            </p>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          <div className="flex items-center gap-3 justify-end">
            <Button
              variant="outline"
              onClick={onClose}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleSubmit}
              loading={loading}
            >
              Save Notes
            </Button>
          </div>
        </div>
      </Card>
    </div>
  )
}

