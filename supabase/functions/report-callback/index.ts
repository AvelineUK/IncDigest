// Edge Function: report-callback
// Called by Python worker when report generation completes

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

serve(async (req) => {
  try {
    // Initialize Supabase client with service role (bypass RLS)
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    // Parse callback data from Python worker
    const { 
      job_id, 
      status, 
      report_id, 
      error, 
      refunded,
      existing_report,
      no_charge,
    } = await req.json()

    console.log(`Callback received for job ${job_id}: ${status}`)

    // TODO: In future, you could:
    // - Send email notification to user
    // - Trigger webhook to user's systems
    // - Update a job_status table for frontend polling
    // - Send push notification

    if (status === 'completed') {
      console.log(`✓ Report ${report_id} completed successfully`)
      
      if (refunded) {
        console.log(`⚠ Quality issues detected - user was refunded`)
      }
      
      if (existing_report) {
        console.log(`📦 Returned cached report${no_charge ? ' (no charge)' : ''}`)
      }
    } else if (status === 'failed') {
      console.error(`✗ Job ${job_id} failed: ${error}`)
    }

    // Return success
    return new Response(
      JSON.stringify({ 
        success: true, 
        message: 'Callback received' 
      }),
      { 
        status: 200, 
        headers: { 'Content-Type': 'application/json' } 
      }
    )

  } catch (error) {
    console.error('Error in report-callback:', error)
    return new Response(
      JSON.stringify({ 
        error: 'callback_error', 
        message: error.message 
      }),
      { 
        status: 500, 
        headers: { 'Content-Type': 'application/json' } 
      }
    )
  }
})
