import React from 'react';
import { s } from '@/lib/style';
import { User } from './types';

interface RolesViewProps {
  user: User | null;
}

export default function RolesView({ user }: RolesViewProps) {
  const isProv = user?.role === 'tinh';
  const roleRowStyle = (active: boolean) => `display:flex; align-items:flex-start; gap:14px; padding:15px; border-radius:12px; margin-bottom:10px; border:1px solid ${active ? '#25ADE3' : '#EEF2F6'}; background:${active ? '#F5FCFF' : '#FBFCFD'};`;

  const roleRows = [
    { name: 'Cán bộ Tỉnh / Huyện', icon: '🏛️', bg: '#EAF7FD', current: isProv, perms: 'Giám sát toàn cảnh bản đồ tỉnh · Upload văn bản chỉ đạo (RAG) · Kích hoạt cảnh báo · Xem mọi xã.' },
    { name: 'Cán bộ Xã', icon: '🏘️', bg: '#E7F6EF', current: !isProv, perms: 'Xem chi tiết xã phụ trách · Theo dõi trạng thái trưởng bản · Gửi lại SMS / Gọi khẩn cấp.' },
    { name: 'Trưởng bản (chỉ nhận)', icon: '📢', bg: '#FFF6E6', current: false, perms: 'Nhận SMS/Zalo/Gọi + file Audio MP3 để phát trên loa phát thanh của bản.' },
  ];

  return (
    <div style={s('padding:22px 26px 34px; max-width:900px;')}>
      <div style={s('background:#fff; border:1px solid #E1E7EE; border-radius:14px; padding:22px; margin-bottom:16px;')}>
        <div style={s('font-family:Georgia,serif; font-weight:700; font-size:16px; margin-bottom:4px;')}>Phân quyền theo cấp</div>
        <div style={s('font-size:12px; color:#7C8896; margin-bottom:18px;')}>Quyền hạn tự động thay đổi theo vai trò đăng nhập ở thanh bên.</div>
        {roleRows.map((r, i) => (
          <div key={i} style={s(roleRowStyle(r.current))}>
            <div style={s(`width:44px; height:44px; border-radius:11px; background:${r.bg}; display:flex; align-items:center; justify-content:center; font-size:20px; flex:0 0 44px;`)}>{r.icon}</div>
            <div style={s('flex:1;')}>
              <div style={s('font-size:14px; font-weight:700; color:#0F1E2A;')}>{r.name} {r.current && <span style={s('font-size:10px; background:#25ADE3; color:#0F1E2A; padding:2px 8px; border-radius:20px; margin-left:6px; font-weight:700;')}>Đang đăng nhập</span>}</div>
              <div style={s('font-size:11.5px; color:#7C8896; margin-top:4px;')}>{r.perms}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
