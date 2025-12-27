'use client'

import { useState, useRef, useEffect } from 'react'
import { Mic, MicOff, Square } from 'lucide-react'
import { Button } from '@/components/ui/Button'

interface VoiceRecorderProps {
  onAudioStart: () => void
  onAudioEnd: (audioBlob: Blob) => void
  disabled?: boolean
  isRecording?: boolean
}

export function VoiceRecorder({
  onAudioStart,
  onAudioEnd,
  disabled = false,
  isRecording: externalIsRecording = false,
}: VoiceRecorderProps) {
  const [isRecording, setIsRecording] = useState(false)
  const [hasPermission, setHasPermission] = useState<boolean | null>(null)
  const [error, setError] = useState<string | null>(null)
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const streamRef = useRef<MediaStream | null>(null)

  // Check microphone permission on mount
  useEffect(() => {
    checkMicrophonePermission()
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopRecording()
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
      }
    }
  }, [])

  const checkMicrophonePermission = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      stream.getTracks().forEach(track => track.stop()) // Stop immediately, just checking permission
      setHasPermission(true)
    } catch (err: any) {
      setHasPermission(false)
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setError('Microphone permission denied. Please allow microphone access and refresh the page.')
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        setError('No microphone found. Please connect a microphone and refresh the page.')
      } else {
        setError('Failed to access microphone. Please check your browser settings.')
      }
    }
  }

  const startRecording = async () => {
    if (disabled || isRecording) return

    try {
      setError(null)
      
      // Get microphone stream
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      })
      
      streamRef.current = stream
      audioChunksRef.current = []

      // Create MediaRecorder with WebM/Opus (browser-native, widely supported)
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : MediaRecorder.isTypeSupported('audio/webm')
        ? 'audio/webm'
        : 'audio/mp4' // Fallback

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType,
        audioBitsPerSecond: 128000, // 128 kbps - good quality, reasonable file size
      })

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      mediaRecorder.onstop = () => {
        // Combine all audio chunks into a single blob
        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType })
        audioChunksRef.current = []
        
        // Stop all tracks
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop())
          streamRef.current = null
        }

        // Call callback with audio blob
        onAudioEnd(audioBlob)
      }

      mediaRecorder.onerror = (event) => {
        console.error('MediaRecorder error', event)
        setError('Recording error occurred. Please try again.')
        stopRecording()
      }

      mediaRecorderRef.current = mediaRecorder
      mediaRecorder.start(1000) // Collect data every 1 second
      setIsRecording(true)
      onAudioStart()
      
    } catch (err: any) {
      console.error('Failed to start recording', err)
      setError('Failed to start recording. Please try again.')
      setIsRecording(false)
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
    }
  }

  const recording = isRecording || externalIsRecording

  if (hasPermission === false) {
    return (
      <div className="flex flex-col items-center gap-2 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
        <MicOff className="w-5 h-5 text-red-600 dark:text-red-400" />
        <p className="text-sm text-red-700 dark:text-red-400 text-center">{error || 'Microphone access required'}</p>
        <Button
          variant="primary"
          size="sm"
          onClick={checkMicrophonePermission}
          className="mt-2"
        >
          Retry
        </Button>
      </div>
    )
  }

  return (
    <div className="flex flex-col items-center gap-3">
      {error && (
        <p className="text-sm text-red-600 dark:text-red-400 text-center">{error}</p>
      )}
      
      <div className="flex items-center gap-3">
        {!recording ? (
          <Button
            variant="primary"
            onClick={startRecording}
            disabled={disabled || hasPermission === false}
            className="flex items-center gap-2 px-6 py-3"
            size="lg"
          >
            <Mic className="w-5 h-5" />
            <span>Start Recording</span>
          </Button>
        ) : (
          <Button
            variant="primary"
            onClick={stopRecording}
            disabled={disabled}
            className="flex items-center gap-2 px-6 py-3 bg-red-600 hover:bg-red-700"
            size="lg"
          >
            <Square className="w-5 h-5" />
            <span>Stop Recording</span>
          </Button>
        )}
      </div>

      {recording && (
        <div className="flex items-center gap-2 text-sm text-red-600 dark:text-red-400">
          <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
          <span>Recording...</span>
        </div>
      )}
    </div>
  )
}

