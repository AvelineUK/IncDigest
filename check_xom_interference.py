"""
Check what's at position 162,200 for XOM
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

# Item 7 is at 161,937
item7_pos = 161937

print("Looking for Item 7A and Item 8 after position 161,937:")
print("="*80)

# Find all next markers
pattern_7a = re.compile(r'item\s*7a\b', re.IGNORECASE)
pattern_8 = re.compile(r'item\s*8\b', re.IGNORECASE)

print("\nItem 7A occurrences:")
for match in pattern_7a.finditer(all_text_lower):
    pos = match.start()
    if pos > item7_pos and pos < item7_pos + 5000:  # Show nearby ones
        context_before = all_text[max(0, pos-50):pos]
        context_after = all_text[pos:pos+150]
        
        skip_words = ['see', ' in ', 'to ', 'refer', 'discuss', 'includ', 'describ']
        is_reference = any(word in context_before.lower() for word in skip_words)
        
        print(f"\nPosition {pos:,} (distance: {pos-item7_pos:,})")
        print(f"Before: ...{context_before[-50:]}")
        print(f"After: {context_after[:100]}...")
        print(f"Is reference? {is_reference}")

print("\n" + "="*80)
print("\nItem 8 occurrences:")
for match in pattern_8.finditer(all_text_lower):
    pos = match.start()
    if pos > item7_pos and pos < item7_pos + 5000:
        context_before = all_text[max(0, pos-50):pos]
        context_after = all_text[pos:pos+150]
        
        skip_words = ['see', ' in ', 'to ', 'refer', 'discuss', 'includ', 'describ']
        is_reference = any(word in context_before.lower() for word in skip_words)
        
        print(f"\nPosition {pos:,} (distance: {pos-item7_pos:,})")
        print(f"Before: ...{context_before[-50:]}")
        print(f"After: {context_after[:100]}...")
        print(f"Is reference? {is_reference}")
