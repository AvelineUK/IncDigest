"""
Debug Pfizer cross-reference filtering
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

# The interfering Item 8 is at position 323,064
pos = 323064

# Get context before
context_before = all_text_lower[max(0, pos-50):pos]

print("Testing cross-reference patterns on Pfizer's interfering Item 8:")
print("="*80)
print(f"\nContext before position {pos}:")
print(f"'{context_before}'")

# Test patterns
cross_ref_patterns = [
    r'see\s+item',
    r'in\s+item',
    r'to\s+item', 
    r'refer.*item',
    r'discuss.*item',
    r'includ.*item',
    r'describ.*item',
]

print(f"\nPattern matching results:")
for pattern in cross_ref_patterns:
    match = re.search(pattern, context_before)
    if match:
        print(f"  ✓ '{pattern}' matched: '{match.group()}'")
    else:
        print(f"  ✗ '{pattern}' did not match")

# Overall result
is_reference = False
for ref_pattern in cross_ref_patterns:
    if re.search(ref_pattern, context_before):
        is_reference = True
        break

print(f"\nFinal result: is_reference = {is_reference}")
print(f"Should be: True (this IS a cross-reference)")
