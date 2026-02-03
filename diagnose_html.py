"""
Diagnostic Script - Examine 10-K HTML Structure
This helps us understand why section extraction is failing
"""

from sec_fetcher import SECFetcher
from bs4 import BeautifulSoup
import re

def diagnose_filing_structure():
    """Examine the HTML structure of Apple's latest 10-K"""
    
    print("="*80)
    print("DIAGNOSTIC: Examining 10-K HTML Structure")
    print("="*80)
    
    fetcher = SECFetcher()
    
    # Get Apple's CIK
    cik = fetcher.get_company_cik('AAPL')
    print(f"\nCIK: {cik}")
    
    # Get latest filing
    filings = fetcher.get_latest_10k_filings(cik, count=1)
    
    if not filings:
        print("Could not fetch filing")
        return
    
    filing = filings[0]
    print(f"\nFiling Date: {filing['filing_date']}")
    print(f"Accession: {filing['accession']}")
    print(f"URL: {filing['filing_url']}")
    
    # Fetch the HTML
    print("\nFetching HTML content...")
    needs_index = filing.get('needs_index_parsing', False)
    accession = filing.get('accession_no_hyphens')
    cik_num = filing.get('cik')
    
    html_content = fetcher.fetch_10k_html(
        filing['filing_url'],
        needs_index_parsing=needs_index,
        accession_no_hyphens=accession,
        cik=cik_num
    )
    
    if not html_content:
        print("Failed to fetch HTML")
        return
    
    print(f"HTML Length: {len(html_content):,} characters")
    
    # Parse it
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Look for common section markers
    print("\n" + "="*80)
    print("SEARCHING FOR SECTION MARKERS")
    print("="*80)
    
    search_patterns = [
        (r'item\s*1\b', "Item 1 (Business)"),
        (r'item\s*1a', "Item 1A (Risk Factors)"),
        (r'item\s*7\b', "Item 7 (MD&A)"),
        (r'item\s*8\b', "Item 8 (Financial Statements)"),
        (r'part\s*i\b', "Part I"),
        (r'table\s*of\s*contents', "Table of Contents"),
    ]
    
    for pattern, description in search_patterns:
        regex = re.compile(pattern, re.IGNORECASE)
        matches = soup.find_all(string=regex)
        print(f"\n{description}: Found {len(matches)} matches")
        
        if matches:
            # Show first few matches with context
            for i, match in enumerate(matches[:3]):
                parent = match.parent
                if parent:
                    text = parent.get_text(strip=True)[:100]
                    tag_name = parent.name
                    print(f"  Match {i+1}: <{tag_name}> {text}...")
    
    # Look at the overall structure
    print("\n" + "="*80)
    print("DOCUMENT STRUCTURE")
    print("="*80)
    
    # Count different tag types
    tag_counts = {}
    for tag in soup.find_all():
        tag_name = tag.name
        tag_counts[tag_name] = tag_counts.get(tag_name, 0) + 1
    
    print("\nTop tags by count:")
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
    for tag, count in sorted_tags[:15]:
        print(f"  {tag}: {count}")
    
    # Look for any text that might be section headers
    print("\n" + "="*80)
    print("POTENTIAL SECTION HEADERS (short text in bold/strong tags)")
    print("="*80)
    
    headers = []
    for tag in soup.find_all(['b', 'strong', 'h1', 'h2', 'h3', 'h4', 'span']):
        text = tag.get_text(strip=True)
        if len(text) > 5 and len(text) < 100:
            # Check if it looks like a section header
            if any(word in text.lower() for word in ['item', 'part', 'business', 'risk', 'management']):
                headers.append((tag.name, text))
    
    # Show unique headers
    unique_headers = list(set(headers))[:20]
    print(f"\nFound {len(unique_headers)} potential headers (showing first 20):")
    for tag_name, text in unique_headers:
        print(f"  <{tag_name}> {text}")
    
    # Save a sample of the HTML for manual inspection
    print("\n" + "="*80)
    print("SAVING HTML SAMPLE")
    print("="*80)
    
    output_file = "sample_10k.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        # Save first 50,000 characters
        f.write(html_content[:50000])
    
    print(f"\nSaved first 50,000 characters to: {output_file}")
    print("You can open this file in a browser to see the structure")
    
    print("\n" + "="*80)
    print("DIAGNOSIS COMPLETE")
    print("="*80)
    print("\nNext steps:")
    print("1. Look at the 'POTENTIAL SECTION HEADERS' output above")
    print("2. Open sample_10k.html in a browser")
    print("3. Use browser's 'Find' (Ctrl+F) to search for 'Item 1'")
    print("4. See how the actual HTML is structured")
    print("5. We'll update the extraction logic based on what we find")

if __name__ == "__main__":
    diagnose_filing_structure()
