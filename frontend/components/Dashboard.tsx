'use client';

import { useEffect, useRef, useState } from 'react';
import { CheckCircle, WarningCircle, XCircle } from '@phosphor-icons/react';
import { API_BASE_URL, useDashboardData, useDetailData } from '@/lib/api';
import type { User } from './dashboard/types';
import Sidebar from './dashboard/Sidebar';
import Header from './dashboard/Header';
import MapView from './dashboard/MapView';
import OverviewView from './dashboard/OverviewView';
import CommunesView from './dashboard/CommunesView';
import PolicyView from './dashboard/PolicyView';
import ChannelsView from './dashboard/ChannelsView';
import RolesView from './dashboard/RolesView';
import ResidentsDB from './ResidentsDB';
import CommuneDetailSlideOver from './dashboard/CommuneDetailSlideOver';
import UploadModal from './dashboard/UploadModal';
import DocumentReviewModal from './dashboard/DocumentReviewModal';
import FeedbackView from './dashboard/FeedbackView';

type ViewKey = 'map' | 'overview' | 'communes' | 'policy' | 'channels' | 'roles' | 'database' | 'feedback';

interface Props {
  user: User | null;
  onLogout: () => void;
  onLoginRequest: () => void;
}

export default function Dashboard({ user, onLogout, onLoginRequest }: Props) {
  const [view, setView] = useState<ViewKey>('map');
  const [policyRefresh, setPolicyRefresh] = useState(0);
  const [timeRange, setTimeRange] = useState('today');
  const [emergency, setEmergency] = useState(false);
  const [detailId, setDetailId] = useState<string | number | null>(null);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [reviewDocumentId, setReviewDocumentId] = useState<number | null>(null);
  const [clock, setClock] = useState('');
  const [toast, setToast] = useState<{ message: string; tone: 'success' | 'warning' | 'error' } | null>(null);
  const toastTimer = useRef<number | null>(null);

  const { data: snapshot, isLoading, isError } = useDashboardData(emergency, timeRange);
  const { data: detail } = useDetailData(detailId, emergency);

  const showToast = (message: string, tone: 'success' | 'warning' | 'error' = 'success') => {
    setToast({ message, tone });
    if (toastTimer.current) window.clearTimeout(toastTimer.current);
    toastTimer.current = window.setTimeout(() => setToast(null), 3400);
  };

  useEffect(() => {
    const format = () => setClock(new Intl.DateTimeFormat('vi-VN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }).format(new Date()));
    format();
    const timer = window.setInterval(format, 1000);
    return () => window.clearInterval(timer);
  }, []);

  const toggleEmergency = async () => {
    if (!user) {
      onLoginRequest();
      return;
    }
    const next = !emergency;
    setEmergency(next);
    if (!next) {
      showToast('Đã trở về chế độ giám sát thường trực.');
      return;
    }
    showToast('Đang tạo phiên điều phối khẩn cấp...', 'warning');
    
    // Lấy dữ liệu thực tế
    let affectedIds = [1, 2, 3];
    let disasterType = 'Lũ quét';
    if (snapshot) {
      const alertCommunes = snapshot.communes.filter(c => c.statusLabel === 'Cảnh báo');
      if (alertCommunes.length > 0) {
        affectedIds = alertCommunes.map((commune) => Number(commune.id));
      } else {
        affectedIds = snapshot.communes.map((commune) => Number(commune.id)).slice(0, 3);
      }
      
      if (snapshot.predictions && snapshot.predictions.length > 0) {
        disasterType = snapshot.predictions[0].disaster_type || 'Lũ quét';
      }
    }
    
    try {
      const token = window.localStorage.getItem('auth_token');
      const response = await fetch(`${API_BASE_URL}/api/agent/manual-trigger`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ 
          commune_ids: affectedIds, 
          disaster_type: disasterType, 
          message: 'Cảnh báo phát đi từ trung tâm điều hành' 
        }),
      });
      if (!response.ok) throw new Error('trigger failed');
      showToast('Phiên điều phối đã được tạo và thông báo đã được gửi.');
    } catch {
      showToast('Không thể kết nối máy chủ hoặc lỗi phân quyền. Giao diện đang ở chế độ mô phỏng.', 'error');
    }
  };

  const handleAction = async (action: string, communeId: string | number, hamletId: number, hamletName: string) => {
    if (!user) return onLoginRequest();
    try {
      const token = window.localStorage.getItem('auth_token');
      const response = await fetch(`${API_BASE_URL}/api/notifications/${action}`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ commune_id: Number(communeId), hamlet_id: hamletId }),
      });
      if (!response.ok) throw new Error('action failed');
      showToast(`Đã ghi nhận hành động cho ${hamletName}.`);
    } catch {
      showToast('Không thể hoàn tất hành động lúc này hoặc lỗi phân quyền.', 'error');
    }
  };

  if (isLoading || !snapshot) {
    return (
      <div className="app-shell" aria-busy="true">
        <aside className="rail" />
        <div className="app-boot" />
      </div>
    );
  }

  return (
    <div className="app-shell">
      <Sidebar
        user={user}
        view={view}
        setView={(next) => { setView(next as ViewKey); setDetailId(null); }}
        emergency={emergency}
        onLogout={onLogout}
        onLoginRequest={onLoginRequest}
        handleToggleEmergency={toggleEmergency}
      />
      <section className="workspace">
        <Header view={view} timeRange={timeRange} setTimeRange={setTimeRange} clock={clock} user={user} />
        {isError && (
          <div className="data-center-banner" role="alert">
            <WarningCircle size={17} weight="fill" />
            <span>Mất kết nối tới trung tâm dữ liệu</span>
            <button type="button" onClick={() => window.location.reload()}>Thử kết nối lại</button>
          </div>
        )}
        {emergency && (
          <div className="emergency-banner">
            <WarningCircle size={17} weight="fill" />
            <span>Phiên điều phối khẩn cấp đang mở. Dữ liệu mô phỏng cần được cán bộ xác minh trước khi phát cảnh báo.</span>
          </div>
        )}
        <main className="content">
          {view === 'map' && <MapView m={snapshot} emergency={emergency} setDetailId={setDetailId} view={view} />}
          {view === 'overview' && <OverviewView m={snapshot} />}
          {view === 'communes' && <CommunesView m={snapshot} setDetailId={setDetailId} />}
          {view === 'policy' && <PolicyView key={policyRefresh} m={snapshot} user={user} setUploadOpen={setUploadOpen} />}
          {view === 'channels' && <ChannelsView m={snapshot} />}
          {view === 'roles' && <RolesView user={user} />}
          {view === 'database' && <ResidentsDB isProv={user?.role === 'tinh'} assignedCommuneId={user?.commune_id} showToast={showToast} communesData={snapshot.communes} />}
          {view === 'feedback' && <FeedbackView user={user} showToast={showToast} />}
        </main>
      </section>

      {detail && (
        <CommuneDetailSlideOver
          detail={detail}
          setDetailId={setDetailId}
          showToast={(message) => showToast(message)}
          user={user}
          onLoginRequest={onLoginRequest}
          handleAction={handleAction}
        />
      )}
      {uploadOpen && <UploadModal setUploadOpen={setUploadOpen} showToast={(message, tone) => showToast(message, tone as any)} onUploaded={setReviewDocumentId} />}
      {reviewDocumentId && <DocumentReviewModal documentId={reviewDocumentId} communes={snapshot.communes.map((commune) => ({ id: Number(commune.id), name: commune.name }))} onClose={() => setReviewDocumentId(null)} onDone={() => { setReviewDocumentId(null); setView('policy'); setPolicyRefresh((version) => version + 1); showToast('Văn bản đã được duyệt và hiển thị trong mục Đã duyệt.'); }} />}
      {toast && (
        <div className="toast" role="status">
          {toast.tone === 'success' ? <CheckCircle size={17} weight="fill" /> : toast.tone === 'warning' ? <WarningCircle size={17} weight="fill" /> : <XCircle size={17} weight="fill" />}
          {toast.message}
        </div>
      )}
    </div>
  );
}
