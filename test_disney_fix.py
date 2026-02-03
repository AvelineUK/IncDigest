"""
Quick Disney Test - Just test Item 8 extraction
"""

from sec_fetcher import SECFetcher

def test_disney_item8():
    print("="*80)
    print("TESTING DISNEY ITEM 8 EXTRACTION")
    print("="*80)
    
    fetcher = SECFetcher()
    
    # Get Disney's latest filing
    cik = fetcher.get_company_cik('DIS')
    print(f"\nDisney CIK: {cik}")
    
    filings = fetcher.get_latest_10k_filings(cik, count=1)
    
    if not filings:
        print("Failed to fetch filings")
        return
    
    filing = filings[0]
    print(f"Filing date: {filing['filing_date']}")
    
    # Fetch HTML
    print("\nFetching HTML...")
    html_content = fetcher.fetch_10k_html(
        filing['filing_url'],
        needs_index_parsing=filing.get('needs_index_parsing', False),
        accession_no_hyphens=filing.get('accession_no_hyphens'),
        cik=filing.get('cik')
    )
    
    if not html_content:
        print("Failed to fetch HTML")
        return
    
    print(f"HTML fetched: {len(html_content):,} characters")
    
    # Try to extract Item 8
    print("\n" + "="*80)
    print("EXTRACTING ITEM 8")
    print("="*80)
    
    item8 = fetcher.extract_section(html_content, 'Item 8')
    
    if item8:
        print(f"\n✓ SUCCESS!")
        print(f"Extracted: {len(item8):,} characters ({len(item8.split())} words)")
        print(f"\nFirst 500 characters:")
        print("-"*80)
        print(item8[:500])
        print("-"*80)
    else:
        print("\n✗ FAILED - Could not extract Item 8")

if __name__ == "__main__":
    test_disney_item8()
