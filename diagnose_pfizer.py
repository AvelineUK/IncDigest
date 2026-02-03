"""
Diagnose Pfizer Item 7 Issue
"""

from sec_fetcher import SECFetcher
import re

def diagnose_pfizer_item7():
    """Debug why Pfizer Item 7 extraction is failing"""
    
    fetcher = SECFetcher()
    
    cik = fetcher.get_company_cik('PFE')
    print(f"Pfizer CIK: {cik}")
    
    filings = fetcher.get_latest_10k_filings(cik, count=1)
    
    filing = filings[0]
    print(f"\nFiling: {filing['filing_date']}")
    
    html_content = fetcher.fetch_10k_html(
        filing['filing_url'],
        needs_index_parsing=filing.get('needs_index_parsing', False),
        accession_no_hyphens=filing.get('accession_no_hyphens'),
        cik=filing.get('cik')
    )
    
    print(f"HTML size: {len(html_content):,} characters")
    
    from bs4 import BeautifulSoup
    all_text = BeautifulSoup(html_content, 'html.parser').get_text()
    
    # Find all "Item 7" occurrences
    pattern = re.compile(r'item\s*7\b', re.IGNORECASE)
    item7_matches = []
    
    for match in pattern.finditer(all_text.lower()):
        pos = match.start()
        context = all_text[pos:pos+200]
        item7_matches.append((pos, context))
    
    print(f"\nFound {len(item7_matches)} 'Item 7' occurrences:")
    for i, (pos, context) in enumerate(item7_matches[:10]):
        print(f"\n{i+1}. Position {pos:,}:")
        print(f"   {context[:150]}...")
    
    # Find all "Item 7A" and "Item 8" occurrences
    pattern7a = re.compile(r'item\s*7a\b', re.IGNORECASE)
    item7a_matches = []
    
    for match in pattern7a.finditer(all_text.lower()):
        pos = match.start()
        item7a_matches.append(pos)
    
    pattern8 = re.compile(r'item\s*8\b', re.IGNORECASE)
    item8_matches = []
    
    for match in pattern8.finditer(all_text.lower()):
        pos = match.start()
        item8_matches.append(pos)
    
    print(f"\n\nFound {len(item7a_matches)} 'Item 7A' occurrences")
    print(f"Found {len(item8_matches)} 'Item 8' occurrences")
    
    # Calculate distances
    print("\n\nAnalyzing Item 7 → next section distances:")
    for i7_pos, _ in item7_matches:
        # Find nearest Item 7A or Item 8
        next_pos = None
        next_name = None
        
        for i7a_pos in item7a_matches:
            if i7a_pos > i7_pos:
                next_pos = i7a_pos
                next_name = "Item 7A"
                break
        
        if not next_pos:
            for i8_pos in item8_matches:
                if i8_pos > i7_pos:
                    next_pos = i8_pos
                    next_name = "Item 8"
                    break
        
        if next_pos:
            distance = next_pos - i7_pos
            print(f"Item 7 at {i7_pos:,} → {next_name} at {next_pos:,} = {distance:,} chars")

if __name__ == "__main__":
    diagnose_pfizer_item7()
