/**
 * Plan Change Modal
 * Modal for changing organization subscription plan
 */

'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { apiClient } from '@/lib/api/client'
import { X } from 'lucide-react'

interface PlanChangeModalProps {
  isOpen: boolean
  onClose: () => void
  currentPlan?: string
  orgName: string
  onSuccess: () => void
}

export function PlanChangeModal({
  isOpen,
  onClose,
  currentPlan = 'free',
  orgName,
  onSuccess
}: PlanChangeModalProps) {
  const [selectedPlan, setSelectedPlan] = useState(currentPlan)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!isOpen) return null

  const handleSubmit = async () => {
    if (selectedPlan === currentPlan) {
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
        `/admin/organizations/${encodeURIComponent(orgName)}/subscription-plan`,
        { subscription_plan: selectedPlan }
      )

      if (response.success) {
        onSuccess()
        onClose()
      } else {
        throw new Error(response.message || 'Failed to update subscription plan')
      }
    } catch (err: any) {
      setError(err.message || 'Failed to update subscription plan')
    } finally {
      setLoading(false)
    }
  }

  const planOptions = [
    { value: 'free', label: 'Free', description: 'Basic features, limited usage' },
    { value: 'starter', label: 'Starter', description: 'Entry-level plan for small teams' },
    { value: 'professional', label: 'Professional', description: 'Full features for growing teams' },
    { value: 'enterprise', label: 'Enterprise', description: 'Advanced features and support' },
    { value: 'custom', label: 'Custom', description: 'Customized plan with special pricing' },
  ]

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
      <Card className="w-full max-w-md mx-4" onClick={(e) => e.stopPropagation()}>
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900">Change Subscription Plan</h2>
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
            <p className="text-sm text-gray-600 mb-4">Current Plan: <span className="font-semibold capitalize">{currentPlan}</span></p>

            <label className="block text-sm font-medium text-gray-700 mb-2">
              New Subscription Plan
            </label>
            <select
              value={selectedPlan}
              onChange={(e) => setSelectedPlan(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white text-gray-900"
              disabled={loading}
            >
              {planOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-2">
              {planOptions.find(o => o.value === selectedPlan)?.description}
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
              Update Plan
            </Button>
          </div>
        </div>
      </Card>
    </div>
  )
}

