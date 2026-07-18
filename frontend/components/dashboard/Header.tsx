import React from 'react';
import { s } from '@/lib/style';
import { TIME_META, VIEW_TITLES } from '@/lib/data';

interface HeaderProps {
  view: string;
  timeRange: string;
  setTimeRange: (t: string) => void;
  clock: string;
}

export default function Header({ view, timeRange, setTimeRange, clock }: HeaderProps) {
  const timeSeg = (active: boolean) => `border:none; cursor:pointer; font-family:inherit; font-size:11.5px; font-weight:600; padding:6px 11px; border-radius:6px; color:${active ? '#fff' : '#5A6675'}; background:${active ? '#0F1E2A' : 'transparent'};`;

  return (
    <header style={s('background:#fff; border-bottom:1px solid #E1E7EE; padding:0 26px; height:64px; flex:0 0 64px; display:flex; align-items:center; gap:20px;')}>
      <div style={s('min-width:0;')}>
        <div style={s('font-size:11px; color:#7C8896; letter-spacing:.02em;')}>GreenForecast · Tỉnh Điện Biên</div>
        <div style={s('font-family:Georgia,serif; font-size:19px; font-weight:700; color:#0F1E2A; line-height:1.1; margin-top:1px;')}>{VIEW_TITLES[view as keyof typeof VIEW_TITLES]}</div>
      </div>
      <div style={s('flex:1;')}></div>
      <div style={s('display:flex; align-items:center; gap:7px; background:#F7F9FB; border:1px solid #E1E7EE; border-radius:9px; padding:4px 6px 4px 11px;')}>
        <span style={s('font-size:13px; opacity:.6;')}>🗓️</span>
        <div style={s('display:flex; background:#fff; border-radius:7px; padding:2px;')}>
          {Object.keys(TIME_META).map((k) => (
            <button key={k} onClick={() => setTimeRange(k)} style={s(timeSeg(timeRange === k))}>{(TIME_META as any)[k].label}</button>
          ))}
        </div>
      </div>
      <div style={s('position:relative;')}>
        <input placeholder="Tìm xã, thôn bản…" style={s('width:180px; height:38px; border:1px solid #E1E7EE; border-radius:9px; padding:0 14px 0 36px; font-family:inherit; font-size:13px; background:#F7F9FB; outline:none; color:#0F1E2A;')} />
        <span style={s('position:absolute; left:12px; top:50%; transform:translateY(-50%); font-size:14px; opacity:.5;')}>🔍</span>
      </div>
      <div style={s('display:flex; align-items:center; gap:6px; padding:7px 13px; background:#F0FAFE; border:1px solid #CBEBF9; border-radius:9px;')}>
        <span style={s('width:8px; height:8px; border-radius:50%; background:#1E9E6A; display:inline-block; animation:gf-blink 2s infinite;')}></span>
        <span style={s('font-size:11.5px; color:#0F1E2A; font-weight:600;')}>Realtime</span>
        <span style={s('font-size:11.5px; color:#7C8896;')}>·</span>
        <span style={s('font-size:12.5px; color:#0F1E2A; font-weight:600; font-variant-numeric:tabular-nums;')}>{clock}</span>
      </div>
      <button style={s('width:40px; height:40px; border-radius:9px; border:1px solid #E1E7EE; background:#fff; font-size:16px; cursor:pointer; position:relative;')}>🔔<span style={s('position:absolute; top:7px; right:7px; width:7px; height:7px; border-radius:50%; background:#E23D3D;')}></span></button>
    </header>
  );
}
