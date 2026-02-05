import Link from 'next/link'
import Footer from '@/components/Footer'
import styles from './blog.module.css'

export const metadata = {
  title: 'Blog - IncDigest',
  description: 'Insights on SEC filings, 10-K analysis, and investor research',
}

// TODO: Replace with database/CMS integration
const posts = [
  {
    slug: 'how-to-read-10k-filings',
    title: 'How to Read 10-K Filings: A Complete Guide',
    excerpt: 'Learn the essential sections of SEC 10-K filings and what investors should focus on.',
    date: '2026-02-01',
    category: 'Education'
  },
  {
    slug: 'ai-analysis-vs-analyst-reports',
    title: 'AI Analysis vs Traditional Analyst Reports',
    excerpt: 'Why AI-powered filing analysis is becoming essential for modern investors.',
    date: '2026-01-28',
    category: 'Technology'
  },
  {
    slug: 'understanding-risk-factors',
    title: 'Understanding Item 1A: Risk Factors That Matter',
    excerpt: 'How to identify material changes in risk disclosures and what they mean for your investment.',
    date: '2026-01-25',
    category: 'Analysis'
  }
]

export default function BlogIndex() {
  return (
    <div className={styles.page}>
      <nav className={styles.nav}>
        <div className="container">
          <div className={styles.navContent}>
            <Link href="/" className={styles.logo}>IncDigest</Link>
            <div className={styles.navLinks}>
              <Link href="/blog">Blog</Link>
              <Link href="/pricing">Pricing</Link>
              <Link href="/login">Login</Link>
              <Link href="/signup" className="button primary">Sign Up</Link>
            </div>
          </div>
        </div>
      </nav>

      <main className="container-narrow">
        <header className={styles.header}>
          <h1>Blog</h1>
          <p className="text-secondary">
            Insights on SEC filings, investment analysis, and financial reporting.
          </p>
        </header>

        <div className={styles.posts}>
          {posts.map((post) => (
            <article key={post.slug} className={styles.post}>
              <div className={styles.postMeta}>
                <span className={styles.category}>{post.category}</span>
                <span className="text-secondary text-sm">{new Date(post.date).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}</span>
              </div>
              <h2>
                <Link href={`/blog/${post.slug}`}>{post.title}</Link>
              </h2>
              <p className="text-secondary">{post.excerpt}</p>
              <Link href={`/blog/${post.slug}`} className={styles.readMore}>
                Read more →
              </Link>
            </article>
          ))}
        </div>
      </main>

      <Footer />
    </div>
  )
}
