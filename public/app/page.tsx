import Link from 'next/link'
import styles from './page.module.css'

export default function Home() {
  return (
    <div className={styles.page}>
      <nav className={styles.nav}>
        <div className="container">
          <div className={styles.navContent}>
            <h1 className={styles.logo}>IncDigest</h1>
            <div className={styles.navLinks}>
              <Link href="/blog">Blog</Link>
              <Link href="/pricing">Pricing</Link>
              <Link href="/login">Login</Link>
              <Link href="/signup" className="button primary">Sign Up</Link>
            </div>
          </div>
        </div>
      </nav>

      <main>
        <section className={styles.hero}>
          <div className="container-narrow">
            <h1 className={styles.heroTitle}>
              AI-Powered 10-K Analysis for Investors
            </h1>
            <p className={styles.heroSubtitle}>
              Automated summaries of material changes between annual SEC filings. 
              Focus on what matters, skip the noise.
            </p>
            <div className={styles.heroCta}>
              <Link href="/signup" className="button primary">
                Get Started
              </Link>
              <Link href="/demo" className="button">
                View Demo Report
              </Link>
            </div>
          </div>
        </section>

        <section className={styles.features}>
          <div className="container">
            <div className={styles.featureGrid}>
              <div className={styles.feature}>
                <h3>Material Changes Only</h3>
                <p className="text-secondary">
                  Our AI identifies and summarizes substantive changes in Items 1, 1A, 7, and 8. 
                  Ignores formatting, page numbers, and routine updates.
                </p>
              </div>
              <div className={styles.feature}>
                <h3>10,300+ Companies</h3>
                <p className="text-secondary">
                  Coverage of all SEC-registered U.S. companies. 
                  Particularly valuable for micro-caps lacking analyst coverage.
                </p>
              </div>
              <div className={styles.feature}>
                <h3>Bloomberg-Grade Quality</h3>
                <p className="text-secondary">
                  Powered by Claude Sonnet 4. Professional-grade analysis 
                  that focuses on investor-relevant information.
                </p>
              </div>
              <div className={styles.feature}>
                <h3>Token-Based Pricing</h3>
                <p className="text-secondary">
                  Pay only for what you use. $1 per report. 
                  No subscriptions, no hidden fees.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section className={styles.cta}>
          <div className="container-narrow text-center">
            <h2>Ready to streamline your research?</h2>
            <p className="text-secondary">
              Start analyzing 10-Ks in seconds.
            </p>
            <Link href="/signup" className="button primary">
              Create Free Account
            </Link>
          </div>
        </section>
      </main>

      <footer className={styles.footer}>
        <div className="container">
          <div className={styles.footerDisclaimer}>
            <p className="text-secondary text-sm">
              <strong>Disclaimer:</strong> IncDigest provides AI-generated analysis of SEC filings for informational purposes only. 
              This is not investment, financial, legal, or tax advice. All reports may contain errors or inaccuracies. 
              You are solely responsible for verifying information and making investment decisions. Consult qualified professionals before investing. 
              Past performance does not guarantee future results.
            </p>
          </div>
          <div className={styles.footerContent}>
            <p className="text-secondary text-sm">
              © 2026 IncDigest. All rights reserved.
            </p>
            <div className={styles.footerLinks}>
              <Link href="/terms" className="text-secondary text-sm">Terms & Conditions</Link>
              <Link href="/privacy" className="text-secondary text-sm">Privacy Policy</Link>
              <Link href="/contact" className="text-secondary text-sm">Contact</Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
