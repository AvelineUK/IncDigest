# Setup Guide for SEC 10-K Analysis Validation

This guide will walk you through setting up and running the validation pipeline.

## Prerequisites

- Python 3.8 or higher
- Internet connection (to fetch from SEC EDGAR and call Anthropic API)
- Anthropic API key (get from https://console.anthropic.com/)

## Step-by-Step Setup

### 1. Verify Python Installation

```bash
python3 --version
# Should show Python 3.8 or higher
```

### 2. Install Dependencies

The project needs these packages:
- `beautifulsoup4` - Parse HTML from SEC filings
- `requests` - Fetch data from SEC EDGAR
- `lxml` - XML/HTML parser (faster than default)
- `anthropic` - Claude API client

Install them:

```bash
pip install beautifulsoup4 requests lxml anthropic
```

Or use the requirements file:

```bash
pip install -r requirements.txt
```

### 3. Get Anthropic API Key

1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Go to API Keys section
4. Create a new API key
5. Copy the key (starts with `sk-ant-...`)

### 4. Set API Key as Environment Variable

**On Mac/Linux:**
```bash
export ANTHROPIC_API_KEY='sk-ant-your-key-here'
```

To make it permanent, add to your shell config:
```bash
echo 'export ANTHROPIC_API_KEY="sk-ant-your-key-here"' >> ~/.bashrc
source ~/.bashrc
```

**On Windows (PowerShell):**
```powershell
$env:ANTHROPIC_API_KEY='sk-ant-your-key-here'
```

**Verify it's set:**
```bash
echo $ANTHROPIC_API_KEY
# Should print your key
```

### 5. Run Initial Test (No API Key Needed)

First, test that fetching and parsing work:

```bash
python test_pipeline.py
```

This will:
- Fetch Apple's latest 2 10-K filings
- Extract sections
- Perform diff analysis
- Show what changed

**No API calls** = **No cost** for this test.

If this works, you're ready for the full validation.

### 6. Run Full Validation Pipeline

Once the test passes and you have your API key set:

```bash
python validation_pipeline.py
```

This will:
1. Ask for confirmation (shows estimated cost)
2. Test 5 companies: AAPL, TSLA, JPM, WMT, NVDA
3. Generate AI summaries for each
4. Save results to `validation_results/`

**Expected cost:** $1-3 USD total

**Expected time:** 5-10 minutes

### 7. Review Results

Check the generated reports:

```bash
ls validation_results/
# Shows all generated files

# View a specific report
cat validation_results/AAPL_*.txt
```

Each report shows:
- Company and filing dates
- AI-generated summaries for each section
- What changed between filings
- Total cost and token usage

## Troubleshooting

### "ModuleNotFoundError: No module named 'anthropic'"

**Fix:**
```bash
pip install anthropic
```

### "Error: ANTHROPIC_API_KEY environment variable not set"

**Fix:**
```bash
export ANTHROPIC_API_KEY='your-key-here'
```

Verify:
```bash
echo $ANTHROPIC_API_KEY
```

### "Could not find start of Item 1A"

This is **expected** for some companies. 10-K HTML structure varies.

The validation tests multiple companies specifically to see success rate.

If 4 out of 5 work, that's good enough to proceed.

### Network/Rate Limit Errors

SEC EDGAR allows 10 requests per second. We include delays, but if you hit issues:

Edit `sec_fetcher.py`:
```python
RATE_LIMIT_DELAY = 0.3  # Increase from 0.15 to 0.3
```

### API Errors

If you get Anthropic API errors:

1. Check your API key is valid
2. Check your account has credits
3. Try with fewer companies (edit `test_tickers` list in `validation_pipeline.py`)

## What to Look For in Results

When reviewing the AI-generated summaries, evaluate:

### ✅ Good Signs:
- Summaries are factual and specific
- Changes are clearly described
- No obvious hallucinations
- Focuses on material changes (not minor wording)
- Appropriate level of detail

### ❌ Red Flags:
- Summaries mention things not in the actual filing
- Misses obvious important changes
- Too vague or generic
- Focuses on trivial changes
- Inconsistent quality across sections

## Next Steps After Validation

### If AI Quality is Good (Summaries are accurate and useful):

✅ **Proceed to build MVP**

Next tasks:
1. Build backend API (Flask/FastAPI)
2. Add PDF generation
3. Implement caching
4. Build frontend
5. Add payments

See `Brief.md` for full roadmap.

### If AI Quality Needs Work:

🔧 **Refine and iterate**

Options:
1. Improve prompts (more specific instructions)
2. Add citation requirements
3. Test different section combinations
4. Try different models
5. Adjust diff algorithm

Then re-run validation.

### If AI Quality is Poor:

❌ **Back to drawing board**

Consider:
- Different approach (maybe AI + human in the loop?)
- Different sections (focus on most valuable ones)
- Different product altogether

## Cost Management

### Validation Testing:
- 5 companies × ~$0.20 each = ~$1.00
- Can test more companies if needed
- Cost scales linearly with number of tests

### Production Estimates (from Brief):
- Fresh report: ~$0.20 per company
- Cached report: ~$0.00001 per company
- With 70% cache hit rate: ~$0.06 average per report

## Files Overview

```
├── sec_fetcher.py         # Fetches and parses 10-K filings
├── diff_analyzer.py       # Compares sections, identifies changes  
├── ai_analyzer.py         # Generates AI summaries via Claude API
├── validation_pipeline.py # Main orchestrator (run this)
├── test_pipeline.py       # Quick test without API calls
├── requirements.txt       # Python dependencies
├── README.md             # Usage documentation
└── SETUP.md              # This file
```

## Support

If you encounter issues not covered here:

1. Check the README.md for additional details
2. Review the Brief.md for project context
3. Check error messages carefully
4. Try with a single company first before batch testing

## Quick Reference

**Test without API:**
```bash
python test_pipeline.py
```

**Full validation with AI:**
```bash
python validation_pipeline.py
```

**Set API key:**
```bash
export ANTHROPIC_API_KEY='your-key'
```

**Check results:**
```bash
cat validation_results/AAPL_*.txt
```

---

Good luck with validation! 🚀
