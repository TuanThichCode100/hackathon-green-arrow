import { CheckCircle, IdentificationCard, ShieldCheck } from '@phosphor-icons/react';
import type { User } from './types';

const roles = [
  ['Cán bộ tỉnh', 'Giám sát toàn tỉnh, quản lý văn bản và mở phiên điều phối.'],
  ['Cán bộ xã', 'Theo dõi địa bàn phụ trách, gửi lại cảnh báo và xác nhận thôn bản.'],
  ['Trưởng bản', 'Nhận nội dung cảnh báo và xác nhận việc phát thông tin tại địa bàn.'],
];

export default function RolesView({ user }: { user: User | null }) {
  return (
    <div className="view-page">
      <div className="section-heading"><div><h2>Quyền truy cập</h2><p>Vai trò phải được xác thực ở cả giao diện và backend.</p></div></div>
      <section className="data-section">
        {roles.map(([name, description], index) => (
          <div className="bar-row" key={name}>
            <div className="bar-meta"><strong><IdentificationCard size={18} /> {name}</strong>{(index === 0 && user?.role === 'tinh') || (index === 1 && user?.role === 'xa') ? <span className="status-pill status-safe"><CheckCircle size={14} />Đang sử dụng</span> : null}</div>
            <p style={{ margin: '7px 0 0', color: 'var(--ink-muted)', fontSize: 12 }}>{description}</p>
          </div>
        ))}
      </section>
    </div>
  );
}
