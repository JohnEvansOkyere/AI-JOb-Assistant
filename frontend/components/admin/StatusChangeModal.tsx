/**
 * Status Change Modal
 * Modal for changing organization status
 */

'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { apiClient } from '@/lib/api/client'
import { X, AlertTriangle } from 'lucide-react'

interface StatusChangeModalProps {
  isOpen: boolean
  onClose: () => void
  currentStatus?: string
  orgName: string
  onSuccess: () => void
}

export function StatusChangeModal({
  isOpen,
  onClose,
  currentStatus = 'active',
  orgName,
  onSuccess
}: StatusChangeModalProps) {
  const [selectedStatus, setSelectedStatus] = useState(currentStatus)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!isOpen) return null

  const handleSubmit = async () => {
    if (selectedStatus === currentStatus) {
      onClose()
      return
    }

    setLoading(true)
    setError(null)

    try {
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }

      const response = await apiClient.put(
        `/admin/organizations/${encodeURIComponent(orgName)}/status`,
        { status: selectedStatus }
      )

      if (response.success) {
        onSuccess()
        onClose()
      } else {
        throw new Error(response.message || 'Failed to update status')
      }
    } catch (err: any) {
      setError(err.message || 'Failed to update organization status')
    } finally {
      setLoading(false)
    }
  }

  const statusOptions = [
    { value: 'active', label: 'Active', description: 'Organization can use all features normally' },
    { value: 'paused', label: 'Paused', description: 'Temporarily paused - no new interviews' },
    { value: 'suspended', label: 'Suspended', description: 'Suspended - no access allowed' },
    { value: 'trial', label: 'Trial', description: 'Trial period - limited access' },
  ]

  const isDestructive = selectedStatus === 'suspended' || selectedStatus === 'paused'

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
      <div className="w-full max-w-md mx-4" onClick={(e) => e.stopPropagation()}>
        <Card>
          <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900">Change Organization Status</h2>
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
            <p className="text-sm text-gray-600 mb-4">Current Status: <span className="font-semibold capitalize">{currentStatus}</span></p>

            <label className="block text-sm font-medium text-gray-700 mb-2">
              New Status
            </label>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white text-gray-900"
              disabled={loading}
            >
              {statusOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-2">
              {statusOptions.find(o => o.value === selectedStatus)?.description}
            </p>
          </div>

          {isDestructive && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-4">
              <div className="flex items-start gap-2">
                <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-yellow-800">
                  <p className="font-semibold mb-1">Warning</p>
                  <p>This action will restrict organization access. Make sure this is intentional.</p>
                </div>
              </div>
            </div>
          )}

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
              variant={isDestructive ? 'danger' : 'primary'}
              onClick={handleSubmit}
              loading={loading}
            >
              Update Status
            </Button>
          </div>
        </div>
        </Card>
      </div>
    </div>
  )
}

