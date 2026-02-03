"""
Find Disney's actual financial statements
"""

from sec_fetcher import SECFetcher
import re

def find_disney_financials():
    """Find where the actual financial statements are"""
    
    fetcher = SECFetcher()
    
    cik = fetcher.get_company_cik('DIS')
    filings = fetcher.get_latest_10k_filings(cik, count=1)
    
    filing = filings[0]
    
    html_content = fetcher.fetch_10k_html(
        filing['filing_url'],
        needs_index_parsing=filing.get('needs_index_parsing', False),
        accession_no_hyphens=filing.get('accession_no_hyphens'),
        cik=filing.get('cik')
    )
    
    from bs4 import BeautifulSoup
    all_text = BeautifulSoup(html_content, 'html.parser').get_text()
    
    print(f"Total document length: {len(all_text):,} characters")
    
    # Search for common financial statement markers
    searches = [
        r'consolidated statements of income',
        r'consolidated balance sheets',
        r'index to financial statements',
        r'report of independent registered public accounting firm',
    ]
    
    print("\nSearching for financial statement markers:")
    for search_term in searches:
        pattern = re.compile(search_term, re.IGNORECASE)
        matches = list(pattern.finditer(all_text.lower()))
        
        print(f"\n'{search_term}': {len(matches)} occurrence(s)")
        for i, match in enumerate(matches[:3]):  # Show first 3
            pos = match.start()
            context = all_text[pos:pos+150]
            print(f"  {i+1}. Position {pos:,}: {context[:100]}...")

if __name__ == "__main__":
    find_disney_financials()
