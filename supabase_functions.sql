-- SQL Function: deduct_token
-- Atomically deducts a token from user's balance
-- Returns error if insufficient tokens

CREATE OR REPLACE FUNCTION deduct_token(p_user_id UUID)
RETURNS void AS $$
DECLARE
  current_balance INTEGER;
BEGIN
  -- Lock the row for update
  SELECT tokens_remaining INTO current_balance
  FROM profiles
  WHERE id = p_user_id
  FOR UPDATE;

  -- Check if user has enough tokens
  IF current_balance < 1 THEN
    RAISE EXCEPTION 'Insufficient tokens: balance is %, need 1', current_balance;
  END IF;

  -- Deduct the token
  UPDATE profiles
  SET tokens_remaining = tokens_remaining - 1
  WHERE id = p_user_id;

END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION deduct_token TO authenticated;
