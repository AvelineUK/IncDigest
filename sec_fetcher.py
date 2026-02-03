"""
SEC EDGAR 10-K Fetcher and Parser
Fetches 10-K filings from SEC EDGAR and extracts relevant sections
"""

import requests
import requests.exceptions
import time
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Tuple
import re
from datetime import datetime

# Import local cache
try:
    from local_cache import get_cache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False

class SECFetcher:
    """Handles fetching and parsing of SEC 10-K filings"""
    
    BASE_URL = "https://www.sec.gov"
    RATE_LIMIT_DELAY = 0.2  # SEC allows 10 requests/second, using 5/second to be safe
    
    # Required headers for SEC EDGAR API  
    # SEC requires proper User-Agent with contact information
    HEADERS = {
        'User-Agent': 'SEC Filing Analyzer onbritishpolitics@gmail.com',
        'Accept-Encoding': 'gzip, deflate',
        'Host': 'www.sec.gov'
    }
    
    def __init__(self, use_cache: bool = True):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self.use_cache = use_cache and CACHE_AVAILABLE
        
        if self.use_cache:
            self.cache = get_cache()
            print("✓ Local caching enabled")
        else:
            self.cache = None
            if use_cache and not CACHE_AVAILABLE:
                print("⚠ Cache requested but local_cache module not available")
    
    def get_company_cik(self, ticker: str) -> Optional[str]:
        """
        Get CIK number for a given ticker symbol
        Returns CIK with leading zeros (10 digits)
        """
        # SEC maintains a company tickers JSON file
        url = "https://www.sec.gov/files/company_tickers.json"
        
        try:
            time.sleep(self.RATE_LIMIT_DELAY)
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            # Search for ticker in the data
            for entry in data.values():
                if entry['ticker'].upper() == ticker.upper():
                    # Return CIK with leading zeros (10 digits)
                    return str(entry['cik_str']).zfill(10)
            
            print(f"Ticker {ticker} not found in SEC database")
            return None
            
        except Exception as e:
            print(f"Error fetching CIK for {ticker}: {e}")
            return None
    
    def get_latest_10k_filings(self, cik: str, count: int = 2) -> List[Dict]:
        """
        Get the latest N 10-K filings for a company using SEC's JSON API
        This is more reliable than the XML approach
        """
        cik_unpadded = str(int(cik))
        cik_padded = cik  # Keep padded version for JSON API
        
        # Use the newer JSON submissions API
        # Important: URL uses PADDED CIK (with leading zeros)
        url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
        
        # Need special headers for the data.sec.gov API
        json_headers = self.HEADERS.copy()
        json_headers['Accept'] = 'application/json'
        json_headers['Host'] = 'data.sec.gov'
        
        try:
            print(f"Fetching filings via JSON API...")
            time.sleep(self.RATE_LIMIT_DELAY)
            response = self.session.get(url, headers=json_headers)
            response.raise_for_status()
            
            data = response.json()
            
            # Get recent filings
            recent = data.get('filings', {}).get('recent', {})
            
            # Extract 10-K filings
            filings = []
            forms = recent.get('form', [])
            filing_dates = recent.get('filingDate', [])
            accession_numbers = recent.get('accessionNumber', [])
            primary_documents = recent.get('primaryDocument', [])
            company_name = data.get('name', 'Unknown')
            
            for i in range(len(forms)):
                # Include both 10-K and 10-K/A (amendments)
                if forms[i] == '10-K' or forms[i] == '10-K/A':
                    accession = accession_numbers[i]
                    accession_no_hyphens = accession.replace('-', '')
                    
                    # Construct URL to the primary document
                    # Note: Document URLs use UNPADDED CIK
                    primary_doc = primary_documents[i]
                    doc_url = f"https://www.sec.gov/Archives/edgar/data/{cik_unpadded}/{accession_no_hyphens}/{primary_doc}"
                    
                    filings.append({
                        'accession': accession,
                        'accession_no_hyphens': accession_no_hyphens,
                        'filing_date': datetime.strptime(filing_dates[i], '%Y-%m-%d').date(),
                        'company_name': company_name,
                        'filing_url': doc_url,
                        'cik': cik_unpadded,
                        'needs_index_parsing': False  # Direct URL to document
                    })
            
            print(f"Found {len(filings)} 10-K filings")
            
            # Return the requested count
            return filings[:count]
            
        except Exception as e:
            print(f"Error fetching 10-K filings for CIK {cik}: {e}")
            return []
    
    def _get_filings_html_fallback(self, cik: str, count: int = 2) -> List[Dict]:
        """
        Fallback method to get filings by parsing HTML instead of XML
        """
        url = f"{self.BASE_URL}/cgi-bin/browse-edgar"
        params = {
            'action': 'getcompany',
            'CIK': cik,
            'type': '10-K',
            'dateb': '',
            'owner': 'exclude',
            'count': str(count * 2)  # Get more in case some aren't 10-K annual reports
        }
        
        try:
            time.sleep(self.RATE_LIMIT_DELAY)
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the results table
            results_table = soup.find('table', class_='tableFile2')
            if not results_table:
                print("Could not find results table in HTML response")
                return []
            
            filings = []
            rows = results_table.find_all('tr')
            
            for row in rows[1:]:  # Skip header row
                cols = row.find_all('td')
                if len(cols) < 4:
                    continue
                
                # Column 0: Filing type
                filing_type = cols[0].text.strip()
                if filing_type != '10-K':
                    continue
                
                # Column 1: Links to documents
                doc_link = cols[1].find('a', id='documentsbutton')
                if not doc_link:
                    continue
                doc_href = doc_link.get('href', '')
                
                # Column 3: Filing date
                filing_date_str = cols[3].text.strip()
                filing_date = datetime.strptime(filing_date_str, '%Y-%m-%d').date()
                
                # Column 4: Accession number
                accession = cols[4].text.strip()
                accession_no_hyphens = accession.replace('-', '')
                
                # Construct filing URL
                # From the documents page, we need to get to the actual filing
                # Format: /cgi-bin/viewer?action=view&cik=...&accession_number=...
                # We'll need to fetch the document page to get the actual filing HTML
                filing_url = self.BASE_URL + doc_href
                
                filings.append({
                    'accession': accession,
                    'accession_no_hyphens': accession_no_hyphens,
                    'filing_date': filing_date,
                    'company_name': 'Unknown',  # Not in this view
                    'filing_url': filing_url,
                    'needs_doc_page_fetch': True
                })
                
                if len(filings) >= count:
                    break
            
            print(f"Found {len(filings)} filings via HTML fallback")
            return filings
            
        except Exception as e:
            print(f"Error in HTML fallback: {e}")
            return []
    
    def fetch_10k_html(self, filing_url: str, needs_index_parsing: bool = False, 
                      accession_no_hyphens: str = None, cik: str = None) -> Optional[str]:
        """
        Fetch the HTML content of a 10-K filing
        Now we get direct URLs from the JSON API, so this is simpler
        """
        # Check cache first
        if self.use_cache and self.cache:
            cached_html = self.cache.get_html(filing_url)
            if cached_html:
                return cached_html
        
        max_retries = 3
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                if needs_index_parsing:
                    # Old path - parse index to find document
                    # (keeping for backwards compatibility but shouldn't be used)
                    print(f"    Fetching index page... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(self.RATE_LIMIT_DELAY)
                    
                    response = self.session.get(filing_url, timeout=30)
                    
                    if response.status_code == 503:
                        if attempt < max_retries - 1:
                            wait_time = retry_delay * (attempt + 1)
                            print(f"    Got 503 error, waiting {wait_time}s before retry...")
                            time.sleep(wait_time)
                            continue
                        else:
                            print(f"    Failed after {max_retries} attempts")
                            return None
                    
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    doc_table = soup.find('table', class_='tableFile')
                    
                    if not doc_table:
                        print("    Could not find document table")
                        return None
                    
                    primary_doc_url = None
                    for row in doc_table.find_all('tr')[1:]:
                        cols = row.find_all('td')
                        if len(cols) < 4:
                            continue
                        
                        doc_link = cols[2].find('a')
                        if not doc_link:
                            continue
                        
                        doc_type = cols[3].text.strip()
                        filename = doc_link.text.strip()
                        
                        if (filename.endswith('.htm') or filename.endswith('.html')):
                            if '10-K' in doc_type and 'EX-' not in filename:
                                doc_href = doc_link.get('href', '')
                                if doc_href:
                                    primary_doc_url = self.BASE_URL + doc_href
                                    print(f"    Found primary document: {filename}")
                                    break
                    
                    if not primary_doc_url:
                        print("    Could not find primary document")
                        return None
                    
                    filing_url = primary_doc_url
                
                # Fetch the document (either direct URL or found from index)
                time.sleep(self.RATE_LIMIT_DELAY)
                response = self.session.get(filing_url, timeout=30)
                
                if response.status_code == 503:
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (attempt + 1)
                        print(f"    Got 503 error, waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                        continue
                    else:
                        return None
                
                response.raise_for_status()
                html_content = response.text
                
                # Save to cache
                if self.use_cache and self.cache:
                    metadata = {
                        'accession': accession_no_hyphens,
                        'cik': cik
                    }
                    self.cache.save_html(filing_url, html_content, metadata)
                
                return html_content
                    
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (attempt + 1)
                    print(f"    Error: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"    Error after {max_retries} attempts: {e}")
                    return None
            except Exception as e:
                print(f"    Unexpected error: {e}")
                return None
        
        return None
    
    def extract_section(self, html_content: str, section_name: str) -> Optional[str]:
        """
        Extract a specific section from 10-K HTML
        
        Strategy: Find ALL occurrences of the section marker, then pick the one
        with the most content between it and the next section. The real section
        will have thousands of words; TOC entries will have very little.
        
        Special handling:
        - Item 8: Financial statements are in a separate section with auditor report
        - Item 7: MD&A content must be at least 10K chars to avoid TOC entries
        """
        # Get all text
        all_text = BeautifulSoup(html_content, 'html.parser').get_text()
        all_text_lower = all_text.lower()
        
        # Special handling for Item 8 - Financial Statements
        if section_name == 'Item 8':
            return self._extract_financial_statements(all_text, all_text_lower)
        
        # Special handling for Item 7 - MD&A (Management's Discussion and Analysis)
        # Some companies just have a pointer in Item 7, actual content is elsewhere
        if section_name == 'Item 7':
            return self._extract_mda(all_text, all_text_lower)
        
        # Define patterns for other sections
        section_patterns = {
            'Item 1': r'item\s*1\b',
            'Item 1A': r'item\s*1a\b',
            'Item 7': r'item\s*7\b',
        }
        
        # Define what comes next after each section
        next_section_patterns = {
            'Item 1': [r'item\s*1a\b', r'item\s*2\b'],
            'Item 1A': [r'item\s*1b\b', r'item\s*2\b'],
            'Item 7': [r'item\s*7a\b', r'item\s*8\b'],
        }
        
        # Minimum length thresholds to filter out TOC entries
        min_length_thresholds = {
            'Item 1': 1000,
            'Item 1A': 1000,
            'Item 7': 10000,  # MD&A is always substantial, use higher threshold
        }
        
        if section_name not in section_patterns:
            print(f"Unknown section: {section_name}")
            return None
        
        # Find ALL occurrences of this section
        pattern = section_patterns[section_name]
        regex = re.compile(pattern, re.IGNORECASE)
        
        section_matches = []
        for match in regex.finditer(all_text_lower):
            section_matches.append(match.start())
        
        if not section_matches:
            print(f"Could not find {section_name} in text")
            return None
        
        # Find ALL occurrences of next sections
        next_patterns = next_section_patterns[section_name]
        next_section_matches = []
        
        for next_pattern in next_patterns:
            next_regex = re.compile(next_pattern, re.IGNORECASE)
            for match in next_regex.finditer(all_text_lower):
                pos = match.start()
                
                # Filter out cross-references (e.g., "see Item 8" or "in Item 8")
                # We need to look at text before AND include the actual "item X" part
                context_before = all_text_lower[max(0, pos-50):pos]
                context_at = all_text_lower[pos:pos+10]  # "item 7a" or "item 8"
                combined_context = context_before + context_at
                
                # Look for patterns that indicate cross-references
                # like "see Item X", "refer to Item X", "discussed in Item X"
                cross_ref_patterns = [
                    r'see\s+item',
                    r'in\s+item',
                    r'to\s+item', 
                    r'refer.*item',
                    r'discuss.*item',
                    r'includ.*item',
                    r'describ.*item',
                ]
                
                is_reference = False
                for ref_pattern in cross_ref_patterns:
                    if re.search(ref_pattern, combined_context):
                        is_reference = True
                        break
                
                if not is_reference:
                    next_section_matches.append(pos)
        
        if not next_section_matches:
            # No next section found, use end of document
            next_section_matches = [len(all_text)]
        
        # For each section occurrence, find the nearest next section
        # and calculate content length
        candidates = []
        
        for section_pos in section_matches:
            # Find the closest next section AFTER this position
            valid_next = [n for n in next_section_matches if n > section_pos]
            
            if valid_next:
                next_pos = min(valid_next)
                content_length = next_pos - section_pos
                
                candidates.append({
                    'start': section_pos,
                    'end': next_pos,
                    'length': content_length
                })
        
        if not candidates:
            print(f"Could not find valid section boundaries for {section_name}")
            return None
        
        # Get minimum threshold for this section
        min_threshold = min_length_thresholds.get(section_name, 1000)
        
        # Filter out candidates that are too short (TOC entries)
        valid_candidates = [c for c in candidates if c['length'] >= min_threshold]
        
        if not valid_candidates:
            print(f"Longest match for {section_name} is only {max(candidates, key=lambda x: x['length'])['length']} chars (likely no real content)")
            return None
        
        # Pick the candidate with the LONGEST content from valid candidates
        best_candidate = max(valid_candidates, key=lambda x: x['length'])
        
        # Extract the content
        section_text = all_text[best_candidate['start']:best_candidate['end']]
        section_text = section_text.strip()
        
        print(f"    Found {section_name} at position {best_candidate['start']:,}")
        print(f"    Extracted {len(section_text):,} characters")
        
        return section_text
    
    def _extract_financial_statements(self, all_text: str, all_text_lower: str) -> Optional[str]:
        """
        Special extraction for Item 8 - Financial Statements
        
        Item 8 often just says "see page X for financial statements" so we need
        to find the actual financial statements section which has universal markers:
        - Report of Independent Registered Public Accounting Firm (auditor report)
        - Consolidated Statements of Income/Operations
        - Consolidated Balance Sheets
        
        This works for all companies since these are required by SEC.
        """
        # Look for the auditor's report - this marks the start of financials
        auditor_patterns = [
            r'report of independent registered public accounting firm',
            r'independent auditor',
        ]
        
        financial_start = None
        for pattern in auditor_patterns:
            regex = re.compile(pattern, re.IGNORECASE)
            matches = list(regex.finditer(all_text_lower))
            
            if matches:
                # Use the first occurrence (should be the actual report, not references)
                financial_start = matches[0].start()
                print(f"    Found financial statements starting at position {financial_start:,}")
                break
        
        if not financial_start:
            print(f"Could not find auditor's report for Item 8")
            return None
        
        # Look for the end of financial statements
        # Usually marked by Item 9 or "Item 15" (exhibits) or just use a reasonable chunk
        end_patterns = [
            r'item\s*9\b',
            r'item\s*15\b',
        ]
        
        financial_end = len(all_text)  # Default to end of document
        
        for pattern in end_patterns:
            regex = re.compile(pattern, re.IGNORECASE)
            for match in regex.finditer(all_text_lower):
                pos = match.start()
                # Must be after financial start
                if pos > financial_start + 10000:  # At least 10K chars of content
                    financial_end = pos
                    break
            if financial_end < len(all_text):
                break
        
        # Extract financial statements
        section_text = all_text[financial_start:financial_end].strip()
        
        # Sanity check
        if len(section_text) < 5000:
            print(f"Financial statements section only {len(section_text)} chars (too short)")
            return None
        
        print(f"    Extracted {len(section_text):,} characters")
        
        return section_text
    
    def _extract_mda(self, all_text: str, all_text_lower: str) -> Optional[str]:
        """
        Special extraction for Item 7 - Management's Discussion and Analysis (MD&A)
        
        Similar to Item 8, some companies just have a pointer in Item 7 that says
        "see the Financial Section". We need to find the actual MD&A content.
        
        Universal markers for MD&A:
        - "Management's Discussion and Analysis of Financial Condition and Results of Operations"
        - Often followed by sections like "Results of Operations", "Liquidity"
        """
        # Look for the actual MD&A section
        # It usually starts with a full heading of MD&A
        mda_patterns = [
            r"management'?s\s+discussion\s+and\s+analysis\s+of\s+financial\s+condition\s+and\s+results\s+of\s+operations",
            r"results\s+of\s+operations",  # Common MD&A subsection
        ]
        
        mda_start = None
        
        for pattern in mda_patterns:
            regex = re.compile(pattern, re.IGNORECASE)
            matches = list(regex.finditer(all_text_lower))
            
            if matches:
                # Look for a match that has substantial content after it
                # (not just a TOC reference)
                for match in matches:
                    pos = match.start()
                    
                    # Check if this looks like actual content (not TOC)
                    # Look ahead to see if there's substantial text
                    lookahead = all_text_lower[pos:pos+2000]
                    
                    # Real MD&A will have detailed narrative, not just page numbers
                    if len(lookahead) > 1000 and 'page' not in lookahead[:200]:
                        mda_start = pos
                        print(f"    Found MD&A content starting at position {mda_start:,}")
                        break
                
                if mda_start:
                    break
        
        if not mda_start:
            print(f"Could not find MD&A content for Item 7")
            # Fall back to standard extraction
            return None
        
        # Look for the end of MD&A
        # Usually marked by Item 7A or Item 8
        end_patterns = [
            r'item\s*7a\b',
            r'item\s*8\b',
        ]
        
        mda_end = len(all_text)  # Default to end of document
        
        for pattern in end_patterns:
            regex = re.compile(pattern, re.IGNORECASE)
            for match in regex.finditer(all_text_lower):
                pos = match.start()
                # Must be after MD&A start and look like a real section header
                if pos > mda_start + 10000:  # At least 10K chars of content
                    # Check it's not a cross-reference
                    context_before = all_text_lower[max(0, pos-50):pos]
                    skip_words = ['see', ' in ', 'refer', 'discuss']
                    is_reference = any(word in context_before for word in skip_words)
                    
                    if not is_reference:
                        mda_end = pos
                        break
            if mda_end < len(all_text):
                break
        
        # Extract MD&A
        section_text = all_text[mda_start:mda_end].strip()
        
        # Sanity check
        if len(section_text) < 5000:
            print(f"MD&A section only {len(section_text)} chars (too short)")
            return None
        
        print(f"    Extracted {len(section_text):,} characters")
        
        return section_text
    
    def get_10k_sections(self, ticker: str) -> List[Dict]:
        """
        Main method: Get the last 2 10-Ks for a ticker and extract all relevant sections
        Returns list of dicts with filing metadata and extracted sections
        """
        print(f"\n{'='*60}")
        print(f"Fetching 10-K data for {ticker}")
        print(f"{'='*60}\n")
        
        # Get CIK
        cik = self.get_company_cik(ticker)
        if not cik:
            return []
        
        print(f"CIK: {cik}")
        
        # Get latest 2 10-K filings
        filings = self.get_latest_10k_filings(cik, count=2)
        
        if len(filings) < 2:
            print(f"Need at least 2 10-K filings, found {len(filings)}")
            return []
        
        print(f"\nFound {len(filings)} 10-K filings:")
        for i, filing in enumerate(filings):
            print(f"  {i+1}. Filed: {filing['filing_date']} | Accession: {filing['accession']}")
        
        # Extract sections from each filing
        sections_to_extract = ['Item 1', 'Item 1A', 'Item 7', 'Item 8']
        
        results = []
        
        for filing in filings:
            print(f"\nProcessing filing from {filing['filing_date']}...")
            
            needs_index = filing.get('needs_index_parsing', False)
            accession = filing.get('accession_no_hyphens')
            cik = filing.get('cik')
            
            html_content = self.fetch_10k_html(
                filing['filing_url'], 
                needs_index_parsing=needs_index,
                accession_no_hyphens=accession,
                cik=cik
            )
            
            if not html_content:
                print("  Failed to fetch HTML content")
                continue
            
            print(f"  Successfully fetched HTML ({len(html_content):,} characters)")
            
            sections = {}
            for section_name in sections_to_extract:
                print(f"  Extracting {section_name}...", end=' ')
                content = self.extract_section(html_content, section_name)
                
                if content:
                    word_count = len(content.split())
                    print(f"✓ ({word_count} words)")
                    sections[section_name] = content
                else:
                    print("✗ Failed")
            
            filing_data = filing.copy()
            filing_data['sections'] = sections
            results.append(filing_data)
        
        return results


if __name__ == "__main__":
    # Test with a few companies
    test_tickers = ['AAPL', 'MSFT', 'TSLA']
    
    fetcher = SECFetcher()
    
    for ticker in test_tickers:
        filings = fetcher.get_10k_sections(ticker)
        
        if len(filings) >= 2:
            print(f"\n✓ Successfully extracted sections from 2 filings for {ticker}")
        else:
            print(f"\n✗ Failed to get complete data for {ticker}")
        
        print("\n" + "="*60 + "\n")
