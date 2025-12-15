'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'

export default function InterviewTicketEntryPage() {
  const router = useRouter()
  const [ticketCode, setTicketCode] = useState('')

  const handleStart = (e: React.FormEvent) => {
    e.preventDefault()
    const code = ticketCode.trim()
    if (!code) return
    router.push(`/interview/${encodeURIComponent(code)}`)
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        <Card>
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Join AI Interview</h1>
          <p className="text-sm text-gray-600 mb-4">
            Enter the interview ticket code you received from the recruiter to start your session.
          </p>
          <form onSubmit={handleStart} className="space-y-4">
            <Input
              label="Ticket Code"
              type="text"
              value={ticketCode}
              onChange={(e) => setTicketCode(e.target.value)}
              placeholder="e.g., ABCD2345EFGH"
              required
            />
            <Button type="submit" variant="primary" className="w-full">
              Start Interview
            </Button>
          </form>
        </Card>
      </div>
    </div>
  )
}


