'use client';
import { useState } from 'react';
import { s } from '@/lib/style';
import { supabase } from '@/lib/supabase';
import { User } from './dashboard/types';

interface LoginProps {
  onLoginSuccess: (user: User) => void;
  onCancel?: () => void;
}

export default function Login({ onLoginSuccess, onCancel }: LoginProps) {
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!phone || !password) {
      setError('Vui lòng nhập đầy đủ Số điện thoại và Mật khẩu.');
      return;
    }
    
    setLoading(true);
    setError('');

    try {
      const email = `${phone}@dienbien.gov.vn`;
      const { data, error: supaError } = await supabase.auth.signInWithPassword({
        email,
        password
      });

      if (supaError || !data.session) {
        throw new Error('Đăng nhập thất bại. Vui lòng kiểm tra lại Số điện thoại hoặc Mật khẩu.');
      }
      
      const session = data.session;
      const userObj = {
        id: session.user.id as any,
        name: session.user.user_metadata?.name || 'Cán bộ Tỉnh',
        role: session.user.user_metadata?.role || 'tinh',
        commune_id: session.user.user_metadata?.commune_id
      };

      localStorage.setItem('auth_token', session.access_token);
      localStorage.setItem('auth_user', JSON.stringify(userObj));
      onLoginSuccess(userObj);

    } catch (err: any) {
      setError(err.message || 'Lỗi kết nối đến máy chủ.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={s('width:100vw; height:100vh; display:flex; align-items:center; justify-content:center; background:linear-gradient(135deg, #0F1E2A 0%, #1A344A 100%); font-family:Inter, sans-serif; color:#fff;')}>
      <div style={s('background:rgba(255,255,255,0.05); backdrop-filter:blur(10px); padding:40px 50px; border-radius:24px; border:1px solid rgba(255,255,255,0.1); width:100%; max-width:420px; box-shadow:0 20px 40px rgba(0,0,0,0.4);')}>
        <div style={s('text-align:center; margin-bottom:30px; position:relative;')}>
          {onCancel && (
            <button onClick={onCancel} style={s('position:absolute; top:-20px; right:-20px; width:32px; height:32px; border-radius:8px; border:none; background:rgba(255,255,255,.1); color:#fff; font-size:16px; cursor:pointer;')}>✕</button>
          )}
          <div style={s('font-size:42px; margin-bottom:10px;')}>🌱</div>
          <h1 style={s('font-family:Georgia,serif; font-size:26px; font-weight:700; margin:0 0 5px 0;')}>GreenForecast CRM</h1>
          <p style={s('font-size:14px; color:rgba(255,255,255,0.6); margin:0;')}>Hệ thống Cảnh báo Thiên tai sớm</p>
        </div>

        {error && (
          <div style={s('background:rgba(226,61,61,0.15); color:#FF7474; padding:12px; border-radius:8px; font-size:13px; margin-bottom:20px; text-align:center; border:1px solid rgba(226,61,61,0.3);')}>
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} style={s('display:flex; flex-direction:column; gap:20px;')}>
          <div>
            <label style={s('display:block; font-size:13px; margin-bottom:8px; color:rgba(255,255,255,0.8); font-weight:500;')}>Số điện thoại</label>
            <input 
              type="text" 
              value={phone} 
              onChange={e => setPhone(e.target.value)}
              placeholder="VD: 0912345678"
              style={s('width:100%; height:46px; background:rgba(0,0,0,0.2); border:1px solid rgba(255,255,255,0.15); border-radius:10px; padding:0 16px; color:#fff; font-size:15px; outline:none; transition:border 0.2s; box-sizing:border-box;')} 
              onFocus={e => e.target.style.borderColor = '#25ADE3'}
              onBlur={e => e.target.style.borderColor = 'rgba(255,255,255,0.15)'}
            />
          </div>
          <div>
            <label style={s('display:block; font-size:13px; margin-bottom:8px; color:rgba(255,255,255,0.8); font-weight:500;')}>Mật khẩu</label>
            <input 
              type="password" 
              value={password} 
              onChange={e => setPassword(e.target.value)}
              placeholder="Nhập 'demo' để thử nghiệm"
              style={s('width:100%; height:46px; background:rgba(0,0,0,0.2); border:1px solid rgba(255,255,255,0.15); border-radius:10px; padding:0 16px; color:#fff; font-size:15px; outline:none; transition:border 0.2s; box-sizing:border-box;')}
              onFocus={e => e.target.style.borderColor = '#25ADE3'}
              onBlur={e => e.target.style.borderColor = 'rgba(255,255,255,0.15)'}
            />
          </div>
          <button 
            type="submit" 
            disabled={loading}
            style={s(`height:48px; border-radius:10px; background:${loading ? '#5A6675' : '#1E9E6A'}; color:#fff; border:none; font-size:15px; font-weight:600; margin-top:10px; cursor:${loading ? 'not-allowed' : 'pointer'}; transition:background 0.2s;`)}
          >
            {loading ? 'Đang xác thực...' : 'Đăng nhập hệ thống'}
          </button>
        </form>
        
        <div style={s('margin-top:24px; text-align:center; font-size:12px; color:rgba(255,255,255,0.4);')}>
          Dự án Hackathon Green Arrow 2026<br/>Dành cho Cán bộ Tỉnh & Xã
        </div>
      </div>
    </div>
  );
}
