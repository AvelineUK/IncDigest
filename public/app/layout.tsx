import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'IncDigest - AI-Powered 10-K Analysis',
  description: 'Automated SEC 10-K filing summaries for investors',
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
