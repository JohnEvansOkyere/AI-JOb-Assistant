/**
 * Payment Callback Page
 * Handles Paystack payment redirect and verifies payment
 */

'use client'

import { useEffect, useState } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { apiClient } from '@/lib/api/client'
import { CheckCircle, XCircle, Loader } from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'

export default function PaymentCallbackPage() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const reference = searchParams.get('reference') || searchParams.get('trxref')
  const [status, setStatus] = useState<'verifying' | 'success' | 'error'>('verifying')
  const [message, setMessage] = useState('Verifying payment...')

  useEffect(() => {
    if (reference) {
      verifyPayment(reference)
    } else {
      setStatus('error')
      setMessage('No payment reference found')
    }
  }, [reference])

  const verifyPayment = async (ref: string) => {
    try {
      setStatus('verifying')
      setMessage('Verifying payment with Paystack...')

      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }

      const response = await apiClient.post('/subscriptions/verify-payment', {
        reference: ref
      })

      if (response.success) {
        setStatus('success')
        setMessage(response.message || 'Payment verified successfully! Your subscription has been activated.')
        
        // Redirect to dashboard after 3 seconds
        setTimeout(() => {
          router.push('/dashboard?subscription=active')
        }, 3000)
      } else {
        setStatus('error')
        setMessage(response.message || 'Payment verification failed. Please contact support if payment was deducted.')
      }
    } catch (error: any) {
      console.error('Payment verification error:', error)
      setStatus('error')
      setMessage(error.message || 'Failed to verify payment. Please check your subscription status in the dashboard or contact support.')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-turquoise-50 via-white to-yellow-50 py-12 px-4">
      <Card className="max-w-md w-full p-8 text-center">
        {status === 'verifying' && (
          <>
            <Loader className="h-16 w-16 animate-spin text-turquoise-600 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Verifying Payment</h2>
            <p className="text-gray-600">{message}</p>
          </>
        )}

        {status === 'success' && (
          <>
            <CheckCircle className="h-16 w-16 text-green-600 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Payment Successful!</h2>
            <p className="text-gray-600 mb-6">{message}</p>
            <Button
              onClick={() => router.push('/dashboard')}
              variant="primary"
              className="w-full"
            >
              Go to Dashboard
            </Button>
          </>
        )}

        {status === 'error' && (
          <>
            <XCircle className="h-16 w-16 text-red-600 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Verification Failed</h2>
            <p className="text-gray-600 mb-6">{message}</p>
            <div className="space-y-2">
              <Button
                onClick={() => verifyPayment(reference!)}
                variant="primary"
                className="w-full"
              >
                Retry Verification
              </Button>
              <Button
                onClick={() => router.push('/dashboard')}
                variant="outline"
                className="w-full"
              >
                Go to Dashboard
              </Button>
            </div>
          </>
        )}
      </Card>
    </div>
  )
}

