'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { getCurrentUser, signOut, getTwoFactorStatus, setupTwoFactor, verifyTwoFactor, User } from '@/lib/auth'
import { supabase } from '@/lib/supabase'
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
  const [twoFactorEnabled, setTwoFactorEnabled] = useState(false)
  const [showTwoFactorSetup, setShowTwoFactorSetup] = useState(false)
  const [qrCode, setQrCode] = useState('')
  const [factorId, setFactorId] = useState('')
  const [verifyCode, setVerifyCode] = useState('')

  useEffect(() => {
    checkAuth()
  }, [])

  async function checkAuth() {
    try {
      const currentUser = await getCurrentUser()
      if (!currentUser) {
        router.push('/login')
        return
      }
      
      setUser(currentUser)
      
      // Check 2FA status
      const factors = await getTwoFactorStatus()
      const hasTotp = factors?.totp?.some((f: any) => f.status === 'verified')
      setTwoFactorEnabled(!!hasTotp)
      
      // Load reports
      const { data: reportsData } = await supabase
        .from('reports')
        .select('*')
        .eq('user_id', currentUser.id)
        .order('created_at', { ascending: false })
        .limit(10)
      
      if (reportsData) setReports(reportsData)
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

  async function handleSetupTwoFactor() {
    try {
      const { id, totp } = await setupTwoFactor()
      setFactorId(id)
      setQrCode(totp.qr_code)
      setShowTwoFactorSetup(true)
    } catch (error: any) {
      alert('Failed to setup 2FA: ' + error.message)
    }
  }

  async function handleVerifyTwoFactor() {
    try {
      await verifyTwoFactor(factorId, verifyCode)
      setTwoFactorEnabled(true)
      setShowTwoFactorSetup(false)
      alert('Two-factor authentication enabled successfully!')
    } catch (error: any) {
      alert('Invalid code. Please try again.')
    }
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
          {/* Security Section */}
          <div className="card">
            <h2>Security</h2>
            {twoFactorEnabled ? (
              <div className={styles.securityEnabled}>
                <span className={styles.checkmark}>✓</span> Two-factor authentication enabled
              </div>
            ) : (
              <>
                <p className="text-secondary mb-2">
                  Protect your account with two-factor authentication.
                </p>
                <button 
                  onClick={handleSetupTwoFactor}
                  className="button"
                >
                  Enable 2FA
                </button>
              </>
            )}
          </div>

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
                  <div>
                    <strong>{report.ticker}</strong>
                    <span className="text-secondary text-sm ml-1">
                      {new Date(report.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <div className={styles.reportStatus}>
                    <span className={`${styles.statusBadge} ${styles[report.status]}`}>
                      {report.status}
                    </span>
                    {report.status === 'completed' && (
                      <Link href={`/report/${report.id}`} className="button">
                        View
                      </Link>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      {/* 2FA Setup Modal */}
      {showTwoFactorSetup && (
        <div className={styles.modal}>
          <div className={styles.modalContent}>
            <h2>Setup Two-Factor Authentication</h2>
            <p className="text-secondary mb-3">
              Scan this QR code with your authenticator app (Google Authenticator, Authy, etc.)
            </p>
            
            <div className={styles.qrCode}>
              <img src={qrCode} alt="2FA QR Code" />
            </div>
            
            <div className="mt-3">
              <label htmlFor="verifyCode">Enter 6-digit code</label>
              <input
                id="verifyCode"
                type="text"
                maxLength={6}
                value={verifyCode}
                onChange={(e) => setVerifyCode(e.target.value.replace(/\D/g, ''))}
                placeholder="000000"
              />
            </div>
            
            <div className={styles.modalButtons}>
              <button 
                onClick={() => setShowTwoFactorSetup(false)}
                className="button"
              >
                Cancel
              </button>
              <button 
                onClick={handleVerifyTwoFactor}
                className="button primary"
                disabled={verifyCode.length !== 6}
              >
                Verify & Enable
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
