'use client'

import { useState, useRef, useEffect } from 'react'
import { Mic, MicOff, Square } from 'lucide-react'
import { Button } from '@/components/ui/Button'

interface VoiceRecorderProps {
  onAudioStart: () => void
  onAudioEnd: (audioBlob: Blob) => void
  onAudioChunk?: (audioChunk: Blob) => void  // Optional callback for sending audio chunks in real-time
  disabled?: boolean
  isRecording?: boolean
}

export function VoiceRecorder({
  onAudioStart,
  onAudioEnd,
  onAudioChunk,
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
    // Auto-redirect to localhost if accessing via IP address over HTTP
    if (typeof window !== 'undefined') {
      const isHttp = window.location.protocol === 'http:'
      const isIpAddress = !window.location.hostname.includes('localhost') && 
                          !window.location.hostname.includes('127.0.0.1') &&
                          /^\d+\.\d+\.\d+\.\d+$/.test(window.location.hostname)
      
      if (isHttp && isIpAddress && (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia)) {
        const localhostUrl = window.location.href.replace(window.location.hostname, 'localhost')
        console.log('Auto-redirecting to localhost for microphone access', {
          from: window.location.href,
          to: localhostUrl
        })
        window.location.href = localhostUrl
        return
      }
    }
    
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
      
      // Check if MediaDevices API is available first
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        const isHttp = window.location.protocol === 'http:' && !window.location.hostname.includes('localhost') && !window.location.hostname.includes('127.0.0.1')
        if (isHttp) {
          const currentUrl = window.location.href
          const localhostUrl = currentUrl.replace(window.location.hostname, 'localhost')
          setError(`Microphone access requires HTTPS or localhost. You're accessing via ${window.location.hostname} over HTTP. Please use: ${localhostUrl} (or http://127.0.0.1:${window.location.port}${window.location.pathname})`)
        } else {
          setError('Microphone access is not available in this browser. Please use a modern browser that supports the MediaDevices API.')
        }
        setHasPermission(false)
        return false
      }
      
      // This will trigger the browser permission prompt (requires user gesture)
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      stream.getTracks().forEach(track => track.stop()) // Stop immediately, just checking permission
      setHasPermission(true)
      return true
    } catch (err: any) {
      setHasPermission(false)
      console.error('Microphone permission request failed', {
        error: err,
        name: err.name,
        message: err.message,
        stack: err.stack
      })
      
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setError(`Microphone permission denied. Please:
1. Click the lock/info icon in your browser's address bar
2. Allow microphone access
3. Refresh the page and try again`)
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        setError('No microphone found. Please connect a microphone and try again.')
      } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
        setError('Microphone is being used by another application. Please close other apps and try again.')
      } else if (err.name === 'TypeError' && err.message.includes('getUserMedia')) {
        // This happens when navigator.mediaDevices is undefined
        const isHttp = window.location.protocol === 'http:' && !window.location.hostname.includes('localhost') && !window.location.hostname.includes('127.0.0.1')
        if (isHttp) {
          const localhostUrl = window.location.href.replace(window.location.hostname, 'localhost')
          setError(`Cannot access microphone over HTTP from IP address. Redirecting to localhost...`)
          setTimeout(() => {
            window.location.href = localhostUrl
          }, 2000)
        } else {
          setError('Microphone access not available. Please use a modern browser with microphone support.')
        }
      } else {
        setError(`Failed to access microphone: ${err.message || err.name || 'Unknown error'}. Please check your browser settings.`)
      }
      return false
    }
  }

  const startRecording = async () => {
    if (disabled || isRecording) return

    try {
      setError(null)
      
      // Check if MediaDevices API is available
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        const isHttp = window.location.protocol === 'http:' && !window.location.hostname.includes('localhost') && !window.location.hostname.includes('127.0.0.1')
        if (isHttp) {
          const currentUrl = window.location.href
          const localhostUrl = currentUrl.replace(window.location.hostname, 'localhost')
          // Auto-redirect to localhost if on IP address
          console.warn('Redirecting to localhost for microphone access', { from: window.location.href, to: localhostUrl })
          window.location.href = localhostUrl
          return
        } else {
          setError('Microphone access is not available in this browser. Please use a modern browser that supports the MediaDevices API.')
        }
        console.error('MediaDevices API not available', {
          hasMediaDevices: !!navigator.mediaDevices,
          hasGetUserMedia: !!(navigator.mediaDevices?.getUserMedia),
          protocol: window.location.protocol,
          hostname: window.location.hostname
        })
        return
      }
      
      // Request microphone access (this will trigger browser permission prompt on first use)
      // Browsers require a user gesture (click) to show the permission prompt
      console.log('Requesting microphone permission...', {
        hasMediaDevices: !!navigator.mediaDevices,
        hasGetUserMedia: !!(navigator.mediaDevices?.getUserMedia),
        protocol: window.location.protocol,
        hostname: window.location.hostname
      })
      
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      })
      
      console.log('Microphone permission granted! Stream received', {
        active: stream.active,
        audioTracks: stream.getAudioTracks().length
      })
      
      // If we got here, permission was granted
      setHasPermission(true)
      setError(null) // Clear any previous errors
      
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
          // Send audio chunk in real-time if callback provided
          if (onAudioChunk) {
            console.log('Sending audio chunk via callback', { chunkSize: event.data.size })
            onAudioChunk(event.data)
          }
        }
      }

      mediaRecorder.onstop = () => {
        console.log('MediaRecorder onstop event fired', {
          chunksCount: audioChunksRef.current.length,
          totalSize: audioChunksRef.current.reduce((sum, chunk) => sum + chunk.size, 0)
        })
        
        // Combine all audio chunks into a single blob
        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType })
        console.log('Audio blob created', {
          blobSize: audioBlob.size,
          blobType: audioBlob.type
        })
        
        audioChunksRef.current = []
        
        // Stop all tracks
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => {
            track.stop()
            console.log('Stopped audio track in onstop')
          })
          streamRef.current = null
        }

        // Update internal state first
        setIsRecording(false)
        console.log('VoiceRecorder internal isRecording set to false')
        
        // Call callback with audio blob - this will notify parent
        console.log('Calling onAudioEnd callback with audio blob', { blobSize: audioBlob.size })
        if (onAudioEnd) {
          onAudioEnd(audioBlob)
        } else {
          console.warn('onAudioEnd callback is not defined!')
        }
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
    console.log('=== stopRecording called ===', {
      hasMediaRecorder: !!mediaRecorderRef.current,
      isRecording,
      externalIsRecording,
      recording,
      state: mediaRecorderRef.current?.state,
      tracks: streamRef.current?.getTracks().length || 0
    })
    
    try {
      if (mediaRecorderRef.current) {
        const state = mediaRecorderRef.current.state
        console.log('MediaRecorder state:', state)
        
        // Stop the MediaRecorder if it's recording or paused
        if (state === 'recording' || state === 'paused') {
          console.log('Stopping MediaRecorder...')
          mediaRecorderRef.current.stop()
          console.log('MediaRecorder.stop() called successfully')
        } else if (state === 'inactive') {
          // MediaRecorder already stopped - might have stopped elsewhere
          console.warn('MediaRecorder state is already inactive - creating blob from existing chunks')
          // Create blob from existing chunks if any
          if (audioChunksRef.current.length > 0) {
            const mimeType = mediaRecorderRef.current.mimeType || 'audio/webm'
            const audioBlob = new Blob(audioChunksRef.current, { type: mimeType })
            console.log('Created blob from existing chunks', { blobSize: audioBlob.size })
            // Call onAudioEnd if we have audio data
            if (onAudioEnd && audioBlob.size > 0) {
              onAudioEnd(audioBlob)
            }
          }
        } else {
          console.warn('MediaRecorder state is not recording or paused:', state)
        }
      } else {
        console.warn('stopRecording: mediaRecorderRef.current is null')
      }
      
      // Always stop audio tracks regardless of MediaRecorder state
      if (streamRef.current) {
        const tracks = streamRef.current.getTracks()
        console.log('Stopping audio tracks:', tracks.length)
        tracks.forEach((track, index) => {
          track.stop()
          console.log(`Stopped audio track ${index}:`, track.label)
        })
        streamRef.current = null
      }
      
      // Always update state
      setIsRecording(false)
      console.log('VoiceRecorder internal recording state set to false')
      
      // If MediaRecorder was already inactive or doesn't exist, check if onstop already fired
      // Only call onAudioEnd if we haven't already processed the stop
      const currentState = mediaRecorderRef.current?.state
      if ((!mediaRecorderRef.current || currentState === 'inactive') && onAudioEnd) {
        // Check if we have chunks to create a blob
        if (audioChunksRef.current.length > 0) {
          const mimeType = mediaRecorderRef.current?.mimeType || 'audio/webm'
          const audioBlob = new Blob(audioChunksRef.current, { type: mimeType })
          console.log('Calling onAudioEnd with blob (MediaRecorder was already stopped but has chunks)', { 
            blobSize: audioBlob.size,
            chunksCount: audioChunksRef.current.length 
          })
          onAudioEnd(audioBlob)
          // Clear chunks after creating blob
          audioChunksRef.current = []
        } else {
          // No audio chunks and MediaRecorder is already inactive
          // This means onstop already fired and processed the audio
          // Don't call onAudioEnd again to avoid duplicate audio_end messages
          console.log('MediaRecorder already stopped with no chunks - onstop handler likely already processed this')
        }
      } else if (currentState !== 'recording' && currentState !== 'paused' && onAudioEnd) {
        // MediaRecorder is in some other state (like inactive) but onstop might not have fired
        // Only process if we have audio chunks
        if (audioChunksRef.current.length > 0) {
          console.log('MediaRecorder in unexpected state, but has chunks - processing', { state: currentState })
          const mimeType = mediaRecorderRef.current?.mimeType || 'audio/webm'
          const audioBlob = new Blob(audioChunksRef.current, { type: mimeType })
          onAudioEnd(audioBlob)
          audioChunksRef.current = []
        } else {
          console.log('MediaRecorder in unexpected state with no chunks - skipping onAudioEnd to avoid duplicate', { state: currentState })
        }
      }
    } catch (error) {
      console.error('Error in stopRecording:', error)
      // Still update state even if there's an error
      setIsRecording(false)
      // Try to notify parent to update state
      if (onAudioEnd) {
        console.log('Notifying parent of stopRecording error')
        onAudioEnd(new Blob([], { type: 'audio/webm' }))
      }
    }
  }

  const recording = isRecording || externalIsRecording

  // Debug: Log when recording state changes
  useEffect(() => {
    console.log('VoiceRecorder recording state changed', {
      isRecording,
      externalIsRecording,
      recording,
      disabled
    })
  }, [isRecording, externalIsRecording, recording, disabled])

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
    <div className="flex flex-col items-center gap-3" style={{ pointerEvents: 'auto', zIndex: 1 }}>
      {error && (
        <p className="text-sm text-red-600 dark:text-red-400 text-center">{error}</p>
      )}
      
      <div className="flex items-center gap-3" style={{ pointerEvents: 'auto' }}>
        {!recording ? (
          <Button
            variant="primary"
            onClick={startRecording}
            disabled={(() => {
              // Only disable if:
              // 1. Explicitly disabled from parent
              // 2. Permission is explicitly denied (false) AND we're showing error state
              // Don't disable if permission is null (unknown) - let user try to record
              const isDisabled = disabled || (hasPermission === false && !!error)
              console.log('VoiceRecorder button disabled check', {
                disabled,
                hasPermission,
                error: error || 'none',
                isDisabled,
                finalDisabled: isDisabled
              })
              return isDisabled
            })()}
            className="flex items-center gap-2 px-6 py-3"
            size="lg"
          >
            <Mic className="w-5 h-5" />
            <span>Start Recording</span>
          </Button>
        ) : (
          <button
            type="button"
            onClick={(e) => {
              e.preventDefault()
              e.stopPropagation()
              console.log('=== Stop Recording button clicked ===', {
                hasMediaRecorder: !!mediaRecorderRef.current,
                isRecording,
                externalIsRecording,
                recording,
                disabled,
                timestamp: Date.now()
              })
              stopRecording()
              console.log('Stop Recording button clicked - AFTER stopRecording call')
            }}
            disabled={disabled}
            className="flex items-center justify-center gap-2 px-6 py-3 bg-red-600 hover:bg-red-700 text-white font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
            style={{ 
              pointerEvents: disabled ? 'none' : 'auto', 
              zIndex: 10,
              cursor: disabled ? 'not-allowed' : 'pointer'
            }}
          >
            <Square className="w-5 h-5" />
            <span>Stop Recording</span>
          </button>
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

