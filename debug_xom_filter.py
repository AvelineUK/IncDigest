"""
Debug XOM Item 7A filtering
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

# XOM's Item 7A is at position 162,200
pos = 162200

# Get context
context_before = all_text_lower[max(0, pos-50):pos]
context_at = all_text_lower[pos:pos+10]
combined_context = context_before + context_at

print("Testing XOM's Item 7A at position 162,200:")
print("="*80)
print(f"\nContext before: '{context_before}'")
print(f"Context at: '{context_at}'")
print(f"Combined: '{combined_context}'")

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
    match = re.search(pattern, combined_context)
    if match:
        print(f"  ✓ '{pattern}' matched: '{match.group()}'")
    else:
        print(f"  ✗ '{pattern}' did not match")

# Overall result
is_reference = False
for ref_pattern in cross_ref_patterns:
    if re.search(ref_pattern, combined_context):
        is_reference = True
        break

print(f"\nFinal result: is_reference = {is_reference}")
print(f"Should be: False (this is NOT a cross-reference, it's the real header)")

if is_reference:
    print("\n⚠️  PROBLEM: We're incorrectly filtering the real Item 7A header!")
