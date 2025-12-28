'use client'

import { useEffect, useRef, useState } from 'react'
import { useParams, useRouter, useSearchParams } from 'next/navigation'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Send, Bot, User, Loader2, CheckCircle2, AlertCircle } from 'lucide-react'
import { apiClient } from '@/lib/api/client'
import { VoiceRecorder, AudioPlayer } from '@/components/interview'

type Message =
  | { role: 'system'; text: string }
  | { role: 'assistant'; text: string; questionId?: string; audioBlob?: Blob }
  | { role: 'user'; text: string; transcription?: string }

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function InterviewPage() {
  const params = useParams()
  const router = useRouter()
  const ticketCode = params.ticketCode as string
  const searchParams = useSearchParams()
  const urlCandidateName = searchParams.get('name')
  const urlJobTitle = searchParams.get('job')

  const [candidateName, setCandidateName] = useState<string | null>(urlCandidateName)
  const [jobTitle, setJobTitle] = useState<string | null>(urlJobTitle)
  const [companyName, setCompanyName] = useState<string | null>(null)
  const [interviewMode, setInterviewMode] = useState<'text' | 'voice'>('text')

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
  
  // Voice mode state
  const [isRecording, setIsRecording] = useState(false)
  const [currentQuestionAudio, setCurrentQuestionAudio] = useState<Blob | null>(null)
  const [pendingQuestionAudio, setPendingQuestionAudio] = useState<Blob | null>(null) // Audio waiting for question ID
  const [isPlayingQuestion, setIsPlayingQuestion] = useState(false)
  const [lastTranscription, setLastTranscription] = useState<string | null>(null)
  
  const messagesEndRef = useRef<HTMLDivElement | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const streamRef = useRef<MediaStream | null>(null)
  const interviewModeRef = useRef<'text' | 'voice'>('text') // Use ref to track current mode for WebSocket handlers
  const pendingQuestionAudioRef = useRef<Blob | null>(null) // Use ref to track audio for WebSocket handlers (avoid stale closures)
  const currentQuestionAudioRef = useRef<Blob | null>(null) // Use ref for current question audio
  const audioEndSentRef = useRef(false) // Track if audio_end message has been sent to prevent duplicates

  // Load ticket context (candidate, job, company) so the candidate always sees who they are interviewing with
  useEffect(() => {
    const loadContext = async () => {
      try {
        // Backend expects ticket_code as query parameter, not in body
        const response = await apiClient.post<any>(`/tickets/validate?ticket_code=${encodeURIComponent(ticketCode)}`)
        if (response.success && response.data) {
          const data = response.data
          if (!candidateName && data.candidate_name) {
            setCandidateName(data.candidate_name)
          }
          if (!jobTitle && data.job_title) {
            setJobTitle(data.job_title)
          }
          if (data.company_name) {
            setCompanyName(data.company_name)
          }
          // Set interview mode from ticket
          if (data.interview_mode) {
            setInterviewMode(data.interview_mode)
            interviewModeRef.current = data.interview_mode // Update ref immediately
            console.log('Interview mode set to:', data.interview_mode)
          }
        }
      } catch (err) {
        // Soft fail: WebSocket flow will still validate the ticket
        console.error('Failed to load interview context', err)
      }
    }

    loadContext()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ticketCode])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, waitingForAI])

  // Keep refs in sync with state
  useEffect(() => {
    interviewModeRef.current = interviewMode
  }, [interviewMode])
  
  useEffect(() => {
    pendingQuestionAudioRef.current = pendingQuestionAudio
  }, [pendingQuestionAudio])
  
  useEffect(() => {
    currentQuestionAudioRef.current = currentQuestionAudio
  }, [currentQuestionAudio])
  
  // Debug: Log state changes that affect recording button
  useEffect(() => {
    console.log('Recording button state changed', {
      connected,
      waitingForAI,
      isPlayingQuestion,
      interviewComplete,
      canRecord: connected && !waitingForAI && !isPlayingQuestion && !interviewComplete
    })
  }, [connected, waitingForAI, isPlayingQuestion, interviewComplete])

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
      
      // Set binary type to 'blob' to receive audio as Blob objects
      // This is important for handling TTS audio from the server
      socket.binaryType = 'blob'

      socket.onopen = () => {
        console.log('WebSocket opened', { url: wsUrl, binaryType: socket.binaryType })
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

      socket.onmessage = async (event) => {
        console.log('WebSocket message received', {
          dataType: typeof event.data,
          isBlob: event.data instanceof Blob,
          isArrayBuffer: event.data instanceof ArrayBuffer,
          isString: typeof event.data === 'string',
          interviewMode: interviewMode
        })
        
        // Handle binary audio messages
        // WebSocket binary messages can come as Blob or ArrayBuffer depending on binaryType setting
        if (event.data instanceof Blob || event.data instanceof ArrayBuffer) {
          console.log('Binary message detected', {
            size: event.data instanceof Blob ? event.data.size : event.data.byteLength,
            type: event.data instanceof Blob ? event.data.type : 'ArrayBuffer',
            interviewMode: interviewMode,
            interviewModeRef: interviewModeRef.current
          })
          
          // Use ref value which is always current, not state which might be stale in closure
          const currentMode = interviewModeRef.current
          if (currentMode === 'voice' || interviewMode === 'voice') {
            // This is TTS audio for the question
            // Accept audio whenever in voice mode
            // ElevenLabs returns MP3 audio, so set the correct MIME type
            try {
              let blob: Blob
              if (event.data instanceof Blob) {
                // If it's already a Blob, check if it has the correct type
                if (event.data.type && event.data.type !== 'application/octet-stream' && event.data.type.startsWith('audio/')) {
                  blob = event.data
                  console.log('Using Blob as-is with type', event.data.type)
                } else {
                  // Recreate with correct MIME type (default to MP3 for TTS)
                  blob = new Blob([event.data], { type: 'audio/mpeg' })
                  console.log('Recreated Blob with audio/mpeg type')
                }
              } else if (event.data instanceof ArrayBuffer) {
                // Create new Blob with MP3 MIME type (ElevenLabs returns MP3)
                blob = new Blob([event.data], { type: 'audio/mpeg' })
                console.log('Converted ArrayBuffer to Blob with audio/mpeg type')
              } else {
                console.error('Unexpected binary data type', typeof event.data, event.data)
                return
              }
              
              // Validate blob
              if (blob.size === 0) {
                console.error('Received empty audio blob - ignoring')
                return
              }
              
              console.log('Processing audio blob', {
                size: blob.size,
                type: blob.type,
                currentQuestionId: currentQuestionId
              })
              
              // Store in both state and ref (ref for immediate access in handlers, state for UI)
              setPendingQuestionAudio(blob)
              pendingQuestionAudioRef.current = blob
              setCurrentQuestionAudio(blob)
              currentQuestionAudioRef.current = blob
              
              console.log('Audio blob stored successfully', {
                blobSize: blob.size,
                blobType: blob.type,
                currentQuestionId: currentQuestionId,
                hasPendingRef: !!pendingQuestionAudioRef.current,
                hasCurrentRef: !!currentQuestionAudioRef.current
              })
              
              // If we have a current question, update the message with the audio blob
              // This handles the case where audio arrives after the question text
              if (currentQuestionId) {
                setMessages((prev) => 
                  prev.map((msg) => 
                    msg.role === 'assistant' && msg.questionId === currentQuestionId && !msg.audioBlob
                      ? { ...msg, audioBlob: blob }
                      : msg
                  )
                )
                console.log('Updated message with audio blob', { questionId: currentQuestionId })
              }
            } catch (error) {
              console.error('Error processing audio blob', error)
              setError('Failed to process audio. Please try refreshing the page.')
            }
          } else {
            console.warn('Received binary audio but interview mode is not voice', { interviewMode })
          }
          return
        }

        // Handle JSON messages
        try {
          const data = JSON.parse(event.data)
          
          if (data.type === 'question') {
            setWaitingForAI(false)
            setCurrentQuestionId(data.question_id)
            audioEndSentRef.current = false // Reset flag when new question arrives, ready for next recording
            
            // Get the pending audio if available (audio can arrive before or after question text)
            // Use refs to avoid stale closure issues - refs always have current values
            const audioForQuestion = pendingQuestionAudioRef.current || currentQuestionAudioRef.current
            
            console.log('Question received - checking for audio', {
              questionId: data.question_id,
              hasPendingRef: !!pendingQuestionAudioRef.current,
              hasCurrentRef: !!currentQuestionAudioRef.current,
              pendingSize: pendingQuestionAudioRef.current?.size,
              currentSize: currentQuestionAudioRef.current?.size,
              audioAvailable: !!audioForQuestion
            })
            
            setMessages((prev) => [
              ...prev.filter(m => m.role !== 'system' || !m.text.includes('Connecting')),
              { 
                role: 'assistant', 
                text: data.text, 
                questionId: data.question_id,
                audioBlob: audioForQuestion || undefined, // Store audio with the message
              },
            ])
            
            // Clear audio state and refs after associating it with the question
            // This ensures we get fresh audio for the next question
            if (pendingQuestionAudioRef.current) {
              setPendingQuestionAudio(null)
              pendingQuestionAudioRef.current = null
            }
            // Only clear currentQuestionAudio if we used it
            if (audioForQuestion === currentQuestionAudioRef.current) {
              setCurrentQuestionAudio(null)
              currentQuestionAudioRef.current = null
            }
            
            console.log('Question received', data.question_id, 'Audio available:', !!audioForQuestion, 'size:', audioForQuestion?.size, 'type:', audioForQuestion?.type)
          } else if (data.type === 'audio_question_start') {
            // AI is about to speak - prepare for audio
            // Don't clear audio here - it might already be in the buffer from previous question
            // We'll clear it when we actually receive and use it for a question
            setIsPlayingQuestion(true)
            console.log('Audio question starting - waiting for audio blob')
          } else if (data.type === 'audio_question_end') {
            // AI finished speaking (audio transmission complete)
            // Keep isPlayingQuestion true - we'll set it to false when audio actually plays
            console.log('Audio question ended - audio transmission complete, waiting for question text')
          } else if (data.type === 'transcription') {
            // Received transcription of candidate's audio
            setLastTranscription(data.text)
            setMessages((prev) => {
              const lastUserMsg = [...prev].reverse().find(m => m.role === 'user')
              if (lastUserMsg) {
                return prev.map(m => 
                  m === lastUserMsg 
                    ? { ...m, transcription: data.text }
                    : m
                )
              }
              return prev
            })
          } else if (data.type === 'analysis') {
            // Analysis received - backend has processed the response
            // Keep waitingForAI true until next question arrives
            // Don't clear waitingForAI here - wait for question or error
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
            setIsRecording(false)
            stopRecording() // Clean up recording
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

  // Voice recording functions
  const startRecording = async () => {
    if (!ws || ws.readyState !== WebSocket.OPEN || isRecording || interviewComplete) return

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      })

      streamRef.current = stream
      audioChunksRef.current = []

      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : MediaRecorder.isTypeSupported('audio/webm')
        ? 'audio/webm'
        : 'audio/mp4'

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType,
        audioBitsPerSecond: 128000,
      })

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
          // Send audio chunk to server
          if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(event.data)
          }
        }
      }

      mediaRecorder.onstop = () => {
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop())
          streamRef.current = null
        }
      }

      mediaRecorder.onerror = (event) => {
        console.error('MediaRecorder error', event)
        setError('Recording error occurred')
        stopRecording()
      }

      mediaRecorderRef.current = mediaRecorder
      mediaRecorder.start(1000) // Collect data every 1 second
      setIsRecording(true)

      // Send audio_start message
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'audio_start' }))
      }
    } catch (err: any) {
      console.error('Failed to start recording', err)
      setError('Failed to start recording. Please check microphone permissions.')
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)

      // Send audio_end message
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'audio_end' }))
        setWaitingForAI(true) // Wait for transcription
      }
    }
  }

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopRecording()
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
      }
    }
  }, [])

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

  const handleAudioStart = () => {
    console.log('handleAudioStart called from VoiceRecorder - setting parent isRecording to true')
    // VoiceRecorder handles recording internally
    // Just update parent state to reflect recording has started
    setIsRecording(true)
    audioEndSentRef.current = false // Reset flag when starting new recording
    
    // Send audio_start message to server
    if (ws && ws.readyState === WebSocket.OPEN) {
      console.log('Sending audio_start message to server')
      ws.send(JSON.stringify({ type: 'audio_start' }))
    }
  }

  const handleAudioChunk = (audioChunk: Blob) => {
    // Send audio chunk to server via WebSocket
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(audioChunk)
    }
  }

  const handleAudioEnd = (audioBlob: Blob) => {
    console.log('handleAudioEnd called from VoiceRecorder', { 
      blobSize: audioBlob.size,
      currentIsRecording: isRecording,
      alreadySent: audioEndSentRef.current,
      hasAudioData: audioBlob.size > 0
    })
    
    // Prevent duplicate audio_end messages
    if (audioEndSentRef.current) {
      console.warn('audio_end already sent - ignoring duplicate call. If MediaRecorder stopped unexpectedly, this is expected.')
      // Still update state even if we can't send again
      setIsRecording(false)
      return
    }
    
    // If blob is empty and we weren't recording, don't send audio_end
    // This handles edge cases where MediaRecorder stopped unexpectedly
    if (audioBlob.size === 0 && !isRecording) {
      console.warn('handleAudioEnd called with empty blob and isRecording is false - MediaRecorder may have stopped unexpectedly')
      setIsRecording(false)
      return
    }
    
    // VoiceRecorder has already stopped its own recording
    // Just update parent state and send audio_end message
    setIsRecording(false)
    console.log('Parent isRecording set to false')
    
    // Send audio_end message to server (only once)
    // Even if blob is empty (could be a very short recording), we still need to signal the backend
    if (ws && ws.readyState === WebSocket.OPEN) {
      console.log('Sending audio_end message to server', { blobSize: audioBlob.size })
      ws.send(JSON.stringify({ type: 'audio_end' }))
      audioEndSentRef.current = true // Mark as sent
      setWaitingForAI(true) // Wait for transcription
    } else {
      console.error('Cannot send audio_end - WebSocket not connected', { 
        hasWs: !!ws,
        readyState: ws?.readyState 
      })
      // Reset flag if we can't send, so user can try again
      audioEndSentRef.current = false
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
                <h1 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {companyName ? `Interview with ${companyName}` : 'Interview with Recruiter'}
                </h1>
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
                  <div className="flex-1 min-w-0 space-y-2">
                    <div className="bg-white dark:bg-gray-800 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm border border-gray-200 dark:border-gray-700">
                      <p className="text-gray-900 dark:text-gray-100 whitespace-pre-wrap leading-relaxed">
                        {m.text}
                      </p>
                    </div>
                    {/* Show audio player for voice mode questions */}
                    {interviewMode === 'voice' && m.questionId === currentQuestionId && (m.audioBlob || (m.questionId === currentQuestionId ? currentQuestionAudio : null)) && (
                      <AudioPlayer
                        key={`audio-${m.questionId}-${m.audioBlob?.size || currentQuestionAudio?.size || 'none'}`}
                        audioBlob={m.audioBlob || (m.questionId === currentQuestionId ? currentQuestionAudio || undefined : undefined)}
                        autoPlay={true}
                        onPlayStart={() => {
                          setIsPlayingQuestion(true)
                          console.log('Audio playback started for question', m.questionId)
                        }}
                        onPlayEnd={() => {
                          console.log('AudioPlayer onPlayEnd called - current states before update', {
                            isPlayingQuestion,
                            waitingForAI,
                            connected,
                            interviewComplete
                          })
                          setIsPlayingQuestion(false)
                          // Ensure we're ready to accept recording after audio ends
                          setWaitingForAI(false)
                          console.log('Audio playback ended for question', m.questionId, '- States updated, Ready for recording')
                          // Force a small delay to ensure state updates propagate
                          setTimeout(() => {
                            console.log('After state update delay - button should be enabled now')
                          }, 100)
                        }}
                      />
                    )}
                  </div>
                </div>
              )
            }

            if (m.role === 'user') {
              return (
                <div key={idx} className="flex items-start gap-4 justify-end group">
                  <div className="flex-1 min-w-0 flex justify-end">
                    <div className="bg-gradient-to-br from-blue-600 to-blue-700 text-white rounded-2xl rounded-tr-sm px-4 py-3 max-w-[80%] shadow-sm space-y-2">
                      <p className="whitespace-pre-wrap leading-relaxed">{m.text}</p>
                      {/* Show transcription in voice mode */}
                      {interviewMode === 'voice' && m.transcription && m.transcription !== m.text && (
                        <p className="text-xs text-blue-100 italic border-t border-blue-500 pt-2 mt-2">
                          Transcribed: {m.transcription}
                        </p>
                      )}
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
          ) : interviewMode === 'voice' ? (
            // Voice mode input
            <div className="space-y-3">
              {lastTranscription && (
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
                  <p className="text-sm text-blue-800 dark:text-blue-300">
                    <span className="font-medium">Transcription:</span> {lastTranscription}
                  </p>
                </div>
              )}
              <div className="flex items-center justify-center">
                <VoiceRecorder
                  onAudioStart={handleAudioStart}
                  onAudioEnd={handleAudioEnd}
                  onAudioChunk={handleAudioChunk}
                  disabled={(() => {
                    const isDisabled = !connected || waitingForAI || isPlayingQuestion || interviewComplete
                    console.log('VoiceRecorder disabled check', {
                      connected,
                      waitingForAI,
                      isPlayingQuestion,
                      interviewComplete,
                      isDisabled
                    })
                    return isDisabled
                  })()}
                  isRecording={isRecording}
                />
              </div>
              {waitingForAI && (
                <p className="text-center text-sm text-gray-500 dark:text-gray-400">
                  Processing your response...
                </p>
              )}
            </div>
          ) : (
            // Text mode input
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
