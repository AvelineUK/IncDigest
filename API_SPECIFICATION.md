# ============================================================================
# SEC 10-K Analysis Platform - API Specification
# ============================================================================
# Version: 1.0
# Backend: Supabase (PostgreSQL + Edge Functions) + Python Worker
# Frontend: Next.js
# ============================================================================

## ARCHITECTURE OVERVIEW

```
┌─────────────┐
│   Next.js   │
│  Frontend   │
└──────┬──────┘
       │
       │ HTTP/REST
       │
┌──────▼──────────────────────────────────────┐
│         Supabase                             │
│  ┌────────────┐  ┌──────────────┐           │
│  │ PostgreSQL │  │ Edge Funcs   │           │
│  │  Database  │  │  (Deno TS)   │           │
│  └────────────┘  └──────┬───────┘           │
│                         │                    │
│                         │ Queue/Webhook      │
└─────────────────────────┼────────────────────┘
                          │
                 ┌────────▼─────────┐
                 │  Python Worker   │
                 │  (Railway/Render)│
                 │                  │
                 │  - SEC Fetcher   │
                 │  - Diff Analyzer │
                 │  - AI Analyzer   │
                 └──────────────────┘
```

## ============================================================================
## PUBLIC ENDPOINTS (No Auth Required)
## ============================================================================

### GET /api/health
**Purpose:** Health check
**Response:**
```json
{
  "status": "ok",
  "timestamp": "2026-02-02T14:00:00Z",
  "version": "1.0.0"
}
```

### GET /api/companies/search?q={query}
**Purpose:** Search for companies by ticker or name
**Query Params:**
  - q: search query (e.g., "apple" or "AAPL")
  - limit: max results (default 10)

**Response:**
```json
{
  "results": [
    {
      "ticker": "AAPL",
      "company_name": "Apple Inc.",
      "cik": "0000320193",
      "extraction_status": "working"
    }
  ]
}
```

### GET /api/companies/{ticker}/status
**Purpose:** Check if a company's extraction is known to work
**Response:**
```json
{
  "ticker": "AAPL",
  "company_name": "Apple Inc.",
  "extraction_status": "working",
  "success_rate_pct": 95.5,
  "last_successful_extraction": "2026-02-01T10:30:00Z"
}
```

## ============================================================================
## AUTHENTICATED ENDPOINTS (Require Auth)
## ============================================================================

### Authentication
All authenticated endpoints require:
```
Authorization: Bearer {supabase_jwt_token}
```

---

## USER MANAGEMENT

### GET /api/user/profile
**Purpose:** Get current user's profile
**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "subscription_tier": "beta",
  "subscription_status": "active",
  "tokens_remaining": 10,
  "tokens_purchased": 50,
  "created_at": "2026-01-15T10:00:00Z",
  "beta_access": true
}
```

### PATCH /api/user/profile
**Purpose:** Update user profile settings
**Body:**
```json
{
  "full_name": "John Doe",
  "email_notifications": true
}
```

### GET /api/user/stats
**Purpose:** Get user's usage statistics
**Response:**
```json
{
  "total_reports": 25,
  "successful_reports": 23,
  "refunded_reports": 2,
  "total_spent_usd": 1.15,
  "tokens_remaining": 10,
  "last_report_date": "2026-02-02T09:00:00Z"
}
```

---

## TOKEN MANAGEMENT

### GET /api/tokens/balance
**Purpose:** Get current token balance
**Response:**
```json
{
  "tokens_remaining": 10,
  "tokens_purchased": 50,
  "last_purchase_date": "2026-01-20T10:00:00Z"
}
```

### GET /api/tokens/transactions
**Purpose:** Get token transaction history
**Query Params:**
  - limit: number of transactions (default 50)
  - offset: pagination offset

**Response:**
```json
{
  "transactions": [
    {
      "id": "uuid",
      "transaction_type": "purchase",
      "tokens_amount": 10,
      "amount_gbp": 10.00,
      "description": "10 tokens purchased",
      "created_at": "2026-01-20T10:00:00Z"
    },
    {
      "id": "uuid",
      "transaction_type": "usage",
      "tokens_amount": -1,
      "description": "Report generated for AAPL",
      "report_id": "uuid",
      "created_at": "2026-01-21T14:30:00Z"
    },
    {
      "id": "uuid",
      "transaction_type": "refund",
      "tokens_amount": 1,
      "description": "Quality issues detected - refund for TSLA",
      "report_id": "uuid",
      "created_at": "2026-01-21T14:31:00Z"
    }
  ],
  "pagination": {
    "total": 47,
    "limit": 50,
    "offset": 0
  }
}
```

### POST /api/tokens/purchase
**Purpose:** Initiate token purchase (Stripe Checkout)
**Body:**
```json
{
  "package": "10_tokens", // "10_tokens", "50_tokens", "100_tokens"
  "success_url": "https://app.example.com/tokens/success",
  "cancel_url": "https://app.example.com/tokens/cancel"
}
```

**Response:**
```json
{
  "checkout_url": "https://checkout.stripe.com/...",
  "session_id": "cs_..."
}
```

### POST /api/webhooks/stripe
**Purpose:** Handle Stripe webhook events (payment success, etc.)
**Note:** This is called by Stripe, not the frontend
**Body:** Standard Stripe webhook payload

---

## REPORT GENERATION

### POST /api/reports/generate
**Purpose:** Generate a new 10-K analysis report
**Body:**
```json
{
  "ticker": "AAPL"
}
```

**Response (Immediate):**
```json
{
  "job_id": "uuid",
  "status": "queued",
  "estimated_time_seconds": 120,
  "message": "Report generation started"
}
```

**Error Responses:**
```json
// Insufficient tokens
{
  "error": "insufficient_tokens",
  "message": "You need 1 token to generate a report. Current balance: 0",
  "tokens_required": 1,
  "tokens_remaining": 0
}

// Company not found
{
  "error": "company_not_found",
  "message": "Ticker INVALID not found"
}

// Rate limited
{
  "error": "rate_limited",
  "message": "Please wait 60 seconds before generating another report",
  "retry_after": 60
}
```

### GET /api/reports/status/{job_id}
**Purpose:** Check report generation status
**Response:**
```json
{
  "job_id": "uuid",
  "status": "processing", // "queued", "processing", "completed", "failed"
  "progress": 65, // 0-100
  "current_step": "Analyzing Item 7...",
  "estimated_time_remaining_seconds": 45
}
```

### GET /api/reports/{report_id}
**Purpose:** Get a completed report
**Response:**
```json
{
  "id": "uuid",
  "ticker": "AAPL",
  "company_name": "Apple Inc.",
  "newer_filing_date": "2025-10-31",
  "older_filing_date": "2024-11-01",
  "extraction_success": true,
  "sections_extracted": ["Item 1", "Item 1A", "Item 7", "Item 8"],
  "extraction_issues": [],
  "refunded": false,
  "ai_summaries": {
    "Item 1": "Summary of business changes...",
    "Item 1A": "Summary of risk factor changes...",
    "Item 7": "Summary of MD&A changes...",
    "Item 8": "Summary of financial statement changes..."
  },
  "report_url": "https://storage.supabase.co/.../report.pdf",
  "created_at": "2026-02-02T14:00:00Z",
  "generation_time_seconds": 125,
  "ai_cost_usd": 0.09,
  "total_tokens_consumed": 24900
}
```

**If Quality Issues:**
```json
{
  "id": "uuid",
  "ticker": "ABNORMAL",
  "extraction_success": false,
  "extraction_issues": [
    "Item 7: Content too short (only 245 words, expected 5000+)",
    "Item 1A: Extraction failed"
  ],
  "refunded": true,
  "ai_summaries": {
    "Item 1": "Partial summary available...",
    "Item 8": "Partial summary available..."
  },
  "quality_notice": "We detected quality issues with this extraction and have refunded 1 token to your account. The partial report is still available below.",
  "created_at": "2026-02-02T14:00:00Z"
}
```

### GET /api/reports
**Purpose:** List user's reports
**Query Params:**
  - limit: number of reports (default 20)
  - offset: pagination offset
  - ticker: filter by ticker (optional)
  - sort: "newest" or "oldest" (default "newest")

**Response:**
```json
{
  "reports": [
    {
      "id": "uuid",
      "ticker": "AAPL",
      "company_name": "Apple Inc.",
      "newer_filing_date": "2025-10-31",
      "extraction_success": true,
      "refunded": false,
      "created_at": "2026-02-02T14:00:00Z"
    }
  ],
  "pagination": {
    "total": 47,
    "limit": 20,
    "offset": 0
  }
}
```

### DELETE /api/reports/{report_id}
**Purpose:** Delete a report (soft delete, mark as hidden)
**Response:**
```json
{
  "success": true,
  "message": "Report deleted"
}
```

---

## ============================================================================
## ADMIN ENDPOINTS (Require Admin Role)
## ============================================================================

### GET /api/admin/dashboard/stats
**Purpose:** Get platform statistics
**Response:**
```json
{
  "users": {
    "total": 150,
    "active_last_30_days": 87,
    "beta_users": 50,
    "paying_users": 45
  },
  "reports": {
    "total": 2500,
    "last_24_hours": 125,
    "success_rate_pct": 92.3,
    "refund_rate_pct": 7.7
  },
  "revenue": {
    "total_gbp": 1850.00,
    "this_month_gbp": 450.00,
    "avg_per_user_gbp": 41.11
  },
  "errors": {
    "open": 15,
    "resolved_this_week": 23
  }
}
```

### GET /api/admin/error-logs
**Purpose:** Get error logs for debugging
**Query Params:**
  - status: "open", "investigating", "resolved", "wontfix"
  - ticker: filter by ticker
  - limit: number of logs (default 50)

**Response:**
```json
{
  "logs": [
    {
      "id": "uuid",
      "ticker": "ABNORMAL",
      "company_name": "Abnormal Corp",
      "error_type": "extraction_failed",
      "error_message": "Item 7: only 263 chars extracted",
      "sections_failed": ["Item 7"],
      "status": "open",
      "created_at": "2026-02-02T13:00:00Z",
      "filing_url": "https://sec.gov/..."
    }
  ]
}
```

### PATCH /api/admin/error-logs/{log_id}
**Purpose:** Update error log status
**Body:**
```json
{
  "status": "resolved",
  "resolution_notes": "Fixed Item 7 extraction for this company type"
}
```

### PATCH /api/admin/companies/{ticker}
**Purpose:** Update company extraction status
**Body:**
```json
{
  "extraction_status": "working" // or "broken" or "unknown"
}
```

### POST /api/admin/users/{user_id}/grant-tokens
**Purpose:** Grant tokens to a user (e.g., for beta testing)
**Body:**
```json
{
  "tokens_amount": 10,
  "description": "Beta tester grant"
}
```

### GET /api/admin/users
**Purpose:** List all users with stats
**Query Params:**
  - search: search by email/name
  - subscription_tier: filter by tier
  - limit: number of users

---

## ============================================================================
## PYTHON WORKER API (Internal)
## ============================================================================

The Python worker is called by Supabase Edge Functions and communicates via:
- HTTP API (for job status updates)
- Direct database writes (for results)

### POST /worker/generate-report (Called by Edge Function)
**Purpose:** Process a report generation job
**Body:**
```json
{
  "job_id": "uuid",
  "user_id": "uuid",
  "ticker": "AAPL",
  "callback_url": "https://project.supabase.co/functions/v1/report-callback"
}
```

**Worker Process:**
1. Fetch 10-Ks from SEC
2. Extract sections
3. Run diff analysis
4. Generate AI summaries
5. Validate quality
6. Write to database
7. Call callback_url with status

**Callback Payload (Success):**
```json
{
  "job_id": "uuid",
  "status": "completed",
  "report_id": "uuid"
}
```

**Callback Payload (Failure):**
```json
{
  "job_id": "uuid",
  "status": "failed",
  "error": "Extraction failed for Item 7",
  "error_log_id": "uuid"
}
```

---

## ============================================================================
## ERROR CODES
## ============================================================================

| Code                    | HTTP | Description                          |
|-------------------------|------|--------------------------------------|
| insufficient_tokens     | 402  | User doesn't have enough tokens      |
| company_not_found       | 404  | Ticker not found                     |
| report_not_found        | 404  | Report ID doesn't exist              |
| rate_limited            | 429  | Too many requests                    |
| unauthorized            | 401  | Not authenticated                    |
| forbidden               | 403  | Not authorized (e.g., not admin)     |
| validation_error        | 400  | Invalid request body                 |
| internal_error          | 500  | Server error                         |
| worker_timeout          | 504  | Report generation timed out          |

---

## ============================================================================
## RATE LIMITS
## ============================================================================

| Endpoint                  | Limit                    |
|---------------------------|--------------------------|
| POST /api/reports/generate| 1 per minute per user    |
| GET /api/companies/search | 60 per minute per IP     |
| All other authenticated   | 120 per minute per user  |
| Admin endpoints           | No limit                 |

---

## ============================================================================
## WEBHOOKS
## ============================================================================

### Stripe → /api/webhooks/stripe
Events to handle:
- `checkout.session.completed` - Token purchase succeeded
- `customer.subscription.updated` - Subscription changed
- `customer.subscription.deleted` - Subscription cancelled

### Python Worker → /functions/v1/report-callback
Called when report generation completes or fails

---

## ============================================================================
## IMPLEMENTATION NOTES
## ============================================================================

### Supabase Edge Functions (Deno TypeScript)
- `/api/reports/generate` - Queue job, deduct token, call Python worker
- `/api/webhooks/stripe` - Handle Stripe events
- `/functions/v1/report-callback` - Receive worker completion

### Supabase Database
- Most GET endpoints query database directly (via PostgREST)
- RLS policies handle security
- Real-time subscriptions possible for job status

### Python Worker (Railway/Render)
- Runs our extraction/analysis scripts
- Receives jobs via HTTP
- Writes results directly to Supabase
- Calls callback when done

### Frontend (Next.js)
- Calls Supabase client for auth
- Calls API endpoints for data
- Uses Supabase real-time for job progress
- Handles Stripe checkout redirect

---

## ============================================================================
## EXAMPLE FLOW: Generate Report
## ============================================================================

1. **User clicks "Generate Report" for AAPL**
   - Frontend: POST /api/reports/generate { "ticker": "AAPL" }

2. **Edge Function validates & queues**
   - Check tokens_remaining >= 1
   - Deduct 1 token (create transaction)
   - Create job record in database
   - Call Python worker
   - Return job_id to frontend

3. **Frontend polls status**
   - GET /api/reports/status/{job_id} every 5 seconds
   - Shows progress bar

4. **Python worker processes**
   - Fetches 10-Ks
   - Extracts sections
   - Runs AI analysis
   - Validates quality
   - Writes report to database
   - If quality issues: creates refund transaction
   - Calls callback URL

5. **Edge Function receives callback**
   - Updates job status
   - Frontend gets status update
   - Redirects to report page

6. **User views report**
   - GET /api/reports/{report_id}
   - Displays summaries
   - Shows quality notice if refunded

---

## NEXT STEPS

1. Implement Edge Functions in Supabase
2. Build Python worker service
3. Create Next.js frontend routes
4. Set up Stripe integration
5. Deploy worker to Railway/Render

