"""
Item 1A Specific Diagnostic
"""

from sec_fetcher import SECFetcher
import re

def diagnose_item_1a():
    """Debug why Item 1A extraction is failing"""
    
    print("="*80)
    print("ITEM 1A DIAGNOSTIC")
    print("="*80)
    
    fetcher = SECFetcher()
    
    # Use Apple's known CIK
    cik = '0000320193'
    print(f"Using CIK: {cik}")
    
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
    
    # Manual search for Item 1A
    all_text_lower = html_content.lower()
    
    print("\n" + "="*80)
    print("SEARCHING FOR ALL 'ITEM 1A' OCCURRENCES")
    print("="*80)
    
    pattern = re.compile(r'item\s*1a', re.IGNORECASE)
    matches = []
    
    for match in pattern.finditer(all_text_lower):
        pos = match.start()
        context = html_content[pos:pos+200]
        matches.append((pos, context))
    
    print(f"\nFound {len(matches)} occurrences of 'Item 1A':")
    for i, (pos, context) in enumerate(matches):
        print(f"\n{i+1}. Position {pos:,}:")
        print(f"   Context: {context[:100]}...")
        if pos > 50000:
            print(f"   → This is likely the ACTUAL section (past TOC)")
    
    # Look for Item 1B
    print("\n" + "="*80)
    print("SEARCHING FOR 'ITEM 1B'")
    print("="*80)
    
    pattern_1b = re.compile(r'item\s*1b', re.IGNORECASE)
    matches_1b = []
    
    for match in pattern_1b.finditer(all_text_lower):
        pos = match.start()
        context = html_content[pos:pos+200]
        matches_1b.append((pos, context))
    
    print(f"\nFound {len(matches_1b)} occurrences of 'Item 1B':")
    for i, (pos, context) in enumerate(matches_1b):
        print(f"\n{i+1}. Position {pos:,}:")
        print(f"   Context: {context[:100]}...")
        if pos > 50000:
            print(f"   → This is likely the ACTUAL section (past TOC)")
    
    # Look for Item 2
    print("\n" + "="*80)
    print("SEARCHING FOR 'ITEM 2'")
    print("="*80)
    
    pattern_2 = re.compile(r'item\s*2\b', re.IGNORECASE)
    matches_2 = []
    
    for match in pattern_2.finditer(all_text_lower):
        pos = match.start()
        context = html_content[pos:pos+200]
        matches_2.append((pos, context))
    
    print(f"\nFound {len(matches_2)} occurrences of 'Item 2':")
    for i, (pos, context) in enumerate(matches_2):
        print(f"\n{i+1}. Position {pos:,}:")
        print(f"   Context: {context[:100]}...")
        if pos > 50000:
            print(f"   → This is likely the ACTUAL section (past TOC)")
    
    # Calculate distances
    print("\n" + "="*80)
    print("ANALYSIS")
    print("="*80)
    
    # Find actual Item 1A (after position 50000)
    item1a_pos = None
    for pos, _ in matches:
        if pos > 50000:
            item1a_pos = pos
            break
    
    if not item1a_pos:
        print("\n⚠️  Could not find Item 1A past position 50,000!")
        print("    It might be earlier in the document.")
        if matches:
            item1a_pos = matches[-1][0]  # Use last occurrence
            print(f"    Using last occurrence at position {item1a_pos:,}")
    else:
        print(f"\n✓ Item 1A found at position {item1a_pos:,}")
    
    # Find next section
    next_section_pos = None
    next_section_name = None
    
    for pos, _ in matches_1b:
        if pos > item1a_pos and pos > 50000:
            next_section_pos = pos
            next_section_name = "Item 1B"
            break
    
    if not next_section_pos:
        for pos, _ in matches_2:
            if pos > item1a_pos and pos > 50000:
                next_section_pos = pos
                next_section_name = "Item 2"
                break
    
    if next_section_pos:
        distance = next_section_pos - item1a_pos
        print(f"✓ {next_section_name} found at position {next_section_pos:,}")
        print(f"✓ Distance: {distance:,} characters")
        
        if distance < 100:
            print(f"\n⚠️  PROBLEM: Distance is only {distance} characters!")
            print("    This is why extraction fails (< 100 char minimum)")
            print("\n    The actual Item 1A content must be between different markers.")
            
            # Show what's in between
            print(f"\n    Content between Item 1A and {next_section_name}:")
            print("    " + "-"*76)
            between = html_content[item1a_pos:next_section_pos]
            print(f"    {between}")
            print("    " + "-"*76)
    else:
        print(f"\n⚠️  Could not find next section after Item 1A!")

if __name__ == "__main__":
    diagnose_item_1a()
