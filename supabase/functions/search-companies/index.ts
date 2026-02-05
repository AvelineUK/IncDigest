// Edge Function: search-companies
// Server-side company search to avoid client-side limits

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

  try {
    const { query } = await req.json()

    if (!query || query.length < 1) {
      return new Response(
        JSON.stringify({ results: [] }),
        { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    const searchTerm = query.toLowerCase().trim()

    // Search with pattern matching - no row limit issues
    const { data, error } = await supabase
      .from('companies')
      .select('ticker, company_name, cik')
      .or(`ticker.ilike.%${searchTerm}%,company_name.ilike.%${searchTerm}%`)
      .limit(50) // Return max 50 results

    if (error) {
      console.error('Search error:', error)
      return new Response(
        JSON.stringify({ error: 'Search failed', results: [] }),
        { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Score and sort results
    const scored = (data || []).map(c => {
      const ticker = c.ticker.toLowerCase()
      const name = c.company_name.toLowerCase()
      let score = 0

      if (ticker === searchTerm) score = 10000
      else if (ticker.startsWith(searchTerm)) score = 5000
      else if (ticker.includes(searchTerm)) score = 1000
      else if (name === searchTerm) score = 9000
      else if (name.startsWith(searchTerm)) score = 4000
      else if (name.match(new RegExp('\\b' + searchTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')))) score = 3000
      else if (name.includes(searchTerm)) score = 100

      return { ...c, score }
    })

    scored.sort((a, b) => b.score - a.score)
    const results = scored.slice(0, 20).map(({ score, ...company }) => company)

    return new Response(
      JSON.stringify({ results }),
      { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    console.error('Error:', error)
    return new Response(
      JSON.stringify({ error: 'Internal error', results: [] }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
})
