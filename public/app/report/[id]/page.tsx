'use client'

import { useState, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'
import Link from 'next/link'
import { getCurrentUser, signOut, User } from '@/lib/auth'
import { supabase } from '@/lib/supabase'
import Footer from '@/components/Footer'
import styles from './report.module.css'

interface ReportSection {
  section: string
  summary: string
}

interface Report {
  id: string
  ticker: string
  company_name: string
  newer_filing_date: string
  older_filing_date: string
  ai_summaries: Record<string, string>
  extraction_success: boolean
  refunded: boolean
  created_at: string
}

export default function ReportPage() {
  const router = useRouter()
  const params = useParams()
  const reportId = params?.id as string

  const [user, setUser] = useState<User | null>(null)
  const [report, setReport] = useState<Report | null>(null)
  const [sections, setSections] = useState<ReportSection[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    loadUserAndReport()
  }, [reportId])

  async function loadUserAndReport() {
    try {
      const currentUser = await getCurrentUser()
      if (!currentUser) {
        router.push('/login')
        return
      }
      setUser(currentUser)

      // Load report
      const { data: reportData, error: reportError } = await supabase
        .from('reports')
        .select('*')
        .eq('id', reportId)
        .single()

      if (reportError || !reportData) {
        setError('Report not found')
        setLoading(false)
        return
      }

      // Check if user owns this report (unless admin)
      if (reportData.user_id !== currentUser.id && !currentUser.is_admin) {
        setError('You do not have access to this report')
        setLoading(false)
        return
      }

      setReport(reportData)

      // Parse and sort sections: Item 1, Item 1A, Item 7, Item 8
      if (reportData.ai_summaries) {
        const sectionOrder = ['Item 1', 'Item 1A', 'Item 7', 'Item 8']
        const sortedSections: ReportSection[] = sectionOrder
          .map(section => ({
            section,
            summary: reportData.ai_summaries[section] || ''
          }))
          .filter(s => s.summary) // Only include sections with summaries

        setSections(sortedSections)
      }

      setLoading(false)
    } catch (err) {
      console.error('Error loading report:', err)
      setError('Failed to load report')
      setLoading(false)
    }
  }

  async function handleSignOut() {
    await signOut()
    router.push('/')
  }

  // Simple markdown parser for bold text
  function renderMarkdown(text: string) {
    // Convert **bold** to <strong>bold</strong>
    return text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  }

  if (loading) {
    return (
      <div className={styles.page}>
        <div className={styles.loading}>
          <div className={styles.loadingSpinner}></div>
          Loading report...
        </div>
      </div>
    )
  }

  if (error || !report || !user) {
    return (
      <div className={styles.page}>
        <nav className="nav">
          <div className="container">
            <div className="nav-content">
              <Link href="/" className="nav-logo">IncDigest</Link>
              <div className="nav-links">
                <Link href="/dashboard">Dashboard</Link>
              </div>
            </div>
          </div>
        </nav>

        <main className="container-narrow">
          <div className={styles.error}>
            <h1>Report Not Found</h1>
            <p>{error || 'The requested report could not be found.'}</p>
            <Link href="/dashboard" className="button primary">
              Back to Dashboard
            </Link>
          </div>
        </main>

        <Footer />
      </div>
    )
  }

  return (
    <div className={styles.page}>
      <nav className="nav">
        <div className="container">
          <div className="nav-content">
            <Link href="/" className="nav-logo">IncDigest</Link>
            <div className="nav-links">
              <Link href="/dashboard">Dashboard</Link>
              {user.is_admin && (
                <Link href="/admin" style={{ color: 'var(--color-primary)' }}>Admin</Link>
              )}
              <button onClick={handleSignOut} className="sign-out-btn">
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="container-narrow">
        {/* Report Header */}
        <div className={styles.reportHeader}>
          <div className={styles.companyInfo}>
            <h1>{report.ticker}</h1>
            <p className="text-secondary">{report.company_name}</p>
          </div>
          <div className={styles.filingInfo}>
            <div>
              <span className="text-secondary text-sm">Comparing Filings:</span>
              <p>
                {new Date(report.newer_filing_date).toLocaleDateString('en-US', { 
                  month: 'long', 
                  day: 'numeric', 
                  year: 'numeric' 
                })} vs {new Date(report.older_filing_date).toLocaleDateString('en-US', { 
                  month: 'long', 
                  day: 'numeric', 
                  year: 'numeric' 
                })}
              </p>
            </div>
            <div>
              <span className="text-secondary text-sm">Generated:</span>
              <p>
                {new Date(report.created_at).toLocaleDateString('en-US', { 
                  month: 'long', 
                  day: 'numeric', 
                  year: 'numeric' 
                })} at {new Date(report.created_at).toLocaleTimeString('en-US', { 
                  hour: '2-digit', 
                  minute: '2-digit' 
                })}
              </p>
            </div>
          </div>
        </div>

        {report.refunded && (
          <div className={styles.refundNotice}>
            <strong>⚠️ This report was refunded</strong> due to quality issues or generation failure. No tokens were charged.
          </div>
        )}

        {/* Report Sections */}
        {sections.length > 0 ? (
          <div className={styles.sections}>
            {sections.map((section) => (
              <div key={section.section} className={styles.section}>
                <h2>{section.section}</h2>
                <div className={styles.sectionContent}>
                  {section.summary.split('\n').map((paragraph, i) => (
                    paragraph.trim() && (
                      <p 
                        key={i} 
                        dangerouslySetInnerHTML={{ __html: renderMarkdown(paragraph) }}
                      />
                    )
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className={styles.noContent}>
            <p>No analysis available for this report.</p>
          </div>
        )}

        {/* Bottom Disclaimer */}
        <div className={styles.disclaimerBottom}>
          <h3>⚠️ IMPORTANT DISCLAIMER</h3>
          <p>
            <strong>AI-GENERATED ANALYSIS - NOT INVESTMENT ADVICE</strong> | This report may contain errors. 
            Verify all information independently. Consult qualified professionals before investing. 
            You are solely responsible for your decisions. See full <Link href="/terms">disclaimers</Link>.
          </p>
        </div>

        <div className={styles.actions}>
          <Link href="/search" className="button primary">
            Generate Another Report
          </Link>
          <Link href="/dashboard" className="button">
            Back to Dashboard
          </Link>
        </div>
      </main>

      <Footer />
    </div>
  )
}
