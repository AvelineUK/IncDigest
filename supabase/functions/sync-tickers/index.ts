// Edge Function: sync-tickers
// Fetches SEC company ticker list and syncs to companies table
// Runs daily via cron job

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  if (req.method !== 'GET' && req.method !== 'POST') {
    return new Response('Method not allowed', { status: 405 })
  }

  try {
    console.log('Starting SEC ticker sync...')

    // Initialize Supabase with service role (bypass RLS)
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    // Fetch SEC company tickers JSON
    console.log('Fetching SEC company tickers...')
    const secResponse = await fetch('https://www.sec.gov/files/company_tickers.json', {
      headers: {
        'User-Agent': 'IncDigest contact@incdigest.com', // SEC requires user agent
      },
    })

    if (!secResponse.ok) {
      throw new Error(`SEC API returned ${secResponse.status}`)
    }

    const tickersData = await secResponse.json()
    
    // Convert object to array
    // Format: { "0": { "cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc." }, ... }
    const companies = Object.values(tickersData) as Array<{
      cik_str: number
      ticker: string
      title: string
    }>

    console.log(`Found ${companies.length} companies from SEC`)

    // Batch upsert to companies table
    // Process in chunks of 500 to avoid payload limits
    const BATCH_SIZE = 500
    let processed = 0
    let created = 0
    let updated = 0

    for (let i = 0; i < companies.length; i += BATCH_SIZE) {
      const batch = companies.slice(i, i + BATCH_SIZE)
      
      // Prepare data for upsert
      const upsertData = batch.map(company => ({
        ticker: company.ticker,
        company_name: company.title,
        cik: String(company.cik_str).padStart(10, '0'), // Pad CIK to 10 digits
        // Don't overwrite extraction_status if already set
        // extraction_status defaults to 'unknown' in the table
      }))

      // Upsert: update if ticker exists, insert if new
      // On conflict (ticker), update company_name and cik but preserve extraction_status
      const { data, error } = await supabaseClient
        .from('companies')
        .upsert(upsertData, {
          onConflict: 'ticker',
          ignoreDuplicates: false, // We want to update existing records
        })

      if (error) {
        console.error(`Error upserting batch ${i}-${i + batch.length}:`, error)
        // Continue with next batch even if one fails
      } else {
        processed += batch.length
        console.log(`Processed ${processed}/${companies.length} companies...`)
      }
    }

    // Get stats
    const { count: totalCount } = await supabaseClient
      .from('companies')
      .select('*', { count: 'exact', head: true })

    console.log('Sync complete!')
    console.log(`Total companies in database: ${totalCount}`)

    return new Response(
      JSON.stringify({
        success: true,
        message: 'SEC ticker sync completed',
        stats: {
          sec_companies: companies.length,
          processed: processed,
          total_in_db: totalCount,
        },
      }),
      {
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    )

  } catch (error) {
    console.error('Error in sync-tickers:', error)
    return new Response(
      JSON.stringify({
        error: 'sync_failed',
        message: error.message || 'Failed to sync tickers',
      }),
      {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    )
  }
})