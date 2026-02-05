'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { getCurrentUser, signOut, User } from '@/lib/auth'
import { supabase } from '@/lib/supabase'
import Footer from '@/components/Footer'
import styles from './search.module.css'

interface Company {
  ticker: string
  company_name: string
  cik: string
}

export default function SearchPage() {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [companies, setCompanies] = useState<Company[]>([]) // Keep for display only
  const [filteredCompanies, setFilteredCompanies] = useState<Company[]>([])
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null)
  const [agreedToDisclaimer, setAgreedToDisclaimer] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState('')
  const [searching, setSearching] = useState(false)

  useEffect(() => {
    loadUser()
  }, [])

  async function loadUser() {
    try {
      const currentUser = await getCurrentUser()
      if (!currentUser) {
        router.push('/login')
        return
      }
      setUser(currentUser)
    } catch (error) {
      router.push('/login')
    } finally {
      setLoading(false)
    }
  }

  // Search companies via Edge Function (server-side)
  useEffect(() => {
    const searchCompanies = async () => {
      if (searchQuery.length < 1) {
        setFilteredCompanies([])
        return
      }

      setSearching(true)
      
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_SUPABASE_URL}/functions/v1/search-companies`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY}`,
            },
            body: JSON.stringify({ query: searchQuery }),
          }
        )

        const data = await response.json()
        console.log('Search results:', data.results?.length || 0)
        setFilteredCompanies(data.results || [])
      } catch (err) {
        console.error('Search error:', err)
        setFilteredCompanies([])
      } finally {
        setSearching(false)
      }
    }

    // Debounce search
    const timer = setTimeout(searchCompanies, 150)
    return () => clearTimeout(timer)
  }, [searchQuery])

  function selectCompany(company: Company) {
    setSelectedCompany(company)
    setSearchQuery('')
    setFilteredCompanies([])
    setError('')
  }

  async function handleGenerateReport() {
    if (!selectedCompany || !user) return
    
    if (!agreedToDisclaimer) {
      setError('You must acknowledge the disclaimer before generating a report')
      return
    }

    if (user.tokens_remaining < 1) {
      setError('Insufficient tokens. Please purchase more tokens to generate reports.')
      return
    }

    setGenerating(true)
    setError('')

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_SUPABASE_URL}/functions/v1/generate-report`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY}`,
          },
          body: JSON.stringify({
            ticker: selectedCompany.ticker,
            user_id: user.id,
          }),
        }
      )

      console.log('Response status:', response.status)
      const responseText = await response.text()
      console.log('Response body:', responseText)

      if (!response.ok) {
        let errorData
        try {
          errorData = JSON.parse(responseText)
        } catch {
          errorData = { error: responseText }
        }
        throw new Error(errorData.error || `Server error: ${response.status}`)
      }

      const result = JSON.parse(responseText)
      
      // If we got a report_id (cached report), redirect immediately
      if (result.report_id) {
        router.push(`/report/${result.report_id}`)
      } else {
        // New report being generated - show message
        setError('')
        alert(`Report generation started for ${selectedCompany.ticker}. This will take 30-60 seconds. Check your dashboard for the completed report.`)
        router.push('/dashboard')
      }
    } catch (err: any) {
      setError(err.message || 'Failed to generate report. Please try again.')
      setGenerating(false)
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

  if (!user) {
    return null
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
        <div className={styles.header}>
          <h1>Generate Report</h1>
          <p className="text-secondary">
            Search for a company ticker to analyze their latest 10-K filing
          </p>
          <div className={styles.tokenBadge}>
            {user.tokens_remaining} {user.tokens_remaining === 1 ? 'token' : 'tokens'} remaining
          </div>
        </div>

        <div className={styles.searchSection}>
          <div className={styles.searchBox}>
            <input
              type="text"
              placeholder="Search by ticker or company name (e.g., AAPL, Apple)"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              disabled={generating}
            />
            
            {filteredCompanies.length > 0 && (
              <div className={styles.dropdown}>
                {filteredCompanies.map((company) => (
                  <div
                    key={company.ticker}
                    className={styles.dropdownItem}
                    onClick={() => selectCompany(company)}
                  >
                    <strong>{company.ticker}</strong> - {company.company_name}
                  </div>
                ))}
              </div>
            )}
          </div>

          {selectedCompany && (
            <div className={styles.selectedCompany}>
              <h2>{selectedCompany.ticker}</h2>
              <p className="text-secondary">{selectedCompany.company_name}</p>
              <button
                onClick={() => {
                  setSelectedCompany(null)
                  setAgreedToDisclaimer(false)
                  setError('')
                }}
                className="button"
                disabled={generating}
              >
                Change Company
              </button>
            </div>
          )}
        </div>

        {selectedCompany && (
          <>
            <div className={styles.disclaimer}>
              <h3>⚠️ Important Disclaimer</h3>
              <p>
                This report will be generated by artificial intelligence and is for <strong>informational purposes only</strong>. 
                It is <strong>not investment advice</strong>. The AI analysis may contain errors, omissions, or inaccuracies. 
                You are solely responsible for verifying all information and making your own investment decisions. 
                Consult qualified professionals before investing.
              </p>
              
              <label className={styles.checkboxLabel}>
                <input
                  type="checkbox"
                  checked={agreedToDisclaimer}
                  onChange={(e) => setAgreedToDisclaimer(e.target.checked)}
                  disabled={generating}
                />
                <span>
                  I understand this is AI-generated analysis, not investment advice, and may contain errors. 
                  I am solely responsible for my investment decisions.
                </span>
              </label>
            </div>

            {error && (
              <div className={styles.error}>
                {error}
              </div>
            )}

            <div className={styles.actions}>
              <button
                onClick={handleGenerateReport}
                className="button primary"
                disabled={!agreedToDisclaimer || generating}
                style={{ width: '100%', padding: 'var(--spacing-md) var(--spacing-xl)' }}
              >
                {generating ? (
                  <>
                    <span className={styles.spinner}></span>
                    Generating Report...
                  </>
                ) : (
                  `Generate Report (1 token)`
                )}
              </button>
              
              <p className="text-secondary text-sm text-center">
                This will cost 1 token. Report typically takes 30-60 seconds to generate.
              </p>
            </div>
          </>
        )}
      </main>

      <Footer />
    </div>
  )
}
