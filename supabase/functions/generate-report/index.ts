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
    // Initialize Supabase client with user's auth token
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_ANON_KEY') ?? '',
      {
        global: {
          headers: { Authorization: req.headers.get('Authorization')! },
        },
      }
    )

    // Get authenticated user
    const {
      data: { user },
      error: userError,
    } = await supabaseClient.auth.getUser()

    if (userError || !user) {
      return new Response(
        JSON.stringify({ error: 'unauthorized', message: 'Not authenticated' }),
        { status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Parse request body
    const { ticker } = await req.json()

    if (!ticker) {
      return new Response(
        JSON.stringify({ error: 'missing_ticker', message: 'Ticker is required' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    const tickerUpper = ticker.toUpperCase()

    // ============================================================
    // STEP 1: Check for existing cached report (last 30 days)
    // ============================================================
    const thirtyDaysAgo = new Date()
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30)

    const { data: existingReports, error: reportCheckError } = await supabaseClient
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
      
      // If it's a good report (not refunded), still charge the user
      if (!cachedReport.refunded) {
        // Charge token for cached report
        const { error: tokenError } = await supabaseClient.rpc('deduct_token', {
          p_user_id: user.id,
        })

        if (tokenError) {
          return new Response(
            JSON.stringify({ 
              error: 'insufficient_tokens', 
              message: 'Insufficient tokens to access report' 
            }),
            { status: 402, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
          )
        }

        // Log the token usage
        await supabaseClient.from('token_transactions').insert({
          user_id: user.id,
          report_id: cachedReport.id,
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
          report_id: cachedReport.id,
          message: cachedReport.refunded 
            ? 'Returned cached report (quality issues - no charge)'
            : 'Returned cached report (1 token charged)',
        }),
        { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // ============================================================
    // STEP 2: No cached report - generate new one
    // ============================================================

    // Check if user has tokens (done by Python worker, but check here too for better UX)
    const { data: profile, error: profileError } = await supabaseClient
      .from('profiles')
      .select('tokens_remaining')
      .eq('id', user.id)
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
        user_id: user.id,
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
