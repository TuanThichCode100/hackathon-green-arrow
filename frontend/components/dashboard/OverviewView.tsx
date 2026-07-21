import { Pulse, Broadcast, ChartBar, UsersThree } from '@phosphor-icons/react';
import type { DashboardData } from './types';

export default function OverviewView({ m }: { m: DashboardData }) {
  return (
    <div className="view-page">
      <div className="section-heading"><div><h2>Bức tranh vận hành</h2><p>Số liệu tổng hợp {m.timeText}, ưu tiên khả năng tiếp cận cảnh báo.</p></div></div>
      <section className="metrics-strip">
        {m.kpis.map((kpi, index) => (
          <div className="metric-block" key={kpi.label}>
            <span className="metric-label">{kpi.label}</span>
            <strong className="mono">{kpi.value}</strong>
            <span className="metric-label">{kpi.sub}</span>
          </div>
        ))}
      </section>
      <div className="data-grid">
        <section className="data-section">
          <div className="data-section-header"><h3><Broadcast size={17} /> Hiệu quả kênh phân phối</h3><p>Tin đã tiếp cận trên tổng số gửi.</p></div>
          {m.channels.length ? m.channels.map((channel) => (
            <div className="bar-row" key={channel.name}>
              <div className="bar-meta"><strong>{channel.name}</strong><span className="mono">{channel.deliveredStr}/{channel.sentStr} · {channel.rateStr}</span></div>
              <div className="bar-track"><div className="bar-fill" style={{ width: channel.pct }} /></div>
            </div>
          )) : <div className="empty-state"><ChartBar size={28} /><p>Chưa có dữ liệu phân phối trong khoảng thời gian này.</p></div>}
        </section>
        <section className="data-section">
          <div className="data-section-header"><h3><UsersThree size={17} /> Phân bố dân cư</h3><p>Dùng để lựa chọn ngôn ngữ và kênh phù hợp.</p></div>
          {m.ethnics.length ? m.ethnics.map((ethnic) => (
            <div className="bar-row" key={ethnic.name}>
              <div className="bar-meta"><strong>{ethnic.name}</strong><span className="mono">{ethnic.popStr} · {ethnic.pct}</span></div>
              <div className="bar-track"><div className="bar-fill" style={{ width: ethnic.pct }} /></div>
            </div>
          )) : <div className="empty-state"><UsersThree size={28} /><p>Chưa có dữ liệu dân tộc.</p></div>}
        </section>
      </div>
      <section className="data-section" style={{ marginTop: 22 }}>
        <div className="data-section-header"><h3><Pulse size={17} /> Hoạt động gần đây</h3></div>
        {m.activities.length ? m.activities.map((item, index) => <div className="bar-row" key={index}><div className="bar-meta"><span>{item.text}</span><span>{item.time}</span></div></div>) : <div className="empty-state"><Pulse size={28} /><p>Chưa ghi nhận hoạt động mới.</p></div>}
      </section>
    </div>
  );
}
