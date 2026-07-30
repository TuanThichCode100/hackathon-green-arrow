import { useState } from 'react';
import useSWR from 'swr';
import { CheckCircle, FloppyDisk, IdentificationCard } from '@phosphor-icons/react';
import type { User } from './types';
import { API_BASE_URL } from '@/lib/api';

type ManagedUser = { id: string; email?: string; name?: string; role?: 'tinh' | 'xa' | null; commune_id?: number | null };
type Commune = { id: number; name: string };

const fetcher = async (url: string) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
  const response = await fetch(url, { headers: token ? { Authorization: `Bearer ${token}` } : {} });
  if (!response.ok) throw new Error('Không thể tải dữ liệu.');
  const body = await response.json();
  return body.data;
};

const roles = [
  ['Cán bộ tỉnh', 'Giám sát toàn tỉnh, quản lý văn bản và mở phiên điều phối.'],
  ['Cán bộ xã', 'Theo dõi địa bàn phụ trách, gửi lại cảnh báo và xác nhận thôn bản.'],
];

export default function RolesView({ user }: { user: User | null }) {
  const { data: users, error, mutate } = useSWR<ManagedUser[]>(user?.role === 'tinh' ? `${API_BASE_URL}/api/users` : null, fetcher);
  const { data: communes } = useSWR<Commune[]>(user?.role === 'tinh' ? `${API_BASE_URL}/api/communes` : null, fetcher);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draft, setDraft] = useState({ name: '', role: 'xa' as 'tinh' | 'xa', commune_id: '' });
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  const beginEdit = (account: ManagedUser) => {
    setEditingId(account.id);
    setDraft({ name: account.name || '', role: account.role || 'xa', commune_id: account.commune_id ? String(account.commune_id) : '' });
    setMessage('');
  };

  const save = async () => {
    if (!editingId) return;
    if (draft.role === 'xa' && !draft.commune_id) {
      setMessage('Hãy chọn xã/phường phụ trách cho cán bộ xã.');
      return;
    }
    setSaving(true);
    setMessage('');
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`${API_BASE_URL}/api/users/${editingId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        body: JSON.stringify({ name: draft.name, role: draft.role, commune_id: draft.role === 'xa' ? Number(draft.commune_id) : null }),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail || 'Không thể cập nhật tài khoản.');
      await mutate((current) => current?.map((account) => account.id === editingId ? body.data : account), false);
      setEditingId(null);
      setMessage('Đã cập nhật quyền tài khoản. Người dùng cần đăng nhập lại để áp dụng quyền mới.');
    } catch (reason) {
      setMessage(reason instanceof Error ? reason.message : 'Không thể cập nhật tài khoản.');
    } finally {
      setSaving(false);
    }
  };

  return <div className="view-page">
    <div className="section-heading"><div><h2>Quyền truy cập</h2><p>Vai trò và danh sách cán bộ đang hoạt động trong hệ thống.</p></div></div>
    <section className="data-section">
      {roles.map(([name, description], index) => <div className="bar-row" key={name}><div className="bar-meta"><strong><IdentificationCard size={18} /> {name}</strong>{(index === 0 && user?.role === 'tinh') || (index === 1 && user?.role === 'xa') ? <span className="status-pill status-safe"><CheckCircle size={14} />Đang sử dụng</span> : null}</div><p style={{ margin: '7px 0 0', color: 'var(--ink-muted)', fontSize: 12 }}>{description}</p></div>)}
    </section>
    {user?.role === 'tinh' && <>
      <div className="section-heading" style={{ marginTop: 24 }}><div><h2>Danh sách tài khoản</h2><p>Chỉ cán bộ tỉnh được gán vai trò và xã/phường phụ trách.</p></div></div>
      <section className="data-section" style={{ padding: '0 20px 20px' }}>
        {!users && !error && <p>Đang tải danh sách tài khoản...</p>}
        {error && <p className="form-error">Không thể tải danh sách tài khoản. Vui lòng kiểm tra quyền truy cập.</p>}
        {message && <p className={message.startsWith('Đã ') ? 'success-message' : 'form-error'} role="status">{message}</p>}
        {users && <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: 10 }}><thead><tr style={{ borderBottom: '1px solid var(--border)', textAlign: 'left', fontSize: 13, color: 'var(--ink-muted)' }}><th style={{ padding: '12px 8px' }}>Email</th><th style={{ padding: '12px 8px' }}>Tên hiển thị</th><th style={{ padding: '12px 8px' }}>Vai trò</th><th style={{ padding: '12px 8px' }}>Xã/phường</th><th style={{ padding: '12px 8px' }} aria-label="Thao tác" /></tr></thead><tbody>
          {users.map((account) => {
            const editing = editingId === account.id;
            return <tr key={account.id} style={{ borderBottom: '1px solid var(--border)', fontSize: 14 }}>
              <td style={{ padding: '12px 8px', fontWeight: 500 }}>{account.email}</td>
              <td style={{ padding: '12px 8px' }}>{editing ? <input value={draft.name} onChange={(event) => setDraft({ ...draft, name: event.target.value })} aria-label="Tên hiển thị" /> : account.name || 'Chưa đặt tên'}</td>
              <td style={{ padding: '12px 8px' }}>{editing ? <select value={draft.role} onChange={(event) => setDraft({ ...draft, role: event.target.value as 'tinh' | 'xa', commune_id: event.target.value === 'tinh' ? '' : draft.commune_id })} aria-label="Vai trò"><option value="tinh">Cán bộ tỉnh</option><option value="xa">Cán bộ xã</option></select> : <span className={`status-pill ${account.role === 'tinh' ? 'status-safe' : account.role === 'xa' ? 'status-watch' : ''}`}>{account.role === 'tinh' ? 'Cán bộ tỉnh' : account.role === 'xa' ? 'Cán bộ xã' : 'Chưa phân quyền'}</span>}</td>
              <td style={{ padding: '12px 8px' }}>{editing ? <select value={draft.commune_id} disabled={draft.role !== 'xa'} onChange={(event) => setDraft({ ...draft, commune_id: event.target.value })} aria-label="Xã/phường phụ trách"><option value="">Chọn xã/phường</option>{communes?.map((commune) => <option key={commune.id} value={commune.id}>{commune.name}</option>)}</select> : account.commune_id ? communes?.find((commune) => commune.id === account.commune_id)?.name || `Xã/phường #${account.commune_id}` : '-'}</td>
              <td style={{ padding: '12px 8px', textAlign: 'right' }}>{editing ? <><button className="secondary-button" onClick={() => setEditingId(null)} disabled={saving}>Hủy</button><button className="primary-button" onClick={save} disabled={saving} style={{ marginLeft: 8 }}><FloppyDisk size={16} />{saving ? 'Đang lưu…' : 'Lưu'}</button></> : <button className="secondary-button" onClick={() => beginEdit(account)}>Chỉnh sửa</button>}</td>
            </tr>;
          })}
        </tbody></table>}
      </section>
    </>}
  </div>;
}
