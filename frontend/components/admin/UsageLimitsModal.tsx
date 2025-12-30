/**
 * Usage Limits Modal
 * Modal for managing organization usage limits
 */

'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { apiClient } from '@/lib/api/client'
import { X } from 'lucide-react'

interface UsageLimitsModalProps {
  isOpen: boolean
  onClose: () => void
  orgName: string
  currentLimits: {
    monthly_interview_limit?: number | null
    monthly_cost_limit_usd?: number | null
    daily_cost_limit_usd?: number | null
  }
  onSuccess: () => void
}

export function UsageLimitsModal({
  isOpen,
  onClose,
  orgName,
  currentLimits,
  onSuccess
}: UsageLimitsModalProps) {
  const [limits, setLimits] = useState({
    monthly_interview_limit: currentLimits.monthly_interview_limit?.toString() || '',
    monthly_cost_limit_usd: currentLimits.monthly_cost_limit_usd?.toString() || '',
    daily_cost_limit_usd: currentLimits.daily_cost_limit_usd?.toString() || '',
  })
  const [unlimited, setUnlimited] = useState({
    monthly_interview: !currentLimits.monthly_interview_limit,
    monthly_cost: !currentLimits.monthly_cost_limit_usd,
    daily_cost: !currentLimits.daily_cost_limit_usd,
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (isOpen) {
      setLimits({
        monthly_interview_limit: currentLimits.monthly_interview_limit?.toString() || '',
        monthly_cost_limit_usd: currentLimits.monthly_cost_limit_usd?.toString() || '',
        daily_cost_limit_usd: currentLimits.daily_cost_limit_usd?.toString() || '',
      })
      setUnlimited({
        monthly_interview: !currentLimits.monthly_interview_limit,
        monthly_cost: !currentLimits.monthly_cost_limit_usd,
        daily_cost: !currentLimits.daily_cost_limit_usd,
      })
    }
  }, [isOpen, currentLimits])

  if (!isOpen) return null

  const handleSubmit = async () => {
    setLoading(true)
    setError(null)

    try {
      const payload: any = {}
      
      if (!unlimited.monthly_interview && limits.monthly_interview_limit) {
        const value = parseInt(limits.monthly_interview_limit)
        if (isNaN(value) || value <= 0) {
          throw new Error('Monthly interview limit must be a positive number')
        }
        payload.monthly_interview_limit = value
      } else {
        payload.monthly_interview_limit = null
      }

      if (!unlimited.monthly_cost && limits.monthly_cost_limit_usd) {
        const value = parseFloat(limits.monthly_cost_limit_usd)
        if (isNaN(value) || value <= 0) {
          throw new Error('Monthly cost limit must be a positive number')
        }
        payload.monthly_cost_limit_usd = value
      } else {
        payload.monthly_cost_limit_usd = null
      }

      if (!unlimited.daily_cost && limits.daily_cost_limit_usd) {
        const value = parseFloat(limits.daily_cost_limit_usd)
        if (isNaN(value) || value <= 0) {
          throw new Error('Daily cost limit must be a positive number')
        }
        payload.daily_cost_limit_usd = value
      } else {
        payload.daily_cost_limit_usd = null
      }

      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }

      const response = await apiClient.put(
        `/admin/organizations/${encodeURIComponent(orgName)}/usage-limits`,
        payload
      )

      if (response.success) {
        onSuccess()
        onClose()
      } else {
        throw new Error(response.message || 'Failed to update usage limits')
      }
    } catch (err: any) {
      setError(err.message || 'Failed to update usage limits')
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
      <div className="w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <Card>
          <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900">Manage Usage Limits</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="mb-4">
            <p className="text-sm text-gray-600 mb-6">
              Organization: <span className="font-semibold">{orgName}</span>
            </p>
            <p className="text-xs text-gray-500 mb-4">Set limits to control organization usage. Leave unlimited for no restrictions.</p>

            {/* Monthly Interview Limit */}
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium text-gray-700">
                  Monthly Interview Limit
                </label>
                <label 
                  className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer"
                  onClick={(e) => e.stopPropagation()}
                >
                  <input
                    type="checkbox"
                    checked={unlimited.monthly_interview}
                    onChange={(e) => {
                      e.stopPropagation()
                      setUnlimited({ ...unlimited, monthly_interview: e.target.checked })
                    }}
                    onClick={(e) => e.stopPropagation()}
                    className="rounded cursor-pointer"
                  />
                  Unlimited
                </label>
              </div>
              <Input
                type="number"
                value={limits.monthly_interview_limit}
                onChange={(e) => setLimits({ ...limits, monthly_interview_limit: e.target.value })}
                placeholder="e.g., 100"
                disabled={unlimited.monthly_interview || loading}
                min="1"
              />
              <p className="text-xs text-gray-500 mt-1">Maximum number of interviews per month</p>
            </div>

            {/* Monthly Cost Limit */}
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium text-gray-700">
                  Monthly Cost Limit (USD)
                </label>
                <label 
                  className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer"
                  onClick={(e) => e.stopPropagation()}
                >
                  <input
                    type="checkbox"
                    checked={unlimited.monthly_cost}
                    onChange={(e) => {
                      e.stopPropagation()
                      setUnlimited({ ...unlimited, monthly_cost: e.target.checked })
                    }}
                    onClick={(e) => e.stopPropagation()}
                    className="rounded cursor-pointer"
                  />
                  Unlimited
                </label>
              </div>
              <Input
                type="number"
                value={limits.monthly_cost_limit_usd}
                onChange={(e) => setLimits({ ...limits, monthly_cost_limit_usd: e.target.value })}
                placeholder="e.g., 500.00"
                disabled={unlimited.monthly_cost || loading}
                min="0"
                step="0.01"
              />
              <p className="text-xs text-gray-500 mt-1">Maximum AI costs in USD per month</p>
            </div>

            {/* Daily Cost Limit */}
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium text-gray-700">
                  Daily Cost Limit (USD)
                </label>
                <label 
                  className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer"
                  onClick={(e) => e.stopPropagation()}
                >
                  <input
                    type="checkbox"
                    checked={unlimited.daily_cost}
                    onChange={(e) => {
                      e.stopPropagation()
                      setUnlimited({ ...unlimited, daily_cost: e.target.checked })
                    }}
                    onClick={(e) => e.stopPropagation()}
                    className="rounded cursor-pointer"
                  />
                  Unlimited
                </label>
              </div>
              <Input
                type="number"
                value={limits.daily_cost_limit_usd}
                onChange={(e) => setLimits({ ...limits, daily_cost_limit_usd: e.target.value })}
                placeholder="e.g., 25.00"
                disabled={unlimited.daily_cost || loading}
                min="0"
                step="0.01"
              />
              <p className="text-xs text-gray-500 mt-1">Maximum AI costs in USD per day</p>
            </div>
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
              Save Limits
            </Button>
          </div>
        </div>
        </Card>
      </div>
    </div>
  )
}

