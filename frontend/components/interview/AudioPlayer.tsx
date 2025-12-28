'use client'

import { useState, useRef, useEffect } from 'react'
import { Play, Pause, Volume2, VolumeX } from 'lucide-react'
import { Button } from '@/components/ui/Button'

interface AudioPlayerProps {
  audioBlob?: Blob
  audioUrl?: string
  autoPlay?: boolean
  onPlayStart?: () => void
  onPlayEnd?: () => void
  className?: string
}

export function AudioPlayer({
  audioBlob,
  audioUrl,
  autoPlay = false,
  onPlayStart,
  onPlayEnd,
  className = '',
}: AudioPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [duration, setDuration] = useState<number>(0)
  const [currentTime, setCurrentTime] = useState<number>(0)
  const [volume, setVolume] = useState(1)
  const [isMuted, setIsMuted] = useState(false)
  
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const objectUrlRef = useRef<string | null>(null)

  // Initialize audio element (only once)
  useEffect(() => {
    const audio = new Audio()
    audio.preload = 'auto'
    audioRef.current = audio

    // Store handler references for proper cleanup
    const handleLoadedMetadata = () => {
      setDuration(audio.duration)
      setIsLoading(false)
    }

    const handleTimeUpdate = () => {
      setCurrentTime(audio.currentTime)
    }

    const handlePlay = () => {
      // Verify audio is actually playing
      if (!audio.paused) {
        setIsPlaying(true)
        onPlayStart?.()
      }
    }

    const handlePause = () => {
      setIsPlaying(false)
    }
    
    const handlePlaying = () => {
      // This event fires when audio actually starts playing (not just when play() is called)
      setIsPlaying(true)
    }

    const handleEnded = () => {
      setIsPlaying(false)
      setCurrentTime(0)
      onPlayEnd?.()
    }

    const handleError = (e: Event) => {
      console.error('Audio playback error', e, audio.error)
      const errorMessage = audio.error 
        ? `Failed to play audio: ${audio.error.code === 4 ? 'Format not supported' : audio.error.message || 'Unknown error'}`
        : 'Failed to play audio'
      setError(errorMessage)
      setIsLoading(false)
      setIsPlaying(false)
    }

    audio.addEventListener('loadedmetadata', handleLoadedMetadata)
    audio.addEventListener('timeupdate', handleTimeUpdate)
    audio.addEventListener('play', handlePlay)
    audio.addEventListener('playing', handlePlaying) // Fires when actually playing
    audio.addEventListener('pause', handlePause)
    audio.addEventListener('ended', handleEnded)
    audio.addEventListener('error', handleError)

    return () => {
      // Cleanup: pause audio and remove all listeners
      // Don't set src to '' - it causes "Empty src attribute" errors
      audio.pause()
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata)
      audio.removeEventListener('timeupdate', handleTimeUpdate)
      audio.removeEventListener('play', handlePlay)
      audio.removeEventListener('playing', handlePlaying)
      audio.removeEventListener('pause', handlePause)
      audio.removeEventListener('ended', handleEnded)
      audio.removeEventListener('error', handleError)
    }
  }, [onPlayStart, onPlayEnd])

  // Create object URL from blob and set audio source atomically
  useEffect(() => {
    if (!audioRef.current) return

    const audio = audioRef.current

    // Create object URL from blob if provided
    if (audioBlob && !audioUrl) {
      // Revoke previous URL if exists
      if (objectUrlRef.current) {
        URL.revokeObjectURL(objectUrlRef.current)
      }
      
      const url = URL.createObjectURL(audioBlob)
      objectUrlRef.current = url
      console.log('AudioPlayer: Created object URL', { blobType: audioBlob.type, blobSize: audioBlob.size })
    }

    // Determine the source to use
    const source = audioUrl || objectUrlRef.current

    if (source && source.trim() !== '') {
      setIsLoading(true)
      setError(null)
      
      console.log('AudioPlayer: Setting audio source', {
        blobSize: audioBlob?.size,
        blobType: audioBlob?.type,
        sourceType: audioUrl ? 'url' : 'blob',
        sourceLength: source.length
      })
      
      // Set source directly
      audio.src = source
      audio.load()

      // Handle load error
      const handleLoadError = () => {
        console.error('Audio load error', {
          error: audio.error,
          code: audio.error?.code,
          message: audio.error?.message
        })
        const errorMsg = audio.error 
          ? `Failed to load audio: ${audio.error.message || 'Unknown error'}`
          : 'Failed to load audio'
        setError(errorMsg)
        setIsLoading(false)
      }
      audio.addEventListener('error', handleLoadError)

      // Handle successful load and play if autoplay is enabled
      const handleCanPlayThrough = () => {
        console.log('AudioPlayer: canplaythrough event fired', {
          autoPlay,
          paused: audio.paused,
          readyState: audio.readyState,
          duration: audio.duration
        })
        setIsLoading(false)
        if (autoPlay && !audio.paused) {
          // Already playing, don't try again
          console.log('AudioPlayer: Audio already playing, skipping autoplay')
          return
        }
        if (autoPlay && audio.paused) {
          console.log('AudioPlayer: Attempting autoplay from canplaythrough')
          const playPromise = audio.play()
          if (playPromise !== undefined) {
            playPromise
              .then(() => {
                console.log('AudioPlayer: Autoplay started successfully from canplaythrough')
                setIsPlaying(true)
              })
              .catch((err) => {
                console.warn('AudioPlayer: Autoplay blocked from canplaythrough', err)
                // Don't show error immediately - user can click play button
                // setError('Autoplay blocked. Click play to start audio.')
                setIsLoading(false)
              })
          }
        }
        audio.removeEventListener('canplaythrough', handleCanPlayThrough)
      }
      
      // Also handle canplay as fallback (fires earlier than canplaythrough)
      const handleCanPlay = () => {
        console.log('AudioPlayer: canplay event fired', { 
          readyState: audio.readyState, 
          paused: audio.paused,
          duration: audio.duration 
        })
        setIsLoading(false)
        if (autoPlay && audio.readyState >= 3 && audio.paused) { // Ready and paused
          console.log('AudioPlayer: Attempting autoplay from canplay')
          const playPromise = audio.play()
          if (playPromise !== undefined) {
            playPromise
              .then(() => {
                console.log('AudioPlayer: Autoplay started successfully from canplay')
                setIsPlaying(true)
              })
              .catch((err) => {
                console.warn('AudioPlayer: Autoplay blocked from canplay', err)
                // Don't set error here - wait for canplaythrough which is more reliable
              })
          }
        }
      }

      // Check if audio is already ready before adding listeners
      // readyState values: 0=HAVE_NOTHING, 1=HAVE_METADATA, 2=HAVE_CURRENT_DATA, 3=HAVE_FUTURE_DATA, 4=HAVE_ENOUGH_DATA
      if (audio.readyState >= 3 && audio.duration > 0) {
        // Audio is already loaded enough to play
        console.log('AudioPlayer: Audio already ready, attempting to play immediately', { 
          readyState: audio.readyState,
          duration: audio.duration,
          paused: audio.paused
        })
        setIsLoading(false)
        if (autoPlay && audio.paused) {
          const playPromise = audio.play()
          if (playPromise !== undefined) {
            playPromise
              .then(() => {
                console.log('AudioPlayer: Autoplay started successfully (already ready)')
                setIsPlaying(true)
              })
              .catch((err) => {
                console.warn('AudioPlayer: Autoplay blocked (already ready)', err)
                // Don't show error - user can click play button
                setIsLoading(false)
              })
          }
        }
      } else {
        // Wait for audio to be ready
        console.log('AudioPlayer: Waiting for audio to load', { 
          readyState: audio.readyState,
          duration: audio.duration || 'unknown'
        })
        audio.addEventListener('canplaythrough', handleCanPlayThrough)
        audio.addEventListener('canplay', handleCanPlay)
      }

      return () => {
        audio.removeEventListener('error', handleLoadError)
        audio.removeEventListener('canplaythrough', handleCanPlayThrough)
        audio.removeEventListener('canplay', handleCanPlay)
      }
    }

    // Cleanup: revoke object URL when blob is removed or audioUrl is provided
    return () => {
      // Only clean up object URL if we're switching away from blob-based audio
      // Don't revoke if audio is still playing or if we're just updating the blob
      if (audioUrl || (!audioBlob && objectUrlRef.current)) {
        const urlToRevoke = objectUrlRef.current
        if (urlToRevoke) {
          URL.revokeObjectURL(urlToRevoke)
          objectUrlRef.current = null
        }
      }
    }
  }, [audioUrl, audioBlob, autoPlay])

  // Update volume and muted state
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = isMuted ? 0 : volume
      audioRef.current.muted = isMuted
      console.log('AudioPlayer: Volume updated', { volume, isMuted, actualVolume: audioRef.current.volume, actualMuted: audioRef.current.muted })
    }
  }, [volume, isMuted])
  
  // Initialize audio volume when element is created
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = volume
      audioRef.current.muted = false // Ensure not muted by default
    }
  }, []) // Only run once when component mounts

  const togglePlay = () => {
    if (!audioRef.current) return

    if (isPlaying) {
      audioRef.current.pause()
    } else {
      audioRef.current.play().catch((err) => {
        console.error('Failed to play audio', err)
        setError('Failed to play audio')
      })
    }
  }

  const toggleMute = () => {
    setIsMuted(!isMuted)
  }

  const formatTime = (seconds: number) => {
    if (isNaN(seconds)) return '0:00'
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  if (!audioBlob && !audioUrl) {
    return null
  }

  return (
    <div className={`flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg ${className}`}>
      <Button
        variant="primary"
        onClick={togglePlay}
        disabled={isLoading || !!error}
        size="sm"
        className="flex-shrink-0"
      >
        {isLoading ? (
          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
        ) : isPlaying ? (
          <Pause className="w-4 h-4" />
        ) : (
          <Play className="w-4 h-4" />
        )}
      </Button>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
          <span>{formatTime(currentTime)}</span>
          <div className="flex-1 h-1 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-600 dark:bg-blue-500 transition-all"
              style={{ width: duration > 0 ? `${(currentTime / duration) * 100}%` : '0%' }}
            />
          </div>
          <span>{formatTime(duration)}</span>
        </div>
        {error && (
          <p className="text-xs text-red-600 dark:text-red-400 mt-1">{error}</p>
        )}
      </div>

      <Button
        variant="ghost"
        onClick={toggleMute}
        size="sm"
        className="flex-shrink-0"
      >
        {isMuted ? (
          <VolumeX className="w-4 h-4" />
        ) : (
          <Volume2 className="w-4 h-4" />
        )}
      </Button>
    </div>
  )
}

