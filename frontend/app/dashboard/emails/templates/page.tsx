/**
 * Email Templates Page
 * Manage email templates for different scenarios
 */

'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { apiClient } from '@/lib/api/client'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { ArrowLeft, Plus, Edit, Trash2, Eye, FileText, Mail, XCircle, CheckCircle, Gift, Inbox, UserX, MessageSquare } from 'lucide-react'

interface EmailTemplate {
  id: string
  name: string
  subject: string
  body_html: string
  body_text?: string
  template_type: 'interview_invitation' | 'acceptance' | 'rejection' | 'cv_rejection' | 'interview_rejection' | 'offer_letter' | 'application_received' | 'custom'
  available_variables?: string[]
  created_at: string
  updated_at: string
}

const TEMPLATE_TYPES = {
  interview_invitation: { label: 'Interview Invitation', icon: Mail, color: 'bg-blue-100 text-blue-700' },
  acceptance: { label: 'Acceptance', icon: CheckCircle, color: 'bg-green-100 text-green-700' },
  rejection: { label: 'Rejection', icon: XCircle, color: 'bg-red-100 text-red-700' },
  cv_rejection: { label: 'CV Rejection', icon: UserX, color: 'bg-orange-100 text-orange-700' },
  interview_rejection: { label: 'Interview Rejection', icon: MessageSquare, color: 'bg-pink-100 text-pink-700' },
  offer_letter: { label: 'Offer Letter', icon: Gift, color: 'bg-purple-100 text-purple-700' },
  application_received: { label: 'Application Received', icon: Inbox, color: 'bg-indigo-100 text-indigo-700' },
  custom: { label: 'Custom', icon: FileText, color: 'bg-gray-100 text-gray-700' },
}

const AVAILABLE_VARIABLES = [
  '{{first_name}}',
  '{{full_name}}',
  '{{candidate_name}}',
  '{{email}}',
  '{{job_title}}',
  '{{job_description_id}}',
  '{{company_name}}',
  '{{primary_color}}',
  '{{application_id}}',
  '{{salary}}',
  '{{start_date}}',
  '{{location}}',
  '{{employment_type}}',
  '{{ticket_code}}',
  '{{interview_link}}',
]

export default function TemplatesPage() {
  const router = useRouter()
  const { isAuthenticated, loading: authLoading } = useAuth()
  const [templates, setTemplates] = useState<EmailTemplate[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingTemplate, setEditingTemplate] = useState<EmailTemplate | null>(null)
  const [previewTemplate, setPreviewTemplate] = useState<EmailTemplate | null>(null)
  const [filterType, setFilterType] = useState<string>('')

  const [formData, setFormData] = useState({
    name: '',
    subject: '',
    body_html: '',
    body_text: '',
    template_type: 'custom' as EmailTemplate['template_type'],
    available_variables: [] as string[],
  })

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
      return
    }

    if (isAuthenticated) {
      loadTemplates()
    }
  }, [isAuthenticated, authLoading, router])

  const loadTemplates = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }

      const url = filterType ? `/email-templates?template_type=${filterType}` : '/email-templates'

      // The backend may return either:
      // - data: EmailTemplate[]
      // - or data: { data: EmailTemplate[] }
      type TemplatesResponse = EmailTemplate[] | { data: EmailTemplate[] }

      const response = await apiClient.get<TemplatesResponse>(url)
      if (response.success && response.data) {
        const raw = response.data as TemplatesResponse
        const templatesList = Array.isArray(raw)
          ? raw
          : Array.isArray(raw.data)
          ? raw.data
          : []
        setTemplates(templatesList)
      }
    } catch (err: any) {
      console.error('Error loading templates:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async () => {
    if (!formData.name || !formData.subject || !formData.body_html) {
      alert('Please fill in all required fields')
      return
    }

    try {
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }

      const response = await apiClient.post('/email-templates', formData)
      if (response.success) {
        alert('Template created successfully!')
        setShowCreateModal(false)
        resetForm()
        loadTemplates()
      } else {
        alert('Failed to create template: ' + response.message)
      }
    } catch (err: any) {
      alert('Error: ' + (err.message || 'Unknown error'))
    }
  }

  const handleUpdate = async () => {
    if (!editingTemplate) return

    try {
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }

      const response = await apiClient.put(`/email-templates/${editingTemplate.id}`, formData)
      if (response.success) {
        alert('Template updated successfully!')
        setEditingTemplate(null)
        resetForm()
        loadTemplates()
      } else {
        alert('Failed to update template: ' + response.message)
      }
    } catch (err: any) {
      alert('Error: ' + (err.message || 'Unknown error'))
    }
  }

  const handleDelete = async (templateId: string) => {
    if (!confirm('Are you sure you want to delete this template?')) {
      return
    }

    try {
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }

      const response = await apiClient.delete(`/email-templates/${templateId}`)
      if (response.success) {
        alert('Template deleted successfully!')
        loadTemplates()
      } else {
        alert('Failed to delete template: ' + response.message)
      }
    } catch (err: any) {
      alert('Error: ' + (err.message || 'Unknown error'))
    }
  }

  const resetForm = () => {
    setFormData({
      name: '',
      subject: '',
      body_html: '',
      body_text: '',
      template_type: 'custom',
      available_variables: [],
    })
  }

  const startEdit = (template: EmailTemplate) => {
    setEditingTemplate(template)
    setFormData({
      name: template.name,
      subject: template.subject,
      body_html: template.body_html,
      body_text: template.body_text || '',
      template_type: template.template_type,
      available_variables: template.available_variables || [],
    })
    setShowCreateModal(true)
  }

  const handlePreview = (template: EmailTemplate) => {
    setPreviewTemplate(template)
  }

  if (authLoading || loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      </DashboardLayout>
    )
  }

  if (!isAuthenticated) {
    return null
  }

  const filteredTemplates = filterType
    ? templates.filter(t => t.template_type === filterType)
    : templates

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => router.push('/dashboard/emails')}
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Email Templates</h1>
              <p className="text-gray-600 mt-1">Create and manage email templates</p>
            </div>
          </div>
          <Button
            variant="primary"
            onClick={() => {
              resetForm()
              setEditingTemplate(null)
              setShowCreateModal(true)
            }}
          >
            <Plus className="w-4 h-4 mr-2" />
            Create Template
          </Button>
        </div>

        {/* Filter */}
        <Card>
          <div className="p-4">
            <div className="flex items-center gap-4">
              <label className="text-sm font-medium text-gray-700">Filter by Type:</label>
              <select
                value={filterType}
                onChange={(e) => {
                  setFilterType(e.target.value)
                  loadTemplates()
                }}
                className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="">All Types</option>
                {Object.entries(TEMPLATE_TYPES).map(([key, { label }]) => (
                  <option key={key} value={key}>{label}</option>
                ))}
              </select>
            </div>
          </div>
        </Card>

        {/* Templates List */}
        {filteredTemplates.length === 0 ? (
          <Card>
            <div className="text-center py-12">
              <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 mb-4">No templates found</p>
              <Button
                variant="primary"
                onClick={() => {
                  resetForm()
                  setEditingTemplate(null)
                  setShowCreateModal(true)
                }}
              >
                <Plus className="w-4 h-4 mr-2" />
                Create Your First Template
              </Button>
            </div>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredTemplates.map((template) => {
              const typeConfig = TEMPLATE_TYPES[template.template_type] || TEMPLATE_TYPES.custom
              const Icon = typeConfig.icon

              return (
                <Card key={template.id}>
                  <div className="p-6 space-y-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg ${typeConfig.color}`}>
                          <Icon className="w-5 h-5" />
                        </div>
                        <div>
                          <h3 className="font-semibold text-gray-900">{template.name}</h3>
                          <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${typeConfig.color}`}>
                            {typeConfig.label}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div>
                      <p className="text-sm text-gray-600 mb-1"><strong>Subject:</strong></p>
                      <p className="text-sm text-gray-900">{template.subject}</p>
                    </div>

                    {template.available_variables && template.available_variables.length > 0 && (
                      <div>
                        <p className="text-xs text-gray-500 mb-1">Variables:</p>
                        <div className="flex flex-wrap gap-1">
                          {template.available_variables.slice(0, 3).map((v, idx) => (
                            <span key={idx} className="text-xs px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded">
                              {v}
                            </span>
                          ))}
                          {template.available_variables.length > 3 && (
                            <span className="text-xs text-gray-500">+{template.available_variables.length - 3}</span>
                          )}
                        </div>
                      </div>
                    )}

                    <div className="flex gap-2 pt-2 border-t">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handlePreview(template)}
                        className="flex-1"
                      >
                        <Eye className="w-3 h-3 mr-1" />
                        Preview
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => startEdit(template)}
                        className="flex-1"
                      >
                        <Edit className="w-3 h-3 mr-1" />
                        Edit
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDelete(template.id)}
                        className="text-red-600 hover:text-red-700"
                      >
                        <Trash2 className="w-3 h-3" />
                      </Button>
                    </div>
                  </div>
                </Card>
              )
            })}
          </div>
        )}

        {/* Create/Edit Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col">
              <div className="flex items-center justify-between p-6 border-b">
                <h2 className="text-xl font-bold text-gray-900">
                  {editingTemplate ? 'Edit Template' : 'Create Template'}
                </h2>
                <button
                  onClick={() => {
                    setShowCreateModal(false)
                    setEditingTemplate(null)
                    resetForm()
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XCircle className="w-5 h-5" />
                </button>
              </div>

              <div className="flex-1 overflow-auto p-6 space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Template Name *
                    </label>
                    <Input
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      placeholder="e.g., Standard Rejection Email"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Template Type *
                    </label>
                    <select
                      value={formData.template_type}
                      onChange={(e) => setFormData({ ...formData, template_type: e.target.value as EmailTemplate['template_type'] })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    >
                      {Object.entries(TEMPLATE_TYPES).map(([key, { label }]) => (
                        <option key={key} value={key}>{label}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Subject *
                  </label>
                  <Input
                    value={formData.subject}
                    onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                    placeholder="e.g., Update on Your Application - {{job_title}}"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Available Variables
                  </label>
                  <div className="flex flex-wrap gap-2 p-3 bg-gray-50 rounded-lg">
                    {AVAILABLE_VARIABLES.map((variable) => (
                      <button
                        key={variable}
                        type="button"
                        onClick={() => {
                          const textarea = document.getElementById('body_html') as HTMLTextAreaElement
                          if (textarea) {
                            const start = textarea.selectionStart
                            const end = textarea.selectionEnd
                            const text = textarea.value
                            const before = text.substring(0, start)
                            const after = text.substring(end)
                            textarea.value = before + variable + after
                            textarea.selectionStart = textarea.selectionEnd = start + variable.length
                            textarea.focus()
                            setFormData({ ...formData, body_html: textarea.value })
                          }
                        }}
                        className="text-xs px-2 py-1 bg-white border border-gray-300 rounded hover:bg-gray-100 cursor-pointer"
                      >
                        {variable}
                      </button>
                    ))}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">Click a variable to insert it into the template</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Body HTML *
                  </label>
                  <textarea
                    id="body_html"
                    value={formData.body_html}
                    onChange={(e) => setFormData({ ...formData, body_html: e.target.value })}
                    rows={12}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 font-mono text-sm"
                    placeholder="<p>Dear {{first_name}},</p>&#10;<p>Thank you for your interest...</p>"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Body Text (Optional)
                  </label>
                  <textarea
                    value={formData.body_text}
                    onChange={(e) => setFormData({ ...formData, body_text: e.target.value })}
                    rows={6}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    placeholder="Plain text version of the email"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 p-6 border-t bg-gray-50">
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowCreateModal(false)
                    setEditingTemplate(null)
                    resetForm()
                  }}
                >
                  Cancel
                </Button>
                <Button
                  variant="primary"
                  onClick={editingTemplate ? handleUpdate : handleCreate}
                >
                  {editingTemplate ? 'Update Template' : 'Create Template'}
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Preview Modal */}
        {previewTemplate && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col">
              <div className="flex items-center justify-between p-6 border-b">
                <h2 className="text-xl font-bold text-gray-900">Template Preview</h2>
                <button
                  onClick={() => setPreviewTemplate(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XCircle className="w-5 h-5" />
                </button>
              </div>

              <div className="flex-1 overflow-auto p-6 bg-gray-50">
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 max-w-2xl mx-auto">
                  <div className="mb-4">
                    <p className="text-sm text-gray-600 mb-1"><strong>Subject:</strong></p>
                    <p className="text-gray-900">{previewTemplate.subject}</p>
                  </div>
                  <div
                    dangerouslySetInnerHTML={{ __html: previewTemplate.body_html }}
                    className="email-preview prose prose-sm max-w-none"
                    style={{
                      fontFamily: 'Arial, sans-serif',
                      lineHeight: '1.6',
                      color: '#333',
                    }}
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 p-6 border-t bg-gray-50">
                <Button
                  variant="outline"
                  onClick={() => setPreviewTemplate(null)}
                >
                  Close
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}

