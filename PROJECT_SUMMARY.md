# SEC 10-K Analysis - Validation Pipeline
## Project Summary

## What We Built

A complete validation pipeline to test the feasibility of AI-powered SEC 10-K analysis before building the full product.

### Core Components

1. **SEC Fetcher** (`sec_fetcher.py`)
   - Fetches 10-K filings from SEC EDGAR API
   - Converts ticker symbols to CIK numbers
   - Parses HTML to extract 4 key sections:
     - Item 1: Business Description
     - Item 1A: Risk Factors
     - Item 7: MD&A
     - Item 8: Auditor's Report
   - Handles rate limiting (10 req/sec)
   - Returns structured data with sections and metadata

2. **Diff Analyzer** (`diff_analyzer.py`)
   - Compares old vs new versions of each section
   - Identifies additions, deletions, and modifications
   - Filters out minor wording changes
   - Returns structured diff with "meaningful changes" flag
   - Provides human-readable diff reports

3. **AI Analyzer** (`ai_analyzer.py`)
   - Sends changes to Claude API for analysis
   - Uses carefully crafted prompts to:
     - Focus only on material changes
     - Avoid hallucinations
     - Provide specific, investor-relevant summaries
   - Tracks token usage and costs
   - Returns structured analysis with metadata

4. **Validation Pipeline** (`validation_pipeline.py`)
   - Orchestrates the full workflow
   - Tests multiple companies (different industries)
   - Saves results as JSON and text reports
   - Calculates total costs
   - Provides summary statistics

5. **Test Suite** (`test_pipeline.py`)
   - Quick test without requiring API key
   - Validates fetching and parsing work
   - Tests diff analysis
   - No cost, no API calls

## How to Use

### Quick Start

```bash
# 1. Install dependencies
pip install beautifulsoup4 requests lxml anthropic

# 2. Set API key
export ANTHROPIC_API_KEY='your-key-here'

# 3. Test without API (free)
python test_pipeline.py

# 4. Run full validation (~$1-3)
python validation_pipeline.py
```

### What Gets Validated

The pipeline tests 5 diverse companies:
- **AAPL** - Tech giant, clean filings
- **TSLA** - Complex business, many changes
- **JPM** - Financial services, different structure
- **WMT** - Traditional retail
- **NVDA** - Semiconductors, hot industry

For each company:
1. ✓ Can we fetch the filings?
2. ✓ Can we extract sections?
3. ✓ Can we identify changes?
4. ✓ Can AI generate useful summaries?

## Expected Costs

### Validation Phase:
- 5 companies × $0.20 = **~$1.00 total**
- Can test more if needed
- One-time cost

### Production (per Brief estimates):
- Fresh report: ~$0.20
- Cached report: ~$0.00001
- Average (70% cache rate): ~$0.06

## Success Criteria

From the Brief, AI quality is the **make-or-break factor**.

### ✅ PASS - Proceed to MVP if:
- Summaries are factually accurate
- No hallucinations
- Highlights material changes
- Appropriate level of detail
- Consistent quality across companies

### ⚠️ REFINE - Improve and re-test if:
- Mostly good but some issues
- Misses some important changes
- Occasionally too vague
- Prompt adjustments could help

### ❌ FAIL - Reconsider approach if:
- Frequent hallucinations
- Misses obvious changes
- Quality inconsistent
- Not useful to investors

## Output Format

Results saved to `validation_results/`:

### JSON File (machine-readable)
```json
{
  "company_name": "Apple Inc.",
  "ticker": "AAPL",
  "old_filing_date": "2023-09-30",
  "new_filing_date": "2024-09-30",
  "sections": [
    {
      "section": "Item 1A: Risk Factors",
      "summary": "AI-generated analysis...",
      "tokens": {...},
      "cost_usd": 0.0375
    }
  ],
  "total_cost_usd": 0.20
}
```

### Text Report (human-readable)
```
SEC 10-K CHANGE ANALYSIS
Company: Apple Inc. (AAPL)
Old Filing: 2023-09-30
New Filing: 2024-09-30

Item 1: Business
----------------
[AI summary of changes]

Item 1A: Risk Factors  
---------------------
[AI summary of changes]

[etc...]
```

## Technical Decisions

### Why HTML not PDF?
- ✅ Structured with tags
- ✅ Sections clearly labeled
- ✅ Easy to parse
- ✅ No OCR needed
- ❌ PDFs are unstructured nightmares

### Why These 4 Sections?
- Narrative content (not just numbers)
- Most likely to have meaningful changes
- Reasonable token count (~60k total)
- What investors actually care about

### Why Claude?
- Excellent at following instructions
- Good with citations (for later)
- 200k context window
- Reliable API
- Good financial text understanding

### Why These Test Companies?
- Different industries
- Different filing styles
- Range of complexity
- Validates robustness

## Next Steps

### If Validation Passes → Build MVP (Weeks 2-7)

**Week 2-3: Backend**
- Flask/FastAPI setup
- Database schema (PostgreSQL)
- Caching logic
- SEC EDGAR integration
- Error handling

**Week 4: PDF Generation**
- ReportLab integration
- Professional formatting
- Citations
- Cloudflare R2 storage

**Week 5: Frontend**
- React dashboard
- Ticker input
- Report display
- User authentication

**Week 6: Payments**
- Stripe integration
- Credit system
- Usage tracking

**Week 7: Beta & Launch**
- Beta testing
- Bug fixes
- Documentation
- Soft launch

### If Validation Needs Work → Iterate (Week 1-2)

- Refine prompts
- Test different sections
- Adjust diff algorithm
- Try different approaches
- Re-run validation

## Key Insights from Building This

### What Worked Well:
1. HTML parsing is much easier than expected
2. SEC EDGAR API is straightforward
3. Diff algorithm effectively filters minor changes
4. Modular design makes testing easy

### Challenges Encountered:
1. HTML structure varies by company (expected)
2. Need to handle parsing failures gracefully
3. Token limits require content truncation
4. Rate limiting needs careful handling

### Lessons Learned:
1. Test with diverse companies (not just tech)
2. Diff analysis is crucial (don't send full docs to AI)
3. Clear prompts are essential
4. Cost tracking important for validation

## Files Included

```
sec-analysis-validation/
├── sec_fetcher.py           # Fetches/parses 10-Ks
├── diff_analyzer.py         # Compares sections
├── ai_analyzer.py           # AI summaries
├── validation_pipeline.py   # Main orchestrator
├── test_pipeline.py         # Quick test
├── requirements.txt         # Dependencies
├── README.md               # Usage guide
├── SETUP.md                # Setup instructions
└── PROJECT_SUMMARY.md      # This file
```

## Cost Breakdown (Detailed)

### Per Company Analysis:
```
Input tokens:  ~60,000 @ $3/million  = $0.18
Output tokens: ~1,600  @ $15/million = $0.024
Total:                                 $0.204
```

### 5 Company Validation:
```
5 companies × $0.204 = $1.02 USD
```

### Production Costs (from Brief):
```
Fresh report:  $0.20
Cached report: $0.00001
Average (70% cache hit): $0.06
```

### Monthly Production Estimate:
```
100 users × 5 reports/month = 500 reports
500 reports × $0.06 avg = $30/month AI costs
Revenue at £10/user = £1,000/month
AI Cost: 3% of revenue (97% margin)
```

## Contact & Support

This is a validation tool built according to the specifications in `Brief.md`.

For questions about:
- **Setup**: See SETUP.md
- **Usage**: See README.md
- **Strategy**: See Brief.md
- **This summary**: You're reading it!

## Final Notes

This validation pipeline is:
- ✅ Complete and ready to run
- ✅ Well-documented
- ✅ Modular and testable
- ✅ Low cost (~$1 to validate)
- ✅ Answers the key question: "Is AI quality good enough?"

The Brief identified AI quality as the critical make-or-break factor. This pipeline tests exactly that, under production-like conditions (same input format, same prompts, same model).

**If the AI summaries are good → This is a viable business**
**If the AI summaries are mediocre → More work needed or pivot**

Only one way to find out: Run the validation! 🚀

---

Built: February 2, 2026
Version: 1.0 (Validation Phase)
Status: Ready for Testing
