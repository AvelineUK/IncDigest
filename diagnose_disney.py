"""
Disney Item 8 Diagnostic
"""

from sec_fetcher import SECFetcher
import re

def diagnose_disney_item8():
    """Debug why Disney Item 8 extraction is failing"""
    
    fetcher = SECFetcher()
    
    # Disney
    cik = fetcher.get_company_cik('DIS')
    print(f"Disney CIK: {cik}")
    
    filings = fetcher.get_latest_10k_filings(cik, count=1)
    
    if not filings:
        print("Failed to fetch filings")
        return
    
    filing = filings[0]
    print(f"\nFiling: {filing['filing_date']}")
    
    # Fetch HTML
    html_content = fetcher.fetch_10k_html(
        filing['filing_url'],
        needs_index_parsing=filing.get('needs_index_parsing', False),
        accession_no_hyphens=filing.get('accession_no_hyphens'),
        cik=filing.get('cik')
    )
    
    if not html_content:
        print("Failed to fetch HTML")
        return
    
    print(f"HTML size: {len(html_content):,} characters")
    
    # Get all text
    from bs4 import BeautifulSoup
    all_text = BeautifulSoup(html_content, 'html.parser').get_text()
    
    # Find all "Item 8" occurrences
    pattern = re.compile(r'item\s*8\b', re.IGNORECASE)
    item8_matches = []
    
    for match in pattern.finditer(all_text.lower()):
        pos = match.start()
        context = all_text[pos:pos+150]
        item8_matches.append((pos, context))
    
    print(f"\nFound {len(item8_matches)} 'Item 8' occurrences:")
    for i, (pos, context) in enumerate(item8_matches[:10]):  # Show first 10
        print(f"\n{i+1}. Position {pos:,}:")
        print(f"   {context[:100]}...")
    
    # Find all "Item 9" occurrences
    pattern9 = re.compile(r'item\s*9\b', re.IGNORECASE)
    item9_matches = []
    
    for match in pattern9.finditer(all_text.lower()):
        pos = match.start()
        context = all_text[pos:pos+150]
        item9_matches.append((pos, context))
    
    print(f"\n\nFound {len(item9_matches)} 'Item 9' occurrences:")
    for i, (pos, context) in enumerate(item9_matches[:10]):  # Show first 10
        print(f"\n{i+1}. Position {pos:,}:")
        print(f"   {context[:100]}...")
    
    # Calculate distances
    print("\n\nAnalyzing all possible Item 8 → Item 9 pairings:")
    for i8_pos, i8_ctx in item8_matches:
        for i9_pos, i9_ctx in item9_matches:
            if i9_pos > i8_pos:
                distance = i9_pos - i8_pos
                print(f"Item 8 at {i8_pos:,} → Item 9 at {i9_pos:,} = {distance:,} chars")
                break  # Only show first valid next section

if __name__ == "__main__":
    diagnose_disney_item8()
