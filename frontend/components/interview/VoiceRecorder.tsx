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

  // Check microphone permission status (non-blocking, doesn't trigger prompt)
  useEffect(() => {
    checkPermissionStatus()
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

  // Check permission status without triggering prompt (using Permissions API if available)
  const checkPermissionStatus = async () => {
    try {
      // Use Permissions API if available (doesn't trigger prompt)
      if (navigator.permissions && navigator.permissions.query) {
        const result = await navigator.permissions.query({ name: 'microphone' as PermissionName })
        setHasPermission(result.state === 'granted')
        // Listen for permission changes
        result.onchange = () => {
          setHasPermission(result.state === 'granted')
          if (result.state === 'denied') {
            setError('Microphone permission denied. Please allow microphone access in your browser settings.')
          } else {
            setError(null)
          }
        }
      } else {
        // Permissions API not available, set to null (unknown)
        setHasPermission(null)
      }
    } catch (err) {
      // Permissions API might not be supported, that's okay
      setHasPermission(null)
    }
  }

  // Request microphone permission (only called on user click)
  const requestMicrophonePermission = async () => {
    try {
      setError(null)
      // This will trigger the browser permission prompt (requires user gesture)
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      stream.getTracks().forEach(track => track.stop()) // Stop immediately, just checking permission
      setHasPermission(true)
      return true
    } catch (err: any) {
      setHasPermission(false)
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setError('Microphone permission denied. Please allow microphone access and try again.')
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        setError('No microphone found. Please connect a microphone and try again.')
      } else {
        setError('Failed to access microphone. Please check your browser settings.')
      }
      return false
    }
  }

  const startRecording = async () => {
    if (disabled || isRecording) return

    try {
      setError(null)
      
      // Request microphone access (this will trigger browser permission prompt on first use)
      // Browsers require a user gesture (click) to show the permission prompt
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      })
      
      // If we got here, permission was granted
      setHasPermission(true)
      
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
      setIsRecording(false)
      setHasPermission(false)
      
      // Provide specific error messages
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setError('Microphone permission denied. Please allow microphone access and try again.')
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        setError('No microphone found. Please connect a microphone and try again.')
      } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
        setError('Microphone is being used by another application. Please close other apps and try again.')
      } else {
        setError('Failed to access microphone. Please check your browser settings and try again.')
      }
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
    }
  }

  const recording = isRecording || externalIsRecording

  // Show error state if permission was explicitly denied
  if (hasPermission === false && error) {
    return (
      <div className="flex flex-col items-center gap-2 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
        <MicOff className="w-5 h-5 text-red-600 dark:text-red-400" />
        <p className="text-sm text-red-700 dark:text-red-400 text-center">{error}</p>
        <Button
          variant="primary"
          size="sm"
          onClick={async () => {
            const granted = await requestMicrophonePermission()
            if (granted) {
              startRecording()
            }
          }}
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

