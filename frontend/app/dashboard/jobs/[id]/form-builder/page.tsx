/**
 * Application Form Builder Page
 * Recruiters can create custom application forms for their jobs
 */

'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { apiClient } from '@/lib/api/client'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'

interface FormField {
  id?: string
  field_key: string
  field_label: string
  field_type: string
  field_options?: { options?: string[] }
  is_required: boolean
  placeholder?: string
  help_text?: string
  order_index: number
}

const FIELD_TYPES = [
  { value: 'text', label: 'Text' },
  { value: 'email', label: 'Email' },
  { value: 'tel', label: 'Phone' },
  { value: 'number', label: 'Number' },
  { value: 'textarea', label: 'Textarea' },
  { value: 'select', label: 'Dropdown' },
  { value: 'radio', label: 'Radio Buttons' },
  { value: 'checkbox', label: 'Checkbox' },
  { value: 'date', label: 'Date' },
]

export default function FormBuilderPage() {
  const params = useParams()
  const router = useRouter()
  const jobId = params.id as string
  const { isAuthenticated, loading: authLoading } = useAuth()
  
  const [fields, setFields] = useState<FormField[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
      return
    }

    if (isAuthenticated) {
      loadFields()
    }
  }, [isAuthenticated, authLoading, router, jobId])

  const loadFields = async () => {
    try {
      setLoading(true)
      setError('')
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }
      
      const response = await apiClient.get<FormField[]>(`/application-forms/fields/job/${jobId}`)
      
      if (response.success && response.data) {
        setFields(response.data)
      } else {
        // If no fields exist yet, that's okay - show empty state
        if (response.message?.includes('not found') || response.message?.includes('404')) {
          setFields([])
        } else {
          setError(response.message || 'Failed to load form fields')
        }
      }
    } catch (err: any) {
      // Handle 404 gracefully - means no fields exist yet
      if (err.status === 404 || err.message?.includes('404') || err.message?.includes('not found')) {
        setFields([])
        setError('')
      } else {
        const errorMsg = err.response?.detail || err.response?.message || err.message || 'Failed to load form fields'
        setError(errorMsg)
        console.error('Error loading form fields:', err)
      }
    } finally {
      setLoading(false)
    }
  }

  const addField = () => {
    const newField: FormField = {
      field_key: `field_${Date.now()}`,
      field_label: '',
      field_type: 'text',
      is_required: false,
      order_index: fields.length,
    }
    setFields([...fields, newField])
  }

  const updateField = (index: number, updates: Partial<FormField>) => {
    const updated = [...fields]
    updated[index] = { ...updated[index], ...updates }
    setFields(updated)
  }

  const removeField = (index: number) => {
    setFields(fields.filter((_, i) => i !== index).map((f, i) => ({ ...f, order_index: i })))
  }

  const moveField = (index: number, direction: 'up' | 'down') => {
    if (
      (direction === 'up' && index === 0) ||
      (direction === 'down' && index === fields.length - 1)
    ) {
      return
    }
    
    const newFields = [...fields]
    const newIndex = direction === 'up' ? index - 1 : index + 1
    ;[newFields[index], newFields[newIndex]] = [newFields[newIndex], newFields[index]]
    
    // Update order_index
    newFields.forEach((f, i) => {
      f.order_index = i
    })
    
    setFields(newFields)
  }

  const handleSave = async () => {
    try {
      setSaving(true)
      setError('')
      setSuccess('')
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }

      // Validate fields
      for (const field of fields) {
        if (!field.field_key || !field.field_label) {
          setError('All fields must have a key and label')
          return
        }
        if (['select', 'radio', 'checkbox'].includes(field.field_type) && !field.field_options?.options?.length) {
          setError(`${field.field_label} requires at least one option`)
          return
        }
      }

      // Create/update fields
      const fieldsToCreate = fields.map(f => ({
        job_description_id: jobId,
        field_key: f.field_key,
        field_label: f.field_label,
        field_type: f.field_type,
        field_options: f.field_options || null,
        is_required: f.is_required,
        placeholder: f.placeholder || null,
        help_text: f.help_text || null,
        order_index: f.order_index,
      }))

      const response = await apiClient.post('/application-forms/fields/batch', fieldsToCreate)
      
      if (response.success) {
        setSuccess('Form fields saved successfully!')
        setTimeout(() => setSuccess(''), 3000)
        loadFields() // Reload to get IDs
      } else {
        setError(response.message || 'Failed to save form fields')
      }
    } catch (err: any) {
      const errorMsg = err.response?.detail || err.response?.message || err.message || 'An error occurred while saving'
      setError(errorMsg)
      console.error('Error saving form fields:', err)
    } finally {
      setSaving(false)
    }
  }

  if (authLoading || loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading...</p>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  if (!isAuthenticated) {
    return null
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Application Form Builder</h1>
            <p className="text-gray-600 mt-1">Create custom fields for candidates to fill when applying</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => router.push(`/dashboard/jobs/${jobId}`)}>
              Back to Job
            </Button>
            <Button variant="primary" onClick={handleSave} loading={saving}>
              Save Form
            </Button>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}

        {success && (
          <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded">
            {success}
          </div>
        )}

        {/* Application Link Card - Always Visible */}
        <Card>
          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Application Link</h3>
              <p className="text-sm text-gray-600 mb-4">
                Share this link with candidates to apply for this position. CV upload and cover letter fields are always included.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex-1 bg-gray-50 border border-gray-200 rounded-lg px-4 py-3">
                <p className="text-xs text-gray-500 mb-1">Application URL</p>
                <p className="text-sm font-mono text-gray-900 break-all">
                  {typeof window !== 'undefined' ? `${window.location.origin}/apply/${jobId}` : 'Loading...'}
                </p>
              </div>
              <Button
                variant="primary"
                onClick={() => {
                  const url = typeof window !== 'undefined' ? `${window.location.origin}/apply/${jobId}` : ''
                  navigator.clipboard.writeText(url)
                  setSuccess('Application link copied to clipboard!')
                  setTimeout(() => setSuccess(''), 3000)
                }}
              >
                Copy Link
              </Button>
            </div>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <p className="text-xs text-blue-800">
                <strong>Note:</strong> CV upload and cover letter fields are always included in the application form and cannot be removed.
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="space-y-6">
            {/* Info about standard fields */}
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-gray-900 mb-2">Standard Fields (Always Included)</h4>
              <ul className="text-xs text-gray-600 space-y-1 list-disc list-inside">
                <li>Full Name (required)</li>
                <li>Email (required)</li>
                <li>Phone Number (optional)</li>
                <li>CV/Resume Upload (required)</li>
                <li>Cover Letter (optional)</li>
              </ul>
              <p className="text-xs text-gray-500 mt-2">
                These fields cannot be removed. Custom fields below are additional fields you can add.
              </p>
            </div>

            {fields.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-600 mb-4">No custom fields yet. Add your first field to get started.</p>
                <Button variant="primary" onClick={addField}>
                  Add First Field
                </Button>
              </div>
            ) : (
              <>
                {fields.map((field, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-4 space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="font-semibold text-gray-900">Field {index + 1}</h3>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => moveField(index, 'up')}
                          disabled={index === 0}
                        >
                          ↑
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => moveField(index, 'down')}
                          disabled={index === fields.length - 1}
                        >
                          ↓
                        </Button>
                        <Button
                          variant="danger"
                          size="sm"
                          onClick={() => removeField(index)}
                        >
                          Remove
                        </Button>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <Input
                        label="Field Key *"
                        value={field.field_key}
                        onChange={(e) => updateField(index, { field_key: e.target.value })}
                        placeholder="e.g., years_experience"
                        helperText="Unique identifier (lowercase, underscores)"
                      />

                      <Input
                        label="Field Label *"
                        value={field.field_label}
                        onChange={(e) => updateField(index, { field_label: e.target.value })}
                        placeholder="e.g., Years of Experience"
                      />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Field Type *
                        </label>
                        <select
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                          value={field.field_type}
                          onChange={(e) => updateField(index, { field_type: e.target.value })}
                        >
                          {FIELD_TYPES.map((type) => (
                            <option key={type.value} value={type.value}>
                              {type.label}
                            </option>
                          ))}
                        </select>
                      </div>

                      <div className="flex items-center pt-6">
                        <input
                          type="checkbox"
                          id={`required-${index}`}
                          checked={field.is_required}
                          onChange={(e) => updateField(index, { is_required: e.target.checked })}
                          className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                        />
                        <label htmlFor={`required-${index}`} className="ml-2 text-sm text-gray-700">
                          Required field
                        </label>
                      </div>
                    </div>

                    {(field.field_type === 'select' || field.field_type === 'radio' || field.field_type === 'checkbox') && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Options (one per line) *
                        </label>
                        <textarea
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                          rows={4}
                          value={field.field_options?.options?.join('\n') || ''}
                          onChange={(e) => {
                            const options = e.target.value.split('\n').filter(o => o.trim())
                            updateField(index, {
                              field_options: { options }
                            })
                          }}
                          placeholder="Option 1&#10;Option 2&#10;Option 3"
                        />
                      </div>
                    )}

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <Input
                        label="Placeholder"
                        value={field.placeholder || ''}
                        onChange={(e) => updateField(index, { placeholder: e.target.value })}
                        placeholder="e.g., Enter your experience..."
                      />

                      <Input
                        label="Help Text"
                        value={field.help_text || ''}
                        onChange={(e) => updateField(index, { help_text: e.target.value })}
                        placeholder="e.g., Please provide your total years of experience"
                      />
                    </div>
                  </div>
                ))}

                <Button variant="outline" onClick={addField} className="w-full">
                  + Add Another Field
                </Button>
              </>
            )}
          </div>
        </Card>
      </div>
    </DashboardLayout>
  )
}

