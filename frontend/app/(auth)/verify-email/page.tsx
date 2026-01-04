/**
 * Email Verification Page
 * Handles email verification via link (token from email)
 */

'use client'

export const dynamic = 'force-dynamic'

import { useEffect, useState, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { apiClient } from '@/lib/api/client'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { ThemeToggle } from '@/components/ui/ThemeToggle'
import Link from 'next/link'
import { Sparkles, CheckCircle2, XCircle, Loader2 } from 'lucide-react'

function VerifyEmailContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const token = searchParams.get('token')
  
  const [status, setStatus] = useState<'verifying' | 'success' | 'error'>('verifying')
  const [message, setMessage] = useState('Verifying your email...')
  const [error, setError] = useState('')

  useEffect(() => {
    if (!token) {
      setStatus('error')
      setError('Invalid verification link. Please check your email for a valid verification link.')
      return
    }

    // Verify email using token
    const verifyEmail = async () => {
      try {
        const response = await apiClient.get<{ access_token: string; token_type: string }>(
          `/auth/verify-email-link/${token}`
        )

        if (response.success && response.data) {
          // Store token and update API client
          localStorage.setItem('auth_token', response.data.access_token)
          apiClient.setToken(response.data.access_token)
          
          setStatus('success')
          setMessage('Email verified successfully! Redirecting to dashboard...')
          
          // Redirect to dashboard after 2 seconds
          setTimeout(() => {
            router.push('/dashboard')
          }, 2000)
        } else {
          throw new Error(response.message || 'Verification failed')
        }
      } catch (err: any) {
        console.error('Verification error:', err)
        setStatus('error')
        setError(err.message || 'Verification failed. The link may have expired or been used already.')
      }
    }

    verifyEmail()
  }, [token, router])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-turquoise-50 via-white to-yellow-50 py-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Decorative background elements */}
      <div className="absolute top-0 left-0 w-72 h-72 bg-turquoise-200/30 rounded-full blur-3xl -translate-x-1/2 -translate-y-1/2"></div>
      <div className="absolute bottom-0 right-0 w-72 h-72 bg-yellow-200/30 rounded-full blur-3xl translate-x-1/2 translate-y-1/2"></div>
      
      <div className="absolute top-4 right-4 z-10">
        <ThemeToggle variant="icon" />
      </div>
      
      <div className="max-w-md w-full relative z-10">
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-2 justify-center mb-6">
            <div className="w-12 h-12 bg-gradient-to-br from-turquoise-500 to-turquoise-600 rounded-lg flex items-center justify-center shadow-lg">
              <Sparkles className="w-7 h-7 text-white" />
            </div>
            <span className="text-2xl font-bold text-gray-900 dark:text-white">VeloxaRecruit</span>
          </Link>
        </div>

        <Card>
          <div className="text-center space-y-6 py-8">
            {status === 'verifying' && (
              <>
                <div className="mx-auto w-16 h-16 bg-turquoise-100 dark:bg-turquoise-900/30 rounded-full flex items-center justify-center">
                  <Loader2 className="w-8 h-8 text-turquoise-600 dark:text-turquoise-400 animate-spin" />
                </div>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Verifying Your Email</h2>
                <p className="text-gray-600 dark:text-gray-400">{message}</p>
              </>
            )}

            {status === 'success' && (
              <>
                <div className="mx-auto w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center">
                  <CheckCircle2 className="w-8 h-8 text-green-600 dark:text-green-400" />
                </div>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Email Verified!</h2>
                <p className="text-gray-600 dark:text-gray-400">{message}</p>
                <div className="pt-4">
                  <div className="inline-block px-4 py-2 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 rounded-full text-sm font-medium">
                    Redirecting...
                  </div>
                </div>
              </>
            )}

            {status === 'error' && (
              <>
                <div className="mx-auto w-16 h-16 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center">
                  <XCircle className="w-8 h-8 text-red-600 dark:text-red-400" />
                </div>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Verification Failed</h2>
                <p className="text-gray-600 dark:text-gray-400">{error}</p>
                <div className="pt-4 space-y-3">
                  <Button
                    onClick={() => router.push('/login')}
                    variant="primary"
                    className="w-full bg-turquoise-600 hover:bg-turquoise-700 text-white"
                  >
                    Go to Login
                  </Button>
                  <Link href="/register" className="block text-sm text-turquoise-600 dark:text-turquoise-400 hover:underline">
                    Register a new account
                  </Link>
                </div>
              </>
            )}
          </div>
        </Card>

        <div className="mt-6 text-center">
          <Link href="/" className="text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300">
            ← Back to home
          </Link>
        </div>
      </div>
    </div>
  )
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-turquoise-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading...</p>
        </div>
      </div>
    }>
      <VerifyEmailContent />
    </Suspense>
  )
}

