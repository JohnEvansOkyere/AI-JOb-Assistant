/**
 * Interview Stage Configuration Component
 * Configure interview stages for a job (template-based or custom)
 */

'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { apiClient } from '@/lib/api/client'
import { ApiErrorHandler } from '@/lib/api/error-handler'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { X, Plus, GripVertical, AlertCircle } from 'lucide-react'

interface Stage {
  id?: string
  stage_number: number
  stage_name: string
  stage_type: 'ai' | 'calendar'
  is_required: boolean
  order_index: number
}

interface StageConfigurationProps {
  jobId: string
  onStagesConfigured?: () => void
}

export function StageConfiguration({ jobId, onStagesConfigured }: StageConfigurationProps) {
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [stages, setStages] = useState<Stage[]>([])
  const [templates, setTemplates] = useState<any>({})
  const [showTemplateModal, setShowTemplateModal] = useState(false)
  const [showCustomBuilder, setShowCustomBuilder] = useState(false)

  useEffect(() => {
    loadTemplates()
    loadExistingStages()
  }, [jobId])

  const loadTemplates = async () => {
    try {
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }
      const response = await apiClient.get('/interview-stages/templates')
      if (response.success && response.data) {
        setTemplates(response.data)
      }
    } catch (err: any) {
      console.error('Error loading templates:', err)
    }
  }

  const loadExistingStages = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }
      const response = await apiClient.get(`/interview-stages/jobs/${jobId}/stages`)
      if (response.success && response.data) {
        setStages(response.data)
        setShowCustomBuilder(response.data.length > 0)
      }
    } catch (err: any) {
      // No stages configured yet
      setStages([])
    } finally {
      setLoading(false)
    }
  }

  const handleUseTemplate = async (templateName: string) => {
    try {
      setSaving(true)
      setError('')
      setSuccess('')
      
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }

      const response = await apiClient.post(
        `/interview-stages/jobs/${jobId}/stages/template`,
        { template_name: templateName }
      )

      if (response.success) {
        setSuccess(`Stages created from "${templates[templateName]?.name || templateName}" template`)
        setShowTemplateModal(false)
        await loadExistingStages()
        onStagesConfigured?.()
      } else {
        setError(response.message || 'Failed to create stages')
      }
    } catch (err: any) {
      const errorMessage = ApiErrorHandler.getErrorMessage(err)
      setError(errorMessage)
    } finally {
      setSaving(false)
    }
  }

  const handleAddStage = () => {
    const newStage: Stage = {
      stage_number: stages.length + 1,
      stage_name: `Stage ${stages.length + 1}`,
      stage_type: 'calendar',
      is_required: true,
      order_index: stages.length + 1,
    }
    setStages([...stages, newStage])
    setShowCustomBuilder(true)
  }

  const handleRemoveStage = (index: number) => {
    setStages(stages.filter((_, i) => i !== index).map((s, i) => ({
      ...s,
      stage_number: i + 1,
      order_index: i + 1,
    })))
  }

  const handleUpdateStage = (index: number, updates: Partial<Stage>) => {
    const updated = [...stages]
    updated[index] = { ...updated[index], ...updates }
    setStages(updated)
  }

  const handleSaveCustomStages = async () => {
    try {
      setSaving(true)
      setError('')
      setSuccess('')

      // Validate
      if (stages.length === 0) {
        setError('Please add at least one stage')
        return
      }

      const aiStages = stages.filter(s => s.stage_type === 'ai')
      if (aiStages.length > 1) {
        setError('Only one AI interview stage is allowed')
        return
      }

      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }

      // Check if we're updating existing stages or creating new ones
      const hasExistingStages = stages.some(s => s.id)
      
      if (hasExistingStages) {
        // Update existing stages individually
        const updatePromises = stages.map(async (stage) => {
          if (stage.id) {
            return apiClient.put(`/interview-stages/stages/${stage.id}`, {
              stage_name: stage.stage_name,
              stage_type: stage.stage_type,
              is_required: stage.is_required,
              order_index: stage.order_index,
            })
          }
        })
        
        await Promise.all(updatePromises.filter(Boolean))
        setSuccess('Stages updated successfully')
      } else {
        // Create new stages
        const response = await apiClient.post(
          `/interview-stages/jobs/${jobId}/stages/custom`,
          { stages: stages.map(({ id, ...rest }) => rest) }
        )

        if (response.success) {
          setSuccess('Stages saved successfully')
        } else {
          setError(response.message || 'Failed to save stages')
          return
        }
      }
      
      await loadExistingStages()
      onStagesConfigured?.()
    } catch (err: any) {
      const errorMessage = ApiErrorHandler.getErrorMessage(err)
      setError(errorMessage.includes('already exist') 
        ? 'Stages already exist for this job. Please refresh the page to view them.' 
        : errorMessage)
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <Card>
        <div className="p-6 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading stages...</p>
        </div>
      </Card>
    )
  }

  return (
    <Card>
      <div className="p-6 space-y-6">
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            Interview Stages Configuration
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Configure the interview process for this job. Define stages that candidates will go through.
          </p>
        </div>

        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
          </div>
        )}

        {success && (
          <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
            <p className="text-sm text-green-700 dark:text-green-300">{success}</p>
          </div>
        )}

        {stages.length === 0 && !showCustomBuilder ? (
          <div className="space-y-4">
            <div>
              <h3 className="text-md font-medium text-gray-900 dark:text-white mb-3">
                Quick Setup with Templates
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {Object.entries(templates).map(([key, template]: [string, any]) => (
                  <div
                    key={key}
                    className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:border-primary-500 dark:hover:border-primary-500 cursor-pointer transition-colors"
                    onClick={() => handleUseTemplate(key)}
                  >
                    <h4 className="font-semibold text-gray-900 dark:text-white mb-1">
                      {template.name}
                    </h4>
                    <p className="text-xs text-gray-600 dark:text-gray-400 mb-3">
                      {template.description}
                    </p>
                    <div className="space-y-1">
                      {template.stages?.map((stage: any, idx: number) => (
                        <div key={idx} className="flex items-center gap-2 text-xs">
                          <span className={`w-2 h-2 rounded-full ${
                            stage.stage_type === 'ai'
                              ? 'bg-blue-500'
                              : 'bg-green-500'
                          }`}></span>
                          <span className="text-gray-700 dark:text-gray-300">
                            {stage.stage_name}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
              <Button
                variant="outline"
                onClick={() => {
                  setShowCustomBuilder(true)
                  handleAddStage()
                }}
                className="w-full"
              >
                <Plus className="w-4 h-4 mr-2" />
                Create Custom Stages
              </Button>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-md font-medium text-gray-900 dark:text-white">
                Current Stages ({stages.length})
              </h3>
              <Button
                variant="outline"
                size="sm"
                onClick={handleAddStage}
              >
                <Plus className="w-4 h-4 mr-2" />
                Add Stage
              </Button>
            </div>

            <div className="space-y-3">
              {stages.map((stage, index) => (
                <div
                  key={index}
                  className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 space-y-3"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <GripVertical className="w-5 h-5 text-gray-400" />
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        Stage {stage.stage_number}
                      </span>
                    </div>
                    {stages.length > 1 && (
                      <button
                        onClick={() => handleRemoveStage(index)}
                        className="text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Stage Name
                      </label>
                      <Input
                        value={stage.stage_name}
                        onChange={(e) => handleUpdateStage(index, { stage_name: e.target.value })}
                        placeholder="e.g., Phone Screen, Technical Interview"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Stage Type
                      </label>
                      <select
                        value={stage.stage_type}
                        onChange={(e) => handleUpdateStage(index, { stage_type: e.target.value as 'ai' | 'calendar' })}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                      >
                        <option value="calendar">Human Interview (Calendar)</option>
                        <option value="ai">AI Interview</option>
                      </select>
                      {stage.stage_type === 'ai' && stages.filter(s => s.stage_type === 'ai').length > 1 && (
                        <p className="text-xs text-red-600 dark:text-red-400 mt-1">
                          Only one AI stage is allowed
                        </p>
                      )}
                    </div>
                  </div>

                  <div>
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={stage.is_required}
                        onChange={(e) => handleUpdateStage(index, { is_required: e.target.checked })}
                        className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                      />
                      <span className="text-sm text-gray-700 dark:text-gray-300">
                        Required stage (cannot be skipped)
                      </span>
                    </label>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
              <Button
                variant="primary"
                onClick={handleSaveCustomStages}
                loading={saving}
                disabled={saving || stages.length === 0}
              >
                Save Stages
              </Button>
              <Button
                variant="outline"
                onClick={() => router.push(`/dashboard/pipeline?job=${jobId}`)}
              >
                View Pipeline
              </Button>
            </div>
          </div>
        )}
      </div>
    </Card>
  )
}

