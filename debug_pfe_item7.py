"""
Debug Pfizer Item 7 - see all candidates
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

# Find all Item 7
pattern = re.compile(r'item\s*7\b', re.IGNORECASE)
section_matches = []
for match in pattern.finditer(all_text_lower):
    section_matches.append(match.start())

print(f"Found {len(section_matches)} Item 7 occurrences")

# Find all Item 7A and Item 8
next_patterns = [r'item\s*7a\b', r'item\s*8\b']
next_section_matches = []

for next_pattern in next_patterns:
    next_regex = re.compile(next_pattern, re.IGNORECASE)
    for match in next_regex.finditer(all_text_lower):
        next_section_matches.append(match.start())

print(f"Found {len(next_section_matches)} next section markers (7A or 8)")

# Build all candidates
candidates = []

for section_pos in section_matches:
    valid_next = [n for n in next_section_matches if n > section_pos]
    
    if valid_next:
        next_pos = min(valid_next)
        content_length = next_pos - section_pos
        
        candidates.append({
            'start': section_pos,
            'end': next_pos,
            'length': content_length
        })

print(f"\nAll candidates:")
for i, c in enumerate(candidates):
    print(f"{i+1}. Start: {c['start']:,}, Length: {c['length']:,} chars")
    if c['length'] >= 10000:
        print(f"   ✓ Above 10K threshold")
    else:
        print(f"   ✗ Below 10K threshold - FILTERED OUT")

# Filter
valid_candidates = [c for c in candidates if c['length'] >= 10000]
print(f"\nValid candidates after filtering: {len(valid_candidates)}")

if valid_candidates:
    best = max(valid_candidates, key=lambda x: x['length'])
    print(f"\nBest candidate: {best['length']:,} chars at position {best['start']:,}")
else:
    print("\n✗ No valid candidates found!")
    print(f"\nLongest candidate was: {max(candidates, key=lambda x: x['length'])['length']:,} chars")
