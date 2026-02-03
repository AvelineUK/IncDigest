"""
Validation Pipeline
End-to-end testing of 10-K analysis pipeline
Fetches filings → Performs diff → Generates AI summaries
"""

import os
import sys
import json
from datetime import datetime
from typing import List, Dict, Optional

from sec_fetcher import SECFetcher
from diff_analyzer import DiffAnalyzer
from ai_analyzer import AIAnalyzer


class ValidationPipeline:
    """Full pipeline for validating 10-K analysis"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.fetcher = SECFetcher()
        self.diff_analyzer = DiffAnalyzer()
        self.ai_analyzer = AIAnalyzer(api_key=api_key)
    
    def run_full_analysis(self, ticker: str) -> Dict:
        """
        Run complete analysis for a single ticker
        
        Steps:
        1. Fetch latest 2 10-K filings
        2. Extract relevant sections
        3. Perform diff analysis
        4. Generate AI summaries
        5. Return structured results
        """
        print(f"\n{'#'*80}")
        print(f"# VALIDATION PIPELINE: {ticker}")
        print(f"{'#'*80}\n")
        
        # Step 1: Fetch filings and extract sections
        print("STEP 1: Fetching 10-K filings and extracting sections...")
        filings = self.fetcher.get_10k_sections(ticker)
        
        if len(filings) < 2:
            return {
                'ticker': ticker,
                'status': 'error',
                'error': f'Need 2 filings, found {len(filings)}'
            }
        
        newer_filing = filings[0]  # Most recent
        older_filing = filings[1]  # Previous year
        
        print(f"\n✓ Successfully fetched filings:")
        print(f"  Newer: {newer_filing['filing_date']} ({len(newer_filing['sections'])} sections)")
        print(f"  Older: {older_filing['filing_date']} ({len(older_filing['sections'])} sections)")
        
        # Step 2: Perform diff analysis
        print("\nSTEP 2: Performing diff analysis...")
        diff_results = self.diff_analyzer.compare_sections(
            old_sections=older_filing['sections'],
            new_sections=newer_filing['sections']
        )
        
        print(f"\n✓ Diff analysis complete:")
        for section, result in diff_results.items():
            status = result['status']
            emoji = '📝' if result['has_meaningful_changes'] else '✓'
            print(f"  {emoji} {section}: {status}")
        
        # Step 3: Generate AI summaries
        print("\nSTEP 3: Generating AI summaries...")
        analysis_result = self.ai_analyzer.analyze_all_sections(
            company_name=newer_filing['company_name'],
            ticker=ticker,
            old_date=older_filing['filing_date'],
            new_date=newer_filing['filing_date'],
            diff_results=diff_results
        )
        
        # Add filing metadata
        analysis_result['older_filing'] = {
            'accession': older_filing['accession'],
            'filing_date': str(older_filing['filing_date']),
            'url': older_filing['filing_url']
        }
        analysis_result['newer_filing'] = {
            'accession': newer_filing['accession'],
            'filing_date': str(newer_filing['filing_date']),
            'url': newer_filing['filing_url']
        }
        analysis_result['generated_at'] = datetime.now().isoformat()
        analysis_result['status'] = 'success'
        
        return analysis_result
    
    def run_batch_analysis(self, tickers: List[str]) -> Dict:
        """
        Run analysis on multiple tickers
        Useful for validation testing across different companies
        """
        results = []
        total_cost = 0.0
        
        for ticker in tickers:
            try:
                result = self.run_full_analysis(ticker)
                results.append(result)
                
                if result.get('total_cost_usd'):
                    total_cost += result['total_cost_usd']
                
            except Exception as e:
                print(f"\n✗ Error processing {ticker}: {e}")
                results.append({
                    'ticker': ticker,
                    'status': 'error',
                    'error': str(e)
                })
        
        return {
            'results': results,
            'total_cost_usd': round(total_cost, 2),
            'total_cost_gbp': round(total_cost * 0.79, 2),
            'analyzed_at': datetime.now().isoformat()
        }
    
    def save_results(self, results: Dict, output_dir: str = './validation_results'):
        """Save validation results to files"""
        try:
            print(f"\n[DEBUG] Attempting to save results...")
            print(f"[DEBUG] Output directory: {output_dir}")
            print(f"[DEBUG] Current working directory: {os.getcwd()}")
            
            # Create directory
            os.makedirs(output_dir, exist_ok=True)
            print(f"[DEBUG] Directory created/verified: {output_dir}")
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Save JSON results
            json_path = os.path.join(output_dir, f'validation_{timestamp}.json')
            print(f"[DEBUG] Saving JSON to: {json_path}")
            
            with open(json_path, 'w') as f:
                json.dump(results, f, indent=2)
            
            print(f"\n✓ Results saved to: {json_path}")
            
            # Generate text reports for each ticker
            if 'results' not in results:
                print(f"[DEBUG] No 'results' key in results dict. Keys: {results.keys()}")
                return
            
            print(f"[DEBUG] Found {len(results['results'])} results to process")
            
            for i, result in enumerate(results['results']):
                print(f"[DEBUG] Processing result {i+1}: {result.get('ticker', 'unknown')}")
                print(f"[DEBUG] Result status: {result.get('status', 'unknown')}")
                
                if result.get('status') == 'success':
                    ticker = result['ticker']
                    
                    print(f"[DEBUG] Generating text report for {ticker}...")
                    try:
                        text_report = self.ai_analyzer.format_report_text(result)
                        print(f"[DEBUG] Report generated, length: {len(text_report)} chars")
                    except Exception as e:
                        print(f"[DEBUG] Error generating report: {e}")
                        import traceback
                        traceback.print_exc()
                        continue
                    
                    report_path = os.path.join(output_dir, f'{ticker}_{timestamp}.txt')
                    print(f"[DEBUG] Saving report to: {report_path}")
                    
                    try:
                        with open(report_path, 'w', encoding='utf-8') as f:
                            f.write(text_report)
                        print(f"  ✓ Report for {ticker}: {report_path}")
                    except Exception as e:
                        print(f"[DEBUG] Error writing file: {e}")
                        import traceback
                        traceback.print_exc()
                else:
                    print(f"[DEBUG] Skipping {result.get('ticker', 'unknown')} - status is {result.get('status')}")
                    
        except Exception as e:
            print(f"\n[ERROR] Failed to save results: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main validation runner"""
    
    # Load .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✓ Loaded .env file")
    except ImportError:
        print("⚠ python-dotenv not installed, trying environment variable")
    
    # Check for API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not found")
        print("\nPlease either:")
        print("  1. Create a .env file with: ANTHROPIC_API_KEY=sk-ant-your-key")
        print("  2. Or set environment variable: $env:ANTHROPIC_API_KEY='your-key'")
        sys.exit(1)
    
    print(f"✓ API key found")
    
    # Final stress test - completely different industries and company types
    test_tickers = [
        'PFE',   # Pfizer - Big pharma, heavily regulated, R&D intensive
        'XOM',   # ExxonMobil - Energy/oil & gas, different accounting standards
        'ABNB',  # Airbnb - Newer IPO (2020), platform/marketplace model
        'GS',    # Goldman Sachs - Financial services, complex instruments
    ]
    
    print("="*80)
    print("SEC 10-K ANALYSIS - FINAL VALIDATION (DIVERSE INDUSTRIES)")
    print("="*80)
    print(f"\nTesting {len(test_tickers)} completely different companies:")
    for ticker in test_tickers:
        print(f"  • {ticker}")
    print("\nThis will:")
    print("  1. Fetch latest 2 10-K filings")
    print("  2. Extract 4 key sections (including fixed Item 8 handling)")
    print("  3. Perform diff analysis")
    print("  4. Generate AI summaries")
    print("  5. Save results")
    print("\nEstimated time: 8-12 minutes")
    print("Estimated cost: ~$0.24 USD (4 companies × ~$0.06)")
    print("="*80)
    
    response = input("\nProceed with validation? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Validation cancelled.")
        return
    
    # Run validation
    pipeline = ValidationPipeline(api_key=api_key)
    results = pipeline.run_batch_analysis(test_tickers)
    
    # Save results
    pipeline.save_results(results)
    
    # Print summary
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    
    successful = sum(1 for r in results['results'] if r.get('status') == 'success')
    failed = len(results['results']) - successful
    
    print(f"\nAnalyzed: {len(results['results'])} companies")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"\nTotal Cost: ${results['total_cost_usd']} USD (£{results['total_cost_gbp']} GBP)")
    
    if successful > 0:
        avg_cost = results['total_cost_usd'] / successful
        print(f"Average Cost per Company: ${avg_cost:.2f} USD")
    
    print("\n" + "="*80)
    print("\nNext steps:")
    print("  1. Review the generated reports in validation_results/")
    print("  2. Evaluate AI summary quality - are they accurate and useful?")
    print("  3. Check if citations are needed (we can add in next iteration)")
    print("  4. If quality is good → proceed to build MVP")
    print("  5. If quality needs work → refine prompts and re-test")
    print("="*80)


if __name__ == "__main__":
    main()
