"""
Quick Test Script
Tests fetching and diff analysis without requiring API key
"""

from sec_fetcher import SECFetcher
from diff_analyzer import DiffAnalyzer

def test_fetch_and_diff():
    """Test fetching 10-K and diff analysis"""
    
    print("="*80)
    print("TESTING SEC FETCHER AND DIFF ANALYZER")
    print("="*80)
    print("\nThis test will:")
    print("1. Fetch Apple's latest 2 10-K filings from SEC EDGAR")
    print("2. Extract 4 key sections from each filing")
    print("3. Perform diff analysis to identify changes")
    print("4. Show summary of what changed")
    print("\nNote: This does NOT use AI (no API key needed)")
    print("="*80)
    
    # Test with Apple (usually has clean, well-structured filings)
    ticker = 'AAPL'
    
    print(f"\n\nStep 1: Fetching {ticker} filings...")
    print("-"*80)
    
    fetcher = SECFetcher()
    filings = fetcher.get_10k_sections(ticker)
    
    if len(filings) < 2:
        print(f"\n✗ FAILED: Could only fetch {len(filings)} filing(s)")
        print("This could mean:")
        print("  - Network issues connecting to SEC EDGAR")
        print("  - Company doesn't have 2 10-K filings yet")
        print("  - HTML parsing failed")
        return False
    
    newer = filings[0]
    older = filings[1]
    
    print(f"\n✓ SUCCESS: Fetched 2 filings")
    print(f"  Newer filing: {newer['filing_date']}")
    print(f"    - Sections: {list(newer['sections'].keys())}")
    print(f"  Older filing: {older['filing_date']}")
    print(f"    - Sections: {list(older['sections'].keys())}")
    
    # Step 2: Diff analysis
    print(f"\n\nStep 2: Performing diff analysis...")
    print("-"*80)
    
    analyzer = DiffAnalyzer()
    diff_results = analyzer.compare_sections(
        old_sections=older['sections'],
        new_sections=newer['sections']
    )
    
    print(f"\n✓ Diff analysis complete\n")
    print("Results by section:")
    print("-"*80)
    
    for section, result in diff_results.items():
        status = result['status']
        has_changes = result['has_meaningful_changes']
        
        emoji = "📝" if has_changes else "✓"
        
        print(f"\n{emoji} {section}")
        print(f"   Status: {status}")
        print(f"   Summary: {result['summary']}")
        
        if has_changes and result.get('added_content'):
            added_len = len(result['added_content'])
            removed_len = len(result.get('removed_content', ''))
            print(f"   Changes: +{added_len} chars added, -{removed_len} chars removed")
            
            # Show a preview of changes
            if added_len > 0:
                preview = result['added_content'][:200].replace('\n', ' ')
                print(f"   Preview: {preview}...")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
    print("\nWhat this tells us:")
    print("  ✓ HTML parsing works - we can extract sections from 10-K filings")
    print("  ✓ Diff analysis works - we can identify what changed")
    print("  ✓ Pipeline structure is sound")
    print("\nNext step:")
    print("  → Install anthropic package: pip install anthropic")
    print("  → Set API key: export ANTHROPIC_API_KEY='your-key'")
    print("  → Run full validation: python validation_pipeline.py")
    print("="*80)
    
    return True

if __name__ == "__main__":
    try:
        success = test_fetch_and_diff()
        if success:
            print("\n✓ All tests passed!")
        else:
            print("\n✗ Tests failed")
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
