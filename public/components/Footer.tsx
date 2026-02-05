import Link from 'next/link'
import styles from './footer.module.css'

export default function Footer() {
  return (
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
  )
}
