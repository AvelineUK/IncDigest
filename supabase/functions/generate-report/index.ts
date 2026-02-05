// Edge Function: generate-report
// Receives requests from frontend, validates tokens, queues jobs with Python worker

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

// CORS headers for frontend requests
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Parse request body
    const { ticker, user_id } = await req.json()

    if (!ticker) {
      return new Response(
        JSON.stringify({ error: 'missing_ticker', message: 'Ticker is required' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    if (!user_id) {
      return new Response(
        JSON.stringify({ error: 'missing_user_id', message: 'User ID is required' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Initialize Supabase client with SERVICE ROLE for admin operations
    const supabaseAdmin = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    // TODO: Re-enable JWT validation after confirming flow works
    // For now, trust the user_id from request body
    console.log('Skipping JWT validation for testing - user_id:', user_id, 'ticker:', ticker)

    const tickerUpper = ticker.toUpperCase()

    // ============================================================
    // STEP 1: Check for existing cached report (last 30 days)
    // ============================================================
    const thirtyDaysAgo = new Date()
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30)

    const { data: existingReports, error: reportCheckError } = await supabaseAdmin
      .from('reports')
      .select('id, refunded, created_at')
      .eq('ticker', tickerUpper)
      .gte('created_at', thirtyDaysAgo.toISOString())
      .order('created_at', { ascending: false })
      .limit(1)

    if (reportCheckError) {
      console.error('Error checking for existing reports:', reportCheckError)
    }

    // If cached report exists, return it immediately
    if (existingReports && existingReports.length > 0) {
      const cachedReport = existingReports[0]
      
      // Get the full cached report data
      const { data: fullReport, error: reportError } = await supabaseAdmin
        .from('reports')
        .select('*')
        .eq('id', cachedReport.id)
        .single()
      
      if (reportError || !fullReport) {
        console.error('Error fetching full cached report:', reportError)
        // Fall through to generate new report
      } else {
        // Create a new report entry for this user pointing to the same data
        const { data: newReport, error: insertError } = await supabaseAdmin
          .from('reports')
          .insert({
            user_id: user_id,
            ticker: fullReport.ticker,
            company_name: fullReport.company_name,
            newer_filing_date: fullReport.newer_filing_date,
            older_filing_date: fullReport.older_filing_date,
            newer_accession: fullReport.newer_accession,
            older_accession: fullReport.older_accession,
            extraction_success: fullReport.extraction_success,
            sections_extracted: fullReport.sections_extracted,
            extraction_issues: fullReport.extraction_issues,
            ai_summaries: fullReport.ai_summaries,
            tokens_used: 1, // User pays 1 token for cached access
            refunded: fullReport.refunded,
            ai_cost_usd: 0, // No AI cost for cached report
            total_tokens_consumed: 0,
            report_url: fullReport.report_url,
            generation_time_seconds: 0, // Instant for cached reports
          })
          .select()
          .single()
        
        if (insertError || !newReport) {
          console.error('Error creating user report entry:', insertError)
          // Fall through to generate new report
        } else {
          // If it's a good report (not refunded), charge the user
          if (!cachedReport.refunded) {
            // Charge token for cached report
            const { error: tokenError } = await supabaseAdmin.rpc('deduct_token', {
              p_user_id: user_id,
            })

            if (tokenError) {
              // Token deduction failed - delete the report we just created
              await supabaseAdmin.from('reports').delete().eq('id', newReport.id)
              
              return new Response(
                JSON.stringify({ 
                  error: 'insufficient_tokens', 
                  message: 'Insufficient tokens to access report' 
                }),
                { status: 402, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
              )
            }

            // Log the token usage
            await supabaseAdmin.from('token_transactions').insert({
              user_id: user_id,
              report_id: newReport.id,
              transaction_type: 'usage',
              tokens_amount: -1,
              description: `Cached report for ${tickerUpper}`,
            })
          }
          // If refunded report, it's free - no token charge

          return new Response(
            JSON.stringify({
              success: true,
              cached: true,
              refunded: cachedReport.refunded,
              report_id: newReport.id, // Return the NEW report ID for this user
              message: cachedReport.refunded 
                ? 'Returned cached report (quality issues - no charge)'
                : 'Returned cached report (1 token charged)',
            }),
            { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
          )
        }
      }
    }

    // ============================================================
    // STEP 2: No cached report - generate new one
    // ============================================================

    // Check if user has tokens (done by Python worker, but check here too for better UX)
    const { data: profile, error: profileError } = await supabaseAdmin
      .from('profiles')
      .select('tokens_remaining')
      .eq('id', user_id)
      .single()

    if (profileError || !profile) {
      return new Response(
        JSON.stringify({ error: 'profile_not_found', message: 'User profile not found' }),
        { status: 404, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    if (profile.tokens_remaining < 1) {
      return new Response(
        JSON.stringify({ 
          error: 'insufficient_tokens', 
          message: 'Insufficient tokens. Please purchase more tokens.',
          tokens_remaining: profile.tokens_remaining,
        }),
        { status: 402, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Generate unique job ID
    const jobId = crypto.randomUUID()

    // Get callback URL for Python worker
    const callbackUrl = `${Deno.env.get('SUPABASE_URL')}/functions/v1/report-callback`

    // Call Python worker
    const workerUrl = Deno.env.get('PYTHON_WORKER_URL')
    if (!workerUrl) {
      throw new Error('PYTHON_WORKER_URL not configured')
    }

    const workerResponse = await fetch(`${workerUrl}/generate-report`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        job_id: jobId,
        user_id: user_id,
        ticker: tickerUpper,
        callback_url: callbackUrl,
      }),
    })

    if (!workerResponse.ok) {
      const errorText = await workerResponse.text()
      console.error('Worker error:', errorText)
      return new Response(
        JSON.stringify({ 
          error: 'worker_error', 
          message: 'Failed to queue report generation',
          details: errorText,
        }),
        { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    const workerData = await workerResponse.json()

    // Return job ID to frontend for polling
    return new Response(
      JSON.stringify({
        success: true,
        job_id: jobId,
        report_id: workerData.report_id, // If worker returns it immediately
        status: 'queued',
        message: `Report generation started for ${tickerUpper}`,
      }),
      { status: 202, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    console.error('Error in generate-report:', error)
    return new Response(
      JSON.stringify({ 
        error: 'internal_error', 
        message: error.message || 'An unexpected error occurred' 
      }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
})
