import useSWR from 'swr';
import { CheckCircle, IdentificationCard, ShieldCheck } from '@phosphor-icons/react';
import type { User } from './types';
import { API_BASE_URL } from '@/lib/api';

const fetcher = async (url: string) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
  const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
  const res = await fetch(url, { headers });
  if (!res.ok) throw new Error('API Error');
  const json = await res.json();
  return json.data;
};

const roles = [
  ['Cán bộ tỉnh', 'Giám sát toàn tỉnh, quản lý văn bản và mở phiên điều phối.'],
  ['Cán bộ xã', 'Theo dõi địa bàn phụ trách, gửi lại cảnh báo và xác nhận thôn bản.'],
  ['Trưởng bản', 'Nhận nội dung cảnh báo và xác nhận việc phát thông tin tại địa bàn.'],
];

export default function RolesView({ user }: { user: User | null }) {
  // Chỉ hiển thị bảng user nếu người dùng là Cán bộ tỉnh
  const { data: users, error } = useSWR(user?.role === 'tinh' ? `${API_BASE_URL}/api/users` : null, fetcher);

  return (
    <div className="view-page">
      <div className="section-heading"><div><h2>Quyền truy cập</h2><p>Vai trò và danh sách cán bộ đang hoạt động trong hệ thống.</p></div></div>
      <section className="data-section">
        {roles.map(([name, description], index) => (
          <div className="bar-row" key={name}>
            <div className="bar-meta"><strong><IdentificationCard size={18} /> {name}</strong>{(index === 0 && user?.role === 'tinh') || (index === 1 && user?.role === 'xa') ? <span className="status-pill status-safe"><CheckCircle size={14} />Đang sử dụng</span> : null}</div>
            <p style={{ margin: '7px 0 0', color: 'var(--ink-muted)', fontSize: 12 }}>{description}</p>
          </div>
        ))}
      </section>

      {user?.role === 'tinh' && (
        <>
          <div className="section-heading" style={{ marginTop: 24 }}><div><h2>Danh sách tài khoản</h2><p>Quản lý các tài khoản hiện có trong hệ thống.</p></div></div>
          <section className="data-section" style={{ padding: '0 20px 20px' }}>
            {!users && !error && <p>Đang tải dữ liệu...</p>}
            {error && <p className="form-error">Lỗi khi tải danh sách người dùng. Vui lòng kiểm tra quyền truy cập.</p>}
            {users && (
              <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: 10 }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border)', textAlign: 'left', fontSize: 13, color: 'var(--ink-muted)' }}>
                    <th style={{ padding: '12px 8px' }}>Email / Tên đăng nhập</th>
                    <th style={{ padding: '12px 8px' }}>Tên hiển thị</th>
                    <th style={{ padding: '12px 8px' }}>Vai trò</th>
                    <th style={{ padding: '12px 8px' }}>ID Xã/Phường</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u: any) => (
                    <tr key={u.id} style={{ borderBottom: '1px solid var(--border)', fontSize: 14 }}>
                      <td style={{ padding: '12px 8px', fontWeight: 500 }}>{u.email}</td>
                      <td style={{ padding: '12px 8px' }}>{u.name}</td>
                      <td style={{ padding: '12px 8px' }}>
                        <span className={`status-pill ${u.role === 'tinh' ? 'status-safe' : 'status-watch'}`}>
                          {u.role === 'tinh' ? 'Cán bộ tỉnh' : 'Cán bộ xã'}
                        </span>
                      </td>
                      <td style={{ padding: '12px 8px' }}>{u.commune_id ? `Xã ${u.commune_id}` : '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>
        </>
      )}
    </div>
  );
}
