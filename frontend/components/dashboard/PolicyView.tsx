import { BookOpenText, FileArrowUp, Files } from '@phosphor-icons/react';
import type { DashboardData, User } from './types';

export default function PolicyView({ m, user, setUploadOpen }: { m: DashboardData; user: User | null; setUploadOpen: (open: boolean) => void }) {
  return (
    <div className="view-page">
      <div className="section-heading">
        <div><h2>Văn bản chỉ đạo</h2><p>Ngữ cảnh hành chính được AI tham chiếu khi tạo dự thảo cảnh báo.</p></div>
        {user && <button className="primary-button" onClick={() => setUploadOpen(true)}><FileArrowUp size={17} />Thêm văn bản</button>}
      </div>
      <section className="metrics-strip">
        <div className="metric-block"><span className="metric-label">Còn hiệu lực</span><strong className="mono">{m.policyActive}</strong></div>
        <div className="metric-block"><span className="metric-label">Sắp hết hạn</span><strong className="mono">{m.policyExpiring}</strong></div>
        <div className="metric-block"><span className="metric-label">Hết hiệu lực</span><strong className="mono">{m.policyExpired}</strong></div>
      </section>
      <div className="table-wrap" style={{ marginTop: 22 }}>
        <table className="data-table">
          <thead><tr><th>Văn bản</th><th>Loại</th><th>Hiệu lực từ</th><th>Đến hết</th><th>Trạng thái</th></tr></thead>
          <tbody>{m.policies.map((policy) => <tr key={policy.code}><td><strong>{policy.title}</strong><br /><span className="metric-label">{policy.code}</span></td><td>{policy.type}</td><td>{policy.start}</td><td>{policy.end}</td><td><span className={`status-pill ${policy.status === 'active' ? 'status-safe' : 'status-watch'}`}>{policy.statusLabel}</span></td></tr>)}</tbody>
        </table>
        {!m.policies.length && <div className="empty-state"><Files size={28} /><p>Chưa có văn bản chỉ đạo.</p>{!user && <span>Đăng nhập để quản lý kho văn bản.</span>}</div>}
      </div>
    </div>
  );
}
