'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { signIn } from '@/lib/auth'
import { supabase } from '@/lib/supabase'
import styles from './auth.module.css'

export default function Login() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    console.log('Login attempt:', email)
    setError('')
    setLoading(true)
    
    try {
      console.log('Calling signIn...')
      await signIn(email, password)
      console.log('SignIn successful, redirecting...')
      
      // Check if session exists
      const { data: { session } } = await supabase.auth.getSession()
      console.log('Session after login:', session)
      
      // Use window.location for full page reload to trigger middleware
      window.location.href = '/dashboard'
    } catch (err: any) {
      console.error('Login error:', err)
      setError(err.message || 'Invalid email or password')
      setLoading(false)
    }
  }

  return (
    <div className={styles.page}>
      <nav className={styles.nav}>
        <div className="container">
          <div className={styles.navContent}>
            <Link href="/" className={styles.logo}>IncDigest</Link>
            <div className={styles.navLinks}>
              <Link href="/blog">Blog</Link>
              <Link href="/pricing">Pricing</Link>
              <Link href="/signup" className="button primary">Sign Up</Link>
            </div>
          </div>
        </div>
      </nav>

      <main className={styles.main}>
        <div className={styles.authCard}>
          <h1>Welcome Back</h1>
          <p className="text-secondary mb-3">
            Log in to your account
          </p>

          {error && (
            <div className={styles.error}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className={styles.formGroup}>
              <label htmlFor="email">Email</label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={loading}
                autoComplete="email"
              />
            </div>

            <div className={styles.formGroup}>
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={loading}
                autoComplete="current-password"
              />
            </div>

            <button 
              type="submit" 
              className="button primary" 
              disabled={loading}
              style={{ width: '100%' }}
            >
              {loading ? 'Logging in...' : 'Log In'}
            </button>
          </form>

          <p className={styles.authFooter}>
            Don't have an account? <Link href="/signup">Sign up</Link>
          </p>
        </div>
      </main>
    </div>
  )
}
