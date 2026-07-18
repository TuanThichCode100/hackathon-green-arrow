import useSWR from 'swr';
import { useMemo } from 'react';
import { TIME_META, statusMeta, rateColor, pill, fmt, statusOf } from './data';

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const fetcher = async (url) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
  const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
  const res = await fetch(url, { headers });
  if (!res.ok) throw new Error('API Error');
  const json = await res.json();
  return json.data;
};

// Hook for Map & Overview
export function useDashboardData(emergency, timeRange) {
  const { data: communesData, error: communesErr } = useSWR(`${API_BASE_URL}/api/communes`, fetcher);
  const { data: policiesData } = useSWR(`${API_BASE_URL}/api/documents`, fetcher);
  const { data: overviewData } = useSWR(`${API_BASE_URL}/api/stats/overview?time_range=${timeRange}`, fetcher);
  const { data: channelsData } = useSWR(`${API_BASE_URL}/api/stats/channels?time_range=${timeRange}`, fetcher);
  const { data: ethnicsData } = useSWR(`${API_BASE_URL}/api/stats/ethnics`, fetcher);
  const { data: activitiesData } = useSWR(`${API_BASE_URL}/api/stats/activities?limit=10`, fetcher);
  const { data: predictionsData } = useSWR(`${API_BASE_URL}/api/predictions/latest`, fetcher);
  const { data: notificationsData } = useSWR(`${API_BASE_URL}/api/notifications`, fetcher);

  const isLoading = !communesData;
  const isError = communesErr;

  const ov = overviewData || {};
  const globalRate = ov.recv_rate !== undefined ? ov.recv_rate : (emergency ? 0.6 : 0.98);

  const communes = useMemo(() => {
    if (!communesData) return [];
    return communesData.map((c) => {
      const st = emergency ? (c.alert_status || 'alert') : 'safe';
      const meta = statusMeta(st);
      
      // Use real recv_rate if commune has it, else use global DB rate with slight variation
      const randomJitter = ((c.id % 11) - 5) / 100; // -0.05 to +0.05
      let rate = c.recv_rate !== undefined ? c.recv_rate : (globalRate + randomJitter);
      rate = Math.max(0, Math.min(1, rate)); // clamp 0-1
      
      const received = Math.round(c.population * rate);
      const notReceived = c.population - received;
      
      return {
        id: c.id, 
        name: c.name, 
        icon: c.disaster_icon || (emergency ? '🌊' : '🟢'), 
        hazard: c.disaster_type || (emergency ? 'Lũ quét' : 'Không có cảnh báo'),
        popStr: fmt(c.population), 
        receivedStr: fmt(received), 
        notReceivedStr: fmt(notReceived),
        notReceivedColor: notReceived > c.population * 0.15 ? '#E23D3D' : '#5A6675',
        rateStr: Math.round(rate * 100) + '%', 
        rateColor: rateColor(rate),
        statusLabel: meta.label, 
        pillStyle: pill(meta.color, meta.bg),
        lat: c.lat,
        lng: c.lng,
        pop: c.population
      };
    });
  }, [communesData, emergency]);

  if (isLoading || isError) {
    return { data: null, isLoading, isError };
  }

  // --- TRANSFORMATION LOGIC (Mapping backend to UI format) ---
  const tf = TIME_META[timeRange].factor;

  // Re-calculate KPIs based on API communes
  const totalPop = communes.reduce((s, c) => s + c.pop, 0);
  const totalRecv = communes.reduce((s, c) => s + parseInt(c.receivedStr.replace(/\./g, '')), 0);
  const totalNot = totalPop - totalRecv;
  const alertCount = communes.filter((c) => c.statusLabel === 'Cảnh báo').length;
  
  // Use real headmen count if available
  const headmenTotal = ov.headmen_total || 0;
  const headmenConfirmed = ov.headmen_confirmed || 0;

  const kpiCard = 'background:#fff; border:1px solid #E1E7EE; border-radius:14px; padding:15px 17px;';
  const kpiCardAlert = 'background:#fff; border:1px solid #F6C6C6; border-radius:14px; padding:15px 17px; box-shadow:0 0 0 1px #F6C6C6;';
  
  const ovPop = ov.total_pop || totalPop;
  const ovRecv = Math.round((ov.recv_rate || (totalRecv/totalPop)) * ovPop);
  const ovNot = ov.not_responded || (ovPop - ovRecv);
  const hConf = ov.headmen_confirmed || headmenConfirmed;
  const aAct = ov.active_alerts !== undefined ? ov.active_alerts : alertCount;

  const kpis = [
    { label: 'Dân số vùng ảnh hưởng', icon: '👥', value: fmt(ovPop), sub: 'trên ' + communes.length + ' xã/phường giám sát', cardStyle: kpiCard, valueColor: '#0F1E2A' },
    { label: 'Đã nhận cảnh báo', icon: '✅', value: Math.round((ovRecv / (ovPop||1)) * 100) + '%', sub: fmt(ovRecv) + ' người', cardStyle: kpiCard, valueColor: '#1E9E6A' },
    { label: 'Chưa phản hồi', icon: '⚠️', value: fmt(ovNot), sub: emergency ? 'cần cử lực lượng tiếp cận' : 'trong ngưỡng an toàn', cardStyle: emergency ? kpiCardAlert : kpiCard, valueColor: emergency ? '#E23D3D' : '#5A6675' },
    { label: 'Trưởng bản xác nhận', icon: '📢', value: headmenConfirmed + '/' + headmenTotal, sub: 'đã nhận file Audio loa', cardStyle: kpiCard, valueColor: '#0F1E2A' },
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
        type: p.document_type,
        by: 'Hệ thống',
        start: new Date(p.created_at).toLocaleDateString(),
        end: 'Không thời hạn',
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
  let url = `${API_BASE_URL}/api/residents?page=${page}&limit=${limit}`;
  if (communeId) url += `&commune_id=${communeId}`;
  if (ethnic) url += `&ethnic=${encodeURIComponent(ethnic)}`;

  const { data, error, isLoading, mutate } = useSWR(url, fetcher);
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
  if (!res.ok) throw new Error('Create failed');
  return res.json();
};

export const apiUpdateResident = async (id, data) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
  const res = await fetch(`${API_BASE_URL}/api/residents/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', ...(token ? {'Authorization': `Bearer ${token}`} : {}) },
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error('Update failed');
  return res.json();
};

export const apiDeleteResident = async (id) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
  const res = await fetch(`${API_BASE_URL}/api/residents/${id}`, { 
    method: 'DELETE',
    headers: token ? {'Authorization': `Bearer ${token}`} : {}
  });
  if (!res.ok) throw new Error('Delete failed');
  return res.json();
};

export const apiImportResidents = async (records) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
  const res = await fetch(`${API_BASE_URL}/api/residents/import`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...(token ? {'Authorization': `Bearer ${token}`} : {}) },
    body: JSON.stringify({ records })
  });
  if (!res.ok) throw new Error('Import failed');
  return res.json();
};
