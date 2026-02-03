// Edge Function: stripe-webhook
// Handles Stripe webhook events for token purchases

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import Stripe from 'https://esm.sh/stripe@14.11.0?target=deno'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type, stripe-signature',
}

serve(async (req) => {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Initialize Stripe
    const stripe = new Stripe(Deno.env.get('STRIPE_SECRET_KEY') || '', {
      apiVersion: '2023-10-16',
      httpClient: Stripe.createFetchHttpClient(),
    })

    // Get webhook signature
    const signature = req.headers.get('stripe-signature')
    if (!signature) {
      throw new Error('No stripe-signature header')
    }

    // Get raw body for signature verification
    const body = await req.text()

    // Verify webhook signature
    const webhookSecret = Deno.env.get('STRIPE_WEBHOOK_SECRET')
    if (!webhookSecret) {
      throw new Error('STRIPE_WEBHOOK_SECRET not configured')
    }

    let event: Stripe.Event
    try {
      event = stripe.webhooks.constructEvent(body, signature, webhookSecret)
    } catch (err) {
      console.error('Webhook signature verification failed:', err.message)
      return new Response(
        JSON.stringify({ error: 'Invalid signature' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      )
    }

    console.log('Webhook event received:', event.type)

    // Initialize Supabase client with service role
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    // Handle different event types
    switch (event.type) {
      case 'checkout.session.completed': {
        const session = event.data.object as Stripe.Checkout.Session

        // Extract metadata
        const userId = session.metadata?.user_id
        const tokensPurchased = parseInt(session.metadata?.tokens || '0')
        const priceId = session.metadata?.price_id

        if (!userId || !tokensPurchased) {
          console.error('Missing metadata in session:', session.id)
          break
        }

        console.log(`Payment completed: ${tokensPurchased} tokens for user ${userId}`)

        // Add tokens to user's account
        const { data: profile, error: fetchError } = await supabaseClient
          .from('profiles')
          .select('tokens_remaining')
          .eq('id', userId)
          .single()

        if (fetchError) {
          console.error('Error fetching user profile:', fetchError)
          throw fetchError
        }

        const newBalance = (profile?.tokens_remaining || 0) + tokensPurchased

        const { error: updateError } = await supabaseClient
          .from('profiles')
          .update({ tokens_remaining: newBalance })
          .eq('id', userId)

        if (updateError) {
          console.error('Error updating token balance:', updateError)
          throw updateError
        }

        // Create transaction record
        const { error: txnError } = await supabaseClient
          .from('token_transactions')
          .insert({
            user_id: userId,
            transaction_type: 'purchase',
            tokens_amount: tokensPurchased,
            description: `Purchased ${tokensPurchased} tokens`,
            stripe_payment_id: session.payment_intent as string,
          })

        if (txnError) {
          console.error('Error creating transaction:', txnError)
          throw txnError
        }

        console.log(`✓ Added ${tokensPurchased} tokens to user ${userId} (new balance: ${newBalance})`)
        break
      }

      case 'payment_intent.succeeded': {
        const paymentIntent = event.data.object as Stripe.PaymentIntent
        console.log(`Payment intent succeeded: ${paymentIntent.id}`)
        // Main handling is done in checkout.session.completed
        break
      }

      case 'payment_intent.payment_failed': {
        const paymentIntent = event.data.object as Stripe.PaymentIntent
        console.error(`Payment failed: ${paymentIntent.id}`)
        // Could log this to database or send notification
        break
      }

      default:
        console.log(`Unhandled event type: ${event.type}`)
    }

    // Return success response
    return new Response(
      JSON.stringify({ received: true }),
      { 
        status: 200, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    )

  } catch (error) {
    console.error('Webhook error:', error)
    return new Response(
      JSON.stringify({ 
        error: 'webhook_error', 
        message: error.message 
      }),
      { 
        status: 400, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    )
  }
})