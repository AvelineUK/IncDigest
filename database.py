"""
Supabase Database Client
Handles all database writes from the worker
"""

from supabase import create_client, Client
import os


class SupabaseClient:
    """
    Client for writing to Supabase database
    Uses SERVICE_KEY (not anon key) to bypass RLS
    """
    
    def __init__(self):
        url = os.environ.get('SUPABASE_URL')
        # IMPORTANT: Use service_role key, not anon key
        # Service key bypasses Row Level Security (RLS)
        # Worker needs full access to write reports
        key = os.environ.get('SUPABASE_SERVICE_KEY')
        
        if not url or not key:
            raise ValueError(
                "Missing SUPABASE_URL or SUPABASE_SERVICE_KEY environment variables"
            )
        
        self.client: Client = create_client(url, key)
    
    def create_report(self, user_id, ticker, company_name, newer_filing_date,
                      older_filing_date, newer_accession, older_accession,
                      sections_extracted, extraction_issues, extraction_success,
                      ai_summaries, ai_cost_usd, total_tokens_consumed,
                      generation_time_seconds):
        """
        Insert report into database
        
        Returns: report_id (UUID)
        """
        
        # Convert date objects to ISO strings if needed
        if hasattr(newer_filing_date, 'isoformat'):
            newer_filing_date = newer_filing_date.isoformat()
        if hasattr(older_filing_date, 'isoformat'):
            older_filing_date = older_filing_date.isoformat()
        
        data = {
            'user_id': user_id,
            'ticker': ticker,
            'company_name': company_name,
            'newer_filing_date': newer_filing_date,
            'older_filing_date': older_filing_date,
            'newer_accession': newer_accession,
            'older_accession': older_accession,
            'sections_extracted': list(sections_extracted),
            'extraction_issues': extraction_issues if extraction_issues else [],
            'extraction_success': extraction_success,
            'ai_summaries': ai_summaries,
            'ai_cost_usd': float(ai_cost_usd),
            'total_tokens_consumed': int(total_tokens_consumed),
            'tokens_used': 1,  # Always 1 token per report
            'refunded': False,  # Will be updated if refund issued
            'generation_time_seconds': generation_time_seconds
        }
        
        result = self.client.table('reports').insert(data).execute()
        
        if not result.data:
            raise Exception("Failed to insert report into database")
        
        return result.data[0]['id']
    
    def create_token_refund(self, user_id, report_id, reason):
        """
        Issue a token refund for quality issues
        
        Does 3 things:
        1. Mark report as refunded
        2. Create refund transaction
        3. Increment user's token balance
        """
        
        # 1. Mark report as refunded
        self.client.table('reports').update({
            'refunded': True
        }).eq('id', report_id).execute()
        
        # 2. Create refund transaction
        self.client.table('token_transactions').insert({
            'user_id': user_id,
            'report_id': report_id,
            'transaction_type': 'refund',
            'tokens_amount': 1,
            'description': f'Auto-refund: {reason}'
        }).execute()
        
        # 3. Update user's token balance
        # This uses a PostgreSQL function (we'll need to create this)
        # For now, we'll do it manually
        result = self.client.table('profiles').select('tokens_remaining').eq('id', user_id).execute()
        
        if result.data:
            current_tokens = result.data[0]['tokens_remaining']
            self.client.table('profiles').update({
                'tokens_remaining': current_tokens + 1
            }).eq('id', user_id).execute()
    
    def create_error_log(self, user_id, ticker, error_type, error_message, stack_trace,
                        sections_attempted=None, sections_succeeded=None, sections_failed=None,
                        word_counts=None, filing_url=None, newer_filing_date=None, 
                        older_filing_date=None):
        """
        Log an error to database for debugging
        
        Args:
            user_id: User ID
            ticker: Stock ticker
            error_type: Type of error (e.g., 'extraction_failed', 'quality_refund')
            error_message: Error description
            stack_trace: Full stack trace (None for quality refunds)
            sections_attempted: List of sections attempted (optional)
            sections_succeeded: List of sections that succeeded (optional)
            sections_failed: List of sections that failed (optional)
            word_counts: Dict of section -> word count (optional)
            filing_url: URL to SEC filing (optional)
            newer_filing_date: Date of newer filing (optional)
            older_filing_date: Date of older filing (optional)
        
        Returns: error_log_id (UUID)
        """
        
        # Convert date objects to ISO strings if needed
        if newer_filing_date and hasattr(newer_filing_date, 'isoformat'):
            newer_filing_date = newer_filing_date.isoformat()
        if older_filing_date and hasattr(older_filing_date, 'isoformat'):
            older_filing_date = older_filing_date.isoformat()
        
        data = {
            'user_id': user_id,
            'ticker': ticker,
            'error_type': error_type,
            'error_message': error_message,
            'stack_trace': stack_trace,
            'status': 'open'
        }
        
        # Add optional fields if provided
        if sections_attempted:
            data['sections_attempted'] = sections_attempted
        if sections_succeeded:
            data['sections_succeeded'] = sections_succeeded
        if sections_failed:
            data['sections_failed'] = sections_failed
        if word_counts:
            data['word_counts'] = word_counts
        if filing_url:
            data['filing_url'] = filing_url
        if newer_filing_date:
            data['newer_filing_date'] = newer_filing_date
        if older_filing_date:
            data['older_filing_date'] = older_filing_date
        
        result = self.client.table('error_logs').insert(data).execute()
        
        if not result.data:
            raise Exception("Failed to insert error log into database")
        
        return result.data[0]['id']
    
    def update_company_status(self, ticker, extraction_status):
        """
        Update company's extraction status
        Used to track which companies work/fail
        Creates company entry if doesn't exist
        """
        
        # Check if company exists
        result = self.client.table('companies').select('id').eq('ticker', ticker).execute()
        
        if result.data:
            # Update existing
            self.client.table('companies').update({
                'extraction_status': extraction_status,
                'last_successful_extraction': 'now()' if extraction_status == 'working' else None,
                'failure_count': 0 if extraction_status == 'working' else None  # Resetfailure count on success
            }).eq('ticker', ticker).execute()
        else:
            # Create new company entry
            # We don't have company_name or CIK here, but that's okay
            # These can be filled in later by background jobs
            self.client.table('companies').insert({
                'ticker': ticker,
                'company_name': None,  # Will be filled by background job
                'cik': None,  # Will be filled by background job
                'extraction_status': extraction_status,
                'last_successful_extraction': 'now()' if extraction_status == 'working' else None,
                'failure_count': 1 if extraction_status == 'broken' else 0
            }).execute()
