"""
Check XOM Item 7 issue
"""

from sec_fetcher import SECFetcher
import re
from bs4 import BeautifulSoup

fetcher = SECFetcher()

cik = fetcher.get_company_cik('XOM')
print(f"ExxonMobil CIK: {cik}")

filings = fetcher.get_latest_10k_filings(cik, count=1)
filing = filings[0]

html = fetcher.fetch_10k_html(
    filing['filing_url'],
    needs_index_parsing=filing.get('needs_index_parsing', False),
    accession_no_hyphens=filing.get('accession_no_hyphens'),
    cik=filing.get('cik')
)

print(f"HTML size: {len(html):,} characters")

all_text = BeautifulSoup(html, 'html.parser').get_text()
all_text_lower = all_text.lower()

# Find all Item 7 occurrences
pattern = re.compile(r'item\s*7\b', re.IGNORECASE)
item7_matches = []

for match in pattern.finditer(all_text_lower):
    pos = match.start()
    context = all_text[pos:pos+200]
    item7_matches.append((pos, context))

print(f"\nFound {len(item7_matches)} 'Item 7' occurrences:")
for i, (pos, context) in enumerate(item7_matches):
    print(f"\n{i+1}. Position {pos:,}:")
    print(f"   {context[:150]}...")

# Find Item 7A and Item 8
pattern_7a = re.compile(r'item\s*7a\b', re.IGNORECASE)
pattern_8 = re.compile(r'item\s*8\b', re.IGNORECASE)

item7a_matches = [m.start() for m in pattern_7a.finditer(all_text_lower)]
item8_matches = [m.start() for m in pattern_8.finditer(all_text_lower)]

print(f"\n\nFound {len(item7a_matches)} 'Item 7A' occurrences")
print(f"Found {len(item8_matches)} 'Item 8' occurrences")

# Calculate distances
print("\n\nAnalyzing Item 7 → next section distances:")
for i7_pos, _ in item7_matches:
    # Find nearest Item 7A or Item 8
    all_next = item7a_matches + item8_matches
    valid_next = [n for n in all_next if n > i7_pos]
    
    if valid_next:
        next_pos = min(valid_next)
        distance = next_pos - i7_pos
        
        # Check if it's a cross-reference
        context_before = all_text_lower[max(0, next_pos-30):next_pos]
        skip_words = ['see', ' in ', 'to ', 'refer', 'discuss', 'includ', 'describ']
        is_reference = any(word in context_before for word in skip_words)
        
        ref_marker = " (CROSS-REF - FILTERED)" if is_reference else ""
        print(f"Item 7 at {i7_pos:,} → next at {next_pos:,} = {distance:,} chars{ref_marker}")
