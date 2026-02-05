"""
AI Analysis Module
Uses Claude API to generate summaries of changes in 10-K sections
"""

from typing import Dict, Optional
import json

# Try to import required packages
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("Warning: anthropic package not installed. Install with: pip install anthropic")

try:
    from config import check_api_key
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    import os


class AIAnalyzer:
    """Generates AI-powered summaries of 10-K changes using Claude API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize with Anthropic API key
        If not provided, will load from .env file via config module
        """
        if api_key:
            self.api_key = api_key
        elif CONFIG_AVAILABLE:
            self.api_key = check_api_key()
        else:
            # Fallback to environment variable
            self.api_key = os.environ.get('ANTHROPIC_API_KEY')
            if not self.api_key:
                raise ValueError(
                    "Anthropic API key required.\n"
                    "Please create a .env file with: ANTHROPIC_API_KEY=sk-ant-your-key\n"
                    "Or set environment variable: export ANTHROPIC_API_KEY='your-key'"
                )
        
        self.model = "claude-sonnet-4-20250514"
        self.max_tokens = 2000  # Per section summary
    
    def create_prompt(self, 
                     section_name: str,
                     company_name: str,
                     ticker: str,
                     old_date: str,
                     new_date: str,
                     removed_content: str,
                     added_content: str) -> str:
        """
        Create the prompt for Claude to analyze section changes
        
        CRITICAL: This prompt is designed to prevent hallucination by requiring
        explicit evidence for every claim. Financial accuracy is paramount.
        """
        prompt = f"""You are analyzing changes in SEC 10-K filings for investors. Your accuracy is critical.

CONTEXT:
Company: {company_name} ({ticker})
Old Filing: 10-K filed {old_date}
New Filing: 10-K filed {new_date}
Section: {section_name}

⚠️ CRITICAL EVIDENCE CONSTRAINT ⚠️

You must use ONLY the REMOVED and ADDED content provided below.

For the purposes of this analysis:

You have no access to any information outside these excerpts
If a fact, number, product, risk, or statement does not appear in the REMOVED or ADDED text, it does not exist
Do NOT rely on prior knowledge, assumptions, or general industry understanding
If a change is not explicitly supported by the diff text, do not report it.

TASK

You are analyzing ONE section of a company’s SEC 10-K filing to identify explicit disclosure changes that fall into predefined material categories.
Your role is not to interpret intent or assess impact — only to classify and report evidenced changes.

MATERIAL CHANGE CATEGORIES (REPORT IF PRESENT)

Report a change IF AND ONLY IF it clearly fits at least one of the following categories and is explicitly shown in the diff:

1. Risk & Uncertainty

New risk disclosures
Expanded or escalated risk language
Added references to regulatory, trade, legal, or macroeconomic risks

2. Business Scope & Structure

Entry into or exit from markets
Geographic expansion or contraction
Changes to business segments or reporting definitions
Additions or removals of product categories or business lines

3. Financial & Performance Metrics

Explicit changes to reported financial figures
Changes to performance indicators or KPIs
Modifications to revenue mix, cost structure, or liquidity disclosures

4. Governance & Leadership

Executive leadership changes (C-suite or board)
Changes to control, oversight, or governance structure

5. Regulatory, Legal, or Compliance

New legal proceedings
Changes to regulatory obligations
Modifications to compliance language or commitments

STRICT EVIDENCE RULES (MANDATORY)

ONLY report changes explicitly shown in the REMOVED vs ADDED content

DO NOT infer, interpret, speculate, or extrapolate
DO NOT restate unchanged background information
DO NOT report figures unless BOTH old and new values appear in the diff
DO NOT describe motivation, strategy, or implications

If no changes meet the categories above, respond ONLY with:
"No material disclosure changes identified in this section."

EXPLICIT EXCLUSIONS (DO NOT REPORT)

❌ Formatting, pagination, ordering, or layout changes
❌ Fiscal year or date rollovers with no substantive disclosure change
❌ Routine wording clarifications with unchanged meaning
❌ Routine product version refreshes unless accompanied by:

product category additions/removals, OR
explicit scope or market changes

SECTION-SPECIFIC SCOPE (IMPORTANT)

You are analyzing ONLY the following section:

Item 1 (Business): operations, products, competitive positioning, structure
Item 1A (Risk Factors): risks, uncertainties, threat escalation
Item 7 (MD&A): performance discussion, trends, liquidity
Item 8 (Financials): accounting policies, audit matters, presentation changes

Only report changes that are relevant to the disclosure purpose of this section.

⚠️ SECTION-SPECIFIC MATERIALITY ADJUSTMENTS:

For Item 7 (MD&A) and Item 8 (Financials):
- Annual financial performance changes ARE material (revenue trends, margin changes, liquidity)
- Significant numerical changes in financial metrics should be reported
- Management's discussion of year-over-year results is material
- Changes in accounting treatment, audit matters, or financial presentation are material
- DO NOT dismiss these as "routine annual updates" - the numbers changing IS the disclosure

For Item 1 (Business) and Item 1A (Risk Factors):
- Apply strict materiality - focus on NEW disclosures, not routine refreshes
- Operational updates are only material if they represent strategic shifts

FAILSAFE RULE (MANDATORY)

If the REMOVED vs ADDED content contains any explicit change that clearly fits a MATERIAL CHANGE CATEGORY above, you MUST report it.
Do NOT default to “No material disclosure changes” when an allowed change exists.

OUTPUT FORMAT

Maximum 5 bullet points
Each bullet must describe a specific, evidenced change
Lead with the most significant change
Keep total output under 500 words

NO PREAMBLE

Bullet points only

QUALITY CHECK (INTERNAL)

For each bullet, ask:

“Would a professional filings analyst reasonably flag this as a disclosure change?”

If NO → do not include.

REMOVED CONTENT (from old filing):
{removed_content if removed_content else "[No content removed]"}

ADDED CONTENT (to new filing):
{added_content if added_content else "[No content added]"}

Analysis (evidence-based only):"""

        return prompt
    
    def analyze_section_changes(self,
                               section_name: str,
                               company_name: str,
                               ticker: str,
                               old_date: str,
                               new_date: str,
                               diff_result: Dict) -> Dict:
        """
        Analyze changes in a single section using Claude API
        
        Returns:
            Dict with analysis results including summary and metadata
        """
        if not diff_result.get('has_meaningful_changes', False):
            return {
                'section': section_name,
                'has_changes': False,
                'summary': 'No material changes in this section.',
                'status': 'unchanged'
            }
        
        removed = diff_result.get('removed_content', '')
        added = diff_result.get('added_content', '')
        
        # Truncate if content is too long (to stay within token limits)
        max_content_length = 15000  # chars per section
        if len(removed) > max_content_length:
            removed = removed[:max_content_length] + "\n\n[Content truncated due to length...]"
        if len(added) > max_content_length:
            added = added[:max_content_length] + "\n\n[Content truncated due to length...]"
        
        prompt = self.create_prompt(
            section_name=section_name,
            company_name=company_name,
            ticker=ticker,
            old_date=old_date,
            new_date=new_date,
            removed_content=removed,
            added_content=added
        )
        
        # Call Claude API
        try:
            if not ANTHROPIC_AVAILABLE:
                return {
                    'section': section_name,
                    'has_changes': True,
                    'summary': '[MOCK] Anthropic package not installed. Install with: pip install anthropic\n\nThis section would contain AI-generated analysis of changes.',
                    'status': 'mock',
                    'tokens': {'input': 10000, 'output': 500, 'total': 10500},
                    'cost_usd': 0.0375  # Estimated cost
                }
            
            client = anthropic.Anthropic(api_key=self.api_key)
            
            message = client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            summary = message.content[0].text
            
            # Strip common preambles that Claude adds
            preambles_to_remove = [
                "Looking at the specific changes between the REMOVED and ADDED content, I identify these material disclosure changes:",
                "Based on the explicit changes shown in the REMOVED vs ADDED content, here are the material disclosure changes:",
                "Looking at the specific changes, I identify these material disclosure changes:",
                "Based on the explicit changes shown, here are the material disclosure changes:",
                "Here are the material disclosure changes:",
                "The material disclosure changes are:",
                "I identify the following material disclosure changes:",
                "Analysis of the changes reveals:",
                "The following material changes were identified:",
            ]
            
            # Remove preambles (case-insensitive, strip whitespace)
            summary_cleaned = summary.strip()
            for preamble in preambles_to_remove:
                if summary_cleaned.lower().startswith(preamble.lower()):
                    summary_cleaned = summary_cleaned[len(preamble):].strip()
                    break
            
            # Get token usage for cost tracking
            input_tokens = message.usage.input_tokens
            output_tokens = message.usage.output_tokens
            
            # Calculate cost (Claude 3.5 Sonnet pricing)
            input_cost = input_tokens * (3.00 / 1_000_000)  # $3 per million input tokens
            output_cost = output_tokens * (15.00 / 1_000_000)  # $15 per million output tokens
            total_cost = input_cost + output_cost
            
            return {
                'section': section_name,
                'has_changes': True,
                'summary': summary_cleaned.strip(),
                'status': 'analyzed',
                'tokens': {
                    'input': input_tokens,
                    'output': output_tokens,
                    'total': input_tokens + output_tokens
                },
                'cost_usd': round(total_cost, 4)
            }
            
        except Exception as e:
            return {
                'section': section_name,
                'has_changes': True,
                'summary': f'Error analyzing section: {str(e)}',
                'status': 'error',
                'error': str(e)
            }
    
    def analyze_all_sections(self,
                           company_name: str,
                           ticker: str,
                           old_date: str,
                           new_date: str,
                           diff_results: Dict[str, Dict]) -> Dict:
        """
        Analyze all sections in a SINGLE Claude API call to avoid repetition across sections
        
        Args:
            company_name: Company name
            ticker: Stock ticker
            old_date: Date of older filing
            new_date: Date of newer filing
            diff_results: Dict mapping section names to diff analysis results
        
        Returns:
            Complete analysis report with all sections
        """
        print(f"\n{'='*60}")
        print(f"AI Analysis (Single Call): {company_name} ({ticker})")
        print(f"Comparing {old_date} vs {new_date}")
        print(f"{'='*60}\n")
        
        # Build comprehensive prompt with all sections
        prompt = f"""You are analyzing changes in SEC 10-K filings for investors. Your accuracy is critical.

CONTEXT:
Company: {company_name} ({ticker})
Old Filing: 10-K filed {old_date}
New Filing: 10-K filed {new_date}

⚠️ CRITICAL LEGAL REQUIREMENT - READ FIRST ⚠️
Under no circumstances use information or data outside of these documents. You cannot use any prior knowledge about this company, its products, its industry, or any other contextual information. For the purposes of this analysis, treat yourself as having ZERO prior knowledge. If it's not in the REMOVED or ADDED content below, it does not exist.

IF YOU BREAK THIS RULE, IT CAN CAUSE SERIOUS LEGAL ISSUES. NEVER, EVER BREAK THIS RULE.

MATERIALITY STANDARD:
Focus ONLY on changes that would affect investment decisions:
✅ New risks or risk escalation
✅ Business model changes or strategic shifts
✅ Market exits/entries or geographic expansion
✅ Significant financial metric changes
✅ Regulatory, legal, or compliance developments
✅ Executive leadership changes (C-suite, board)
✅ Material operational changes (facility closures, restructuring)

❌ Routine operational updates
❌ Minor wording tweaks or clarifications
❌ Formatting, pagination, or organizational changes

⚠️ CRITICAL: AVOID REPETITION ACROSS SECTIONS ⚠️
You are analyzing ALL sections at once. Each material change should be reported ONLY ONCE in the most appropriate section:
- Item 1 (Business): Company operations, products, competitive positioning, organizational structure
- Item 1A (Risk Factors): Risk disclosures, risk escalations, new threats
- Item 7 (MD&A): Management's discussion of financial performance, trends, liquidity
- Item 8 (Financial Statements): Accounting policies, audit matters, financial presentation changes

For company-wide changes (acquisitions, divestitures, restructuring):
- Report the operational/strategic aspects in Item 1
- Report ONLY NEW risks in Item 1A (not facts already in Item 1)
- Report ONLY financial impacts/management discussion in Item 7
- Report ONLY accounting/audit changes in Item 8

DO NOT repeat the same factual change across sections. Focus on what's UNIQUE to each section's purpose.

THE BLOOMBERG TEST (apply to every bullet point):
"Would a Bloomberg terminal analyst include this in a filing summary?"
If NO → Do not include it.

STRICT EVIDENCE RULES (MANDATORY):
1. ONLY report changes explicitly shown in the REMOVED vs ADDED content below
2. DO NOT infer, interpret, or extrapolate beyond what is directly stated
3. DO NOT mention product names, model numbers, or versions unless they appear in BOTH removed and added content showing a clear change
4. DO NOT report percentage changes, employee counts, or financial figures unless explicitly comparing old vs new values shown in the diff
5. If you cannot identify a specific, evidenced change, respond: "No material disclosure changes identified in this section."

FORBIDDEN BEHAVIORS:
❌ Routine updates: product versions, page numbers, fiscal year dates, formatting changes
❌ Annual refresh cycles: iPhone 15→16, Model Year updates, standard version increments
❌ Unsupported claims: mentioning facts not explicitly shown in BOTH old AND new content
❌ Personnel changes: unless C-suite or board level
❌ Background context: restating what the company does

"""
        
        # Add each section's diff content
        for section_name in ['Item 1', 'Item 1A', 'Item 7', 'Item 8']:
            diff_result = diff_results.get(section_name, {})
            
            if not diff_result.get('has_meaningful_changes', False):
                prompt += f"\n{'='*80}\n{section_name}: NO MEANINGFUL CHANGES\n{'='*80}\n\n"
                continue
            
            removed = diff_result.get('removed_content', '')
            added = diff_result.get('added_content', '')
            
            # Truncate if too long
            max_content_length = 15000
            if len(removed) > max_content_length:
                removed = removed[:max_content_length] + "\n\n[Content truncated...]"
            if len(added) > max_content_length:
                added = added[:max_content_length] + "\n\n[Content truncated...]"
            
            prompt += f"""
{'='*80}
{section_name}
{'='*80}

REMOVED CONTENT (from old filing):
{removed if removed else "[No content removed]"}

ADDED CONTENT (to new filing):
{added if added else "[No content added]"}

"""
        
        prompt += """
OUTPUT FORMAT (CRITICAL):

Respond with a JSON object where each key is a section name and each value is the analysis:

{
  "Item 1": "• Bullet point 1\\n• Bullet point 2",
  "Item 1A": "No material disclosure changes identified in this section.",
  "Item 7": "• Bullet point 1",
  "Item 8": "No material disclosure changes identified in this section."
}

Rules:
- Maximum 5 bullet points per section
- Each bullet must pass the Bloomberg test
- Use "No material disclosure changes identified in this section." if nothing material
- Keep under 300 words per section
- NO PREAMBLE - just bullet points starting with •
- NO REPETITION across sections - each change reported ONCE in most relevant section

Respond ONLY with the JSON object, nothing else."""
        
        # Call Claude API
        try:
            if not ANTHROPIC_AVAILABLE:
                # Mock response for testing
                return {
                    'company_name': company_name,
                    'ticker': ticker,
                    'old_filing_date': str(old_date),
                    'new_filing_date': str(new_date),
                    'sections': [
                        {'section': 'Item 1', 'has_changes': True, 'summary': '[MOCK] Analysis pending', 'status': 'mock'},
                        {'section': 'Item 1A', 'has_changes': True, 'summary': '[MOCK] Analysis pending', 'status': 'mock'},
                        {'section': 'Item 7', 'has_changes': True, 'summary': '[MOCK] Analysis pending', 'status': 'mock'},
                        {'section': 'Item 8', 'has_changes': True, 'summary': '[MOCK] Analysis pending', 'status': 'mock'},
                    ],
                    'total_cost_usd': 0.10,
                    'total_cost_gbp': 0.08,
                    'total_tokens': 10000
                }
            
            client = anthropic.Anthropic(api_key=self.api_key)
            
            message = client.messages.create(
                model=self.model,
                max_tokens=4000,  # Increased for all sections
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text.strip()
            
            # Parse JSON response
            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                # Remove first and last lines (``` markers)
                response_text = '\n'.join(lines[1:-1])
                if response_text.startswith('json'):
                    response_text = response_text[4:].strip()
            
            section_summaries = json.loads(response_text)
            
            # Build analyses list
            analyses = []
            for section_name in ['Item 1', 'Item 1A', 'Item 7', 'Item 8']:
                summary = section_summaries.get(section_name, 'No material disclosure changes identified in this section.')
                analyses.append({
                    'section': section_name,
                    'has_changes': summary != 'No material disclosure changes identified in this section.',
                    'summary': summary,
                    'status': 'analyzed'
                })
            
            # Calculate cost
            input_tokens = message.usage.input_tokens
            output_tokens = message.usage.output_tokens
            total_tokens = input_tokens + output_tokens
            
            input_cost = input_tokens * (3.00 / 1_000_000)
            output_cost = output_tokens * (15.00 / 1_000_000)
            total_cost = input_cost + output_cost
            
            print(f"✓ Single call complete")
            print(f"Total cost: ${total_cost:.4f} (£{total_cost * 0.79:.4f})")
            print(f"Total tokens: {total_tokens:,}")
            
            return {
                'company_name': company_name,
                'ticker': ticker,
                'old_filing_date': str(old_date),
                'new_filing_date': str(new_date),
                'sections': analyses,
                'total_cost_usd': round(total_cost, 4),
                'total_cost_gbp': round(total_cost * 0.79, 4),
                'total_tokens': total_tokens,
                'generated_at': None
            }
            
        except Exception as e:
            print(f"✗ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Fall back to empty analyses
            return {
                'company_name': company_name,
                'ticker': ticker,
                'old_filing_date': str(old_date),
                'new_filing_date': str(new_date),
                'sections': [
                    {'section': name, 'has_changes': False, 'summary': f'Error: {str(e)}', 'status': 'error'}
                    for name in ['Item 1', 'Item 1A', 'Item 7', 'Item 8']
                ],
                'total_cost_usd': 0,
                'total_cost_gbp': 0,
                'total_tokens': 0,
                'generated_at': None
            }
    
    def format_report_text(self, analysis_result: Dict) -> str:
        """
        Format the analysis result as readable text (for console output or text file)
        """
        report = f"""
{'='*80}
SEC 10-K CHANGE ANALYSIS
{'='*80}

Company: {analysis_result['company_name']} ({analysis_result['ticker']})
Old Filing: {analysis_result['old_filing_date']}
New Filing: {analysis_result['new_filing_date']}

{'='*80}

"""
        
        for section_analysis in analysis_result['sections']:
            report += f"\n{section_analysis['section']}\n"
            report += f"{'-'*80}\n\n"
            report += f"{section_analysis['summary']}\n\n"
        
        report += f"""
{'='*80}
REPORT METADATA
{'='*80}

Total Analysis Cost: ${analysis_result['total_cost_usd']} (£{analysis_result['total_cost_gbp']})
Total Tokens: {analysis_result['total_tokens']:,}

Generated: {analysis_result.get('generated_at', 'N/A')}
"""
        
        return report


if __name__ == "__main__":
    # This will be tested as part of the full pipeline
    print("AI Analyzer module loaded")
    print("To test, run the full validation pipeline with: python validation_pipeline.py")