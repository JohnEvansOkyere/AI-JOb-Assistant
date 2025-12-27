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

  // Create object URL from blob if provided
  useEffect(() => {
    if (audioBlob && !audioUrl) {
      const url = URL.createObjectURL(audioBlob)
      objectUrlRef.current = url
      
      return () => {
        URL.revokeObjectURL(url)
        objectUrlRef.current = null
      }
    }
  }, [audioBlob, audioUrl])

  // Initialize audio element
  useEffect(() => {
    const audio = new Audio()
    audioRef.current = audio

    audio.addEventListener('loadedmetadata', () => {
      setDuration(audio.duration)
      setIsLoading(false)
    })

    audio.addEventListener('timeupdate', () => {
      setCurrentTime(audio.currentTime)
    })

    audio.addEventListener('play', () => {
      setIsPlaying(true)
      onPlayStart?.()
    })

    audio.addEventListener('pause', () => {
      setIsPlaying(false)
    })

    audio.addEventListener('ended', () => {
      setIsPlaying(false)
      setCurrentTime(0)
      onPlayEnd?.()
    })

    audio.addEventListener('error', (e) => {
      console.error('Audio playback error', e)
      setError('Failed to play audio')
      setIsLoading(false)
      setIsPlaying(false)
    })

    return () => {
      audio.pause()
      audio.src = ''
      if (objectUrlRef.current) {
        URL.revokeObjectURL(objectUrlRef.current)
      }
    }
  }, [onPlayStart, onPlayEnd])

  // Update audio source when blob or URL changes
  useEffect(() => {
    if (!audioRef.current) return

    const audio = audioRef.current
    const source = audioUrl || objectUrlRef.current

    if (source) {
      setIsLoading(true)
      setError(null)
      audio.src = source
      audio.load()

      if (autoPlay) {
        // Handle autoplay policy - browsers may block autoplay
        audio.play().catch((err) => {
          console.warn('Autoplay blocked', err)
          setError('Click play to start audio')
        })
      }
    }
  }, [audioUrl, audioBlob, autoPlay])

  // Update volume
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = isMuted ? 0 : volume
    }
  }, [volume, isMuted])

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

