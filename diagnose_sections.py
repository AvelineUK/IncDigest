"""
Section Extraction Diagnostic
Shows exactly what we're extracting and why it's so short
"""

from sec_fetcher import SECFetcher
from bs4 import BeautifulSoup
import re

def diagnose_section_extraction():
    """Examine what we're actually extracting from sections"""
    
    print("="*80)
    print("SECTION EXTRACTION DIAGNOSTIC")
    print("="*80)
    
    fetcher = SECFetcher()
    
    # Get Apple's latest filing
    cik = fetcher.get_company_cik('AAPL')
    filings = fetcher.get_latest_10k_filings(cik, count=1)
    
    if not filings:
        print("Failed to fetch filings")
        return
    
    filing = filings[0]
    print(f"\nFiling: {filing['filing_date']}")
    print(f"URL: {filing['filing_url']}")
    
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
    
    print(f"\nHTML size: {len(html_content):,} characters")
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Test extraction for Item 1A (which we know is "working" but too short)
    section_name = 'Item 1A'
    print(f"\n{'='*80}")
    print(f"EXTRACTING: {section_name}")
    print(f"{'='*80}")
    
    patterns = [
        r'item\s*1a',
        r'item\s*1a\s*[\.\-\:]?\s*risk\s*factors',
    ]
    
    # Find the start
    section_start = None
    for pattern in patterns:
        regex = re.compile(pattern, re.IGNORECASE)
        
        for tag in soup.find_all(['p', 'div', 'span', 'b', 'strong', 'h1', 'h2', 'h3', 'h4']):
            text = tag.get_text(strip=True)
            if regex.search(text) and len(text) < 200:
                section_start = tag
                print(f"\nFound start in <{tag.name}>: {text[:100]}...")
                break
        
        if section_start:
            break
    
    if not section_start:
        print("Could not find section start")
        return
    
    # Show what we're collecting
    print(f"\nStarting from: <{section_start.name}>")
    print(f"Text: {section_start.get_text(strip=True)[:200]}...")
    
    # Look for end markers
    next_section_patterns = [r'item\s*1b', r'item\s*2\b']
    
    print(f"\nLooking for next section (Item 1B or Item 2)...")
    
    # Collect content
    content_elements = []
    current = section_start.find_next()
    element_count = 0
    max_to_check = 100  # Only check first 100 elements for diagnostic
    
    while current and element_count < max_to_check:
        # Check if we've hit the next section
        if current.name in ['p', 'div', 'span', 'b', 'strong', 'h1', 'h2', 'h3', 'h4']:
            text = current.get_text(strip=True)
            
            # Check for next section
            is_next_section = False
            for pattern in next_section_patterns:
                if re.search(pattern, text, re.IGNORECASE) and len(text) < 200:
                    is_next_section = True
                    print(f"\nFound next section at element {element_count}: {text[:100]}...")
                    break
            
            if is_next_section:
                break
            
            # Add content
            if text:
                content_elements.append(text)
                if element_count < 5:  # Show first 5 elements
                    print(f"  Element {element_count}: <{current.name}> {text[:80]}...")
        
        current = current.find_next()
        element_count += 1
    
    print(f"\nCollected {len(content_elements)} text elements")
    print(f"Checked {element_count} total elements")
    
    # Join content
    section_content = '\n'.join(filter(None, content_elements))
    
    print(f"\n{'='*80}")
    print("EXTRACTED CONTENT")
    print(f"{'='*80}")
    print(f"Length: {len(section_content)} characters")
    print(f"Word count: {len(section_content.split())} words")
    print(f"\nFirst 500 characters:")
    print("-"*80)
    print(section_content[:500])
    print("-"*80)
    
    if len(section_content) < 1000:
        print("\n⚠️  PROBLEM: Section is too short!")
        print("\nPossible issues:")
        print("1. We're stopping too early (hit wrong 'next section' marker)")
        print("2. We're not collecting all the content (skipping elements)")
        print("3. The HTML structure is different than expected")
        print("\nLet's search the HTML manually...")
        
        # Manual search
        print(f"\n{'='*80}")
        print("MANUAL SEARCH FOR 'ITEM 1A' or 'RISK FACTORS'")
        print(f"{'='*80}")
        
        # Get all text
        all_text = soup.get_text()
        
        # Find Item 1A
        item1a_pos = all_text.lower().find('item 1a')
        if item1a_pos >= 0:
            print(f"\nFound 'Item 1A' at position {item1a_pos:,}")
            print("Context:")
            print(all_text[item1a_pos:item1a_pos+500])
        
        # Look for Item 1B or Item 2
        item1b_pos = all_text.lower().find('item 1b', item1a_pos + 100)
        item2_pos = all_text.lower().find('item 2', item1a_pos + 100)
        
        if item1b_pos >= 0:
            print(f"\n\nFound 'Item 1B' at position {item1b_pos:,}")
            distance = item1b_pos - item1a_pos
            print(f"Distance from Item 1A: {distance:,} characters")
        
        if item2_pos >= 0:
            print(f"\n\nFound 'Item 2' at position {item2_pos:,}")
            distance = item2_pos - item1a_pos
            print(f"Distance from Item 1A: {distance:,} characters")
    else:
        print("\n✓ Section length looks reasonable")

if __name__ == "__main__":
    diagnose_section_extraction()
