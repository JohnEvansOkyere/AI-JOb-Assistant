'use client'

import { useEffect, useRef, useState } from 'react'
import { useParams, useRouter, useSearchParams } from 'next/navigation'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Send, Bot, User, Loader2, CheckCircle2, AlertCircle } from 'lucide-react'

type Message =
  | { role: 'system'; text: string }
  | { role: 'assistant'; text: string; questionId?: string }
  | { role: 'user'; text: string }

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function InterviewPage() {
  const params = useParams()
  const router = useRouter()
  const ticketCode = params.ticketCode as string
  const searchParams = useSearchParams()
  const candidateName = searchParams.get('name')
  const jobTitle = searchParams.get('job')

  const [ws, setWs] = useState<WebSocket | null>(null)
  const [connected, setConnected] = useState(false)
  const [connecting, setConnecting] = useState(false)
  const [messages, setMessages] = useState<Message[]>([
    { 
      role: 'system', 
      text: 'Welcome! When you\'re ready, click "Start Interview" to begin your interview session with our recruiter.' 
    },
  ])
  const [currentInput, setCurrentInput] = useState('')
  const [currentQuestionId, setCurrentQuestionId] = useState<string | undefined>(undefined)
  const [error, setError] = useState<string | null>(null)
  const [waitingForAI, setWaitingForAI] = useState(false)
  const [waitingForFinalMessage, setWaitingForFinalMessage] = useState(false)
  const [interviewComplete, setInterviewComplete] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, waitingForAI])

  useEffect(() => {
    return () => {
      if (ws) {
        ws.close()
      }
    }
  }, [ws])

  useEffect(() => {
    if (connected && !waitingForAI && !interviewComplete) {
      inputRef.current?.focus()
    }
  }, [connected, waitingForAI, interviewComplete])

  const connectWebSocket = () => {
    setConnecting(true)
    setError(null)

    try {
      const wsUrl = API_URL.replace(/^http/, 'ws') + `/voice/interview/${ticketCode}`
      const socket = new WebSocket(wsUrl)

      socket.onopen = () => {
        setConnected(true)
        setConnecting(false)
        setWs(socket)
        setWaitingForAI(true)
        setMessages((prev) => [
          ...prev.filter(m => m.role !== 'system'),
          { role: 'system', text: 'Connecting to interview session...' },
        ])
        socket.send(JSON.stringify({ type: 'start' }))
      }

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.type === 'question') {
            setWaitingForAI(false)
            setCurrentQuestionId(data.question_id)
            setMessages((prev) => [
              ...prev.filter(m => m.role !== 'system' || !m.text.includes('Connecting')),
              { role: 'assistant', text: data.text, questionId: data.question_id },
            ])
          } else if (data.type === 'analysis') {
            return
          } else if (data.type === 'info') {
            setWaitingForAI(false)
            setMessages((prev) => [
              ...prev,
              { role: 'system', text: data.message },
            ])
          } else if (data.type === 'final_message_request') {
            setWaitingForAI(false)
            setWaitingForFinalMessage(true)
            setMessages((prev) => [
              ...prev,
              { role: 'assistant', text: data.message },
            ])
          } else if (data.type === 'interview_complete') {
            setWaitingForAI(false)
            setWaitingForFinalMessage(false)
            setInterviewComplete(true)
            setMessages((prev) => [
              ...prev,
              { role: 'system', text: data.message },
            ])
            setTimeout(() => {
              if (socket.readyState === WebSocket.OPEN) {
                socket.close()
              }
            }, 5000)
          } else if (data.type === 'error') {
            setWaitingForAI(false)
            const errorMsg = data.message || 'An error occurred during the interview'
            setError(errorMsg)
            setMessages((prev) => [
              ...prev,
              { role: 'system', text: `⚠️ ${errorMsg}` },
            ])
            if (errorMsg.includes('Invalid ticket') || errorMsg.includes('expired') || errorMsg.includes('already been used')) {
              setInterviewComplete(true)
            }
          }
        } catch (e) {
          console.error('Failed to parse websocket message', e)
        }
      }

      socket.onclose = (event) => {
        setConnected(false)
        setWs(null)
        if (!interviewComplete && event.code !== 1000) {
          if (event.code === 1006) {
            setError('Connection lost. Please refresh the page and try again.')
          } else {
            setError('Connection closed unexpectedly. Please refresh the page and try again.')
          }
        }
      }

      socket.onerror = (event) => {
        console.error('WebSocket error', event)
        setError('Connection error. Please check your internet connection and try again.')
        setWaitingForAI(false)
      }
    } catch (e: any) {
      console.error('Failed to open WebSocket', e)
      setError(e.message || 'Failed to open WebSocket')
      setConnecting(false)
    }
  }

  const handleSend = () => {
    if (!ws || ws.readyState !== WebSocket.OPEN || !currentInput.trim()) return
    if (interviewComplete) return

    const text = currentInput.trim()
    setMessages((prev) => [...prev, { role: 'user', text }])
    setCurrentInput('')

    if (waitingForFinalMessage) {
      setWaitingForFinalMessage(false)
      setWaitingForAI(true)
      ws.send(
        JSON.stringify({
          type: 'final_message',
          text,
        }),
      )
    } else {
      setWaitingForAI(true)
      ws.send(
        JSON.stringify({
          type: 'answer',
          question_id: currentQuestionId,
          text,
        }),
      )
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex flex-col">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 py-3">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <Bot className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-semibold text-gray-900 dark:text-white">Interview with Recruiter</h1>
                <div className="flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
                  {jobTitle && (
                    <span className="flex items-center gap-1">
                      <span className="font-medium">{jobTitle}</span>
                    </span>
                  )}
                  {candidateName && (
                    <span className="flex items-center gap-1">
                      <span>•</span>
                      <span>{candidateName}</span>
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
          {!connected && !interviewComplete && (
            <Button
              variant="primary"
              onClick={connectWebSocket}
              disabled={connecting}
              className="flex items-center gap-2"
            >
              {connecting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Connecting...
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-4 h-4" />
                  Start Interview
                </>
              )}
            </Button>
          )}
          {connected && !interviewComplete && (
            <div className="flex items-center gap-2 text-sm text-green-600 dark:text-green-400">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span>Connected</span>
            </div>
          )}
          {interviewComplete && (
            <div className="flex items-center gap-2 text-sm text-blue-600 dark:text-blue-400">
              <CheckCircle2 className="w-4 h-4" />
              <span>Completed</span>
            </div>
          )}
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border-b border-red-200 dark:border-red-800 px-4 py-3">
          <div className="max-w-4xl mx-auto flex items-center gap-2 text-red-700 dark:text-red-400">
            <AlertCircle className="w-5 h-5" />
            <span className="text-sm">{error}</span>
          </div>
        </div>
      )}

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {messages.map((m, idx) => {
            if (m.role === 'system') {
              return (
                <div key={idx} className="flex justify-center">
                  <div className="bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 px-4 py-2 rounded-full text-sm">
                    {m.text}
                  </div>
                </div>
              )
            }

            if (m.role === 'assistant') {
              return (
                <div key={idx} className="flex items-start gap-4 group">
                  <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="bg-white dark:bg-gray-800 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm border border-gray-200 dark:border-gray-700">
                      <p className="text-gray-900 dark:text-gray-100 whitespace-pre-wrap leading-relaxed">
                        {m.text}
                      </p>
                    </div>
                  </div>
                </div>
              )
            }

            if (m.role === 'user') {
              return (
                <div key={idx} className="flex items-start gap-4 justify-end group">
                  <div className="flex-1 min-w-0 flex justify-end">
                    <div className="bg-gradient-to-br from-blue-600 to-blue-700 text-white rounded-2xl rounded-tr-sm px-4 py-3 max-w-[80%] shadow-sm">
                      <p className="whitespace-pre-wrap leading-relaxed">{m.text}</p>
                    </div>
                  </div>
                  <div className="flex-shrink-0 w-8 h-8 bg-gray-300 dark:bg-gray-600 rounded-full flex items-center justify-center">
                    <User className="w-5 h-5 text-gray-600 dark:text-gray-300" />
                  </div>
                </div>
              )
            }

            return null
          })}

          {/* AI Typing Indicator */}
          {waitingForAI && (
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div className="flex-1">
                <div className="bg-white dark:bg-gray-800 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm border border-gray-200 dark:border-gray-700">
                  <div className="flex items-center gap-1">
                    <div className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 px-4 py-4">
        <div className="max-w-4xl mx-auto">
          {interviewComplete ? (
            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
              <div className="flex items-center gap-3">
                <CheckCircle2 className="w-5 h-5 text-green-600 dark:text-green-400 flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium text-green-800 dark:text-green-300">
                    Interview Completed
                  </p>
                  <p className="text-xs text-green-700 dark:text-green-400 mt-1">
                    Thank you for your time! Your responses have been recorded and will be reviewed by our team.
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex items-end gap-3">
              <div className="flex-1 relative">
                <Input
                  ref={inputRef}
                  type="text"
                  placeholder={
                    connected
                      ? waitingForFinalMessage
                        ? 'Share any final thoughts or questions...'
                        : waitingForAI
                          ? 'AI is thinking...'
                          : 'Type your answer here...'
                      : 'Click "Start Interview" to begin'
                  }
                  value={currentInput}
                  onChange={(e) => setCurrentInput(e.target.value)}
                  disabled={!connected || waitingForAI || interviewComplete}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey && !interviewComplete && currentInput.trim()) {
                      e.preventDefault()
                      handleSend()
                    }
                  }}
                  className="pr-12 resize-none"
                />
              </div>
              <Button
                variant="primary"
                onClick={handleSend}
                disabled={!connected || waitingForAI || interviewComplete || !currentInput.trim()}
                className="flex items-center gap-2 px-4 py-2.5"
                size="lg"
              >
                {waitingForAI ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
                <span className="hidden sm:inline">
                  {waitingForFinalMessage ? 'Send' : 'Send'}
                </span>
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
