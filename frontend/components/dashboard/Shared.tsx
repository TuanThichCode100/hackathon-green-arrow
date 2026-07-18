import React from 'react';
import { s } from '@/lib/style';
import { Kpi } from './types';

export function KpiCard({ k }: { k: Kpi }) {
  return (
    <div style={s(k.cardStyle)}>
      <div style={s('display:flex; align-items:center; justify-content:space-between;')}>
        <span style={s('font-size:11px; color:#7C8896; font-weight:600;')}>{k.label}</span>
        <span style={s('font-size:15px;')}>{k.icon}</span>
      </div>
      <div style={s(`font-family:Georgia,serif; font-size:26px; font-weight:700; margin-top:9px; color:${k.valueColor}; line-height:1;`)}>{k.value}</div>
      <div style={s('font-size:10.5px; color:#8A95A2; margin-top:6px;')}>{k.sub}</div>
    </div>
  );
}

export function Legend({ color, label, ml }: { color: string; label: string; ml?: boolean }) {
  return (
    <span style={s(`font-size:11px; display:flex; align-items:center; gap:5px; color:#5A6675;${ml ? ' margin-left:8px;' : ''}`)}>
      <span style={s(`width:10px;height:10px;border-radius:50%;background:${color};`)}></span>{label}
    </span>
  );
}

export function PolicyStat({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div style={s('background:#fff; border:1px solid #E1E7EE; border-radius:12px; padding:12px 18px; min-width:118px;')}>
      <div style={s('font-size:11px; color:#7C8896;')}>{label}</div>
      <div style={s(`font-family:Georgia,serif; font-size:23px; font-weight:700; color:${color};`)}>{value}</div>
    </div>
  );
}

export function DetailStat({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div style={s('background:#fff; border:1px solid #E1E7EE; border-radius:11px; padding:13px;')}>
      <div style={s('font-size:10.5px; color:#7C8896;')}>{label}</div>
      <div style={s(`font-family:Georgia,serif; font-size:21px; font-weight:700;${color ? ` color:${color};` : ''}`)}>{value}</div>
    </div>
  );
}
