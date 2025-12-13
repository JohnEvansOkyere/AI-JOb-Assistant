/**
 * Supabase Server Client
 * Server-side Supabase client for Next.js server components
 */

import { createClient } from '@supabase/supabase-js'
import { cookies } from 'next/headers'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables')
}

export async function createServerClient() {
  const cookieStore = await cookies()
  
  return createClient(supabaseUrl, supabaseAnonKey, {
    auth: {
      getSession: async () => {
        const accessToken = cookieStore.get('sb-access-token')?.value
        const refreshToken = cookieStore.get('sb-refresh-token')?.value
        
        if (!accessToken || !refreshToken) {
          return { data: { session: null }, error: null }
        }
        
        // Return session from cookies
        return {
          data: {
            session: {
              access_token: accessToken,
              refresh_token: refreshToken,
            }
          },
          error: null
        }
      },
    },
  })
}

