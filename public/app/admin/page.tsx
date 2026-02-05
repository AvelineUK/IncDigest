'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { getCurrentUser, signOut, User } from '@/lib/auth'
import { supabase } from '@/lib/supabase'
import Footer from '@/components/Footer'
import styles from './admin.module.css'

interface SystemStats {
  totalUsers: number
  totalReports: number
  successfulReports: number
  failedReports: number
  pendingReports: number
  totalRevenue: number
  totalTokensIssued: number
  totalTokensRemaining: number
}

interface RecentReport {
  id: string
  ticker: string
  status: string
  created_at: string
  completed_at: string | null
  user_email: string
}

interface UserData {
  id: string
  email: string
  tokens_remaining: number
  total_reports: number
  successful_reports: number
  refunded_reports: number
  total_spent_usd: number
  last_report_date: string | null
}

export default function AdminDashboard() {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<SystemStats | null>(null)
  const [recentReports, setRecentReports] = useState<RecentReport[]>([])
  const [allUsers, setAllUsers] = useState<UserData[]>([])
  const [syncLoading, setSyncLoading] = useState(false)
  const [syncMessage, setSyncMessage] = useState('')
  const [activeTab, setActiveTab] = useState<'overview' | 'reports' | 'users'>('overview')

  useEffect(() => {
    checkAuth()
  }, [])

  async function checkAuth() {
    try {
      const currentUser = await getCurrentUser()
      if (!currentUser || !currentUser.is_admin) {
        router.push('/dashboard')
        return
      }
      
      setUser(currentUser)
      await loadDashboardData()
    } catch (error) {
      console.error('Auth check failed:', error)
      router.push('/login')
    } finally {
      setLoading(false)
    }
  }

  async function loadDashboardData() {
    // Load system stats
    const { data: profiles } = await supabase
      .from('profiles')
      .select('tokens_remaining, subscription_tier')

    const { data: reports } = await supabase
      .from('reports')
      .select('extraction_success, refunded')

    if (profiles && reports) {
      const totalUsers = profiles.length
      const totalReports = reports.length
      const successfulReports = reports.filter(r => r.extraction_success === true && r.refunded === false).length
      const failedReports = reports.filter(r => r.extraction_success === false).length
      const refundedReports = reports.filter(r => r.refunded === true).length
      const pendingReports = 0 // Your schema doesn't have pending status
      
      // Calculate revenue from user_stats if available, otherwise estimate
      const totalRevenue = 0 // TODO: get from user_stats or token_transactions
      const totalTokensRemaining = profiles.reduce((sum, p) => sum + (p.tokens_remaining || 0), 0)
      
      // Estimate tokens issued (rough calculation)
      const totalTokensIssued = totalTokensRemaining + totalReports

      setStats({
        totalUsers,
        totalReports,
        successfulReports,
        failedReports,
        pendingReports: refundedReports, // Use refunded as a proxy
        totalRevenue,
        totalTokensIssued,
        totalTokensRemaining
      })
    }

    // Load recent reports with user emails
    const { data: recentReportsData, error: reportsError } = await supabase
      .from('reports')
      .select(`
        id,
        ticker,
        company_name,
        extraction_success,
        refunded,
        created_at,
        generation_time_seconds,
        profiles!inner(email)
      `)
      .order('created_at', { ascending: false })
      .limit(20)

    if (reportsError) {
      console.error('Reports query error:', reportsError)
    }

    if (recentReportsData) {
      setRecentReports(recentReportsData.map((r: any) => ({
        id: r.id,
        ticker: r.ticker,
        status: r.refunded ? 'refunded' : (r.extraction_success ? 'completed' : 'failed'),
        created_at: r.created_at,
        completed_at: r.created_at, // No separate completion time in your schema
        user_email: r.profiles.email
      })))
    }

    // Load all users
    const { data: usersData } = await supabase
      .from('profiles')
      .select('id, email, tokens_remaining, subscription_tier')
      .order('tokens_remaining', { ascending: false })

    if (usersData) {
      // Map to include placeholder stats
      setAllUsers(usersData.map((u: any) => ({
        ...u,
        total_reports: 0,
        successful_reports: 0,
        refunded_reports: 0,
        total_spent_usd: 0,
        last_report_date: null
      })))
    }
  }

  async function handleSyncTickers() {
    setSyncLoading(true)
    setSyncMessage('')
    
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_SUPABASE_URL}/functions/v1/sync-tickers`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY}`,
          },
        }
      )
      
      if (!response.ok) throw new Error('Sync failed')
      
      const result = await response.json()
      setSyncMessage(`✓ Synced ${result.count} companies successfully!`)
      
      // Reload data
      await loadDashboardData()
    } catch (error) {
      setSyncMessage('✗ Sync failed. Please try again.')
    } finally {
      setSyncLoading(false)
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
          Verifying admin access...
        </div>
      </div>
    )
  }

  if (!user || !user.is_admin) {
    return null // Middleware will redirect, show nothing
  }

  return (
    <div className={styles.page}>
      <nav className={`nav ${styles.nav}`}>
        <div className="container">
          <div className="nav-content">
            <Link href="/" className="nav-logo">IncDigest Admin</Link>
            <div className="nav-links">
              <Link href="/dashboard">User Dashboard</Link>
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
            <h1>Admin Dashboard</h1>
            <p className="text-secondary">{user?.email}</p>
          </div>
        </div>

        {/* Tabs */}
        <div className={styles.tabs}>
          <button 
            className={activeTab === 'overview' ? styles.tabActive : styles.tab}
            onClick={() => setActiveTab('overview')}
          >
            Overview
          </button>
          <button 
            className={activeTab === 'reports' ? styles.tabActive : styles.tab}
            onClick={() => setActiveTab('reports')}
          >
            Reports
          </button>
          <button 
            className={activeTab === 'users' ? styles.tabActive : styles.tab}
            onClick={() => setActiveTab('users')}
          >
            Users
          </button>
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && stats && (
          <>
            <div className={styles.statsGrid}>
              <div className="card">
                <h3 className="text-secondary text-sm">Total Users</h3>
                <p className={styles.statNumber}>{stats.totalUsers}</p>
              </div>
              <div className="card">
                <h3 className="text-secondary text-sm">Total Reports</h3>
                <p className={styles.statNumber}>{stats.totalReports}</p>
              </div>
              <div className="card">
                <h3 className="text-secondary text-sm">Success Rate</h3>
                <p className={styles.statNumber}>
                  {stats.totalReports > 0 
                    ? Math.round((stats.successfulReports / stats.totalReports) * 100)
                    : 0}%
                </p>
              </div>
              <div className="card">
                <h3 className="text-secondary text-sm">Total Revenue</h3>
                <p className={styles.statNumber}>${stats.totalRevenue.toFixed(2)}</p>
              </div>
              <div className="card">
                <h3 className="text-secondary text-sm">Tokens Remaining</h3>
                <p className={styles.statNumber}>{stats.totalTokensRemaining}</p>
              </div>
              <div className="card">
                <h3 className="text-secondary text-sm">Pending Reports</h3>
                <p className={styles.statNumber}>{stats.pendingReports}</p>
              </div>
            </div>

            {/* Admin Actions */}
            <div className="card" style={{ marginTop: 'var(--spacing-xl)' }}>
              <h2>System Actions</h2>
              <div className={styles.actionButtons}>
                <button 
                  onClick={handleSyncTickers}
                  className="button primary"
                  disabled={syncLoading}
                >
                  {syncLoading ? 'Syncing...' : 'Sync Company Tickers'}
                </button>
                <button 
                  onClick={loadDashboardData}
                  className="button"
                >
                  Refresh Data
                </button>
              </div>
              {syncMessage && (
                <p className={`text-sm mt-2 ${syncMessage.includes('✗') ? 'text-secondary' : ''}`}>
                  {syncMessage}
                </p>
              )}
            </div>
          </>
        )}

        {/* Reports Tab */}
        {activeTab === 'reports' && (
          <div className={styles.tableCard}>
            <h2>Recent Reports</h2>
            <div className={styles.tableWrapper}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>Ticker</th>
                    <th>User</th>
                    <th>Status</th>
                    <th>Created</th>
                    <th>Completed</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {recentReports.map((report) => (
                    <tr key={report.id}>
                      <td><strong>{report.ticker}</strong></td>
                      <td className="text-secondary text-sm">{report.user_email}</td>
                      <td>
                        <span className={`${styles.statusBadge} ${styles[report.status]}`}>
                          {report.status}
                        </span>
                      </td>
                      <td className="text-secondary text-sm">
                        {new Date(report.created_at).toLocaleString()}
                      </td>
                      <td className="text-secondary text-sm">
                        {report.completed_at 
                          ? new Date(report.completed_at).toLocaleString()
                          : '-'
                        }
                      </td>
                      <td>
                        {report.status === 'completed' && (
                          <Link href={`/report/${report.id}`} className="button">
                            View
                          </Link>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Users Tab */}
        {activeTab === 'users' && (
          <div className={styles.tableCard}>
            <h2>All Users</h2>
            <div className={styles.tableWrapper}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>Email</th>
                    <th>Tokens</th>
                    <th>Reports</th>
                    <th>Success</th>
                    <th>Refunded</th>
                    <th>Spent</th>
                    <th>Last Activity</th>
                  </tr>
                </thead>
                <tbody>
                  {allUsers.map((u) => (
                    <tr key={u.id}>
                      <td>{u.email}</td>
                      <td>{u.tokens_remaining}</td>
                      <td>{u.total_reports}</td>
                      <td>{u.successful_reports}</td>
                      <td>{u.refunded_reports}</td>
                      <td>${Number(u.total_spent_usd || 0).toFixed(2)}</td>
                      <td className="text-secondary text-sm">
                        {u.last_report_date 
                          ? new Date(u.last_report_date).toLocaleDateString()
                          : 'Never'
                        }
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>

      <Footer />
    </div>
  )
}
