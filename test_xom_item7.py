"""
Test XOM Item 7 with the fix
"""

from sec_fetcher import SECFetcher

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

print("Testing XOM Item 7 extraction...")
item7 = fetcher.extract_section(html, 'Item 7')

if item7:
    print(f"\n✓ SUCCESS! Extracted {len(item7):,} characters ({len(item7.split())} words)")
else:
    print("\n✗ FAILED")
