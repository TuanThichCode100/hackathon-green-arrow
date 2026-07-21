'use client';

import { useEffect, useState } from 'react';
import Dashboard from '@/components/Dashboard';
import Login from '@/components/Login';
import type { User } from '@/components/dashboard/types';

export default function Home() {
  const [user, setUser] = useState<User | null>(null);
  const [authReady, setAuthReady] = useState(false);
  const [showLogin, setShowLogin] = useState(false);

  useEffect(() => {
    const stored = window.localStorage.getItem('auth_user');
    if (stored) {
      try {
        setUser(JSON.parse(stored));
      } catch {
        window.localStorage.removeItem('auth_user');
      }
    }
    setAuthReady(true);
  }, []);

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
      onLogout={() => {
        window.localStorage.removeItem('auth_user');
        window.localStorage.removeItem('auth_token');
        setUser(null);
      }}
    />
  );
}
