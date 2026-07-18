import React from 'react';
import { s } from '@/lib/style';
import { NAV } from '@/lib/data';
import { User, DashboardData } from './types';

interface SidebarProps {
  user: User | null;
  view: string;
  setView: (view: string) => void;
  setDetailId: (id: string | null) => void;
  emergency: boolean;
  m: DashboardData;
  onLogout: () => void;
  onLoginRequest: () => void;
  handleToggleEmergency: () => void;
}

export default function Sidebar({ user, view, setView, setDetailId, emergency, m, onLogout, onLoginRequest, handleToggleEmergency }: SidebarProps) {
  const isProv = user?.role === 'tinh';
  const navBtn = (active: boolean) => `width:100%; display:flex; align-items:center; gap:11px; padding:11px 13px; border:none; border-radius:10px; cursor:pointer; font-family:inherit; font-size:13.5px; font-weight:${active ? '600' : '500'}; color:${active ? '#fff' : 'rgba(255,255,255,.62)'}; background:${active ? 'rgba(37,173,227,.16)' : 'transparent'}; margin-bottom:3px;`;
  const badgePill = 'font-size:10px; font-weight:700; background:#E23D3D; color:#fff; padding:1px 7px; border-radius:20px;';

  return (
    <aside style={s('width:262px; flex:0 0 262px; background:#0F1E2A; color:#fff; display:flex; flex-direction:column; height:100%;')}>
      <div style={s('padding:22px 22px 16px; display:flex; align-items:center; gap:11px; border-bottom:1px solid rgba(255,255,255,.08);')}>
        <svg width="34" height="34" viewBox="0 0 32 32" style={{ flex: '0 0 34px' }}>
          <defs><linearGradient id="ga-grad" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor="#3FD98A" /><stop offset="1" stopColor="#159A5C" /></linearGradient></defs>
          <rect width="32" height="32" rx="9" fill="url(#ga-grad)" />
          <path d="M16 6.5 L24.5 17 H19.4 V25.5 H12.6 V17 H7.5 Z" fill="#fff" />
        </svg>
        <div>
          <div style={s('font-size:14px; font-weight:800; letter-spacing:.01em; line-height:1;')}>Green<span style={{ color: '#3FD98A' }}>Forecast</span></div>
          <div style={s('font-size:9.5px; color:#8FE3B6; font-weight:600; margin-top:3px; letter-spacing:.02em;')}>Cảnh báo thời tiết</div>
        </div>
      </div>

      {user ? (
        <div style={s('padding:16px 18px 6px;')}>
          <div style={s('font-size:10px; text-transform:uppercase; letter-spacing:.09em; color:rgba(255,255,255,.42); margin-bottom:8px;')}>Vai trò đăng nhập</div>
          <div style={s('margin:20px 14px 10px 14px; background:rgba(0,0,0,.15); border-radius:10px; padding:12px; display:flex; flex-direction:column; gap:8px;')}>
            <div style={s('display:flex; align-items:center; gap:10px;')}>
              <div style={s('width:36px; height:36px; border-radius:50%; background:#25ADE3; color:#fff; display:flex; align-items:center; justify-content:center; font-weight:bold; font-size:16px;')}>
                {user?.name?.charAt(0) || 'U'}
              </div>
              <div style={s('flex:1; overflow:hidden;')}>
                <div style={s('color:#fff; font-size:13px; font-weight:600; white-space:nowrap; text-overflow:ellipsis; overflow:hidden;')}>{user?.name}</div>
                <div style={s('color:rgba(255,255,255,0.5); font-size:11px;')}>{isProv ? 'Quản trị viên Tỉnh' : 'Cán bộ Xã'}</div>
              </div>
            </div>
            <button onClick={onLogout} style={s('width:100%; padding:6px 0; border-radius:6px; background:rgba(226,61,61,0.15); color:#E23D3D; border:none; font-size:12px; font-weight:600; cursor:pointer; transition:background 0.2s;')}>
              Đăng xuất
            </button>
          </div>
        </div>
      ) : (
        <div style={s('padding:16px 18px 6px;')}>
          <div style={s('font-size:10px; text-transform:uppercase; letter-spacing:.09em; color:rgba(255,255,255,.42); margin-bottom:8px;')}>Vai trò đăng nhập</div>
          <div style={s('margin:20px 14px 10px 14px;')}>
            <button onClick={onLoginRequest} style={s('width:100%; padding:10px 0; border-radius:8px; background:#25ADE3; color:#fff; border:none; font-size:13px; font-weight:600; cursor:pointer;')}>
              Đăng nhập hệ thống
            </button>
          </div>
        </div>
      )}

      <nav style={s('padding:14px 12px; flex:1; overflow-y:auto;')}>
        {NAV.filter(item => user || !['roles', 'database'].includes(item.key)).map((item) => {
          const active = view === item.key;
          const badge = item.key === 'map' && emergency ? String(m?.alertCount || 0) : null;
          return (
            <button key={item.key} onClick={() => { setView(item.key); setDetailId(null); }} style={s(navBtn(active))}>
              <span style={s('font-size:17px; width:22px; text-align:center; flex:0 0 22px;')}>{item.icon}</span>
              <span style={s('flex:1; text-align:left;')}>{item.label}</span>
              {badge && <span style={s(badgePill)}>{badge}</span>}
            </button>
          );
        })}
      </nav>

      {user && (
        <div style={s('padding:14px 16px; border-top:1px solid rgba(255,255,255,.08);')}>
          <div style={s(`border-radius:11px; padding:12px 13px; background:${emergency ? 'rgba(226,61,61,.14)' : 'rgba(255,255,255,.05)'}; border:1px solid ${emergency ? 'rgba(226,61,61,.4)' : 'rgba(255,255,255,.08)'};`)}>
            <div style={s('display:flex; align-items:center; justify-content:space-between; gap:10px;')}>
              <div>
                <div style={s('font-size:12.5px; font-weight:700;')}>{emergency ? '🚨 Chế độ Khẩn cấp' : 'Chế độ Bình thường'}</div>
                <div style={s('font-size:10px; color:rgba(255,255,255,.6); margin-top:2px;')}>{emergency ? 'Cảnh báo đang phát đi' : 'Giám sát thường trực'}</div>
              </div>
              <button onClick={handleToggleEmergency} style={s(`width:46px; height:26px; border-radius:20px; border:none; cursor:pointer; position:relative; transition:.2s; background:${emergency ? '#E23D3D' : 'rgba(255,255,255,.25)'};`)}>
                <span style={s(`position:absolute; top:3px; left:${emergency ? '23px' : '3px'}; width:20px; height:20px; border-radius:50%; background:#fff; transition:.2s;`)}></span>
              </button>
            </div>
          </div>
        </div>
      )}

      {user && (
        <div style={s('padding:13px 18px; display:flex; align-items:center; gap:11px; border-top:1px solid rgba(255,255,255,.08);')}>
          <div style={s('width:34px; height:34px; border-radius:50%; background:#25ADE3; color:#0F1E2A; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:13px;')}>{isProv ? 'NT' : 'LV'}</div>
          <div style={s('flex:1; min-width:0;')}>
            <div style={s('font-size:12.5px; font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;')}>{isProv ? 'Nguyễn Tiến Dũng' : 'Lò Văn Panh'}</div>
            <div style={s('font-size:10px; color:rgba(255,255,255,.5); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;')}>{isProv ? 'Cán bộ Tỉnh · Toàn quyền' : 'Cán bộ Xã · Mường Nhé'}</div>
          </div>
        </div>
      )}
    </aside>
  );
}
