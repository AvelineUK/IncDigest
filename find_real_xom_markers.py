"""
Find real (non-reference) Item 7A/8 for XOM
"""

from sec_fetcher import SECFetcher
import re
from bs4 import BeautifulSoup

fetcher = SECFetcher()

cik = fetcher.get_company_cik('XOM')
filings = fetcher.get_latest_10k_filings(cik, count=1)
filing = filings[0]

html = fetcher.fetch_10k_html(
    filing['filing_url'],
    needs_index_parsing=filing.get('needs_index_parsing', False),
    accession_no_hyphens=filing.get('accession_no_hyphens'),
    cik=filing.get('cik')
)

all_text = BeautifulSoup(html, 'html.parser').get_text()
all_text_lower = all_text.lower()

item7_pos = 161937

print("Looking for REAL (non-reference) Item 7A and Item 8 after Item 7:")
print("="*80)

pattern_7a = re.compile(r'item\s*7a\b', re.IGNORECASE)
pattern_8 = re.compile(r'item\s*8\b', re.IGNORECASE)

skip_words = ['see', ' in ', 'to ', 'refer', 'discuss', 'includ', 'describ']

valid_markers = []

print("\nAll Item 7A:")
for match in pattern_7a.finditer(all_text_lower):
    pos = match.start()
    if pos > item7_pos:
        context_before = all_text_lower[max(0, pos-30):pos]
        is_reference = any(word in context_before for word in skip_words)
        
        if not is_reference:
            valid_markers.append(('Item 7A', pos))
            context = all_text[pos:pos+100]
            print(f"  ✓ VALID at {pos:,}: {context[:80]}...")

print("\nAll Item 8:")
for match in pattern_8.finditer(all_text_lower):
    pos = match.start()
    if pos > item7_pos:
        context_before = all_text_lower[max(0, pos-30):pos]
        is_reference = any(word in context_before for word in skip_words)
        
        if not is_reference:
            valid_markers.append(('Item 8', pos))
            context = all_text[pos:pos+100]
            print(f"  ✓ VALID at {pos:,}: {context[:80]}...")

print("\n" + "="*80)
if valid_markers:
    valid_markers.sort(key=lambda x: x[1])
    first_valid = valid_markers[0]
    print(f"\nFirst valid marker: {first_valid[0]} at position {first_valid[1]:,}")
    print(f"Distance from Item 7: {first_valid[1] - item7_pos:,} characters")
else:
    print("\n✗ NO VALID MARKERS FOUND!")
    print("This means all Item 7A/8 markers are filtered as cross-references")
