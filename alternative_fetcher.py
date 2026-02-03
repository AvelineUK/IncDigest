"""
Alternative SEC Fetcher - Uses newer JSON API
This might be more reliable than the XML/HTML approach
"""

import requests
import time
import json
from typing import Dict, List, Optional
from datetime import datetime

class AlternativeSECFetcher:
    """Alternative SEC fetcher using JSON API"""
    
    BASE_URL = "https://data.sec.gov"
    RATE_LIMIT_DELAY = 0.2
    
    HEADERS = {
        'User-Agent': 'SEC Filing Analyzer contact@example.com',
        'Accept': 'application/json'
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
    
    def get_cik(self, ticker: str) -> Optional[str]:
        """Get CIK from ticker using SEC's company tickers JSON"""
        url = "https://www.sec.gov/files/company_tickers.json"
        
        try:
            time.sleep(self.RATE_LIMIT_DELAY)
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            
            for entry in data.values():
                if entry['ticker'].upper() == ticker.upper():
                    return str(entry['cik_str']).zfill(10)
            
            return None
        except Exception as e:
            print(f"Error getting CIK: {e}")
            return None
    
    def get_company_filings(self, cik: str) -> List[Dict]:
        """
        Get all filings for a company using the submissions JSON endpoint
        This is more reliable than the browse-edgar endpoint
        """
        cik_unpadded = str(int(cik))
        url = f"{self.BASE_URL}/submissions/CIK{cik}.json"
        
        try:
            print(f"Fetching company submissions from: {url}")
            time.sleep(self.RATE_LIMIT_DELAY)
            response = self.session.get(url)
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
            
            for i in range(len(forms)):
                if forms[i] == '10-K':
                    accession = accession_numbers[i]
                    accession_no_hyphens = accession.replace('-', '')
                    
                    # Construct URL to the primary document
                    primary_doc = primary_documents[i]
                    doc_url = f"https://www.sec.gov/Archives/edgar/data/{cik_unpadded}/{accession_no_hyphens}/{primary_doc}"
                    
                    filings.append({
                        'accession': accession,
                        'accession_no_hyphens': accession_no_hyphens,
                        'filing_date': datetime.strptime(filing_dates[i], '%Y-%m-%d').date(),
                        'company_name': data.get('name', 'Unknown'),
                        'filing_url': doc_url,
                        'cik': cik_unpadded
                    })
            
            print(f"Found {len(filings)} 10-K filings")
            return filings[:10]  # Return up to 10 most recent
            
        except Exception as e:
            print(f"Error fetching company filings: {e}")
            return []


# Test it
if __name__ == "__main__":
    print("Testing Alternative SEC Fetcher...")
    print("="*60)
    
    fetcher = AlternativeSECFetcher()
    
    ticker = 'AAPL'
    cik = fetcher.get_cik(ticker)
    
    if cik:
        print(f"\nCIK for {ticker}: {cik}")
        
        filings = fetcher.get_company_filings(cik)
        
        if filings:
            print(f"\nFound {len(filings)} filings:")
            for i, filing in enumerate(filings[:5]):
                print(f"  {i+1}. {filing['filing_date']} - {filing['accession']}")
                print(f"      URL: {filing['filing_url']}")
            
            # Try fetching one
            if filings:
                print(f"\nTrying to fetch first filing...")
                first_url = filings[0]['filing_url']
                
                try:
                    time.sleep(0.2)
                    response = fetcher.session.get(first_url)
                    print(f"Status: {response.status_code}")
                    print(f"Content length: {len(response.text):,} characters")
                    
                    if response.status_code == 200:
                        print("✓ Successfully fetched filing!")
                    else:
                        print(f"✗ Got status code: {response.status_code}")
                        
                except Exception as e:
                    print(f"Error: {e}")
