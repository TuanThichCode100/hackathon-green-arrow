import React from 'react';
import { s } from '@/lib/style';
import { DetailStat } from './Shared';
import { DetailData, User } from './types';

interface CommuneDetailSlideOverProps {
  detail: DetailData;
  setDetailId: (id: string | null) => void;
  showToast: (msg: string, icon?: string) => void;
  user: User | null;
  onLoginRequest: () => void;
  handleAction: (action: string, communeId: string | number, hamletName: string) => void;
}

export default function CommuneDetailSlideOver({ detail, setDetailId, showToast, user, onLoginRequest, handleAction }: CommuneDetailSlideOverProps) {
  return (
    <div style={s('position:fixed; inset:0; z-index:900;')}>
      <div onClick={() => setDetailId(null)} style={s('position:absolute; inset:0; background:rgba(15,30,42,.42);')}></div>
      <div style={s('position:absolute; top:0; right:0; height:100%; width:520px; max-width:92vw; background:#F5F8FB; box-shadow:-14px 0 40px rgba(15,30,42,.22); animation:gf-slidein .28s cubic-bezier(.22,.9,.3,1); display:flex; flex-direction:column;')}>
        <div style={s(`padding:20px 22px; color:#fff; display:flex; align-items:center; justify-content:space-between; background:${detail.headBg};`)}>
          <div style={s('display:flex; align-items:center; gap:13px;')}>
            <span style={s('font-size:30px;')}>{detail.icon}</span>
            <div>
              <div style={s('font-family:Georgia,serif; font-size:20px; font-weight:700;')}>{detail.name}</div>
              <div style={s('font-size:12px; opacity:.85; margin-top:2px;')}>{detail.hazard}</div>
            </div>
          </div>
          <button onClick={() => setDetailId(null)} style={s('width:34px; height:34px; border-radius:9px; border:none; background:rgba(255,255,255,.16); color:#fff; font-size:17px; cursor:pointer;')}>✕</button>
        </div>
        <div style={s('flex:1; overflow-y:auto; padding:18px 22px;')}>
          <div style={s('display:grid; grid-template-columns:repeat(3,1fr); gap:10px; margin-bottom:18px;')}>
            <DetailStat label="Tổng dân số" value={detail.popStr} />
            <DetailStat label="Đã nhận tin" value={detail.receivedStr} color="#1E9E6A" />
            <DetailStat label="Chưa nhận" value={detail.notReceivedStr} color={detail.notReceivedColor} />
          </div>
          <div style={s('height:10px; background:#E5EBF1; border-radius:6px; overflow:hidden; margin-bottom:6px;')}><div style={s(`height:100%; width:${detail.rateStr}; background:${detail.rateColor};`)}></div></div>
          <div style={s('font-size:11.5px; color:#7C8896; margin-bottom:18px;')}>Tỷ lệ tiếp cận toàn xã: <b style={{ color: detail.rateColor }}>{detail.rateStr}</b></div>

          {detail.hasLost && (
            <div style={s('background:#FDECEC; border:1px solid #F6C6C6; border-radius:12px; padding:14px 16px; margin-bottom:18px;')}>
              <div style={s('display:flex; align-items:center; gap:8px; margin-bottom:10px;')}><span style={s('font-size:16px;')}>📍</span><span style={s('font-size:13px; font-weight:700; color:#C42B2B;')}>Người dân chưa phản hồi — cần cứu hộ ({detail.lostCount})</span></div>
              {detail.lost.map((lp, i) => (
                <div key={i} style={s('display:flex; align-items:center; gap:11px; padding:8px 0; border-top:1px solid #F6C6C6;')}>
                  <span style={s('width:11px; height:11px; border-radius:50%; background:#E23D3D; animation:gf-pulse 1.6s infinite; flex:0 0 11px;')}></span>
                  <div style={s('flex:1;')}><div style={s('font-size:12.5px; font-weight:600; color:#0F1E2A;')}>{lp.name}</div><div style={s('font-size:10.5px; color:#B05656;')}>Tọa độ {lp.coord} · {lp.phone}</div></div>
                  <button onClick={() => showToast(`Điều phối lực lượng cứu hộ tới tọa độ ${lp.coord}`, '🚁')} style={s('font-size:11px; font-weight:600; color:#fff; background:#E23D3D; border:none; border-radius:7px; padding:6px 11px; cursor:pointer;')}>📞 Gọi</button>
                </div>
              ))}
            </div>
          )}

          <div style={s('font-size:13px; font-weight:700; color:#0F1E2A; margin-bottom:10px;')}>Thôn / Bản ({detail.hamletCount})</div>
          {detail.hamlets.map((h, i) => (
            <div key={i} style={s('background:#fff; border:1px solid #E1E7EE; border-radius:11px; padding:13px 15px; margin-bottom:9px;')}>
              <div style={s('display:flex; align-items:center; justify-content:space-between; margin-bottom:8px;')}>
                <div><div style={s('font-size:13px; font-weight:600; color:#0F1E2A;')}>{h.name}</div><div style={s('font-size:10.5px; color:#8A95A2; margin-top:2px;')}>Trưởng bản: {h.headman} · {h.confirmLabel}</div></div>
                <span style={s(`font-size:14px; font-weight:700; color:${h.rateColor}; font-variant-numeric:tabular-nums;`)}>{h.rateStr}</span>
              </div>
              <div style={s('height:7px; background:#EEF2F6; border-radius:5px; overflow:hidden; margin-bottom:11px;')}><div style={s(`height:100%; width:${h.rateStr}; background:${h.rateColor};`)}></div></div>
              {user ? (
                <div style={s('display:flex; gap:8px;')}>
                  <button onClick={() => handleAction('resend', detail.id, h.headman)} style={s('flex:1; font-size:11.5px; font-weight:600; color:#0F1E2A; background:#F0FAFE; border:1px solid #CBEBF9; border-radius:8px; padding:8px; cursor:pointer;')}>✉️ Gửi lại SMS</button>
                  <button onClick={() => handleAction('call', detail.id, h.headman)} style={s('flex:1; font-size:11.5px; font-weight:600; color:#B45309; background:#FFFBF0; border:1px solid #FDE6B5; border-radius:8px; padding:8px; cursor:pointer;')}>📞 Gọi khẩn cấp</button>
                </div>
              ) : (
                <div style={s('display:flex; gap:8px;')}>
                  <button onClick={onLoginRequest} style={s('flex:1; font-size:11.5px; font-weight:600; color:#5A6675; background:#F1F4F8; border:1px solid #E1E7EE; border-radius:8px; padding:8px; cursor:pointer;')}>Đăng nhập để thao tác</button>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
