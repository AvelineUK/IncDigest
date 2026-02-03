"""
Check where XOM's MD&A content actually is
"""

from sec_fetcher import SECFetcher
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

# Show what's at each position
print("Position 161,937 (Item 7 header):")
print("="*80)
print(all_text[161937:162200])
print()

print("Position 162,200 (Item 7A header):")
print("="*80)
print(all_text[162200:162500])
print()

print("Let's look for 'Management's Discussion' which usually starts MD&A:")
import re
pattern = re.compile(r"management'?s discussion", re.IGNORECASE)
matches = list(pattern.finditer(all_text))

print(f"\nFound {len(matches)} occurrences of \"Management's Discussion\":")
for i, match in enumerate(matches):
    pos = match.start()
    context = all_text[pos:pos+200]
    print(f"\n{i+1}. Position {pos:,}:")
    print(f"   {context[:150]}...")
