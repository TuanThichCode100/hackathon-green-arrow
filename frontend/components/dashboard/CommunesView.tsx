import { Buildings } from '@phosphor-icons/react';
import type { DashboardData } from './types';

export default function CommunesView({ m, setDetailId }: { m: DashboardData; setDetailId: (id: string | number) => void }) {
  return (
    <div className="view-page">
      <div className="section-heading"><div><h2>Địa bàn và mức tiếp cận</h2><p>Mở một địa bàn để xem thôn bản và hành động điều phối.</p></div></div>
      <div className="table-wrap">
        <table className="data-table">
          <thead><tr><th>Địa bàn</th><th>Dân số</th><th>Đã nhận</th><th>Chưa nhận</th><th>Tỷ lệ</th><th>Trạng thái</th></tr></thead>
          <tbody>
            {m.communes.map((commune) => (
              <tr key={commune.id} onClick={() => setDetailId(commune.id)}>
                <td><strong>{commune.name}</strong><br /><span className="metric-label">{commune.hazard}</span></td>
                <td className="mono">{commune.popStr}</td><td className="mono">{commune.receivedStr}</td><td className="mono">{commune.notReceivedStr}</td><td className="mono"><strong>{commune.rateStr}</strong></td>
                <td><span className={`status-pill ${commune.statusLabel.includes('Cảnh') ? 'status-alert' : commune.statusLabel.includes('Theo') ? 'status-watch' : 'status-safe'}`}>{commune.statusLabel}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
        {!m.communes.length && <div className="empty-state"><Buildings size={28} /><p>Chưa có địa bàn trong hệ thống.</p></div>}
      </div>
    </div>
  );
}
