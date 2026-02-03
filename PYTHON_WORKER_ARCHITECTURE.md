# ============================================================================
# SEC 10-K Analysis Platform - Python Worker Architecture
# ============================================================================
# Version: 1.0
# Purpose: Process report generation jobs
# Hosting: Railway or Render
# ============================================================================

## OVERVIEW

The Python Worker is a separate service that:
1. Receives report generation requests from Supabase Edge Functions
2. Runs the SEC extraction and AI analysis scripts
3. Writes results back to Supabase database
4. Calls back to notify completion

## ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────┐
│                     PYTHON WORKER SERVICE                    │
│                                                              │
│  ┌────────────────┐                                         │
│  │   Flask API    │  ← Receives jobs via HTTP               │
│  │   (Port 8000)  │                                         │
│  └────────┬───────┘                                         │
│           │                                                  │
│           ▼                                                  │
│  ┌─────────────────────────────────────────┐                │
│  │         Job Queue (in-memory)           │                │
│  │         - Pending jobs                  │                │
│  │         - Processing status             │                │
│  └─────────────────────────────────────────┘                │
│           │                                                  │
│           ▼                                                  │
│  ┌─────────────────────────────────────────┐                │
│  │         Worker Process                  │                │
│  │  ┌──────────────────────────────────┐   │                │
│  │  │  1. SEC Fetcher                  │   │                │
│  │  │     - Fetch 10-K HTML            │   │                │
│  │  │     - Extract sections           │   │                │
│  │  │     - Validate quality           │   │                │
│  │  └──────────────────────────────────┘   │                │
│  │  ┌──────────────────────────────────┐   │                │
│  │  │  2. Diff Analyzer                │   │                │
│  │  │     - Compare sections           │   │                │
│  │  │     - Identify changes           │   │                │
│  │  └──────────────────────────────────┘   │                │
│  │  ┌──────────────────────────────────┐   │                │
│  │  │  3. AI Analyzer                  │   │                │
│  │  │     - Generate summaries         │   │                │
│  │  │     - Call Claude API            │   │                │
│  │  └──────────────────────────────────┘   │                │
│  │  ┌──────────────────────────────────┐   │                │
│  │  │  4. Quality Validator            │   │                │
│  │  │     - Check section lengths      │   │                │
│  │  │     - Detect issues              │   │                │
│  │  │     - Determine if refund needed │   │                │
│  │  └──────────────────────────────────┘   │                │
│  └─────────────────────────────────────────┘                │
│           │                                                  │
│           ▼                                                  │
│  ┌─────────────────────────────────────────┐                │
│  │     Supabase Database Writer            │                │
│  │     - Insert report record              │                │
│  │     - Create refund transaction if bad  │                │
│  │     - Create error log if failed        │                │
│  └─────────────────────────────────────────┘                │
│           │                                                  │
│           ▼                                                  │
│  ┌─────────────────────────────────────────┐                │
│  │     Callback Handler                    │                │
│  │     - Notify Edge Function job complete │                │
│  └─────────────────────────────────────────┘                │
└──────────────────────────────────────────────────────────────┘
```

## ============================================================================
## FILE STRUCTURE
## ============================================================================

```
python-worker/
├── requirements.txt
├── Dockerfile
├── railway.json (or render.yaml)
├── .env.example
├── README.md
│
├── app.py                      # Flask API server
├── worker.py                   # Job processing logic
├── quality_validator.py        # Quality checking
├── database.py                 # Supabase client
│
├── sec_fetcher.py              # (We already have this)
├── diff_analyzer.py            # (We already have this)
├── ai_analyzer.py              # (We already have this)
├── local_cache.py              # (We already have this - optional)
│
└── tests/
    ├── test_worker.py
    └── test_quality_validator.py
```

## ============================================================================
## CORE COMPONENTS
## ============================================================================

### 1. app.py - Flask API Server
```python
from flask import Flask, request, jsonify
import threading
from worker import process_job
import os

app = Flask(__name__)

# In-memory job tracking
jobs = {}  # job_id -> {status, progress, etc.}

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'python-worker',
        'version': '1.0.0'
    })

@app.route('/generate-report', methods=['POST'])
def generate_report():
    """
    Receive job from Supabase Edge Function
    
    Expected body:
    {
        "job_id": "uuid",
        "user_id": "uuid",
        "ticker": "AAPL",
        "callback_url": "https://..."
    }
    """
    data = request.json
    
    job_id = data['job_id']
    user_id = data['user_id']
    ticker = data['ticker']
    callback_url = data['callback_url']
    
    # Add to job queue
    jobs[job_id] = {
        'status': 'queued',
        'progress': 0,
        'ticker': ticker
    }
    
    # Process in background thread
    thread = threading.Thread(
        target=process_job,
        args=(job_id, user_id, ticker, callback_url, jobs)
    )
    thread.start()
    
    return jsonify({
        'job_id': job_id,
        'status': 'queued',
        'message': 'Job queued for processing'
    }), 202

@app.route('/jobs/<job_id>/status', methods=['GET'])
def job_status(job_id):
    """Get job status (optional - for debugging)"""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(jobs[job_id])

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
```

### 2. worker.py - Job Processing Logic
```python
import traceback
from datetime import datetime
from sec_fetcher import SECFetcher
from diff_analyzer import DiffAnalyzer
from ai_analyzer import AIAnalyzer
from quality_validator import QualityValidator
from database import SupabaseClient
import requests

def process_job(job_id, user_id, ticker, callback_url, jobs):
    """
    Main job processing function
    Runs in background thread
    """
    db = SupabaseClient()
    
    try:
        # Update status
        jobs[job_id] = {'status': 'processing', 'progress': 10, 'ticker': ticker}
        
        # Step 1: Fetch and extract sections
        print(f"[{job_id}] Fetching 10-K data for {ticker}")
        fetcher = SECFetcher()
        filings = fetcher.get_10k_sections(ticker)
        
        if len(filings) < 2:
            raise Exception(f"Need 2 filings, found {len(filings)}")
        
        jobs[job_id]['progress'] = 30
        
        # Step 2: Run diff analysis
        print(f"[{job_id}] Performing diff analysis")
        diff_analyzer = DiffAnalyzer()
        diff_results = diff_analyzer.compare_sections(
            old_sections=filings[1]['sections'],
            new_sections=filings[0]['sections']
        )
        
        jobs[job_id]['progress'] = 50
        
        # Step 3: Generate AI summaries
        print(f"[{job_id}] Generating AI summaries")
        ai_analyzer = AIAnalyzer()
        ai_results = ai_analyzer.analyze_all_sections(
            ticker=ticker,
            company_name=filings[0]['company_name'],
            old_filing_date=filings[1]['filing_date'],
            new_filing_date=filings[0]['filing_date'],
            diff_results=diff_results
        )
        
        jobs[job_id]['progress'] = 80
        
        # Step 4: Validate quality
        print(f"[{job_id}] Validating quality")
        validator = QualityValidator()
        quality_result = validator.validate_extraction(
            filings=filings,
            diff_results=diff_results,
            ai_results=ai_results
        )
        
        jobs[job_id]['progress'] = 90
        
        # Step 5: Write to database
        print(f"[{job_id}] Writing to database")
        report_id = db.create_report(
            user_id=user_id,
            ticker=ticker,
            company_name=filings[0]['company_name'],
            newer_filing_date=filings[0]['filing_date'],
            older_filing_date=filings[1]['filing_date'],
            newer_accession=filings[0]['accession'],
            older_accession=filings[1]['accession'],
            sections_extracted=filings[0]['sections'].keys(),
            extraction_issues=quality_result['issues'],
            extraction_success=quality_result['is_valid'],
            ai_summaries=ai_results['summaries'],
            ai_cost_usd=ai_results['total_cost_usd'],
            total_tokens_consumed=ai_results['total_tokens'],
            generation_time_seconds=int((datetime.now() - datetime.fromisoformat(jobs[job_id].get('start_time', datetime.now().isoformat()))).total_seconds())
        )
        
        # Step 6: Handle refund if quality issues
        if not quality_result['is_valid']:
            print(f"[{job_id}] Quality issues detected, issuing refund")
            db.create_token_refund(
                user_id=user_id,
                report_id=report_id,
                reason=f"Quality issues: {', '.join(quality_result['issues'])}"
            )
        
        jobs[job_id]['progress'] = 100
        jobs[job_id]['status'] = 'completed'
        
        # Step 7: Callback to Edge Function
        print(f"[{job_id}] Notifying completion")
        requests.post(callback_url, json={
            'job_id': job_id,
            'status': 'completed',
            'report_id': report_id
        }, timeout=10)
        
    except Exception as e:
        print(f"[{job_id}] Error: {e}")
        traceback.print_exc()
        
        jobs[job_id]['status'] = 'failed'
        jobs[job_id]['error'] = str(e)
        
        # Log error to database
        error_log_id = db.create_error_log(
            user_id=user_id,
            ticker=ticker,
            error_type='extraction_failed',
            error_message=str(e),
            stack_trace=traceback.format_exc()
        )
        
        # Callback with failure
        try:
            requests.post(callback_url, json={
                'job_id': job_id,
                'status': 'failed',
                'error': str(e),
                'error_log_id': error_log_id
            }, timeout=10)
        except:
            pass  # Don't fail if callback fails
```

### 3. quality_validator.py - Quality Checking
```python
class QualityValidator:
    """Validates extraction quality to determine if refund needed"""
    
    def __init__(self):
        # Minimum word counts for each section
        self.min_word_counts = {
            'Item 1': 1000,
            'Item 1A': 5000,
            'Item 7': 5000,
            'Item 8': 10000
        }
    
    def validate_extraction(self, filings, diff_results, ai_results):
        """
        Check if extraction meets quality standards
        
        Returns:
        {
            'is_valid': bool,
            'issues': [list of issue descriptions]
        }
        """
        issues = []
        
        # Check 1: All required sections present
        required_sections = ['Item 1', 'Item 1A', 'Item 7', 'Item 8']
        
        for filing in filings:
            missing = [s for s in required_sections if s not in filing['sections']]
            if missing:
                issues.append(f"Missing sections: {', '.join(missing)}")
        
        # Check 2: Minimum content length
        for filing in filings:
            for section_name, content in filing['sections'].items():
                if section_name in self.min_word_counts:
                    word_count = len(content.split())
                    min_words = self.min_word_counts[section_name]
                    
                    if word_count < min_words:
                        issues.append(
                            f"{section_name}: Content too short "
                            f"({word_count} words, expected {min_words}+)"
                        )
        
        # Check 3: Content quality (not all numbers/tables)
        for filing in filings:
            for section_name, content in filing['sections'].items():
                words = content.split()
                if len(words) > 0:
                    number_words = sum(1 for w in words if any(c.isdigit() for c in w))
                    if number_words / len(words) > 0.8:
                        issues.append(
                            f"{section_name}: Appears to be mostly tables/numbers "
                            f"(may indicate extraction error)"
                        )
        
        # Check 4: AI summaries generated
        if not ai_results.get('summaries'):
            issues.append("No AI summaries generated")
        
        return {
            'is_valid': len(issues) == 0,
            'issues': issues
        }
```

### 4. database.py - Supabase Client
```python
from supabase import create_client, Client
import os
from datetime import datetime

class SupabaseClient:
    """Client for writing to Supabase database"""
    
    def __init__(self):
        url = os.environ.get('SUPABASE_URL')
        key = os.environ.get('SUPABASE_SERVICE_KEY')  # Service key, not anon key
        self.client: Client = create_client(url, key)
    
    def create_report(self, user_id, ticker, company_name, newer_filing_date,
                      older_filing_date, newer_accession, older_accession,
                      sections_extracted, extraction_issues, extraction_success,
                      ai_summaries, ai_cost_usd, total_tokens_consumed,
                      generation_time_seconds):
        """Insert report into database"""
        
        data = {
            'user_id': user_id,
            'ticker': ticker,
            'company_name': company_name,
            'newer_filing_date': newer_filing_date.isoformat(),
            'older_filing_date': older_filing_date.isoformat(),
            'newer_accession': newer_accession,
            'older_accession': older_accession,
            'sections_extracted': list(sections_extracted),
            'extraction_issues': extraction_issues,
            'extraction_success': extraction_success,
            'ai_summaries': ai_summaries,
            'ai_cost_usd': ai_cost_usd,
            'total_tokens_consumed': total_tokens_consumed,
            'tokens_used': 1,
            'refunded': False,
            'generation_time_seconds': generation_time_seconds
        }
        
        result = self.client.table('reports').insert(data).execute()
        return result.data[0]['id']
    
    def create_token_refund(self, user_id, report_id, reason):
        """Issue a token refund"""
        
        # 1. Mark report as refunded
        self.client.table('reports').update({
            'refunded': True
        }).eq('id', report_id).execute()
        
        # 2. Create refund transaction
        self.client.table('token_transactions').insert({
            'user_id': user_id,
            'report_id': report_id,
            'transaction_type': 'refund',
            'tokens_amount': 1,
            'description': f'Quality refund: {reason}'
        }).execute()
        
        # 3. Update user's token balance
        self.client.rpc('increment_tokens', {
            'user_id': user_id,
            'amount': 1
        }).execute()
    
    def create_error_log(self, user_id, ticker, error_type, error_message, stack_trace):
        """Log an error"""
        
        data = {
            'user_id': user_id,
            'ticker': ticker,
            'error_type': error_type,
            'error_message': error_message,
            'stack_trace': stack_trace,
            'status': 'open'
        }
        
        result = self.client.table('error_logs').insert(data).execute()
        return result.data[0]['id']
```

## ============================================================================
## ENVIRONMENT VARIABLES
## ============================================================================

Create `.env` file:
```
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key-here

# Anthropic
ANTHROPIC_API_KEY=your-anthropic-key-here

# Server
PORT=8000
WORKER_THREADS=2

# Optional: Sentry for error tracking
SENTRY_DSN=your-sentry-dsn
```

## ============================================================================
## REQUIREMENTS.TXT
## ============================================================================

```
flask==3.0.0
requests==2.31.0
anthropic==0.18.1
supabase==2.3.4
beautifulsoup4==4.12.3
python-dotenv==1.0.1
gunicorn==21.2.0
```

## ============================================================================
## DOCKERFILE
## ============================================================================

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run with gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "4", "--timeout", "300", "app:app"]
```

## ============================================================================
## DEPLOYMENT
## ============================================================================

### Option 1: Railway

1. **Create `railway.json`:**
```json
{
  "build": {
    "builder": "DOCKERFILE"
  },
  "deploy": {
    "startCommand": "gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 300 app:app",
    "restartPolicyType": "ON_FAILURE"
  }
}
```

2. **Deploy:**
```bash
railway init
railway up
```

3. **Set environment variables in Railway dashboard**

### Option 2: Render

1. **Create `render.yaml`:**
```yaml
services:
  - type: web
    name: sec-analysis-worker
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 300 app:app
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
```

2. **Deploy via Render dashboard or CLI**

## ============================================================================
## TESTING
## ============================================================================

Test locally:
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your keys

# Run server
python app.py

# Test health endpoint
curl http://localhost:8000/health

# Test report generation (mock job)
curl -X POST http://localhost:8000/generate-report \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "test-123",
    "user_id": "test-user",
    "ticker": "AAPL",
    "callback_url": "https://webhook.site/your-unique-url"
  }'
```

## ============================================================================
## MONITORING & LOGGING
## ============================================================================

Recommended:
- **Sentry** for error tracking
- **Railway/Render logs** for debugging
- **Health check endpoint** for uptime monitoring

Add to app.py:
```python
import sentry_sdk
sentry_sdk.init(dsn=os.environ.get('SENTRY_DSN'))
```

## ============================================================================
## SECURITY CONSIDERATIONS
## ============================================================================

1. **Service Key Protection**
   - Use Supabase SERVICE_KEY (not anon key)
   - This bypasses RLS - worker has full access
   - Never expose this key publicly

2. **API Authentication**
   - Add secret token validation on /generate-report endpoint
   - Only Supabase Edge Functions should call this

3. **Rate Limiting**
   - Implement max concurrent jobs
   - Timeout long-running jobs (>5 minutes)

## ============================================================================
## NEXT STEPS
## ============================================================================

1. Create the project structure
2. Copy existing scripts (sec_fetcher.py, etc.)
3. Implement new files (app.py, worker.py, etc.)
4. Test locally
5. Deploy to Railway/Render
6. Get the worker URL
7. Use that URL in Edge Functions

