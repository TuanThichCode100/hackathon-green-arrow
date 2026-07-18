import React from 'react';
import { s } from '@/lib/style';
import { DashboardData } from './types';

interface CommunesViewProps {
  m: DashboardData;
  setDetailId: (id: string | number) => void;
}

export default function CommunesView({ m, setDetailId }: CommunesViewProps) {
  return (
    <div style={s('padding:22px 26px 34px;')}>
      <div style={s('background:#fff; border:1px solid #E1E7EE; border-radius:14px; overflow:hidden;')}>
        <div style={s('padding:16px 20px; border-bottom:1px solid #EEF2F6; display:flex; align-items:center; justify-content:space-between;')}>
          <div style={s('font-family:Georgia,serif; font-weight:700; font-size:16px;')}>Danh sách Xã · Thống kê quân số</div>
          <span style={s('font-size:11.5px; color:#7C8896;')}>Nhấp vào xã để xem chi tiết thôn bản &amp; hành động</span>
        </div>
        <div style={s('display:grid; grid-template-columns:2fr 1.1fr 1fr 1fr 1fr 1.2fr; padding:11px 20px; background:#F7F9FB; font-size:10.5px; font-weight:700; color:#7C8896; text-transform:uppercase; letter-spacing:.05em;')}>
          <span>Xã / Huyện</span><span style={s('text-align:right;')}>Tổng dân</span><span style={s('text-align:right;')}>Đã nhận</span><span style={s('text-align:right;')}>Chưa nhận</span><span style={s('text-align:right;')}>Tỷ lệ</span><span style={s('text-align:center;')}>Trạng thái</span>
        </div>
        {m.communes.map((c) => (
          <button key={c.id} className="gf-table-row" onClick={() => setDetailId(c.id)} style={s('width:100%; display:grid; grid-template-columns:2fr 1.1fr 1fr 1fr 1fr 1.2fr; align-items:center; padding:13px 20px; border:none; border-bottom:1px solid #F1F4F8; background:#fff; cursor:pointer; text-align:left;')}>
            <span style={s('display:flex; align-items:center; gap:11px;')}><span style={s('font-size:19px;')}>{c.icon}</span><span><span style={s('display:block; font-size:13.5px; font-weight:600; color:#0F1E2A;')}>{c.name}</span><span style={s('display:block; font-size:10.5px; color:#9AA4B0;')}>{c.hazard}</span></span></span>
            <span style={s('text-align:right; font-size:13px; font-variant-numeric:tabular-nums;')}>{c.popStr}</span>
            <span style={s('text-align:right; font-size:13px; color:#1E9E6A; font-weight:600; font-variant-numeric:tabular-nums;')}>{c.receivedStr}</span>
            <span style={s(`text-align:right; font-size:13px; color:${c.notReceivedColor}; font-weight:600; font-variant-numeric:tabular-nums;`)}>{c.notReceivedStr}</span>
            <span style={s(`text-align:right; font-size:13.5px; font-weight:700; color:${c.rateColor}; font-variant-numeric:tabular-nums;`)}>{c.rateStr}</span>
            <span style={s('text-align:center;')}><span style={s(c.pillStyle)}>{c.statusLabel}</span></span>
          </button>
        ))}
      </div>
    </div>
  );
}
