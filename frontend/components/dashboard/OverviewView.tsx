import React from 'react';
import { s } from '@/lib/style';
import { KpiCard } from './Shared';
import { DashboardData } from './types';

interface OverviewViewProps {
  m: DashboardData;
}

export default function OverviewView({ m }: OverviewViewProps) {
  return (
    <div style={s('padding:22px 26px 34px;')}>
      <div style={s('display:grid; grid-template-columns:repeat(5,1fr); gap:14px; margin-bottom:18px;')}>
        {m.kpis.map((k, i) => <KpiCard key={i} k={k} />)}
      </div>
      <div style={s('display:grid; grid-template-columns:1.4fr 1fr; gap:16px; margin-bottom:16px;')}>
        <div style={s('background:#fff; border:1px solid #E1E7EE; border-radius:14px; padding:18px 20px;')}>
          <div style={s('font-family:Georgia,serif; font-weight:700; font-size:15px; margin-bottom:4px;')}>Tỷ lệ phân phối theo kênh</div>
          <div style={s('font-size:11px; color:#7C8896; margin-bottom:18px;')}>Số tin đã tiếp cận / tổng số gửi đi · <b style={{ color: '#25ADE3' }}>{m.timeText}</b></div>
          {m.channels.map((ch, i) => (
            <div key={i} style={s('margin-bottom:15px;')}>
              <div style={s('display:flex; justify-content:space-between; align-items:baseline; margin-bottom:6px;')}>
                <span style={s('font-size:13px; font-weight:600; display:flex; align-items:center; gap:8px;')}><span style={s('font-size:15px;')}>{ch.icon}</span>{ch.name}</span>
                <span style={s('font-size:12px; color:#5A6675;')}><b style={{ color: '#0F1E2A' }}>{ch.rateStr}</b> · {ch.deliveredStr}/{ch.sentStr}</span>
              </div>
              <div style={s('height:9px; background:#EEF2F6; border-radius:6px; overflow:hidden;')}>
                <div style={s(`height:100%; width:${ch.pct}; background:${ch.color}; border-radius:6px;`)}></div>
              </div>
            </div>
          ))}
        </div>
        <div style={s('background:#fff; border:1px solid #E1E7EE; border-radius:14px; padding:18px 20px;')}>
          <div style={s('font-family:Georgia,serif; font-weight:700; font-size:15px; margin-bottom:4px;')}>Phân bố theo dân tộc</div>
          <div style={s('font-size:11px; color:#7C8896; margin-bottom:18px;')}>Vùng ảnh hưởng · dịch tự động theo nhóm</div>
          {m.ethnics.map((e, i) => (
            <div key={i} style={s('margin-bottom:13px;')}>
              <div style={s('display:flex; justify-content:space-between; margin-bottom:5px;')}>
                <span style={s('font-size:12.5px; font-weight:600;')}>{e.name}</span>
                <span style={s('font-size:11.5px; color:#7C8896;')}>{e.popStr} · {e.pct}</span>
              </div>
              <div style={s('height:8px; background:#EEF2F6; border-radius:6px; overflow:hidden;')}>
                <div style={s(`height:100%; width:${e.pct}; background:#25ADE3; border-radius:6px;`)}></div>
              </div>
            </div>
          ))}
        </div>
      </div>
      <div style={s('background:#fff; border:1px solid #E1E7EE; border-radius:14px; padding:18px 20px;')}>
        <div style={s('font-family:Georgia,serif; font-weight:700; font-size:15px; margin-bottom:14px;')}>Hoạt động gần đây</div>
        {m.activities.map((a, i) => (
          <div key={i} style={s('display:flex; gap:13px; padding:10px 0; border-bottom:1px solid #F1F4F8;')}>
            <div style={s(`width:32px; height:32px; border-radius:9px; background:${a.bg}; display:flex; align-items:center; justify-content:center; font-size:15px; flex:0 0 32px;`)}>{a.icon}</div>
            <div style={s('flex:1;')}>
              <div style={s('font-size:13px; color:#0F1E2A;')}>{a.text}</div>
              <div style={s('font-size:10.5px; color:#9AA4B0; margin-top:2px;')}>{a.time}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
