import useSWR from 'swr';
import { useMemo } from 'react';
import { TIME_META, statusMeta, rateColor, pill, fmt } from './data';
import type { DashboardData } from '@/components/dashboard/types';

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const finiteNumber = (value: unknown): number | null => typeof value === 'number' && Number.isFinite(value) ? value : null;

const fetcher = async (url) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
  const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
  const res = await fetch(url, { headers });
  if (!res.ok) throw new Error('API Error');
  const json = await res.json();
  return json.data;
};

// Hook for Map & Overview
type DashboardDataResult = {
  data: DashboardData | null;
  isLoading: boolean;
  isError: boolean;
};

const emptyDashboard = (timeRange: string): DashboardData => ({
  kpis: [], communes: [], channels: [], ethnics: [], activities: [], policies: [], logs: [],
  alertCount: 0, alertHeadline: '', timeText: TIME_META[timeRange].text,
  policyActive: 0, policyExpiring: 0, policyExpired: 0, predictions: [],
});

export function useDashboardData(emergency: boolean, timeRange: string): DashboardDataResult {
  const hasToken = typeof window !== 'undefined' ? !!localStorage.getItem('auth_token') : false;
  const { data: communesData, error: communesErr } = useSWR(`${API_BASE_URL}/api/communes`, fetcher);
  const { data: policiesData } = useSWR(hasToken ? `${API_BASE_URL}/api/documents` : null, fetcher);
  const { data: overviewData } = useSWR(`${API_BASE_URL}/api/stats/overview?time_range=${timeRange}`, fetcher);
  const { data: channelsData } = useSWR(`${API_BASE_URL}/api/stats/channels?time_range=${timeRange}`, fetcher);
  const { data: ethnicsData } = useSWR(`${API_BASE_URL}/api/stats/ethnics`, fetcher);
  const { data: activitiesData } = useSWR(`${API_BASE_URL}/api/stats/activities?limit=10`, fetcher);
  const { data: predictionsData } = useSWR(`${API_BASE_URL}/api/predictions/latest`, fetcher);
  const { data: notificationsData } = useSWR(hasToken ? `${API_BASE_URL}/api/notifications` : null, fetcher);

  const isLoading = !communesData && !communesErr;
  const isError = Boolean(communesErr);

  const ov = overviewData || {};

  const communes = useMemo(() => {
    if (!communesData) return [];
    return communesData.map((c) => {
      const st = c.alert_status || 'unverified';
      const meta = statusMeta(st);
      const population = finiteNumber(c.population);
      const rate = finiteNumber(c.recv_rate) === null ? null : Math.max(0, Math.min(1, c.recv_rate));
      
      const received = rate === null || population === null ? null : Math.round(population * rate);
      const notReceived = received === null || population === null ? null : population - received;
      
      return {
        id: c.id, 
        name: c.name, 
        icon: c.disaster_icon || '•', 
        hazard: c.disaster_type || 'Chưa xác thực',
        popStr: fmt(population), 
        receivedStr: received === null ? '—' : fmt(received), 
        notReceivedStr: notReceived === null ? '—' : fmt(notReceived),
        notReceivedColor: '#5A6675',
        rateStr: rate === null ? '—' : Math.round(rate * 100) + '%', 
        rateColor: rate === null ? '#64748B' : rateColor(rate),
        statusLabel: meta.label, 
        pillStyle: pill(meta.color, meta.bg),
        lat: c.lat,
        lng: c.lng,
        pop: population || 0,
        received,
      };
    });
  }, [communesData, emergency]);

  if (isError) return { data: emptyDashboard(timeRange), isLoading: false, isError: true };

  if (isLoading) {
    return { data: null, isLoading: true, isError: false };
  }

  // --- TRANSFORMATION LOGIC (Mapping backend to UI format) ---
  const tf = TIME_META[timeRange].factor;

  // Re-calculate KPIs based on API communes
  const totalPop = communes.reduce((sum, commune) => sum + commune.pop, 0);
  const totalRecv = communes.reduce((sum, commune) => sum + (commune.received || 0), 0);
  const totalNot = totalPop - totalRecv;
  const alertCount = communes.filter((c) => c.statusLabel === 'Cảnh báo').length;
  
  // Use real headmen count if available
  const headmenTotal = ov.headmen_total || 0;
  const headmenConfirmed = ov.headmen_confirmed || 0;

  const kpiCard = 'background:#fff; border:1px solid #E1E7EE; border-radius:14px; padding:15px 17px;';
  const kpiCardAlert = 'background:#fff; border:1px solid #F6C6C6; border-radius:14px; padding:15px 17px; box-shadow:0 0 0 1px #F6C6C6;';
  
  const overviewPopulation = finiteNumber(ov.total_pop);
  const ovPop = overviewPopulation && overviewPopulation > 0 ? overviewPopulation : (totalPop > 0 ? totalPop : null);
  const overviewRate = ovPop === null ? null : finiteNumber(ov.recv_rate);
  const calculatedRate = ovPop && totalRecv >= 0 ? totalRecv / ovPop : null;
  const recvRate = overviewRate ?? calculatedRate;
  const ovRecv = ovPop !== null && recvRate !== null ? Math.round(Math.max(0, Math.min(1, recvRate)) * ovPop) : null;
  const overviewNotResponded = finiteNumber(ov.not_responded);
  const ovNot = overviewNotResponded ?? (ovPop !== null && ovRecv !== null ? Math.max(0, ovPop - ovRecv) : null);
  const hConf = finiteNumber(ov.headmen_confirmed) ?? headmenConfirmed;
  const hasHeadmenData = headmenTotal > 0;
  const aAct = ov.active_alerts !== undefined ? ov.active_alerts : alertCount;

  const kpis = [
    { label: 'Dân số vùng ảnh hưởng', icon: '👥', value: fmt(ovPop), sub: communes.length ? 'trên ' + communes.length + ' xã/phường giám sát' : 'chưa có dữ liệu địa bàn', cardStyle: kpiCard, valueColor: '#0F1E2A' },
    { label: 'Đã nhận cảnh báo', icon: '✅', value: ovPop && ovRecv !== null ? Math.round((ovRecv / ovPop) * 100) + '%' : '—', sub: ovRecv === null ? 'chưa có số liệu xác thực' : fmt(ovRecv) + ' người', cardStyle: kpiCard, valueColor: '#1E9E6A' },
    { label: 'Chưa phản hồi', icon: '⚠️', value: fmt(ovNot), sub: ovNot === null ? 'chưa có số liệu xác thực' : emergency ? 'cần cử lực lượng tiếp cận' : 'trong ngưỡng an toàn', cardStyle: emergency ? kpiCardAlert : kpiCard, valueColor: emergency ? '#E23D3D' : '#5A6675' },
    { label: 'Trưởng bản xác nhận', icon: '📢', value: hasHeadmenData ? hConf + '/' + headmenTotal : '—', sub: hasHeadmenData ? 'đã nhận file Audio loa' : 'chưa có số liệu xác thực', cardStyle: kpiCard, valueColor: '#0F1E2A' },
    { label: emergency ? 'Cảnh báo đang mở' : 'Trạng thái hệ thống', icon: emergency ? '🚨' : '🟢', value: emergency ? String(aAct) : 'Ổn định', sub: emergency ? 'xã ở mức Cảnh báo' : 'giám sát thường trực', cardStyle: emergency ? kpiCardAlert : kpiCard, valueColor: emergency ? '#E23D3D' : '#1E9E6A' },
  ];

  // Channels, Ethnics, Activities (Fallback to hardcoded for demo if backend not fully seeded)
  // (We can connect them fully once backend has data)
  const chBase = channelsData && channelsData.length > 0 ? channelsData : [];
  const channels = chBase.map((ch) => {
    return { name: ch.name, icon: ch.name === 'zalo' ? '💬' : ch.name === 'sms' ? '✉️' : '📞', color: ch.name === 'zalo' ? '#1E9E6A' : ch.name === 'sms' ? '#25ADE3' : '#E8A93B', sentStr: fmt(ch.sent), deliveredStr: fmt(ch.delivered), failedStr: fmt(ch.failed), rateStr: Math.round(ch.rate * 100) + '%', pct: Math.round(ch.rate * 100) + '%' };
  });

  const eth = ethnicsData && ethnicsData.length > 0 ? ethnicsData : [];
  const ethTotal = eth.reduce((s, e) => s + (e.value || 0), 0) || 1;
  const ethnics = eth.map((e) => ({ name: e.name, popStr: fmt(e.value || 0), pct: Math.round(((e.value || 0) / ethTotal) * 100) + '%' }));

  const activities = activitiesData && activitiesData.length > 0 ? activitiesData : [];

  let logs = [];
  if (notificationsData?.items?.length > 0) {
    logs = notificationsData.items.map(n => ({
      time: new Date(n.sent_at).toLocaleTimeString('vi-VN', {hour:'2-digit', minute:'2-digit', second:'2-digit'}),
      commune: `Xã ID: ${n.commune_id}`,
      channel: n.channel,
      channelIcon: n.channel === 'zalo' ? '💬' : n.channel === 'sms' ? '✉️' : '📞',
      ethnic: n.ethnic_language,
      recipientsStr: fmt(n.recipient_count),
      statusLabel: n.status === 'delivered' ? 'Đã gửi' : n.status === 'failed' ? 'Thất bại' : 'Đang xử lý',
      pillStyle: n.status === 'delivered' ? pill('#1E9E6A', '#E7F6EF') : n.status === 'failed' ? pill('#E23D3D', '#FDECEC') : pill('#25ADE3', '#EAF7FD')
    }));
  }

  // Policies mapping
  let policies = [];
  if (policiesData) {
    policies = policiesData.map(p => {
      const isAct = p.status === 'active';
      const meta = isAct ? { label: 'Còn hiệu lực', color: '#1E9E6A', bg: '#E7F6EF' } : { label: 'Hết hiệu lực', color: '#9AA4B0', bg: '#EEF2F6' };
      return {
        code: p.id,
        title: p.title,
        type: p.doc_type,
        by: p.issued_by,
        start: p.start_date ? new Date(p.start_date).toLocaleDateString('vi-VN') : 'Chưa xác định',
        end: p.end_date ? new Date(p.end_date).toLocaleDateString('vi-VN') : 'Không xác định',
        status: p.status,
        statusLabel: meta.label,
        pillStyle: pill(meta.color, meta.bg)
      };
    });
  }

  const aHeadline = predictionsData && predictionsData.length > 0 
    ? `Hệ thống ghi nhận nguy cơ ${predictionsData[0].disaster_type} với xác suất ${Math.round(predictionsData[0].probability*100)}%` 
    : 'Hệ thống đang phát cảnh báo khẩn cấp dựa trên dự đoán AI.';
  const alertHeadline = emergency ? aHeadline : '';

  return {
    data: {
      kpis, communes, channels, ethnics, activities, policies, logs,
      alertCount, alertHeadline,
      timeText: TIME_META[timeRange].text,
      policyActive: policies.filter(p => p.status === 'active').length,
      policyExpiring: 0,
      policyExpired: policies.filter(p => p.status !== 'active').length,
      predictions: predictionsData,
    },
    isLoading: false,
    isError: false
  };
}

export function useDetailData(id, emergency) {
  const { data: detailData, error, isLoading } = useSWR(id ? `${API_BASE_URL}/api/communes/${id}` : null, fetcher);

  if (isLoading || error || !detailData) {
    return { data: null, isLoading, error };
  }

  const c = detailData;
  const st = emergency ? 'alert' : 'safe';
  const rate = emergency ? (c.recv_rate || 0.6) : (c.recv_rate || 0.98);
  const received = Math.round(c.population * rate);
  const notReceived = c.population - received;
  
  const hamlets = (c.hamlets || []).map((h, i) => {
    const hr = Math.min(1, Math.max(0.3, rate + (i % 2 === 0 ? 0.04 : -0.06)));
    const confirmed = !emergency || hr >= 0.75;
    return { 
      id: h.id,
      name: h.name, 
      headman: h.headman_name || 'Đang cập nhật', 
      rateStr: Math.round(hr * 100) + '%', 
      rateColor: rateColor(hr), 
      confirmLabel: confirmed ? 'đã xác nhận ✅' : 'CHƯA xác nhận ⚠️' 
    };
  });

  const hasLost = !!(emergency && st === 'alert'); // Simplified
  const headBg = (st as string) === 'alert' ? 'linear-gradient(135deg,#C42B2B,#E23D3D)' : (st as string) === 'watch' ? 'linear-gradient(135deg,#0F1E2A,#2A4A5E)' : 'linear-gradient(135deg,#0F1E2A,#1E9E6A)';

  return {
    data: {
      id: c.id, 
      icon: c.disaster_icon || '🌊', 
      name: c.name, 
      hazard: emergency ? (c.disaster_type || 'Lũ quét') : 'Không có cảnh báo',
      popStr: fmt(c.population), 
      receivedStr: fmt(received), 
      notReceivedStr: fmt(notReceived),
      notReceivedColor: notReceived > c.population * 0.15 ? '#E23D3D' : '#5A6675',
      rateStr: Math.round(rate * 100) + '%', 
      rateColor: rateColor(rate),
      hamletCount: hamlets.length, 
      hamlets,
      hasLost: false, 
      lostCount: 0,
      lost: [],
      headBg,
    },
    isLoading: false,
    error: false
  };
}

// Residents Hooks
export function useResidents(communeId, ethnic, page, limit = 50) {
  const hasToken = typeof window !== 'undefined' ? !!localStorage.getItem('auth_token') : false;
  let url = `${API_BASE_URL}/api/residents?page=${page}&limit=${limit}`;
  if (communeId) url += `&commune_id=${communeId}`;
  if (ethnic) url += `&ethnic=${encodeURIComponent(ethnic)}`;

  const { data, error, isLoading, mutate } = useSWR(hasToken ? url : null, fetcher);
  return {
    data: data,
    isLoading,
    isError: error,
    mutate
  };
}

export const apiCreateResident = async (data) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
  const res = await fetch(`${API_BASE_URL}/api/residents`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...(token ? {'Authorization': `Bearer ${token}`} : {}) },
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || 'Không thể thêm dân cư');
  return res.json();
};

export const apiUpdateResident = async (id, data) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
  const res = await fetch(`${API_BASE_URL}/api/residents/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', ...(token ? {'Authorization': `Bearer ${token}`} : {}) },
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || 'Không thể cập nhật dân cư');
  return res.json();
};

export const apiDeleteResident = async (id) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
  const res = await fetch(`${API_BASE_URL}/api/residents/${id}`, { 
    method: 'DELETE',
    headers: token ? {'Authorization': `Bearer ${token}`} : {}
  });
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || 'Không thể xóa dân cư');
  return res.json();
};

export const apiImportResidents = async (records) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
  const res = await fetch(`${API_BASE_URL}/api/residents/import`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...(token ? {'Authorization': `Bearer ${token}`} : {}) },
    body: JSON.stringify({ records })
  });
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || 'Không thể import CSV');
  return res.json();
};
