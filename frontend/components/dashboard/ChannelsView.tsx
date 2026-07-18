import React from 'react';
import { s } from '@/lib/style';
import { DashboardData } from './types';

interface ChannelsViewProps {
  m: DashboardData;
}

export default function ChannelsView({ m }: ChannelsViewProps) {
  return (
    <div style={s('padding:22px 26px 34px;')}>
      <div style={s('display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom:16px;')}>
        {m.channels.map((ch, i) => (
          <div key={i} style={s('background:#fff; border:1px solid #E1E7EE; border-radius:14px; padding:16px 18px;')}>
            <div style={s('display:flex; align-items:center; gap:10px; margin-bottom:12px;')}><span style={s('font-size:22px;')}>{ch.icon}</span><span style={s('font-size:13.5px; font-weight:700;')}>{ch.name}</span></div>
            <div style={s(`font-family:Georgia,serif; font-size:24px; font-weight:700; color:${ch.color};`)}>{ch.rateStr}</div>
            <div style={s('font-size:10.5px; color:#8A95A2; margin-top:3px;')}>tiếp cận thành công</div>
            <div style={s('display:flex; justify-content:space-between; margin-top:13px; padding-top:11px; border-top:1px solid #F1F4F8;')}>
              <span style={s('font-size:11px; color:#7C8896;')}>Đã gửi<br /><b style={s('color:#0F1E2A; font-size:13px;')}>{ch.sentStr}</b></span>
              <span style={s('font-size:11px; color:#7C8896; text-align:right;')}>Thất bại<br /><b style={s('color:#E23D3D; font-size:13px;')}>{ch.failedStr}</b></span>
            </div>
          </div>
        ))}
      </div>
      <div style={s('background:#fff; border:1px solid #E1E7EE; border-radius:14px; overflow:hidden;')}>
        <div style={s('padding:16px 20px; border-bottom:1px solid #EEF2F6; display:flex; align-items:center; justify-content:space-between;')}>
          <div style={s('font-family:Georgia,serif; font-weight:700; font-size:16px;')}>Nhật ký phân phối tin nhắn · <span style={s('font-size:12px; color:#25ADE3;')}>{m.timeText}</span></div>
          <span style={s('font-size:11px; color:#7C8896; display:flex; align-items:center; gap:6px;')}><span style={s('width:7px;height:7px;border-radius:50%;background:#1E9E6A; animation:gf-blink 2s infinite;')}></span>Cập nhật realtime</span>
        </div>
        <div style={s('display:grid; grid-template-columns:.8fr 1.4fr 1fr 1.3fr .9fr 1fr; padding:11px 20px; background:#F7F9FB; font-size:10.5px; font-weight:700; color:#7C8896; text-transform:uppercase; letter-spacing:.05em;')}>
          <span>Thời gian</span><span>Địa bàn</span><span>Kênh</span><span>Ngôn ngữ / Dân tộc</span><span style={s('text-align:right;')}>Số nhận</span><span style={s('text-align:center;')}>Trạng thái</span>
        </div>
        {m.logs.map((l, i) => (
          <div key={i} style={s('display:grid; grid-template-columns:.8fr 1.4fr 1fr 1.3fr .9fr 1fr; align-items:center; padding:12px 20px; border-bottom:1px solid #F1F4F8;')}>
            <span style={s('font-size:12px; color:#5A6675; font-variant-numeric:tabular-nums;')}>{l.time}</span>
            <span style={s('font-size:12.5px; font-weight:600; color:#0F1E2A;')}>{l.commune}</span>
            <span style={s('font-size:12px; color:#5A6675;')}>{l.channelIcon} {l.channel}</span>
            <span style={s('font-size:12px; color:#5A6675;')}>{l.ethnic}</span>
            <span style={s('text-align:right; font-size:12.5px; font-variant-numeric:tabular-nums;')}>{l.recipientsStr}</span>
            <span style={s('text-align:center;')}><span style={s(l.pillStyle)}>{l.statusLabel}</span></span>
          </div>
        ))}
      </div>
    </div>
  );
}
