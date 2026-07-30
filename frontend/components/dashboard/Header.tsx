import { useEffect, useState } from 'react';
import { Bell, Check, CloudCheck, Spinner, X } from '@phosphor-icons/react';
import { API_BASE_URL } from '@/lib/api';
import type { User } from './types';

const titles: Record<string, string> = { map: 'Bản đồ rủi ro', overview: 'Tổng quan vận hành', communes: 'Địa bàn và mức tiếp cận', policy: 'Văn bản chỉ đạo', channels: 'Phân phối cảnh báo', roles: 'Quyền truy cập', database: 'Dữ liệu dân cư' };
const ranges = [['today', 'Hôm nay'], ['24h', '24 giờ'], ['7d', '7 ngày'], ['30d', '30 ngày']];
type Notice = { id: number; actor_name: string; actor_role: string; title: string; subtitle: string; created_at: string; read: boolean; request_id?: number; actionable?: boolean };

const roleLabel = (role: string) => role === 'tinh' ? 'Cán bộ tỉnh' : role === 'xa' ? 'Cán bộ xã' : 'Hệ thống';
const relativeTime = (value: string) => { const minutes = Math.max(0, Math.floor((Date.now() - new Date(value).getTime()) / 60000)); return minutes < 1 ? 'Vừa xong' : minutes < 60 ? `${minutes} phút trước` : `${Math.floor(minutes / 60)} giờ trước`; };

export default function Header({ view, timeRange, setTimeRange, clock, user }: { view: string; timeRange: string; setTimeRange: (value: string) => void; clock: string; user: User | null }) {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<Notice[]>([]);
  const [loading, setLoading] = useState(false);
  const [actingId, setActingId] = useState<number | null>(null);
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const unread = items.filter((item) => !item.read).length;

  const load = async (): Promise<Notice[]> => {
    if (!user) { setItems([]); return []; }
    setLoading(true);
    try { const response = await fetch(`${API_BASE_URL}/api/documents/notifications`, { headers }); const body = await response.json(); if (!response.ok) throw new Error(); const notices = body.data || []; setItems(notices); return notices; } catch { setItems([]); return []; } finally { setLoading(false); }
  };
  useEffect(() => { load(); /* Initial count for the bell. */ // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.id]);

  const toggleNotifications = async () => {
    const next = !open; setOpen(next);
    if (!next) return;
    const latest = await load();
    const unreadIds = latest.filter((item) => !item.read).map((item) => item.id);
    if (unreadIds.length) {
      await fetch(`${API_BASE_URL}/api/documents/notifications/read`, { method: 'POST', headers: { 'Content-Type': 'application/json', ...headers }, body: JSON.stringify({ event_ids: unreadIds }) });
      setItems((current) => current.map((item) => ({ ...item, read: true })));
    }
  };
  const decide = async (notice: Notice, approve: boolean) => {
    if (!notice.request_id) return;
    setActingId(notice.id);
    try {
      const response = await fetch(`${API_BASE_URL}/api/documents/view-requests/${notice.request_id}/decision`, { method: 'POST', headers: { 'Content-Type': 'application/json', ...headers }, body: JSON.stringify({ approve }) });
      if (!response.ok) throw new Error();
      await load();
    } finally { setActingId(null); }
  };

  return <header className="topbar"><div className="page-heading"><p className="eyebrow">Tỉnh Điện Biên</p><h1>{titles[view]}</h1></div><div className="topbar-spacer" /><div className="time-control" aria-label="Khoảng thời gian">{ranges.map(([key, label]) => <button key={key} className={timeRange === key ? 'active' : ''} onClick={() => setTimeRange(key)}>{label}</button>)}</div><div className="live-status"><span className="live-dot" /><CloudCheck size={16} />Đồng bộ <span className="mono">{clock}</span></div><div className="notification-wrap"><button className="icon-button notification-button" aria-label="Thông báo" aria-expanded={open} onClick={toggleNotifications}><Bell size={18} />{unread > 0 && <span className="notification-badge">{unread > 9 ? '9+' : unread}</span>}</button>{open && <section className="notification-popover" aria-label="Danh sách thông báo"><header><div><p className="eyebrow">Thông báo</p><h2>Hoạt động gần đây</h2></div></header>{loading && <div className="notification-empty"><Spinner size={20} className="spin" />Đang tải thông báo…</div>}{!loading && !items.length && <div className="notification-empty">Chưa có thông báo mới.</div>}{!loading && items.map((notice) => <article className={`notification-card ${notice.read ? '' : 'unread'}`} key={notice.id}><div className="notification-avatar">{notice.actor_name.slice(0, 1).toUpperCase()}</div><div className="notification-copy"><strong>{notice.actor_name} <span>· {roleLabel(notice.actor_role)}</span></strong><b>{notice.title}</b><p>{notice.subtitle}</p><time>{relativeTime(notice.created_at)}</time>{notice.actionable && <div className="notification-actions"><button className="primary-button" disabled={actingId === notice.id} onClick={() => decide(notice, true)}><Check size={15} />Duyệt</button><button className="secondary-button" disabled={actingId === notice.id} onClick={() => decide(notice, false)}><X size={15} />Từ chối</button></div>}</div></article>)}</section>}</div></header>;
}
