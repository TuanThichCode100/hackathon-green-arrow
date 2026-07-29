'use client';

import { useEffect, useState } from 'react';
import Dashboard from '@/components/Dashboard';
import Login from '@/components/Login';
import type { User } from '@/components/dashboard/types';
import { createClient } from '@/utils/supabase/clients';

export default function Home() {
  const [user, setUser] = useState<User | null>(null);
  const [authReady, setAuthReady] = useState(false);
  const [showLogin, setShowLogin] = useState(false);
  const supabase = createClient();

  useEffect(() => {
    const initAuth = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      if (session && session.user) {
        const u = session.user;
        setUser({
          id: u.id,
          name: u.user_metadata?.name || 'Cán bộ',
          role: u.user_metadata?.role === 'xa' ? 'xa' : 'tinh',
          commune_id: u.user_metadata?.commune_id,
        });
        window.localStorage.setItem('auth_token', session.access_token);
      } else {
        window.localStorage.removeItem('auth_token');
        setUser(null);
      }
      setAuthReady(true);
    };
    initAuth();

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session && session.user) {
        const u = session.user;
        setUser({
          id: u.id,
          name: u.user_metadata?.name || 'Cán bộ',
          role: u.user_metadata?.role === 'xa' ? 'xa' : 'tinh',
          commune_id: u.user_metadata?.commune_id,
        });
        window.localStorage.setItem('auth_token', session.access_token);
      } else {
        window.localStorage.removeItem('auth_token');
        setUser(null);
      }
    });

    return () => {
      subscription.unsubscribe();
    };
  }, [supabase.auth]);

  if (!authReady) return <div className="app-boot" aria-label="Đang khởi tạo hệ thống" />;
  if (showLogin) {
    return (
      <Login
        onLoginSuccess={(nextUser) => {
          setUser(nextUser);
          setShowLogin(false);
        }}
        onCancel={() => setShowLogin(false)}
      />
    );
  }

  return (
    <Dashboard
      user={user}
      onLoginRequest={() => setShowLogin(true)}
      onLogout={async () => {
        await supabase.auth.signOut();
        window.localStorage.removeItem('auth_token');
        setUser(null);
      }}
    />
  );
}
