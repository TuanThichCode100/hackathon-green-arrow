'use client';

import React, { useState, useEffect, useRef } from 'react';
import { s } from '@/lib/style';
import { useDashboardData, useDetailData } from '@/lib/api';

import { User } from './dashboard/types';
import Sidebar from './dashboard/Sidebar';
import Header from './dashboard/Header';
import MapView from './dashboard/MapView';
import OverviewView from './dashboard/OverviewView';
import CommunesView from './dashboard/CommunesView';
import PolicyView from './dashboard/PolicyView';
import ChannelsView from './dashboard/ChannelsView';
import RolesView from './dashboard/RolesView';
import CommuneDetailSlideOver from './dashboard/CommuneDetailSlideOver';
import UploadModal from './dashboard/UploadModal';

interface MainDashboardProps {
  user: User | null;
  onLogout: () => void;
  onLoginRequest: () => void;
}

export default function Dashboard({ user, onLogout, onLoginRequest }: MainDashboardProps) {
  const [view, setView] = useState('map');
  const [timeRange, setTimeRange] = useState('today');
  const [emergency, setEmergency] = useState(false);
  const [detailId, setDetailId] = useState<string | number | null>(null);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [toastIcon, setToastIcon] = useState('✅');
  const [clock, setClock] = useState('');

  const { data: m, isLoading: mLoading } = useDashboardData(emergency, timeRange);
  const { data: detail, isLoading: dLoading } = useDetailData(detailId, emergency);

  const toastTimer = useRef<NodeJS.Timeout | null>(null);
  const showToast = (msg: string, icon = '✅') => {
    setToast(msg); setToastIcon(icon);
    if (toastTimer.current) clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToast(null), 3200);
  };

  const handleToggleEmergency = async () => {
    const nextState = !emergency;
    setEmergency(nextState);
    if (nextState) {
      showToast('Đang phân tích rủi ro & gọi AI Agent...', '⏳');
      try {
        const res = await fetch('http://localhost:8000/api/agent/manual-trigger', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            commune_ids: [1, 2, 3],
            disaster_type: "Lũ quét nguy hiểm",
            message: "Mưa lớn kéo dài"
          })
        });
        const data = await res.json();
        if (res.ok) {
          showToast('AI Agent đã ra quyết định hành động!', '🤖');
          console.log("AI Decision:", data);
        } else {
          showToast('Lỗi khi gọi AI Agent', '❌');
        }
      } catch (err) {
        showToast('Không kết nối được tới Backend', '❌');
        console.error(err);
      }
    } else {
      showToast('Đã tắt chế độ khẩn cấp', '✅');
    }
  };

  const handleAction = async (action: string, communeId: string | number, hamletName: string) => {
    try {
      showToast(`Đang xử lý yêu cầu ${action}...`, '⏳');
      const res = await fetch(`http://localhost:8000/api/notifications/${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ commune_id: communeId, hamlet_id: 1 })
      });
      if (res.ok) {
        showToast(`Đã hoàn tất gửi tới ${hamletName}`, '✅');
      } else {
        showToast('Có lỗi xảy ra', '❌');
      }
    } catch (e) {
      showToast('Không thể kết nối Backend', '❌');
    }
  };

  // realtime clock
  useEffect(() => {
    const p = (n: number) => String(n).padStart(2, '0');
    const tick = () => { const d = new Date(); setClock(`${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`); };
    tick();
    const t = setInterval(tick, 1000);
    return () => clearInterval(t);
  }, []);

  if (mLoading || !m) {
    return <div style={{display:'flex',height:'100vh',alignItems:'center',justifyContent:'center',background:'#0F1E2A',color:'#3FD98A',fontSize:'18px',fontWeight:'700'}}>Đang đồng bộ dữ liệu từ hệ thống...</div>;
  }

  return (
    <div style={s('display:flex; height:100vh; width:100%; overflow:hidden; background:#EEF2F6;')}>
      <Sidebar 
        user={user} view={view} setView={setView} setDetailId={setDetailId} 
        emergency={emergency} m={m} onLogout={onLogout} onLoginRequest={onLoginRequest} 
        handleToggleEmergency={handleToggleEmergency} 
      />

      <div style={s('flex:1; display:flex; flex-direction:column; height:100%; min-width:0;')}>
        <Header view={view} timeRange={timeRange} setTimeRange={setTimeRange} clock={clock} />

        {emergency && (
          <div style={s('background:linear-gradient(90deg,#C42B2B,#E23D3D); color:#fff; padding:11px 26px; display:flex; align-items:center; gap:14px;')}>
            <span style={s('font-size:19px; animation:gf-blink 1.1s infinite;')}>⚠️</span>
            <div style={s('flex:1;')}>
              <span style={s('font-weight:700; font-size:13.5px;')}>TÌNH TRẠNG KHẨN CẤP ĐANG KÍCH HOẠT</span>
              <span style={s('font-size:12.5px; opacity:.95; margin-left:10px;')}>{m.alertHeadline}</span>
            </div>
            <span style={s('font-size:12px; background:rgba(255,255,255,.18); padding:5px 11px; border-radius:20px; font-weight:600;')}>Độ trễ hệ thống: 38 giây</span>
          </div>
        )}

        <main style={s('flex:1; overflow-y:auto; overflow-x:hidden;')}>
          {view === 'map' && <MapView m={m} emergency={emergency} setDetailId={setDetailId} view={view} />}
          {view === 'overview' && <OverviewView m={m} />}
          {view === 'communes' && <CommunesView m={m} setDetailId={setDetailId} />}
          {view === 'policy' && <PolicyView m={m} user={user} setUploadOpen={setUploadOpen} />}
          {view === 'channels' && <ChannelsView m={m} />}
          {view === 'roles' && <RolesView user={user} />}
        </main>
      </div>

      {detail && (
        <CommuneDetailSlideOver 
          detail={detail} setDetailId={setDetailId} showToast={showToast} 
          user={user} onLoginRequest={onLoginRequest} handleAction={handleAction} 
        />
      )}

      {uploadOpen && (
        <UploadModal setUploadOpen={setUploadOpen} showToast={showToast} />
      )}

      {toast && (
        <div style={s('position:fixed; bottom:26px; left:50%; transform:translateX(-50%); z-index:1000; background:#0F1E2A; color:#fff; padding:13px 20px; border-radius:11px; box-shadow:0 12px 34px rgba(15,30,42,.3); display:flex; align-items:center; gap:11px; animation:gf-toastin .3s ease;')}>
          <span style={s('font-size:17px;')}>{toastIcon}</span>
          <span style={s('font-size:13px; font-weight:500;')}>{toast}</span>
        </div>
      )}
    </div>
  );
}
