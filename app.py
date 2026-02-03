"""
SEC Analysis Worker - Flask API Server
Receives report generation jobs and processes them
"""

from flask import Flask, request, jsonify
import threading
from worker import process_job
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# In-memory job tracking
# In production, you'd use Redis or a proper queue
jobs = {}  # job_id -> {status, progress, ticker, start_time}


@app.route('/health', methods=['GET'])
def health():
    """
    Health check endpoint
    Used by Railway/Render to check if service is running
    """
    return jsonify({
        'status': 'ok',
        'service': 'sec-analysis-worker',
        'version': '1.0.0',
        'active_jobs': len([j for j in jobs.values() if j['status'] == 'processing'])
    })


@app.route('/generate-report', methods=['POST'])
def generate_report():
    """
    Main endpoint: Receive job from Supabase Edge Function
    
    Expected JSON body:
    {
        "job_id": "uuid-here",
        "user_id": "uuid-here",
        "ticker": "AAPL",
        "callback_url": "https://your-edge-function-url",
        "dry_run": false  (optional - if true, skips AI analysis for testing)
    }
    
    Returns immediately with 202 Accepted
    Job processes in background
    """
    try:
        data = request.json
        
        # Validate required fields
        required = ['job_id', 'user_id', 'ticker', 'callback_url']
        missing = [f for f in required if f not in data]
        if missing:
            return jsonify({
                'error': 'missing_fields',
                'missing': missing
            }), 400
        
        job_id = data['job_id']
        user_id = data['user_id']
        ticker = data['ticker'].upper()
        callback_url = data['callback_url']
        dry_run = data.get('dry_run', False)  # Optional dry run mode
        
        # Check if job already exists
        if job_id in jobs:
            return jsonify({
                'error': 'duplicate_job',
                'message': f'Job {job_id} already exists',
                'current_status': jobs[job_id]['status']
            }), 409
        
        # Add to job queue
        from datetime import datetime
        jobs[job_id] = {
            'status': 'queued',
            'progress': 0,
            'ticker': ticker,
            'start_time': datetime.now().isoformat(),
            'dry_run': dry_run
        }
        
        # Process in background thread
        thread = threading.Thread(
            target=process_job,
            args=(job_id, user_id, ticker, callback_url, jobs, dry_run),
            daemon=True  # Thread dies when main program exits
        )
        thread.start()
        
        message = f'Report generation started for {ticker}'
        if dry_run:
            message += ' (DRY RUN - no AI analysis)'
        
        print(f"✓ Job {job_id} queued for {ticker}{' (DRY RUN)' if dry_run else ''}")
        
        return jsonify({
            'job_id': job_id,
            'status': 'queued',
            'message': message
        }), 202
        
    except Exception as e:
        print(f"✗ Error in generate_report: {e}")
        return jsonify({
            'error': 'internal_error',
            'message': str(e)
        }), 500


@app.route('/jobs/<job_id>/status', methods=['GET'])
def job_status(job_id):
    """
    Get job status (optional endpoint for debugging)
    In production, frontend polls Edge Function which checks database
    """
    if job_id not in jobs:
        return jsonify({
            'error': 'job_not_found',
            'message': f'Job {job_id} does not exist'
        }), 404
    
    return jsonify(jobs[job_id])


@app.route('/jobs', methods=['GET'])
def list_jobs():
    """
    List all jobs (for debugging)
    Shows what the worker is currently processing
    """
    return jsonify({
        'total_jobs': len(jobs),
        'queued': len([j for j in jobs.values() if j['status'] == 'queued']),
        'processing': len([j for j in jobs.values() if j['status'] == 'processing']),
        'completed': len([j for j in jobs.values() if j['status'] == 'completed']),
        'failed': len([j for j in jobs.values() if j['status'] == 'failed']),
        'jobs': list(jobs.values())[:10]  # Show last 10
    })


if __name__ == '__main__':
    # Get port from environment (Railway/Render set this)
    port = int(os.environ.get('PORT', 8000))
    
    print("="*60)
    print("SEC Analysis Worker Starting")
    print("="*60)
    print(f"Port: {port}")
    print(f"Environment: {os.environ.get('ENVIRONMENT', 'development')}")
    print("="*60)
    
    # Run Flask app
    # debug=False for production
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False
    )
