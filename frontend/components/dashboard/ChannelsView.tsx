import { PhoneCall, X } from '@phosphor-icons/react';
import { useEffect, useState } from 'react';
import { API_BASE_URL } from '@/lib/api';
import type { DashboardData, Log } from './types';

type DispatchDetail = {
  commune_name: string;
  total_residents: number;
  notified_residents: number;
  not_notified_residents: number;
  channels: Record<string, string[]>;
  people: Array<{ id: number; name: string; phone: string; ethnic: string; primary_language: string; notified: boolean; progress: string; channels: Record<string, Array<{ language: string; status: string }>> }>;
};

type ResidentSummary = { id: number; name: string; phone: string; ethnic: string; primary_language: string };

const languageLabel = (language: string) => ({ vi: 'Tiếng Kinh', hmn: 'Tiếng Mông', tai: 'Tiếng Thái', khmu: 'Tiếng Khơ Mú', dao: 'Tiếng Dao', tay: 'Tiếng Tày', muong: 'Tiếng Mường' }[language] || language);
const channelLabel = (channel: string) => ({ zalo: 'Zalo', sms: 'SMS', loa: 'Loa truyền thanh' }[channel] || channel);
const deliveryLabel = (status: string) => ({ awaiting_commune_confirmation: 'Chờ xác nhận', pending: 'Sẵn sàng gửi', sent: 'Đã gửi', received: 'Đã nhận', failed: 'Gửi thất bại', waiting_content: 'Chờ nội dung' }[status] || status);

function DispatchDetailContent({ log, canOperate = false, summaryOnly = false }: { log: Log; canOperate?: boolean; summaryOnly?: boolean }) {
  const [detail, setDetail] = useState<DispatchDetail | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    setDetail(null); setError('');
    fetch(`${API_BASE_URL}/api/notifications/dispatches/${log.decisionId}/${log.communeId}`, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
      .then(async (response) => { const body = await response.json(); if (!response.ok) throw new Error(body.detail || 'Không thể tải đợt phân phối.'); return body.data; })
      .then(setDetail).catch((reason) => setError(reason instanceof Error ? reason.message : 'Không thể tải đợt phân phối.'));
  }, [log.decisionId, log.communeId]);

  if (error) return <p className="form-error" style={{ padding: 24 }}>{error}</p>;
  if (!detail) return <div className="empty-state"><p>Đang tải danh sách người nhận…</p></div>;
  if (summaryOnly) return <div className="dispatch-detail-body"><section className="dispatch-summary"><div><span>Tổng dân cư</span><strong>{detail.total_residents}</strong></div><div><span>Đã được thông báo</span><strong>{detail.notified_residents}</strong></div><div><span>Chưa được thông báo</span><strong>{detail.not_notified_residents}</strong></div></section><p className="metric-label">Cán bộ tỉnh theo dõi tiến độ tổng hợp; cán bộ xã thực hiện liên lạc và phân phối tại địa bàn.</p></div>;
  const activate = async () => {
    const token = localStorage.getItem('auth_token');
    const response = await fetch(`${API_BASE_URL}/api/notifications/dispatches/${log.decisionId}/${log.communeId}/activate`, { method: 'POST', headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) }, body: JSON.stringify({ channels: Object.keys(detail.channels) }) });
    if (!response.ok) { setError('Không thể kích hoạt các kênh đã chọn.'); return; }
    setDetail((await response.json()).data);
  };
  return <div className="dispatch-detail-body"><section className="dispatch-summary"><div><span>Tổng dân cư</span><strong>{detail.total_residents}</strong></div><div><span>Đã được thông báo</span><strong>{detail.notified_residents}</strong></div><div><span>Chưa được thông báo</span><strong>{detail.not_notified_residents}</strong></div></section>{canOperate && <button className="primary-button" onClick={activate}>Bắt đầu phân phối qua các kênh sẵn sàng</button>}<p className="metric-label">Ưu tiên người chưa được thông báo. Một người được tính là đã được thông báo khi có ít nhất một kênh xác nhận đã gửi hoặc đã nhận.</p><div className="table-wrap"><table className="data-table"><thead><tr><th>Họ và tên</th><th>Số điện thoại</th><th>Dân tộc</th><th>Ngôn ngữ sử dụng chính</th><th>Phân phối</th>{canOperate && <th></th>}</tr></thead><tbody>{detail.people.map((person) => <tr key={person.id}><td><strong>{person.name}</strong><br /><span className="metric-label">{person.progress}</span></td><td className="mono">{person.phone}</td><td>{person.ethnic}</td><td>{languageLabel(person.primary_language)}</td><td><div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>{Object.entries(person.channels).map(([channel, states]) => <span key={channel} className="status-pill status-watch">{channelLabel(channel)} · {states.map((state) => deliveryLabel(state.status)).join(', ')}</span>)}</div></td>{canOperate && <td><a className="secondary-button" href={`tel:${person.phone.replace(/\s/g, '')}`}><PhoneCall size={16} />Gọi khẩn cấp</a></td>}</tr>)}</tbody></table></div></div>;
}

function DispatchDetailModal({ log, onClose }: { log: Log; onClose: () => void }) {
  return <div className="review-backdrop" role="presentation"><section className="dispatch-detail" role="dialog" aria-modal="true" aria-labelledby="dispatch-detail-title"><header className="document-review-header"><div><p className="eyebrow">Đợt phân phối cảnh báo</p><h2 id="dispatch-detail-title">{log.commune}</h2><p className="metric-label" style={{ margin: '5px 0 0' }}>Khởi tạo {log.time}, tiến độ ghi nhận gần nhất {log.updatedAt}</p></div><button className="icon-button" onClick={onClose} aria-label="Đóng"><X size={18} /></button></header><DispatchDetailContent log={log} /></section></div>;
}

function LocalResidentRegistry({ communeId }: { communeId: number }) {
  const [people, setPeople] = useState<ResidentSummary[] | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    fetch(`${API_BASE_URL}/api/residents?commune_id=${communeId}&limit=50`, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
      .then(async (response) => { const body = await response.json(); if (!response.ok) throw new Error(body.detail || 'Không thể tải sổ dân cư.'); return body.data.items as ResidentSummary[]; })
      .then(setPeople).catch((reason) => setError(reason instanceof Error ? reason.message : 'Không thể tải sổ dân cư.'));
  }, [communeId]);

  return <section className="dispatch-detail" style={{ width: '100%', marginTop: 22 }}><header className="document-review-header"><div><p className="eyebrow">Sổ dân cư địa bàn</p><h2>Chưa có đợt phân phối</h2><p className="metric-label" style={{ margin: '5px 0 0' }}>Danh sách sẵn sàng để lập đợt gửi khi có cảnh báo.</p></div></header>{error ? <p className="form-error" style={{ padding: 24 }}>{error}</p> : people === null ? <div className="empty-state"><p>Đang tải dữ liệu dân cư…</p></div> : <div className="dispatch-detail-body"><div className="table-wrap"><table className="data-table"><thead><tr><th>Họ và tên</th><th>Số điện thoại</th><th>Dân tộc</th><th>Ngôn ngữ sử dụng chính</th></tr></thead><tbody>{people.map((person) => <tr key={person.id}><td><strong>{person.name}</strong></td><td className="mono">{person.phone}</td><td>{person.ethnic}</td><td>{languageLabel(person.primary_language)}</td></tr>)}</tbody></table>{!people.length && <div className="empty-state"><p>Chưa có dân cư tại xã/phường phụ trách.</p></div>}</div></div>}</section>;
}

export default function ChannelsView({ m, isProv, assignedCommuneId }: { m: DashboardData; isProv?: boolean; assignedCommuneId?: number | string }) {
  const [selected, setSelected] = useState<Log | null>(null);
  const localLogs = assignedCommuneId ? m.logs.filter((log) => log.communeId === Number(assignedCommuneId)) : m.logs;
  const currentLocalDispatch = localLogs[0];
  const latestLogByCommune = new Map<number, Log>();
  m.logs.forEach((log) => { if (!latestLogByCommune.has(log.communeId)) latestLogByCommune.set(log.communeId, log); });

  return <div className="view-page"><div className="section-heading"><div><h2>Phân phối cảnh báo</h2><p>{isProv ? 'Theo dõi toàn bộ các đợt gửi theo từng địa bàn; bấm một dòng để xem chi tiết.' : 'Chi tiết đợt phân phối mới nhất tại địa bàn phụ trách.'}</p></div></div>
    <section className="metrics-strip dispatch-channel-strip">{m.channels.map((channel) => <div className="metric-block" key={channel.name}><strong>{channel.name === 'loa' ? 'Loa truyền thanh' : channel.name.toUpperCase()}</strong><span className="metric-label">{channel.pendingStr} chờ gửi · {channel.sentStr} đã gửi · {channel.receivedStr} đã nhận · {channel.failedStr} thất bại</span></div>)}</section>
    {isProv ? <><div className="table-wrap" style={{ marginTop: 22 }}><table className="data-table"><thead><tr><th>Khởi tạo</th><th>Địa bàn</th><th>Kênh phân phối</th><th>Ngôn ngữ</th><th>Mục tiêu</th><th>Tiến độ</th><th>Tiến độ ghi nhận gần nhất</th></tr></thead><tbody>{m.communes.map((commune) => { const log = latestLogByCommune.get(Number(commune.id)); return <tr key={commune.id} onClick={() => log && setSelected(log)} style={log ? { cursor: 'pointer' } : undefined}><td className="mono">{log?.time || '—'}</td><td><strong>{commune.name}</strong></td><td>{log?.channelSummary || 'Chưa có đợt gửi'}</td><td>{log?.ethnic || '—'}</td><td className="mono">{log?.recipientsStr || '—'}</td><td>{log?.progressStr || 'Chưa có dữ liệu phân phối'}</td><td className="mono">{log?.updatedAt || '—'}</td></tr>; })}</tbody></table></div>{selected && <DispatchDetailModal log={selected} onClose={() => setSelected(null)} />}</> : currentLocalDispatch ? <section className="dispatch-detail" style={{ width: '100%', marginTop: 22 }}><header className="document-review-header"><div><p className="eyebrow">Đợt phân phối cảnh báo</p><h2>{currentLocalDispatch.commune}</h2><p className="metric-label" style={{ margin: '5px 0 0' }}>Khởi tạo {currentLocalDispatch.time}, tiến độ ghi nhận gần nhất {currentLocalDispatch.updatedAt}</p></div></header><DispatchDetailContent log={currentLocalDispatch} canOperate /></section> : assignedCommuneId ? <LocalResidentRegistry communeId={Number(assignedCommuneId)} /> : <div className="empty-state" style={{ marginTop: 22 }}><p>Chưa xác định xã/phường phụ trách.</p></div>}
  </div>;
}
