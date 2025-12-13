import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'AI Voice Interview Platform',
  description: 'Conduct AI-powered voice interviews based on job descriptions and CVs',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}

