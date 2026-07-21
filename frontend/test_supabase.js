const { createClient } = require('@supabase/supabase-js');

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;

if (!supabaseUrl || !supabaseKey) {
  console.error("Missing Supabase credentials in .env.local");
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

async function testConnection() {
  console.log("Testing connection to Supabase...");
  console.log(`URL: ${supabaseUrl}`);
  
  // Test query - we just want to see if the API responds
  try {
    const { data, error } = await supabase.from('_nonexistent_table_test_').select('*').limit(1);
    
    // We expect an error about the table not existing, but that confirms the connection worked!
    if (error && error.code === 'PGRST116' || error.code === '42P01') {
      console.log("✅ Successfully connected to Supabase! (Received expected relation error)");
    } else if (error) {
       console.log("Received error from Supabase API:", error.message, error.code);
       console.log("✅ Still successfully connected to Supabase API (it responded).");
    } else {
      console.log("✅ Successfully connected to Supabase!");
    }
  } catch (err) {
    console.error("❌ Failed to connect to Supabase:", err.message);
  }
}

testConnection();
