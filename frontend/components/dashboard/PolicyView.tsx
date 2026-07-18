import React from 'react';
import { s } from '@/lib/style';
import { PolicyStat } from './Shared';
import { DashboardData, User } from './types';

interface PolicyViewProps {
  m: DashboardData;
  user: User | null;
  setUploadOpen: (open: boolean) => void;
}

export default function PolicyView({ m, user, setUploadOpen }: PolicyViewProps) {
  return (
    <div style={s('padding:22px 26px 34px;')}>
      <div style={s('display:flex; align-items:center; justify-content:space-between; margin-bottom:16px;')}>
        <div style={s('display:flex; gap:12px;')}>
          <PolicyStat label="Còn hiệu lực" value={m.policyActive} color="#1E9E6A" />
          <PolicyStat label="Sắp hết hạn" value={m.policyExpiring} color="#E8A93B" />
          <PolicyStat label="Đã hết hiệu lực" value={m.policyExpired} color="#9AA4B0" />
        </div>
        {user && (
          <button onClick={() => setUploadOpen(true)} style={s('font-size:13px; font-weight:700; color:#0F1E2A; background:#25ADE3; border:none; border-radius:10px; padding:11px 18px; cursor:pointer;')}>＋ Upload văn bản chỉ đạo</button>
        )}
      </div>
      <div style={s('background:#0F1E2A; color:#fff; border-radius:12px; padding:14px 18px; display:flex; align-items:center; gap:14px; margin-bottom:16px;')}>
        <span style={s('font-size:22px;')}>🧠</span>
        <div style={s('flex:1; font-size:12.5px; line-height:1.5;')}><b style={{ color: '#25ADE3' }}>RAG Policy Engine.</b> Trước mỗi quyết định phân phối, AI Agent truy vấn kho văn bản còn hiệu lực. Chỉ đạo hành chính sẽ <b>ghi đè (override)</b> kịch bản mặc định của AI.</div>
        <span style={s('font-size:11px; background:rgba(37,173,227,.16); color:#25ADE3; padding:5px 11px; border-radius:20px; font-weight:600;')}>Ưu tiên cao nhất</span>
      </div>
      <div style={s('background:#fff; border:1px solid #E1E7EE; border-radius:14px; overflow:hidden;')}>
        <div style={s('display:grid; grid-template-columns:2.4fr 1fr 1.2fr 1.2fr 1fr; padding:11px 20px; background:#F7F9FB; font-size:10.5px; font-weight:700; color:#7C8896; text-transform:uppercase; letter-spacing:.05em;')}>
          <span>Văn bản</span><span>Loại</span><span>Hiệu lực từ</span><span>Đến hết</span><span style={s('text-align:center;')}>Trạng thái</span>
        </div>
        {m.policies.map((p, i) => (
          <div key={i} style={s('display:grid; grid-template-columns:2.4fr 1fr 1.2fr 1.2fr 1fr; align-items:center; padding:14px 20px; border-bottom:1px solid #F1F4F8;')}>
            <span style={s('display:flex; align-items:center; gap:12px;')}><span style={s('font-size:20px;')}>📄</span><span><span style={s('display:block; font-size:13px; font-weight:600; color:#0F1E2A;')}>{p.title}</span><span style={s('display:block; font-size:10.5px; color:#9AA4B0;')}>{p.code} · {p.by}</span></span></span>
            <span style={s('font-size:12px; color:#5A6675;')}>{p.type}</span>
            <span style={s('font-size:12.5px; color:#5A6675; font-variant-numeric:tabular-nums;')}>{p.start}</span>
            <span style={s('font-size:12.5px; color:#5A6675; font-variant-numeric:tabular-nums;')}>{p.end}</span>
            <span style={s('text-align:center;')}><span style={s(p.pillStyle)}>{p.statusLabel}</span></span>
          </div>
        ))}
      </div>
    </div>
  );
}
