import { PhoneCall, X } from '@phosphor-icons/react';
import { useEffect, useState } from 'react';
import { API_BASE_URL } from '@/lib/api';
import type { DashboardData, Log } from './types';

type DispatchDetail = {
  commune_name: string;
  total_residents: number;
  notified_residents: number;
  not_notified_residents: number;
  people: Array<{ id: number; name: string; phone: string; ethnic: string; preferred_alert_language: string; notified: boolean; progress: string; channels: Record<string, Array<{ language: string; status: string }>> }>;
};

const languageLabel = (language: string) => ({ vi: 'Tiếng Việt', hmn: 'Tiếng Mông', tai: 'Tiếng Thái', khmu: 'Tiếng Khơ Mú', dao: 'Tiếng Dao' }[language] || language);

function DispatchDetailModal({ log, onClose }: { log: Log; onClose: () => void }) {
  const [detail, setDetail] = useState<DispatchDetail | null>(null);
  const [error, setError] = useState('');
  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    fetch(`${API_BASE_URL}/api/notifications/dispatches/${log.decisionId}/${log.communeId}`, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
      .then(async (response) => { const body = await response.json(); if (!response.ok) throw new Error(body.detail || 'Không thể tải đợt phân phối.'); return body.data; })
      .then(setDetail).catch((reason) => setError(reason instanceof Error ? reason.message : 'Không thể tải đợt phân phối.'));
  }, [log.decisionId, log.communeId]);
  return <div className="review-backdrop" role="presentation"><section className="dispatch-detail" role="dialog" aria-modal="true" aria-labelledby="dispatch-detail-title">
    <header className="document-review-header"><div><p className="eyebrow">Đợt phân phối cảnh báo</p><h2 id="dispatch-detail-title">{detail?.commune_name || log.commune}</h2><p className="metric-label" style={{ margin: '5px 0 0' }}>Khởi tạo {log.time}, cập nhật {log.updatedAt}</p></div><button className="icon-button" onClick={onClose} aria-label="Đóng"><X size={18} /></button></header>
    {error ? <p className="form-error" style={{ padding: 24 }}>{error}</p> : !detail ? <div className="empty-state"><p>Đang tải danh sách người nhận…</p></div> : <div className="dispatch-detail-body"><section className="dispatch-summary"><div><span>Tổng dân cư</span><strong>{detail.total_residents}</strong></div><div><span>Đã được thông báo</span><strong>{detail.notified_residents}</strong></div><div><span>Chưa được thông báo</span><strong>{detail.not_notified_residents}</strong></div></section><p className="metric-label">Ưu tiên người chưa được thông báo. Một người được tính là đã được thông báo khi có ít nhất một kênh xác nhận đã gửi hoặc đã nhận.</p><div className="table-wrap"><table className="data-table"><thead><tr><th>Họ và tên</th><th>Số điện thoại</th><th>Dân tộc</th><th>Ngôn ngữ ưu tiên</th><th>Phân phối</th><th></th></tr></thead><tbody>{detail.people.map((person) => <tr key={person.id}><td><strong>{person.name}</strong><br /><span className="metric-label">{person.progress}</span></td><td className="mono">{person.phone}</td><td>{person.ethnic}</td><td>{languageLabel(person.preferred_alert_language)}</td><td>{Object.entries(person.channels).map(([channel, states]) => <div key={channel}>{channel}: {states.map((state) => state.status === 'waiting_content' ? 'chờ nội dung' : state.status).join(', ')}</div>)}</td><td><button className="secondary-button" disabled title="Chức năng sẽ được kích hoạt khi hệ thống kết nối tổng đài"><PhoneCall size={16} />Gọi thủ công</button></td></tr>)}</tbody></table></div></div>}
  </section></div>;
}

export default function ChannelsView({ m }: { m: DashboardData }) {
  const [selected, setSelected] = useState<Log | null>(null);
  return <div className="view-page"><div className="section-heading"><div><h2>Phân phối cảnh báo</h2><p>Theo dõi tiến độ gửi cảnh báo đến người dân tại các địa bàn được chọn.</p></div></div>
    <section className="metrics-strip dispatch-channel-strip">{m.channels.map((channel) => <div className="metric-block" key={channel.name}><strong>{channel.name === 'loa' ? 'Loa truyền thanh' : channel.name.toUpperCase()}</strong><span className="metric-label">{channel.pendingStr} chờ gửi · {channel.sentStr} đã gửi · {channel.receivedStr} đã nhận · {channel.failedStr} thất bại</span></div>)}</section>
    <div className="table-wrap" style={{ marginTop: 22 }}><table className="data-table"><thead><tr><th>Khởi tạo</th><th>Địa bàn</th><th>Kênh phân phối</th><th>Ngôn ngữ</th><th>Mục tiêu</th><th>Tiến độ</th><th>Cập nhật</th></tr></thead><tbody>{m.logs.map((log) => <tr key={`${log.decisionId}-${log.communeId}`} onClick={() => setSelected(log)}><td className="mono">{log.time}</td><td><strong>{log.commune}</strong></td><td>{log.channelSummary}</td><td>{log.ethnic}</td><td className="mono">{log.recipientsStr}</td><td>{log.progressStr}</td><td className="mono">{log.updatedAt}</td></tr>)}</tbody></table>{!m.logs.length && <div className="empty-state"><p>Chưa có đợt phân phối. Khi kích hoạt cảnh báo, hệ thống sẽ tạo danh sách người nhận theo địa bàn và ngôn ngữ ưu tiên.</p></div>}</div>
    {selected && <DispatchDetailModal log={selected} onClose={() => setSelected(null)} />}
  </div>;
}
