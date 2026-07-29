import { ArrowClockwise, PhoneCall, SignIn, X } from '@phosphor-icons/react';
import type { DetailData, User } from './types';

interface Props {
  detail: DetailData;
  setDetailId: (id: string | null) => void;
  showToast: (message: string, icon?: string) => void;
  user: User | null;
  onLoginRequest: () => void;
  handleAction: (action: string, communeId: string | number, hamletId: number, hamletName: string) => void;
}

export default function CommuneDetailSlideOver({ detail, setDetailId, user, onLoginRequest, handleAction }: Props) {
  return (
    <>
      <button className="slideover-backdrop" aria-label="Đóng chi tiết" onClick={() => setDetailId(null)} />
      <aside className="slideover" aria-label={`Chi tiết ${detail.name}`}>
        <header className="slideover-header">
          <div><p className="eyebrow">Chi tiết địa bàn</p><h2 style={{ margin: 0 }}>{detail.name}</h2><p style={{ margin: '5px 0 0', color: 'var(--ink-muted)', fontSize: 12 }}>{detail.hazard}</p></div>
          <button className="icon-button" onClick={() => setDetailId(null)} aria-label="Đóng"><X size={18} /></button>
        </header>
        <div className="slideover-body">
          <section className="metrics-strip" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
            <div className="metric-block"><span className="metric-label">Dân số</span><strong className="mono">{detail.popStr}</strong></div>
            <div className="metric-block"><span className="metric-label">Đã nhận</span><strong className="mono">{detail.receivedStr}</strong></div>
            <div className="metric-block"><span className="metric-label">Chưa nhận</span><strong className="mono">{detail.notReceivedStr}</strong></div>
          </section>
          <div className="data-section" style={{ marginTop: 20 }}>
            <div className="data-section-header"><h3>Thôn, bản ({detail.hamletCount})</h3></div>
            {detail.hamlets.map((hamlet) => (
              <div className="bar-row" key={hamlet.name}>
                <div className="bar-meta"><div><strong>{hamlet.name}</strong><span className="metric-label">{hamlet.headman} · {hamlet.confirmLabel}</span></div><strong className="mono">{hamlet.rateStr}</strong></div>
                <div className="bar-track"><div className="bar-fill" style={{ width: hamlet.rateStr }} /></div>
                <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                  {user ? <><button className="secondary-button" onClick={() => handleAction('resend', detail.id, hamlet.id, hamlet.name)}><ArrowClockwise size={16} />Gửi lại</button><button className="secondary-button" onClick={() => handleAction('call', detail.id, hamlet.id, hamlet.name)}><PhoneCall size={16} />Gọi</button></> : <button className="secondary-button" onClick={onLoginRequest}><SignIn size={16} />Đăng nhập để thao tác</button>}
                </div>
              </div>
            ))}
          </div>
        </div>
      </aside>
    </>
  );
}
