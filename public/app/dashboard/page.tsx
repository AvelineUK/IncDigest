'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { getCurrentUser, signOut, User } from '@/lib/auth'
import { supabase } from '@/lib/supabase'
import Footer from '@/components/Footer'
import styles from './dashboard.module.css'

interface Report {
  id: string
  ticker: string
  status: string
  created_at: string
  completed_at: string | null
}

export default function Dashboard() {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [reports, setReports] = useState<Report[]>([])
  const [loading, setLoading] = useState(true)
  const [openDropdown, setOpenDropdown] = useState<string | null>(null)

  useEffect(() => {
    checkAuth()
  }, [])

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (openDropdown) {
        const target = event.target as HTMLElement
        if (!target.closest(`.${styles.dropdown}`)) {
          setOpenDropdown(null)
        }
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [openDropdown])

  async function checkAuth() {
    try {
      const currentUser = await getCurrentUser()
      if (!currentUser) {
        router.push('/login')
        return
      }
      
      setUser(currentUser)
      
      // Load reports
      const { data: reportsData } = await supabase
        .from('reports')
        .select('id, ticker, extraction_success, refunded, created_at')
        .eq('user_id', currentUser.id)
        .order('created_at', { ascending: false })
        .limit(10)
      
      if (reportsData) {
        // Map database fields to UI status
        const mappedReports = reportsData.map(r => ({
          id: r.id,
          ticker: r.ticker,
          status: r.refunded ? 'refunded' : (r.extraction_success ? 'completed' : 'failed'),
          created_at: r.created_at,
          completed_at: r.created_at
        }))
        setReports(mappedReports)
      }
    } catch (error) {
      console.error('Auth check failed:', error)
      router.push('/login')
    } finally {
      setLoading(false)
    }
  }

  async function handleSignOut() {
    await signOut()
    router.push('/')
  }

  if (loading) {
    return (
      <div className={styles.page}>
        <div className={styles.loading}>
          <div className={styles.loadingSpinner}></div>
          Loading...
        </div>
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
              {user?.is_admin && (
                <Link href="/admin" style={{ color: 'var(--color-primary)' }}>Admin</Link>
              )}
              <button onClick={handleSignOut} className="sign-out-btn">
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="container">
        <div className={styles.header}>
          <div>
            <h1>Dashboard</h1>
            <p className="text-secondary">{user?.email}</p>
          </div>
          <div className={styles.tokens}>
            <div className={styles.tokenBadge}>
              {user?.tokens_remaining || 0} tokens
            </div>
            <Link href="/pricing" className="button primary">
              Buy Tokens
            </Link>
          </div>
        </div>

        <div className={styles.grid}>
          {/* Quick Actions */}
          <div className="card">
            <h2>Generate Report</h2>
            <p className="text-secondary mb-2">
              Analyze any U.S. 10-K filer
            </p>
            <Link href="/search" className="button primary">
              Search Ticker
            </Link>
          </div>
        </div>

        {/* Recent Reports */}
        <div className={styles.reports}>
          <h2>Recent Reports</h2>
          {reports.length === 0 ? (
            <p className="text-secondary">No reports yet. Generate your first one!</p>
          ) : (
            <div className={styles.reportList}>
              {reports.map((report) => (
                <div key={report.id} className={styles.reportItem}>
                  <div className={styles.reportInfo}>
                    {report.status === 'completed' ? (
                      <Link href={`/report/${report.id}`} className={styles.reportTicker}>
                        {report.ticker}
                      </Link>
                    ) : (
                      <span className={styles.reportTicker}>{report.ticker}</span>
                    )}
                    <span className={styles.reportDate}>
                      {new Date(report.created_at).toLocaleDateString('en-US', { 
                        month: '2-digit', 
                        day: '2-digit', 
                        year: 'numeric' 
                      })}
                    </span>
                  </div>
                  <div className={styles.reportActions}>
                    <span className={`${styles.statusBadge} ${styles[report.status]}`}>
                      {report.status}
                    </span>
                    {report.status === 'completed' && (
                      <div className={styles.dropdown}>
                        <button 
                          className={styles.dropdownButton}
                          onClick={() => setOpenDropdown(openDropdown === report.id ? null : report.id)}
                        >
                          •••
                        </button>
                        {openDropdown === report.id && (
                          <div className={styles.dropdownMenu}>
                            <Link href={`/report/${report.id}`} className={styles.dropdownItem}>
                              View Report
                            </Link>
                            <a href="#" className={styles.dropdownItem} onClick={(e) => { e.preventDefault(); alert('PDF export coming soon!'); }}>
                              Download PDF
                            </a>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      <Footer />
    </div>
  )
}
