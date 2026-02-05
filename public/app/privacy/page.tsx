import Link from 'next/link'
import styles from '../terms/legal.module.css'

export default function PrivacyPage() {
  return (
    <div className={styles.page}>
      <nav className="nav">
        <div className="container">
          <div className="nav-content">
            <Link href="/" className="nav-logo">IncDigest</Link>
            <div className="nav-links">
              <Link href="/blog">Blog</Link>
              <Link href="/pricing">Pricing</Link>
              <Link href="/login">Login</Link>
            </div>
          </div>
        </div>
      </nav>

      <main className={styles.main}>
        <div className="container-narrow">
          <h1>Privacy Policy</h1>
          <p className={styles.lastUpdated}>Last Updated: February 4, 2026</p>

          <div className={styles.content}>
            <p>
              <strong>IncDigest</strong> ("we," "us," "our") is committed to protecting your privacy. This Privacy Policy explains 
              how we collect, use, disclose, and safeguard your information when you use our service at incdigest.com ("Service").
            </p>
            
            <p>
              <strong>By using IncDigest, you agree to the collection and use of information in accordance with this Privacy Policy.</strong>
            </p>

            <h2>1. Information We Collect</h2>
            
            <h3>1.1 Information You Provide</h3>
            <p><strong>Account Information:</strong></p>
            <ul>
              <li>Email address (required for account creation)</li>
              <li>Password (encrypted and hashed)</li>
              <li>Two-factor authentication settings (if enabled)</li>
            </ul>

            <p><strong>Payment Information:</strong></p>
            <ul>
              <li>Processed by Stripe (we do not store credit card details)</li>
              <li>Billing email and payment history</li>
              <li>Token purchase records</li>
            </ul>

            <h3>1.2 Automatically Collected Information</h3>
            <p><strong>Usage Data:</strong></p>
            <ul>
              <li>Ticker symbols searched</li>
              <li>Reports generated (company, date, time)</li>
              <li>Tokens remaining and consumed</li>
              <li>Login timestamps and IP addresses</li>
              <li>Browser type and device information</li>
              <li>Pages visited and features used</li>
            </ul>

            <p><strong>Technical Data:</strong></p>
            <ul>
              <li>Session tokens and authentication cookies</li>
              <li>API request logs</li>
              <li>Error logs and debugging information</li>
            </ul>

            <h3>1.3 Information from Third Parties</h3>
            <p>We receive limited data from:</p>
            <ul>
              <li><strong>Stripe:</strong> Payment confirmation and transaction status</li>
              <li><strong>Supabase:</strong> Authentication and database services</li>
              <li><strong>Railway:</strong> Service logs and performance metrics</li>
            </ul>

            <h2>2. How We Use Your Information</h2>
            <p>We use collected information to:</p>

            <p><strong>Provide the Service:</strong></p>
            <ul>
              <li>Create and manage your account</li>
              <li>Generate AI-powered SEC filing analyses</li>
              <li>Process token purchases and track usage</li>
              <li>Enable two-factor authentication</li>
            </ul>

            <p><strong>Improve the Service:</strong></p>
            <ul>
              <li>Analyze usage patterns to enhance features</li>
              <li>Debug technical issues and errors</li>
              <li>Optimize AI model performance</li>
              <li>Develop new functionality</li>
            </ul>

            <p><strong>Communicate with You:</strong></p>
            <ul>
              <li>Send service-related notifications</li>
              <li>Respond to support inquiries</li>
              <li>Notify of Terms or Privacy Policy changes</li>
              <li>Send account security alerts</li>
            </ul>

            <p><strong>Legal and Security:</strong></p>
            <ul>
              <li>Prevent fraud and abuse</li>
              <li>Enforce our Terms and Conditions</li>
              <li>Comply with legal obligations</li>
              <li>Protect our rights and property</li>
            </ul>

            <h2>3. How We Share Your Information</h2>

            <h3>3.1 Third-Party Service Providers</h3>
            <p>We share data with trusted partners who help operate the Service:</p>

            <p><strong>Stripe (Payment Processing):</strong></p>
            <ul>
              <li>Email address and payment amount</li>
              <li>Purpose: Process token purchases</li>
              <li>Privacy: <a href="https://stripe.com/privacy" target="_blank" rel="noopener">https://stripe.com/privacy</a></li>
            </ul>

            <p><strong>Anthropic (AI Analysis):</strong></p>
            <ul>
              <li>SEC filing text for analysis</li>
              <li>Purpose: Generate report summaries</li>
              <li>Privacy: <a href="https://www.anthropic.com/legal/privacy" target="_blank" rel="noopener">https://www.anthropic.com/legal/privacy</a></li>
              <li>Note: No personal information sent</li>
            </ul>

            <p><strong>Supabase (Database & Auth):</strong></p>
            <ul>
              <li>Account and usage data</li>
              <li>Purpose: Data storage and authentication</li>
              <li>Privacy: <a href="https://supabase.com/privacy" target="_blank" rel="noopener">https://supabase.com/privacy</a></li>
            </ul>

            <p><strong>Railway (Python Functions):</strong></p>
            <ul>
              <li>Report generation requests</li>
              <li>Purpose: Backend processing</li>
              <li>Privacy: <a href="https://railway.app/legal/privacy" target="_blank" rel="noopener">https://railway.app/legal/privacy</a></li>
            </ul>

            <h3>3.2 We Do Not Sell Your Data</h3>
            <p>We do <strong>not</strong> sell, rent, or trade your personal information to third parties for marketing purposes.</p>

            <h3>3.3 Legal Requirements</h3>
            <p>We may disclose information if required by law, legal process, or government request, or to:</p>
            <ul>
              <li>Protect our legal rights</li>
              <li>Prevent fraud or security threats</li>
              <li>Enforce our Terms and Conditions</li>
            </ul>

            <h2>4. Data Retention</h2>
            <p><strong>Account Data:</strong></p>
            <ul>
              <li>Retained while your account is active</li>
              <li>Deleted within 30 days of account deletion (unless legally required to retain)</li>
            </ul>

            <p><strong>Usage Logs:</strong></p>
            <ul>
              <li>Retained for 12 months for service improvement and security</li>
              <li>Older logs automatically deleted</li>
            </ul>

            <p><strong>Generated Reports:</strong></p>
            <ul>
              <li>Cached for 30 days for performance optimization</li>
              <li>Accessible to you while your account is active</li>
              <li>Deleted when account is terminated</li>
            </ul>

            <h2>5. Data Security</h2>
            <p>We implement security measures to protect your information:</p>

            <p><strong>Technical Safeguards:</strong></p>
            <ul>
              <li>Encryption in transit (HTTPS/TLS)</li>
              <li>Encrypted password storage (bcrypt hashing)</li>
              <li>Secure database access controls</li>
              <li>Regular security updates and patches</li>
            </ul>

            <p><strong>Access Controls:</strong></p>
            <ul>
              <li>Limited employee access to data</li>
              <li>Two-factor authentication available</li>
              <li>Session timeout mechanisms</li>
            </ul>

            <p><strong>However:</strong> No method of transmission over the internet is 100% secure. We cannot guarantee absolute security of your data.</p>

            <h2>6. Your Privacy Rights</h2>

            <h3>6.1 Access and Control</h3>
            <p><strong>You have the right to:</strong></p>
            <ul>
              <li>Access your account information via the dashboard</li>
              <li>Update your email or password</li>
              <li>Enable or disable two-factor authentication</li>
              <li>View your report generation history</li>
              <li>Check your token balance and purchases</li>
            </ul>

            <h3>6.2 Data Deletion</h3>
            <p><strong>You can request deletion by:</strong></p>
            <ul>
              <li>Deleting your account through the dashboard</li>
              <li>Contacting support@incdigest.com</li>
            </ul>

            <p><strong>Upon deletion:</strong></p>
            <ul>
              <li>Account information removed within 30 days</li>
              <li>Generated reports deleted</li>
              <li>Payment history retained for legal/tax purposes (up to 7 years)</li>
            </ul>

            <h3>6.3 GDPR Rights (EU/UK Users)</h3>
            <p>If you are in the European Union or United Kingdom, you have additional rights:</p>
            <ul>
              <li><strong>Right to access</strong> your personal data</li>
              <li><strong>Right to rectification</strong> of inaccurate data</li>
              <li><strong>Right to erasure</strong> ("right to be forgotten")</li>
              <li><strong>Right to restrict processing</strong></li>
              <li><strong>Right to data portability</strong></li>
              <li><strong>Right to object</strong> to processing</li>
              <li><strong>Right to withdraw consent</strong></li>
            </ul>
            <p>To exercise these rights, contact: privacy@incdigest.com</p>

            <h2>7. Cookies and Tracking</h2>

            <h3>7.1 Essential Cookies</h3>
            <p>We use cookies necessary for the Service to function:</p>
            <ul>
              <li><strong>Authentication cookies:</strong> Keep you logged in</li>
              <li><strong>Session cookies:</strong> Maintain your session state</li>
              <li><strong>Security cookies:</strong> Prevent fraud and protect your account</li>
            </ul>

            <h3>7.2 Analytics</h3>
            <p>We may use analytics to understand Service usage:</p>
            <ul>
              <li>Pages visited and time spent</li>
              <li>Features used most frequently</li>
              <li>Error rates and performance metrics</li>
            </ul>
            <p><strong>Note:</strong> We do not use third-party advertising cookies or track you across other websites.</p>

            <h3>7.3 Your Cookie Choices</h3>
            <p>You can control cookies through your browser settings. Disabling essential cookies may prevent you from using the Service.</p>

            <h2>8. International Data Transfers</h2>
            <p><strong>Our Service is based in the United Kingdom.</strong> Your data may be transferred to and processed in:</p>
            <ul>
              <li>United Kingdom (Supabase, Railway servers)</li>
              <li>United States (Anthropic, Stripe)</li>
              <li>European Union (backup servers)</li>
            </ul>

            <p>We ensure adequate protection through:</p>
            <ul>
              <li>Standard contractual clauses</li>
              <li>Third-party privacy certifications</li>
              <li>Compliance with GDPR and UK data protection laws</li>
            </ul>

            <h2>9. Children's Privacy</h2>
            <p>
              IncDigest is <strong>not intended for users under 18 years of age.</strong> We do not knowingly collect information from children. 
              If we discover we have collected data from someone under 18, we will delete it immediately.
            </p>
            <p>If you believe a child has provided us with personal information, contact: privacy@incdigest.com</p>

            <h2>10. Third-Party Links</h2>
            <p>
              The Service may contain links to third-party websites (e.g., SEC EDGAR). We are not responsible for the privacy practices 
              of these sites. We encourage you to review their privacy policies.
            </p>

            <h2>11. Changes to This Privacy Policy</h2>
            <p>We may update this Privacy Policy from time to time. Changes will be posted with a new "Last Updated" date at the top of this page.</p>
            
            <p><strong>Material changes will be notified via:</strong></p>
            <ul>
              <li>Email to your registered address</li>
              <li>Prominent notice on the Service</li>
            </ul>
            <p>Continued use after changes constitutes acceptance of the updated Privacy Policy.</p>

            <h2>12. California Privacy Rights (CCPA)</h2>
            <p>If you are a California resident, you have the right to:</p>
            <ul>
              <li>Know what personal information we collect</li>
              <li>Know whether we sell or disclose your information (we do not sell)</li>
              <li>Access your personal information</li>
              <li>Request deletion of your information</li>
              <li>Opt-out of data sales (not applicable, as we don't sell data)</li>
              <li>Non-discrimination for exercising your rights</li>
            </ul>
            <p>To exercise these rights, contact: privacy@incdigest.com</p>

            <h2>13. Contact Us</h2>
            <p>For questions about this Privacy Policy or our privacy practices:</p>
            <ul>
              <li><strong>Email:</strong> privacy@incdigest.com</li>
              <li><strong>Support:</strong> support@incdigest.com</li>
              <li><strong>Website:</strong> https://incdigest.com/contact</li>
            </ul>

            <h2>14. Data Protection Officer</h2>
            <p>For GDPR-related inquiries, you may contact our Data Protection Officer at: dpo@incdigest.com</p>
          </div>

          <div className={styles.footer}>
            <p className="text-secondary text-sm">Last Updated: February 4, 2026</p>
            <p className="text-secondary text-sm">© 2026 IncDigest. All rights reserved.</p>
          </div>
        </div>
      </main>
    </div>
  )
}
