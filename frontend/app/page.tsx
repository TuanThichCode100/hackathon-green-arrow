'use client';
import { useState, useEffect } from 'react';
import Dashboard from '@/components/Dashboard';
import Login from '@/components/Login';
import { User } from '@/components/dashboard/types';

export default function Home() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const [showLogin, setShowLogin] = useState(false);

  useEffect(() => {
    // Check local storage on mount
    const savedUser = localStorage.getItem('auth_user');
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (e) {
        localStorage.removeItem('auth_user');
      }
    }
    setLoading(false);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('auth_user');
    localStorage.removeItem('auth_token');
    setUser(null);
  };

  if (loading) return null; // Prevent hydration mismatch

  if (showLogin) {
    return <Login onLoginSuccess={(u) => { setUser(u); setShowLogin(false); }} onCancel={() => setShowLogin(false)} />;
  }

  return <Dashboard user={user} onLogout={handleLogout} onLoginRequest={() => setShowLogin(true)} />;
}
