import { Broadcast, Radio } from '@phosphor-icons/react';
import type { DashboardData } from './types';

export default function ChannelsView({ m }: { m: DashboardData }) {
  return (
    <div className="view-page">
      <div className="section-heading"><div><h2>Phân phối cảnh báo</h2><p>Theo dõi khả năng tiếp cận và lỗi của từng kênh.</p></div></div>
      <section className="metrics-strip">
        {m.channels.map((channel) => <div className="metric-block" key={channel.name}><span className="metric-label">{channel.name}</span><strong className="mono">{channel.rateStr}</strong><span className="metric-label">{channel.failedStr} thất bại</span></div>)}
      </section>
      <div className="table-wrap" style={{ marginTop: 22 }}>
        <table className="data-table">
          <thead><tr><th>Thời gian</th><th>Địa bàn</th><th>Kênh</th><th>Ngôn ngữ</th><th>Người nhận</th><th>Trạng thái</th></tr></thead>
          <tbody>{m.logs.map((log, index) => <tr key={index}><td className="mono">{log.time}</td><td>{log.commune}</td><td>{log.channel}</td><td>{log.ethnic}</td><td className="mono">{log.recipientsStr}</td><td>{log.statusLabel}</td></tr>)}</tbody>
        </table>
        {!m.logs.length && <div className="empty-state"><Radio size={28} /><p>Chưa có bản ghi phân phối.</p></div>}
      </div>
    </div>
  );
}
