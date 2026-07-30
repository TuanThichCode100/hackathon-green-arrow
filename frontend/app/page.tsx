'use client';

import { useEffect, useState } from 'react';
import Dashboard from '@/components/Dashboard';
import Login from '@/components/Login';
import type { User } from '@/components/dashboard/types';
import { createClient } from '@/utils/supabase/clients';

function staffUser(authUser: any): User | null {
  const access = authUser.app_metadata || {};
  if (access.role !== 'tinh' && access.role !== 'xa') return null;
  if (access.role === 'xa' && typeof access.commune_id !== 'number') return null;
  return {
    id: authUser.id,
    name: authUser.user_metadata?.name || 'Cán bộ',
    role: access.role,
    commune_id: access.commune_id,
  };
}

export default function Home() {
  const [user, setUser] = useState<User | null>(null);
  const [authReady, setAuthReady] = useState(false);
  const [showLogin, setShowLogin] = useState(false);
  const supabase = createClient();

  useEffect(() => {
    const syncSession = (session: any) => {
      const nextUser = session?.user ? staffUser(session.user) : null;
      setUser(nextUser);
      if (nextUser && session) window.localStorage.setItem('auth_token', session.access_token);
      else window.localStorage.removeItem('auth_token');
    };

    const initAuth = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      syncSession(session);
      setAuthReady(true);
    };
    initAuth();

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => syncSession(session));
    return () => subscription.unsubscribe();
  }, [supabase.auth]);

  if (!authReady) return <div className="app-boot" aria-label="Đang khởi tạo hệ thống" />;
  if (showLogin) {
    return <Login onLoginSuccess={(nextUser) => { setUser(nextUser); setShowLogin(false); }} onCancel={() => setShowLogin(false)} />;
  }

  return <Dashboard user={user} onLoginRequest={() => setShowLogin(true)} onLogout={async () => {
    await supabase.auth.signOut();
    window.localStorage.removeItem('auth_token');
    setUser(null);
  }} />;
}
