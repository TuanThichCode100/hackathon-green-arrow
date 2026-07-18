import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://qunzkuxuduqmqyjvtuqf.supabase.co';
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF1bnprdXh1ZHVxbXF5anZ0dXFmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQzOTk3NTcsImV4cCI6MjA5OTk3NTc1N30.H1toe-UChtLQE88ZdvsvvyftQ8EBGT8hTlKczFhQAdI';

export const supabase = createClient(supabaseUrl, supabaseKey);
