"""
Check what's at position 323,064 that's being detected as Item 7A/8
"""

from sec_fetcher import SECFetcher
import re
from bs4 import BeautifulSoup

fetcher = SECFetcher()

cik = fetcher.get_company_cik('PFE')
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

# Item 7 is at 322,603
item7_pos = 322603

# Find all Item 7A/8 after this
print("Looking for all Item 7A and Item 8 markers after position 322,603:")
print("="*80)

# Item 7A
pattern_7a = re.compile(r'item\s*7a\b', re.IGNORECASE)
for match in pattern_7a.finditer(all_text_lower):
    pos = match.start()
    if pos > item7_pos:
        context = all_text[pos-50:pos+150]
        print(f"\nItem 7A at position {pos:,} (distance: {pos-item7_pos:,} chars)")
        print(f"Context: {context}")
        if pos < item7_pos + 5000:  # Show first few
            print("^ This is the one being picked!")

print("\n" + "="*80)

# Item 8
pattern_8 = re.compile(r'item\s*8\b', re.IGNORECASE)
for match in pattern_8.finditer(all_text_lower):
    pos = match.start()
    if pos > item7_pos:
        context = all_text[pos-50:pos+150]
        print(f"\nItem 8 at position {pos:,} (distance: {pos-item7_pos:,} chars)")
        print(f"Context: {context}")
        if pos < item7_pos + 5000:  # Show first few
            print("^ This is the one being picked!")
