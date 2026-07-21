import { Bell, CloudCheck } from '@phosphor-icons/react';

const titles: Record<string, string> = {
  map: 'Bản đồ rủi ro',
  overview: 'Tổng quan vận hành',
  communes: 'Địa bàn và mức tiếp cận',
  policy: 'Văn bản chỉ đạo',
  channels: 'Phân phối cảnh báo',
  roles: 'Quyền truy cập',
  database: 'Dữ liệu dân cư',
};

const ranges = [
  ['today', 'Hôm nay'], ['24h', '24 giờ'], ['7d', '7 ngày'], ['30d', '30 ngày'],
];

export default function Header({ view, timeRange, setTimeRange, clock }: { view: string; timeRange: string; setTimeRange: (value: string) => void; clock: string }) {
  return (
    <header className="topbar">
      <div className="page-heading"><p className="eyebrow">Tỉnh Điện Biên</p><h1>{titles[view]}</h1></div>
      <div className="topbar-spacer" />
      <div className="time-control" aria-label="Khoảng thời gian">
        {ranges.map(([key, label]) => <button key={key} className={timeRange === key ? 'active' : ''} onClick={() => setTimeRange(key)}>{label}</button>)}
      </div>
      <div className="live-status"><span className="live-dot" /><CloudCheck size={16} />Đồng bộ <span className="mono">{clock}</span></div>
      <button className="icon-button" aria-label="Thông báo"><Bell size={18} /></button>
    </header>
  );
}
