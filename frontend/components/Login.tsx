'use client';

import { useState } from 'react';
import { ArrowLeft, SignIn, TreeStructure } from '@phosphor-icons/react';
import { createClient } from '@/utils/supabase/clients';
import type { User } from './dashboard/types';

export default function Login({ onLoginSuccess, onCancel }: { onLoginSuccess: (user: User) => void; onCancel?: () => void }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    const isEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(username);
    const isPhone = /^0\d{9}$/.test(username);
    if (!isEmail && !isPhone) return setError('Vui lòng nhập đúng email công vụ hoặc số điện thoại (10 chữ số).');
    if (isEmail && !username.trim().toLowerCase().endsWith('@dienbien.gov.vn')) return setError('Hệ thống chỉ tiếp nhận email công vụ @dienbien.gov.vn.');
    if (!password) return setError('Vui lòng nhập mật khẩu.');

    setLoading(true);
    setError('');
    try {
      const supabase = createClient();
      const loginEmail = isEmail ? username.trim() : `${username}@dienbien.gov.vn`;
      const { data, error: authError } = await supabase.auth.signInWithPassword({ email: loginEmail, password });
      if (authError || !data.session) throw new Error('Thông tin đăng nhập không chính xác.');
      const access = data.user.app_metadata || {};
      if ((access.role !== 'tinh' && access.role !== 'xa') || (access.role === 'xa' && typeof access.commune_id !== 'number')) {
        await supabase.auth.signOut();
        throw new Error('Tài khoản chưa được cấp quyền truy cập hệ thống.');
      }
      const nextUser: User = {
        id: data.user.id,
        name: data.user.user_metadata?.name || 'Cán bộ Điện Biên',
        role: access.role,
        commune_id: access.commune_id,
      };
      window.localStorage.setItem('auth_token', data.session.access_token);
      window.localStorage.setItem('auth_user', JSON.stringify(nextUser));
      onLoginSuccess(nextUser);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Không thể kết nối hệ thống xác thực.');
    } finally {
      setLoading(false);
    }
  };

  return <main className="auth-page">
    <section className="auth-context"><div className="brand-mark"><TreeStructure size={21} weight="bold" /></div><p className="eyebrow">GreenForecast · Điện Biên</p><h1>Thông tin đúng địa bàn, hành động đúng thời điểm.</h1><p>Không gian tác nghiệp dành cho cán bộ theo dõi rủi ro, kiểm tra mức tiếp cận và điều phối cảnh báo.</p></section>
    <section className="auth-form-wrap"><form className="auth-form" onSubmit={submit}>
      {onCancel && <button type="button" className="secondary-button" onClick={onCancel}><ArrowLeft size={16} />Quay lại bản đồ</button>}
      <div><p className="eyebrow">Xác thực cán bộ</p><h2>Đăng nhập hệ thống</h2></div>
      <label><span>Số điện thoại / Email công vụ</span><input value={username} onChange={(event) => setUsername(event.target.value)} inputMode="text" autoComplete="username" placeholder="09xx xxx xxx hoặc ten@dienbien.gov.vn" /></label>
      <label><span>Mật khẩu</span><input value={password} onChange={(event) => setPassword(event.target.value)} type="password" autoComplete="current-password" /></label>
      {error && <p className="form-error" role="alert">{error}</p>}
      <button className="primary-button" disabled={loading}>{loading ? 'Đang xác thực…' : <><SignIn size={17} />Đăng nhập</>}</button>
    </form></section>
  </main>;
}
