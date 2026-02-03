"""
Worker - Processes report generation jobs
Runs in background thread
"""

import traceback
from datetime import datetime
from sec_fetcher import SECFetcher
from diff_analyzer import DiffAnalyzer
from ai_analyzer import AIAnalyzer
from quality_validator import QualityValidator
from database import SupabaseClient
import requests


def process_job(job_id, user_id, ticker, callback_url, jobs, dry_run=False):
    """
    Main job processing function
    Runs the entire pipeline: fetch → extract → diff → AI → validate → save
    
    Args:
        job_id: Unique job identifier
        user_id: User who requested the report
        ticker: Stock ticker (e.g., "AAPL")
        callback_url: URL to call when done
        jobs: Shared dict for status tracking
        dry_run: If True, skip AI analysis (for testing without API costs)
    """
    
    # Track start time
    start_time = datetime.now()
    
    # Initialize clients
    db = SupabaseClient()
    
    try:
        print(f"\n{'='*60}")
        print(f"Processing job {job_id} for {ticker}")
        print(f"{'='*60}")
        
        # Update status
        jobs[job_id]['status'] = 'processing'
        jobs[job_id]['progress'] = 5
        jobs[job_id]['current_step'] = 'Checking for existing reports...'
        
        # Check if user already has a recent report for this ticker
        print(f"[{job_id}] Checking for existing reports")
        try:
            from datetime import timedelta
            thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
            
            # Global cache - any user's report for this ticker
            # Return both good and bad reports (we'll handle charging differently)
            existing = db.client.table('reports').select('id, created_at, extraction_success, refunded').eq(
                'ticker', ticker
            ).gte(
                'created_at', thirty_days_ago
            ).order(
                'created_at', desc=True
            ).limit(1).execute()
            
            if existing.data:
                report = existing.data[0]
                is_refunded = report.get('refunded', False)
                
                if is_refunded:
                    # Bad report - return for free
                    print(f"[{job_id}] ✓ Found cached report (refunded) from {report['created_at']}")
                    print(f"[{job_id}] Returning flawed report (no charge)")
                else:
                    # Good report - still charge token
                    print(f"[{job_id}] ✓ Found cached report (good quality) from {report['created_at']}")
                    print(f"[{job_id}] Returning cached report (1 token charged - saves API costs)")
                    
                    # Charge the token for the good cached report
                    try:
                        result = db.client.table('profiles').select('tokens_remaining').eq('id', user_id).execute()
                        if result.data:
                            current_tokens = result.data[0]['tokens_remaining']
                            
                            if current_tokens < 1:
                                raise Exception(f"Insufficient tokens: balance is {current_tokens}, need 1")
                            
                            db.client.table('profiles').update({
                                'tokens_remaining': current_tokens - 1
                            }).eq('id', user_id).execute()
                            
                            # Create usage transaction
                            db.client.table('token_transactions').insert({
                                'user_id': user_id,
                                'transaction_type': 'usage',
                                'tokens_amount': -1,
                                'description': f'Cached report for {ticker}',
                                'report_id': report['id']
                            }).execute()
                            
                            print(f"[{job_id}] ✓ Token charged (balance: {current_tokens - 1})")
                    except Exception as token_error:
                        print(f"[{job_id}] ⚠ Could not charge token: {token_error}")
                
                jobs[job_id]['status'] = 'completed'
                jobs[job_id]['progress'] = 100
                jobs[job_id]['report_id'] = report['id']
                
                # Callback with existing report
                try:
                    requests.post(
                        callback_url,
                        json={
                            'job_id': job_id,
                            'status': 'completed',
                            'report_id': report['id'],
                            'existing_report': True,
                            'no_charge': is_refunded,
                            'message': f'Returned cached report ({"no charge - quality issues" if is_refunded else "1 token charged"})'
                        },
                        timeout=10
                    )
                    print(f"[{job_id}] ✓ Callback sent with existing report")
                except Exception as callback_error:
                    print(f"[{job_id}] ⚠ Callback failed: {callback_error}")
                
                print(f"[{job_id}] ✓ Job completed (existing report, 1 token charged)")
                print(f"{'='*60}\n")
                return
            
            print(f"[{job_id}] ✓ No recent reports found, generating new report")
            
        except Exception as check_error:
            print(f"[{job_id}] ⚠ Could not check for existing reports: {check_error}")
            # Continue anyway - better to generate duplicate than fail
        
        jobs[job_id]['progress'] = 10
        jobs[job_id]['current_step'] = 'Checking token balance...'
        
        # Check if user has enough tokens
        print(f"[{job_id}] Checking token balance")
        try:
            result = db.client.table('profiles').select('tokens_remaining').eq('id', user_id).execute()
            if not result.data:
                raise Exception("User not found")
            
            current_tokens = result.data[0]['tokens_remaining']
            
            if current_tokens < 1:
                raise Exception(f"Insufficient tokens: balance is {current_tokens}, need 1")
            
            print(f"[{job_id}] ✓ Balance check passed (balance: {current_tokens})")
            
        except Exception as balance_error:
            print(f"[{job_id}] ✗ Balance check failed: {balance_error}")
            jobs[job_id]['status'] = 'failed'
            jobs[job_id]['error'] = str(balance_error)
            
            # Callback with failure
            try:
                requests.post(
                    callback_url,
                    json={
                        'job_id': job_id,
                        'status': 'failed',
                        'error': str(balance_error)
                    },
                    timeout=10
                )
            except:
                pass
            return
        
        # Deduct token
        print(f"[{job_id}] Deducting 1 token from user balance")
        try:
            db.client.table('profiles').update({
                'tokens_remaining': current_tokens - 1
            }).eq('id', user_id).execute()
            
            # Create usage transaction
            db.client.table('token_transactions').insert({
                'user_id': user_id,
                'transaction_type': 'usage',
                'tokens_amount': -1,
                'description': f'Report generation for {ticker}'
            }).execute()
            
            print(f"[{job_id}] ✓ Token deducted (balance: {current_tokens - 1})")
        except Exception as token_error:
            print(f"[{job_id}] ⚠ Could not deduct token: {token_error}")
        
        # Update status
        jobs[job_id]['progress'] = 15
        jobs[job_id]['current_step'] = 'Fetching SEC filings...'
        
        # ========================================
        # STEP 1: Fetch and extract sections
        # ========================================
        print(f"[{job_id}] Step 1: Fetching 10-K data for {ticker}")
        fetcher = SECFetcher()
        filings = fetcher.get_10k_sections(ticker)
        
        if len(filings) < 2:
            raise Exception(f"Need 2 10-K filings to compare, found {len(filings)}")
        
        print(f"[{job_id}] ✓ Fetched {len(filings)} filings")
        print(f"[{job_id}]   Newer: {filings[0]['filing_date']}")
        print(f"[{job_id}]   Older: {filings[1]['filing_date']}")
        
        jobs[job_id]['progress'] = 30
        jobs[job_id]['current_step'] = 'Analyzing differences...'
        
        # ========================================
        # STEP 2: Run diff analysis
        # ========================================
        print(f"[{job_id}] Step 2: Performing diff analysis")
        diff_analyzer = DiffAnalyzer()
        diff_results = diff_analyzer.compare_sections(
            old_sections=filings[1]['sections'],
            new_sections=filings[0]['sections']
        )
        
        print(f"[{job_id}] ✓ Diff analysis complete")
        print(f"[{job_id}]   Sections compared: {len(diff_results)}")
        
        jobs[job_id]['progress'] = 50
        jobs[job_id]['current_step'] = 'Generating AI summaries...'
        
        # ========================================
        # STEP 3: Generate AI summaries (skip if dry run)
        # ========================================
        if dry_run:
            print(f"[{job_id}] Step 3: Skipping AI analysis (DRY RUN)")
            ai_results = {
                'sections': [],
                'total_cost_usd': 0.0,
                'total_tokens': 0
            }
            summaries = {
                'Item 1': '[DRY RUN] AI analysis skipped',
                'Item 1A': '[DRY RUN] AI analysis skipped',
                'Item 7': '[DRY RUN] AI analysis skipped',
                'Item 8': '[DRY RUN] AI analysis skipped'
            }
        else:
            print(f"[{job_id}] Step 3: Generating AI summaries")
            ai_analyzer = AIAnalyzer()
            ai_results = ai_analyzer.analyze_all_sections(
                ticker=ticker,
                company_name=filings[0]['company_name'],
                old_date=str(filings[1]['filing_date']),
                new_date=str(filings[0]['filing_date']),
                diff_results=diff_results
            )
            
            print(f"[{job_id}] ✓ AI analysis complete")
            print(f"[{job_id}]   Cost: ${ai_results['total_cost_usd']:.4f}")
            print(f"[{job_id}]   Tokens: {ai_results['total_tokens']:,}")
            
            # Convert sections list to summaries dict for database
            summaries = {}
            for section in ai_results.get('sections', []):
                section_name = section.get('section')  # It's 'section', not 'section_name'
                summary = section.get('summary', '')
                if section_name and summary:
                    summaries[section_name] = summary
        
        jobs[job_id]['progress'] = 80
        jobs[job_id]['current_step'] = 'Validating quality...'
        
        # Step 4: Validate quality
        print(f"[{job_id}] Step 4: Validating quality")
        validator = QualityValidator()
        quality_result = validator.validate_extraction(
            filings=filings,
            diff_results=diff_results,
            ai_results={'summaries': summaries}  # Pass summaries dict
        )
        
        if quality_result['is_valid']:
            print(f"[{job_id}] ✓ Quality check passed")
        else:
            print(f"[{job_id}] ⚠ Quality issues detected:")
            for issue in quality_result['issues']:
                print(f"[{job_id}]   - {issue}")
        
        jobs[job_id]['progress'] = 90
        jobs[job_id]['current_step'] = 'Saving report...'
        
        # ========================================
        # STEP 5: Write to database
        # ========================================
        print(f"[{job_id}] Step 5: Writing to database")
        
        generation_time = int((datetime.now() - start_time).total_seconds())
        
        report_id = db.create_report(
            user_id=user_id,
            ticker=ticker,
            company_name=filings[0]['company_name'],
            newer_filing_date=filings[0]['filing_date'],
            older_filing_date=filings[1]['filing_date'],
            newer_accession=filings[0]['accession'],
            older_accession=filings[1]['accession'],
            sections_extracted=list(filings[0]['sections'].keys()),
            extraction_issues=quality_result['issues'],
            extraction_success=quality_result['is_valid'],
            ai_summaries=summaries,  # Use the summaries dict we created
            ai_cost_usd=ai_results['total_cost_usd'],
            total_tokens_consumed=ai_results['total_tokens'],
            generation_time_seconds=generation_time
        )
        
        print(f"[{job_id}] ✓ Report saved: {report_id}")
        
        # Update company status to 'working' since extraction succeeded
        try:
            db.update_company_status(ticker, 'working')
            print(f"[{job_id}] ✓ Company status updated: {ticker} -> working")
        except Exception as status_error:
            print(f"[{job_id}] ⚠ Could not update company status: {status_error}")
        
        # ========================================
        # STEP 6: Handle refund if needed
        # ========================================
        if not quality_result['is_valid']:
            print(f"[{job_id}] Step 6: Issuing refund")
            
            # Log to error_logs so we can track and fix
            try:
                db.create_error_log(
                    user_id=user_id,
                    ticker=ticker,
                    error_type='quality_refund',
                    error_message=f"Quality issues detected: {'; '.join(quality_result['issues'])}",
                    stack_trace=None,
                    sections_attempted=['Item 1', 'Item 1A', 'Item 7', 'Item 8'],
                    sections_succeeded=list(filings[0]['sections'].keys()),
                    sections_failed=[],
                    word_counts={
                        section: len(content.split())
                        for section, content in filings[0]['sections'].items()
                    },
                    filing_url=filings[0].get('filing_url'),
                    newer_filing_date=filings[0]['filing_date'],
                    older_filing_date=filings[1]['filing_date']
                )
                print(f"[{job_id}] ✓ Quality issue logged to error_logs")
            except Exception as log_error:
                print(f"[{job_id}] ⚠ Could not log quality issue: {log_error}")
            
            # Issue the refund
            db.create_token_refund(
                user_id=user_id,
                report_id=report_id,
                reason=f"Quality issues: {', '.join(quality_result['issues'][:2])}"
            )
            print(f"[{job_id}] ✓ Refund issued")
        
        jobs[job_id]['progress'] = 100
        jobs[job_id]['status'] = 'completed'
        jobs[job_id]['report_id'] = report_id
        
        # ========================================
        # STEP 7: Callback to Edge Function
        # ========================================
        print(f"[{job_id}] Step 7: Notifying completion")
        try:
            response = requests.post(
                callback_url,
                json={
                    'job_id': job_id,
                    'status': 'completed',
                    'report_id': report_id,
                    'refunded': not quality_result['is_valid']
                },
                timeout=10
            )
            response.raise_for_status()
            print(f"[{job_id}] ✓ Callback successful")
        except Exception as callback_error:
            print(f"[{job_id}] ⚠ Callback failed: {callback_error}")
            # Don't fail the job if callback fails
        
        print(f"[{job_id}] ✓ Job completed in {generation_time}s")
        print(f"{'='*60}\n")
        
    except Exception as e:
        # ========================================
        # ERROR HANDLING
        # ========================================
        print(f"\n[{job_id}] ✗ ERROR: {e}")
        traceback.print_exc()
        
        jobs[job_id]['status'] = 'failed'
        jobs[job_id]['error'] = str(e)
        
        # Refund the token since job failed
        try:
            result = db.client.table('profiles').select('tokens_remaining').eq('id', user_id).execute()
            if result.data:
                current_tokens = result.data[0]['tokens_remaining']
                db.client.table('profiles').update({
                    'tokens_remaining': current_tokens + 1
                }).eq('id', user_id).execute()
                
                # Create refund transaction
                db.client.table('token_transactions').insert({
                    'user_id': user_id,
                    'transaction_type': 'refund',
                    'tokens_amount': 1,
                    'description': f'Job failed for {ticker}: {str(e)[:100]}'
                }).execute()
                
                print(f"[{job_id}] ✓ Token refunded due to job failure (balance: {current_tokens + 1})")
        except Exception as refund_error:
            print(f"[{job_id}] ⚠ Could not refund token: {refund_error}")
        
        # Mark company as broken since extraction failed
        try:
            db.update_company_status(ticker, 'broken')
            print(f"[{job_id}] ✓ Company status updated: {ticker} -> broken")
        except Exception as status_error:
            print(f"[{job_id}] ⚠ Could not update company status: {status_error}")
        
        # Log error to database
        try:
            error_log_id = db.create_error_log(
                user_id=user_id,
                ticker=ticker,
                error_type='extraction_failed',
                error_message=str(e),
                stack_trace=traceback.format_exc()
            )
            print(f"[{job_id}] ✓ Error logged: {error_log_id}")
        except Exception as log_error:
            print(f"[{job_id}] ⚠ Could not log error: {log_error}")
        
        # Callback with failure
        try:
            requests.post(
                callback_url,
                json={
                    'job_id': job_id,
                    'status': 'failed',
                    'error': str(e)
                },
                timeout=10
            )
            print(f"[{job_id}] ✓ Failure callback sent")
        except Exception as callback_error:
            print(f"[{job_id}] ⚠ Callback failed: {callback_error}")
        
        print(f"{'='*60}\n")
