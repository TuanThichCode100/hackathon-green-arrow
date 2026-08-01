import { Radio } from '@phosphor-icons/react';
import type { DashboardData } from './types';

export default function ChannelsView({ m }: { m: DashboardData }) {
  return (
    <div className="view-page">
      <div className="section-heading">
        <div>
          <h2>Phân phối cảnh báo</h2>
          <p>Theo dõi người nhận theo trạng thái xác thực. Dữ liệu cũ không có danh sách người nhận được tách riêng.</p>
        </div>
      </div>
      <section className="metrics-strip">
        {m.channels.map((channel) => (
          <div className="metric-block" key={channel.name}>
            <span className="metric-label">{channel.icon} {channel.name}</span>
            <strong className="mono">{channel.receivedStr}</strong>
            <span className="metric-label">đã nhận · {channel.sentStr} đã gửi · {channel.pendingStr} chờ gửi · {channel.failedStr} thất bại</span>
          </div>
        ))}
      </section>
      <div className="table-wrap" style={{ marginTop: 22 }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Thời gian</th><th>Địa bàn</th><th>Kênh</th><th>Ngôn ngữ</th>
              <th>Mục tiêu</th><th>Chờ gửi</th><th>Đã gửi</th><th>Đã nhận</th><th>Thất bại</th><th>Trạng thái</th>
            </tr>
          </thead>
          <tbody>
            {m.logs.map((log, index) => (
              <tr key={index}>
                <td className="mono">{log.time}</td><td>{log.commune}</td><td>{log.channel}</td><td>{log.ethnic}</td>
                <td className="mono">{log.recipientsStr}</td>
                <td className="mono">{log.trackingAvailable ? log.pendingStr : '—'}</td>
                <td className="mono">{log.trackingAvailable ? log.sentStr : '—'}</td>
                <td className="mono">{log.trackingAvailable ? log.receivedStr : '—'}</td>
                <td className="mono">{log.trackingAvailable ? log.failedStr : '—'}</td>
                <td>{log.statusLabel}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {!m.logs.length && <div className="empty-state"><Radio size={28} /><p>Chưa có đợt phân phối.</p></div>}
      </div>
    </div>
  );
}
