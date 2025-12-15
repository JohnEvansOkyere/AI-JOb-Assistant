'use client'

import { useEffect, useRef, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'

type Message =
  | { role: 'system'; text: string }
  | { role: 'assistant'; text: string; questionId?: string }
  | { role: 'user'; text: string }

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function InterviewPage() {
  const params = useParams()
  const router = useRouter()
  const ticketCode = params.ticketCode as string

  const [ws, setWs] = useState<WebSocket | null>(null)
  const [connected, setConnected] = useState(false)
  const [connecting, setConnecting] = useState(false)
  const [messages, setMessages] = useState<Message[]>([
    { role: 'system', text: 'When you are ready, click "Start Interview" to begin.' },
  ])
  const [currentInput, setCurrentInput] = useState('')
  const [currentQuestionId, setCurrentQuestionId] = useState<string | undefined>(undefined)
  const [error, setError] = useState<string | null>(null)
  const [waitingForAI, setWaitingForAI] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    return () => {
      if (ws) {
        ws.close()
      }
    }
  }, [ws])

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
        socket.send(JSON.stringify({ type: 'start' }))
      }

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.type === 'question') {
            setWaitingForAI(false)
            setCurrentQuestionId(data.question_id)
            setMessages((prev) => [
              ...prev,
              { role: 'assistant', text: data.text, questionId: data.question_id },
            ])
          } else if (data.type === 'analysis') {
            // Keep analysis internal for scoring; do not show raw JSON to the candidate
            return
          } else if (data.type === 'info') {
            setWaitingForAI(false)
            setMessages((prev) => [...prev, { role: 'system', text: data.message }])
          } else if (data.type === 'error') {
            setWaitingForAI(false)
            setError(data.message || 'Interview error')
            setMessages((prev) => [...prev, { role: 'system', text: `Error: ${data.message}` }])
          }
        } catch (e) {
          console.error('Failed to parse websocket message', e)
        }
      }

      socket.onclose = () => {
        setConnected(false)
        setWs(null)
      }

      socket.onerror = (event) => {
        console.error('WebSocket error', event)
        setError('WebSocket connection error')
      }
    } catch (e: any) {
      console.error('Failed to open WebSocket', e)
      setError(e.message || 'Failed to open WebSocket')
      setConnecting(false)
    }
  }

  const handleSend = () => {
    if (!ws || ws.readyState !== WebSocket.OPEN || !currentInput.trim()) return

    const text = currentInput.trim()
    setMessages((prev) => [...prev, { role: 'user', text }])
    setCurrentInput('')
    setWaitingForAI(true)

    ws.send(
      JSON.stringify({
        type: 'answer',
        question_id: currentQuestionId,
        text,
      }),
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="max-w-3xl w-full">
        <Card>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">AI Interview</h1>
              <p className="text-sm text-gray-600">
                Ticket: <span className="font-mono">{ticketCode}</span>
              </p>
            </div>
            <Button
              variant="primary"
              onClick={connectWebSocket}
              disabled={connected || connecting}
            >
              {connected ? 'Connected' : connecting ? 'Connecting...' : 'Start Interview'}
            </Button>
          </div>

          {error && (
            <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-2 rounded">
              {error}
            </div>
          )}

          <div className="h-80 overflow-y-auto border border-gray-200 rounded-lg p-3 mb-4 bg-white">
            {messages.map((m, idx) => (
              <div
                key={idx}
                className={`mb-2 ${
                  m.role === 'user'
                    ? 'text-right'
                    : m.role === 'assistant'
                    ? 'text-left'
                    : 'text-center text-xs text-gray-500'
                }`}
              >
                {m.role === 'user' && (
                  <span className="inline-block bg-blue-600 text-white px-3 py-1 rounded-lg">
                    {m.text}
                  </span>
                )}
                {m.role === 'assistant' && (
                  <span className="inline-block bg-gray-100 text-gray-900 px-3 py-1 rounded-lg">
                    {m.text}
                  </span>
                )}
                {m.role === 'system' && <span>{m.text}</span>}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {waitingForAI && (
            <div className="flex items-center gap-2 mb-3 text-xs text-gray-500">
              <div className="h-4 w-4 border-2 border-gray-300 border-t-primary-500 rounded-full animate-spin" />
              <span>AI is thinking and preparing the next question...</span>
            </div>
          )}

          <div className="flex gap-2">
            <Input
              type="text"
              placeholder={
                connected
                  ? waitingForAI
                    ? 'Waiting for the next question...'
                    : 'Type your answer here...'
                  : 'Click "Start Interview" to begin'
              }
              value={currentInput}
              onChange={(e) => setCurrentInput(e.target.value)}
              disabled={!connected || waitingForAI}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault()
                  handleSend()
                }
              }}
            />
            <Button
              variant="primary"
              onClick={handleSend}
              disabled={!connected || waitingForAI || !currentInput}
            >
              Send
            </Button>
          </div>
        </Card>
      </div>
    </div>
  )
}


