'use client';

import { useState, useEffect, useRef } from 'react';
import 'leaflet/dist/leaflet.css';
import { s } from '@/lib/style';
import {
  COMMUNES, NAV, TIME_META, VIEW_TITLES, statusOf, buildModel, buildDetail,
} from '@/lib/data';

export default function Dashboard() {
  const [view, setView] = useState('map');
  const [role, setRole] = useState('province');
  const [timeRange, setTimeRange] = useState('today');
  const [emergency, setEmergency] = useState(false);
  const [detailId, setDetailId] = useState(null);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [toast, setToast] = useState(null);
  const [toastIcon, setToastIcon] = useState('✅');
  const [clock, setClock] = useState('');

  const toastTimer = useRef(null);
  const showToast = (msg, icon = '✅') => {
    setToast(msg); setToastIcon(icon);
    clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToast(null), 3200);
  };

  const handleToggleEmergency = async () => {
    const nextState = !emergency;
    setEmergency(nextState);
    if (nextState) {
      showToast('Đang phân tích rủi ro & gọi AI Agent...', '⏳');
      try {
        const res = await fetch('http://localhost:8000/api/trigger-alert', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            forecast: [],
            disasters: [
              { title: "Lũ quét nguy hiểm", probability: 95 },
              { title: "Sạt lở đất", probability: 85 }
            ]
          })
        });
        const data = await res.json();
        if (data.status === 'success') {
          showToast('AI Agent đã ra quyết định hành động!', '🤖');
          console.log("AI Decision:", data.ai_decision);
          setTimeout(() => alert("Quyết định từ AI Agent:\n\n" + data.ai_decision), 1000);
        } else {
          showToast('Lỗi khi gọi AI Agent', '❌');
        }
      } catch (err) {
        showToast('Không kết nối được tới Backend', '❌');
        console.error(err);
      }
    } else {
      showToast('Đã tắt chế độ khẩn cấp', '✅');
    }
  };

  // realtime clock
  useEffect(() => {
    const p = (n) => String(n).padStart(2, '0');
    const tick = () => { const d = new Date(); setClock(`${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`); };
    tick();
    const t = setInterval(tick, 1000);
    return () => clearInterval(t);
  }, []);

  // Leaflet map — re-init when entering map view or when emergency changes
  useEffect(() => {
    if (view !== 'map') return;
    let map = null;
    let cancelled = false;
    (async () => {
      const L = (await import('leaflet')).default;
      if (cancelled) return;
      const el = document.getElementById('gf-map');
      if (!el || el._leaflet_id) return;
      map = L.map(el, { zoomControl: true, attributionControl: false }).setView([21.55, 103.05], 9);
      L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', { maxZoom: 18 }).addTo(map);
      const layer = L.layerGroup().addTo(map);
      COMMUNES.forEach((c) => {
        const st = statusOf(c, emergency);
        const color = st === 'alert' ? '#E23D3D' : st === 'watch' ? '#E8A93B' : '#1E9E6A';
        const rate = emergency ? c.recvAlert : c.recvNormal;
        // ranh giới xã — viền đỏ nhạt phân biệt từng xã
        L.circle([c.lat, c.lng], {
          radius: c.pop > 30000 ? 9000 : c.pop > 12000 ? 7000 : 5500,
          color: '#E23D3D', weight: 1.5, opacity: 0.55, dashArray: '5 5', fillColor: '#E23D3D', fillOpacity: 0.05,
        }).addTo(layer);
        const m = L.circleMarker([c.lat, c.lng], {
          radius: c.pop > 30000 ? 15 : c.pop > 12000 ? 12 : 9,
          fillColor: color, color: '#fff', weight: 2.5, fillOpacity: 0.9,
        }).addTo(layer);
        m.bindTooltip(`<b>${c.name}</b><br>${c.district} · ${Math.round(rate * 100)}% đã nhận`, { direction: 'top', offset: [0, -6] });
        m.on('click', () => setDetailId(c.id));
        if (emergency && st === 'alert' && c.lost) {
          c.lost.forEach((lp) => {
            L.marker([lp.lat, lp.lng], { icon: L.divIcon({ className: '', html: '<div class="gf-lost-pin"></div>', iconSize: [16, 16], iconAnchor: [8, 8] }) })
              .addTo(layer)
              .bindTooltip(`📍 ${lp.name}<br>Chưa phản hồi`, { direction: 'top', offset: [0, -8] });
          });
        }
      });
      setTimeout(() => { if (map) map.invalidateSize(); }, 200);
    })();
    return () => { cancelled = true; if (map) map.remove(); };
  }, [view, emergency]);

  const m = buildModel(emergency, timeRange);
  const detail = detailId ? buildDetail(detailId, emergency) : null;
  const isProv = role === 'province';

  // ---- style helpers (ported) ----
  const navBtn = (active) => `width:100%; display:flex; align-items:center; gap:11px; padding:11px 13px; border:none; border-radius:10px; cursor:pointer; font-family:inherit; font-size:13.5px; font-weight:${active ? '600' : '500'}; color:${active ? '#fff' : 'rgba(255,255,255,.62)'}; background:${active ? 'rgba(37,173,227,.16)' : 'transparent'}; margin-bottom:3px;`;
  const roleTab = (active) => `flex:1; padding:8px 4px; border:none; border-radius:7px; cursor:pointer; font-family:inherit; font-size:12px; font-weight:600; color:${active ? '#0F1E2A' : 'rgba(255,255,255,.6)'}; background:${active ? '#25ADE3' : 'transparent'};`;
  const timeSeg = (active) => `border:none; cursor:pointer; font-family:inherit; font-size:11.5px; font-weight:600; padding:6px 11px; border-radius:6px; color:${active ? '#fff' : '#5A6675'}; background:${active ? '#0F1E2A' : 'transparent'};`;
  const roleRowStyle = (active) => `display:flex; align-items:flex-start; gap:14px; padding:15px; border-radius:12px; margin-bottom:10px; border:1px solid ${active ? '#25ADE3' : '#EEF2F6'}; background:${active ? '#F5FCFF' : '#FBFCFD'};`;
  const badgePill = 'font-size:10px; font-weight:700; background:#E23D3D; color:#fff; padding:1px 7px; border-radius:20px;';

  const roleRows = [
    { name: 'Cán bộ Tỉnh / Huyện', icon: '🏛️', bg: '#EAF7FD', current: isProv, perms: 'Giám sát toàn cảnh bản đồ tỉnh · Upload văn bản chỉ đạo (RAG) · Kích hoạt cảnh báo · Xem mọi xã.' },
    { name: 'Cán bộ Xã', icon: '🏘️', bg: '#E7F6EF', current: !isProv, perms: 'Xem chi tiết xã phụ trách · Theo dõi trạng thái trưởng bản · Gửi lại SMS / Gọi khẩn cấp.' },
    { name: 'Trưởng bản (chỉ nhận)', icon: '📢', bg: '#FFF6E6', current: false, perms: 'Nhận SMS/Zalo/Gọi + file Audio MP3 để phát trên loa phát thanh của bản.' },
  ];

  return (
    <div style={s('display:flex; height:100vh; width:100%; overflow:hidden; background:#EEF2F6;')}>
      {/* ============ SIDEBAR ============ */}
      <aside style={s('width:262px; flex:0 0 262px; background:#0F1E2A; color:#fff; display:flex; flex-direction:column; height:100%;')}>
        <div style={s('padding:22px 22px 16px; display:flex; align-items:center; gap:11px; border-bottom:1px solid rgba(255,255,255,.08);')}>
          <svg width="34" height="34" viewBox="0 0 32 32" style={{ flex: '0 0 34px' }}>
            <defs><linearGradient id="ga-grad" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor="#3FD98A" /><stop offset="1" stopColor="#159A5C" /></linearGradient></defs>
            <rect width="32" height="32" rx="9" fill="url(#ga-grad)" />
            <path d="M16 6.5 L24.5 17 H19.4 V25.5 H12.6 V17 H7.5 Z" fill="#fff" />
          </svg>
          <div>
            <div style={s('font-size:14px; font-weight:800; letter-spacing:.01em; line-height:1;')}>Green<span style={{ color: '#3FD98A' }}>Forecast</span></div>
            <div style={s('font-size:9.5px; color:#8FE3B6; font-weight:600; margin-top:3px; letter-spacing:.02em;')}>Cảnh báo thời tiết</div>
          </div>
        </div>

        {/* role switcher */}
        <div style={s('padding:16px 18px 6px;')}>
          <div style={s('font-size:10px; text-transform:uppercase; letter-spacing:.09em; color:rgba(255,255,255,.42); margin-bottom:8px;')}>Vai trò đăng nhập</div>
          <div style={s('display:flex; background:rgba(255,255,255,.06); border-radius:9px; padding:3px;')}>
            <button onClick={() => setRole('province')} style={s(roleTab(isProv))}>Cán bộ Tỉnh</button>
            <button onClick={() => setRole('commune')} style={s(roleTab(!isProv))}>Cán bộ Xã</button>
          </div>
        </div>

        <nav style={s('padding:14px 12px; flex:1; overflow-y:auto;')}>
          {NAV.map((item) => {
            const active = view === item.key;
            const badge = item.key === 'map' && emergency ? String(m.alertCount) : null;
            return (
              <button key={item.key} onClick={() => { setView(item.key); setDetailId(null); }} style={s(navBtn(active))}>
                <span style={s('font-size:17px; width:22px; text-align:center; flex:0 0 22px;')}>{item.icon}</span>
                <span style={s('flex:1; text-align:left;')}>{item.label}</span>
                {badge && <span style={s(badgePill)}>{badge}</span>}
              </button>
            );
          })}
        </nav>

        {/* emergency toggle */}
        <div style={s('padding:14px 16px; border-top:1px solid rgba(255,255,255,.08);')}>
          <div style={s(`border-radius:11px; padding:12px 13px; background:${emergency ? 'rgba(226,61,61,.14)' : 'rgba(255,255,255,.05)'}; border:1px solid ${emergency ? 'rgba(226,61,61,.4)' : 'rgba(255,255,255,.08)'};`)}>
            <div style={s('display:flex; align-items:center; justify-content:space-between; gap:10px;')}>
              <div>
                <div style={s('font-size:12.5px; font-weight:700;')}>{emergency ? '🚨 Chế độ Khẩn cấp' : 'Chế độ Bình thường'}</div>
                <div style={s('font-size:10px; color:rgba(255,255,255,.6); margin-top:2px;')}>{emergency ? 'Cảnh báo đang phát đi' : 'Giám sát thường trực'}</div>
              </div>
              <button onClick={handleToggleEmergency} style={s(`width:46px; height:26px; border-radius:20px; border:none; cursor:pointer; position:relative; transition:.2s; background:${emergency ? '#E23D3D' : 'rgba(255,255,255,.25)'};`)}>
                <span style={s(`position:absolute; top:3px; left:${emergency ? '23px' : '3px'}; width:20px; height:20px; border-radius:50%; background:#fff; transition:.2s;`)}></span>
              </button>
            </div>
          </div>
        </div>

        <div style={s('padding:13px 18px; display:flex; align-items:center; gap:11px; border-top:1px solid rgba(255,255,255,.08);')}>
          <div style={s('width:34px; height:34px; border-radius:50%; background:#25ADE3; color:#0F1E2A; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:13px;')}>{isProv ? 'NT' : 'LV'}</div>
          <div style={s('flex:1; min-width:0;')}>
            <div style={s('font-size:12.5px; font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;')}>{isProv ? 'Nguyễn Tiến Dũng' : 'Lò Văn Panh'}</div>
            <div style={s('font-size:10px; color:rgba(255,255,255,.5); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;')}>{isProv ? 'Cán bộ Tỉnh · Toàn quyền' : 'Cán bộ Xã · Mường Nhé'}</div>
          </div>
        </div>
      </aside>

      {/* ============ MAIN ============ */}
      <div style={s('flex:1; display:flex; flex-direction:column; height:100%; min-width:0;')}>
        {/* topbar */}
        <header style={s('background:#fff; border-bottom:1px solid #E1E7EE; padding:0 26px; height:64px; flex:0 0 64px; display:flex; align-items:center; gap:20px;')}>
          <div style={s('min-width:0;')}>
            <div style={s('font-size:11px; color:#7C8896; letter-spacing:.02em;')}>GreenForecast · Tỉnh Điện Biên</div>
            <div style={s('font-family:Georgia,serif; font-size:19px; font-weight:700; color:#0F1E2A; line-height:1.1; margin-top:1px;')}>{VIEW_TITLES[view]}</div>
          </div>
          <div style={s('flex:1;')}></div>
          <div style={s('display:flex; align-items:center; gap:7px; background:#F7F9FB; border:1px solid #E1E7EE; border-radius:9px; padding:4px 6px 4px 11px;')}>
            <span style={s('font-size:13px; opacity:.6;')}>🗓️</span>
            <div style={s('display:flex; background:#fff; border-radius:7px; padding:2px;')}>
              {Object.keys(TIME_META).map((k) => (
                <button key={k} onClick={() => setTimeRange(k)} style={s(timeSeg(timeRange === k))}>{TIME_META[k].label}</button>
              ))}
            </div>
          </div>
          <div style={s('position:relative;')}>
            <input placeholder="Tìm xã, thôn bản…" style={s('width:180px; height:38px; border:1px solid #E1E7EE; border-radius:9px; padding:0 14px 0 36px; font-family:inherit; font-size:13px; background:#F7F9FB; outline:none; color:#0F1E2A;')} />
            <span style={s('position:absolute; left:12px; top:50%; transform:translateY(-50%); font-size:14px; opacity:.5;')}>🔍</span>
          </div>
          <div style={s('display:flex; align-items:center; gap:6px; padding:7px 13px; background:#F0FAFE; border:1px solid #CBEBF9; border-radius:9px;')}>
            <span style={s('width:8px; height:8px; border-radius:50%; background:#1E9E6A; display:inline-block; animation:gf-blink 2s infinite;')}></span>
            <span style={s('font-size:11.5px; color:#0F1E2A; font-weight:600;')}>Realtime</span>
            <span style={s('font-size:11.5px; color:#7C8896;')}>·</span>
            <span style={s('font-size:12.5px; color:#0F1E2A; font-weight:600; font-variant-numeric:tabular-nums;')}>{clock}</span>
          </div>
          <button style={s('width:40px; height:40px; border-radius:9px; border:1px solid #E1E7EE; background:#fff; font-size:16px; cursor:pointer; position:relative;')}>🔔<span style={s('position:absolute; top:7px; right:7px; width:7px; height:7px; border-radius:50%; background:#E23D3D;')}></span></button>
        </header>

        {/* emergency banner */}
        {emergency && (
          <div style={s('background:linear-gradient(90deg,#C42B2B,#E23D3D); color:#fff; padding:11px 26px; display:flex; align-items:center; gap:14px;')}>
            <span style={s('font-size:19px; animation:gf-blink 1.1s infinite;')}>⚠️</span>
            <div style={s('flex:1;')}>
              <span style={s('font-weight:700; font-size:13.5px;')}>TÌNH TRẠNG KHẨN CẤP ĐANG KÍCH HOẠT</span>
              <span style={s('font-size:12.5px; opacity:.95; margin-left:10px;')}>{m.alertHeadline}</span>
            </div>
            <span style={s('font-size:12px; background:rgba(255,255,255,.18); padding:5px 11px; border-radius:20px; font-weight:600;')}>Độ trễ hệ thống: 38 giây</span>
          </div>
        )}

        {/* scroll region */}
        <main style={s('flex:1; overflow-y:auto; overflow-x:hidden;')}>
          {/* ===== VIEW: MAP ===== */}
          {view === 'map' && (
            <div style={s('padding:22px 26px 30px;')}>
              <div style={s('display:grid; grid-template-columns:repeat(5,1fr); gap:14px; margin-bottom:18px;')}>
                {m.kpis.map((k, i) => <KpiCard key={i} k={k} />)}
              </div>
              <div style={s('display:grid; gap:16px;')}>
                <div style={s('background:#fff; border:1px solid #E1E7EE; border-radius:14px; overflow:hidden; display:flex; flex-direction:column;')}>
                  <div style={s('padding:14px 18px; display:flex; align-items:center; justify-content:space-between; border-bottom:1px solid #EEF2F6;')}>
                    <div>
                      <div style={s('font-family:Georgia,serif; font-weight:700; font-size:15px;')}>Bản đồ giám sát — Tỉnh Điện Biên</div>
                      <div style={s('font-size:11px; color:#7C8896; margin-top:2px;')}>Zoom Tỉnh → Huyện → Xã → Bản · Chấm đỏ = người dân chưa phản hồi</div>
                    </div>
                    <div style={s('display:flex; gap:6px;')}>
                      <Legend color="#1E9E6A" label="An toàn" />
                      <Legend color="#E8A93B" label="Theo dõi" ml />
                      <Legend color="#E23D3D" label="Cảnh báo" ml />
                    </div>
                  </div>
                  <div id="gf-map" style={s('flex:1; min-height:660px; width:100%; background:#dfe7ee;')}></div>
                </div>

                <div style={s('background:#fff; border:1px solid #E1E7EE; border-radius:14px; display:flex; flex-direction:column; overflow:hidden;')}>
                  <div style={s('padding:14px 18px; border-bottom:1px solid #EEF2F6; display:flex; align-items:center; justify-content:space-between;')}>
                    <div style={s('font-family:Georgia,serif; font-weight:700; font-size:15px;')}>Trạng thái theo Xã</div>
                    <span style={s('font-size:11px; color:#7C8896;')}>{m.communes.length} xã</span>
                  </div>
                  <div style={s('display:grid; grid-template-columns:repeat(3,1fr); gap:4px; padding:10px;')}>
                    {m.communes.map((c) => (
                      <button key={c.id} className="gf-commune-card" onClick={() => setDetailId(c.id)} style={s('width:100%; text-align:left; display:flex; align-items:center; gap:12px; padding:11px 12px; border:1px solid #EEF2F6; background:#fff; border-radius:10px; cursor:pointer;')}>
                        <span style={s('font-size:20px; width:30px; text-align:center;')}>{c.icon}</span>
                        <div style={s('flex:1; min-width:0;')}>
                          <div style={s('font-size:13px; font-weight:600; color:#0F1E2A;')}>{c.name}</div>
                          <div style={s('font-size:10.5px; color:#8A95A2;')}>{c.district} · {c.popStr} dân</div>
                        </div>
                        <div style={s('text-align:right;')}>
                          <div style={s(`font-size:13px; font-weight:700; color:${c.rateColor}; font-variant-numeric:tabular-nums;`)}>{c.rateStr}</div>
                          <span style={s(c.pillStyle)}>{c.statusLabel}</span>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ===== VIEW: OVERVIEW ===== */}
          {view === 'overview' && (
            <div style={s('padding:22px 26px 34px;')}>
              <div style={s('display:grid; grid-template-columns:repeat(5,1fr); gap:14px; margin-bottom:18px;')}>
                {m.kpis.map((k, i) => <KpiCard key={i} k={k} />)}
              </div>
              <div style={s('display:grid; grid-template-columns:1.4fr 1fr; gap:16px; margin-bottom:16px;')}>
                <div style={s('background:#fff; border:1px solid #E1E7EE; border-radius:14px; padding:18px 20px;')}>
                  <div style={s('font-family:Georgia,serif; font-weight:700; font-size:15px; margin-bottom:4px;')}>Tỷ lệ phân phối theo kênh</div>
                  <div style={s('font-size:11px; color:#7C8896; margin-bottom:18px;')}>Số tin đã tiếp cận / tổng số gửi đi · <b style={{ color: '#25ADE3' }}>{m.timeText}</b></div>
                  {m.channels.map((ch, i) => (
                    <div key={i} style={s('margin-bottom:15px;')}>
                      <div style={s('display:flex; justify-content:space-between; align-items:baseline; margin-bottom:6px;')}>
                        <span style={s('font-size:13px; font-weight:600; display:flex; align-items:center; gap:8px;')}><span style={s('font-size:15px;')}>{ch.icon}</span>{ch.name}</span>
                        <span style={s('font-size:12px; color:#5A6675;')}><b style={{ color: '#0F1E2A' }}>{ch.rateStr}</b> · {ch.deliveredStr}/{ch.sentStr}</span>
                      </div>
                      <div style={s('height:9px; background:#EEF2F6; border-radius:6px; overflow:hidden;')}>
                        <div style={s(`height:100%; width:${ch.pct}; background:${ch.color}; border-radius:6px;`)}></div>
                      </div>
                    </div>
                  ))}
                </div>
                <div style={s('background:#fff; border:1px solid #E1E7EE; border-radius:14px; padding:18px 20px;')}>
                  <div style={s('font-family:Georgia,serif; font-weight:700; font-size:15px; margin-bottom:4px;')}>Phân bố theo dân tộc</div>
                  <div style={s('font-size:11px; color:#7C8896; margin-bottom:18px;')}>Vùng ảnh hưởng · dịch tự động theo nhóm</div>
                  {m.ethnics.map((e, i) => (
                    <div key={i} style={s('margin-bottom:13px;')}>
                      <div style={s('display:flex; justify-content:space-between; margin-bottom:5px;')}>
                        <span style={s('font-size:12.5px; font-weight:600;')}>{e.name}</span>
                        <span style={s('font-size:11.5px; color:#7C8896;')}>{e.popStr} · {e.pct}</span>
                      </div>
                      <div style={s('height:8px; background:#EEF2F6; border-radius:6px; overflow:hidden;')}>
                        <div style={s(`height:100%; width:${e.pct}; background:#25ADE3; border-radius:6px;`)}></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div style={s('background:#fff; border:1px solid #E1E7EE; border-radius:14px; padding:18px 20px;')}>
                <div style={s('font-family:Georgia,serif; font-weight:700; font-size:15px; margin-bottom:14px;')}>Hoạt động gần đây</div>
                {m.activities.map((a, i) => (
                  <div key={i} style={s('display:flex; gap:13px; padding:10px 0; border-bottom:1px solid #F1F4F8;')}>
                    <div style={s(`width:32px; height:32px; border-radius:9px; background:${a.bg}; display:flex; align-items:center; justify-content:center; font-size:15px; flex:0 0 32px;`)}>{a.icon}</div>
                    <div style={s('flex:1;')}>
                      <div style={s('font-size:13px; color:#0F1E2A;')}>{a.text}</div>
                      <div style={s('font-size:10.5px; color:#9AA4B0; margin-top:2px;')}>{a.time}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ===== VIEW: COMMUNES TABLE ===== */}
          {view === 'communes' && (
            <div style={s('padding:22px 26px 34px;')}>
              <div style={s('background:#fff; border:1px solid #E1E7EE; border-radius:14px; overflow:hidden;')}>
                <div style={s('padding:16px 20px; border-bottom:1px solid #EEF2F6; display:flex; align-items:center; justify-content:space-between;')}>
                  <div style={s('font-family:Georgia,serif; font-weight:700; font-size:16px;')}>Danh sách Xã · Thống kê quân số</div>
                  <span style={s('font-size:11.5px; color:#7C8896;')}>Nhấp vào xã để xem chi tiết thôn bản &amp; hành động</span>
                </div>
                <div style={s('display:grid; grid-template-columns:2fr 1.1fr 1fr 1fr 1fr 1.2fr; padding:11px 20px; background:#F7F9FB; font-size:10.5px; font-weight:700; color:#7C8896; text-transform:uppercase; letter-spacing:.05em;')}>
                  <span>Xã / Huyện</span><span style={s('text-align:right;')}>Tổng dân</span><span style={s('text-align:right;')}>Đã nhận</span><span style={s('text-align:right;')}>Chưa nhận</span><span style={s('text-align:right;')}>Tỷ lệ</span><span style={s('text-align:center;')}>Trạng thái</span>
                </div>
                {m.communes.map((c) => (
                  <button key={c.id} className="gf-table-row" onClick={() => setDetailId(c.id)} style={s('width:100%; display:grid; grid-template-columns:2fr 1.1fr 1fr 1fr 1fr 1.2fr; align-items:center; padding:13px 20px; border:none; border-bottom:1px solid #F1F4F8; background:#fff; cursor:pointer; text-align:left;')}>
                    <span style={s('display:flex; align-items:center; gap:11px;')}><span style={s('font-size:19px;')}>{c.icon}</span><span><span style={s('display:block; font-size:13.5px; font-weight:600; color:#0F1E2A;')}>{c.name}</span><span style={s('display:block; font-size:10.5px; color:#9AA4B0;')}>{c.district} · {c.hazard}</span></span></span>
                    <span style={s('text-align:right; font-size:13px; font-variant-numeric:tabular-nums;')}>{c.popStr}</span>
                    <span style={s('text-align:right; font-size:13px; color:#1E9E6A; font-weight:600; font-variant-numeric:tabular-nums;')}>{c.receivedStr}</span>
                    <span style={s(`text-align:right; font-size:13px; color:${c.notReceivedColor}; font-weight:600; font-variant-numeric:tabular-nums;`)}>{c.notReceivedStr}</span>
                    <span style={s(`text-align:right; font-size:13.5px; font-weight:700; color:${c.rateColor}; font-variant-numeric:tabular-nums;`)}>{c.rateStr}</span>
                    <span style={s('text-align:center;')}><span style={s(c.pillStyle)}>{c.statusLabel}</span></span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* ===== VIEW: POLICY (RAG) ===== */}
          {view === 'policy' && (
            <div style={s('padding:22px 26px 34px;')}>
              <div style={s('display:flex; align-items:center; justify-content:space-between; margin-bottom:16px;')}>
                <div style={s('display:flex; gap:12px;')}>
                  <PolicyStat label="Còn hiệu lực" value={m.policyActive} color="#1E9E6A" />
                  <PolicyStat label="Sắp hết hạn" value={m.policyExpiring} color="#E8A93B" />
                  <PolicyStat label="Đã hết hiệu lực" value={m.policyExpired} color="#9AA4B0" />
                </div>
                <button onClick={() => setUploadOpen(true)} style={s('font-size:13px; font-weight:700; color:#0F1E2A; background:#25ADE3; border:none; border-radius:10px; padding:11px 18px; cursor:pointer;')}>＋ Upload văn bản chỉ đạo</button>
              </div>
              <div style={s('background:#0F1E2A; color:#fff; border-radius:12px; padding:14px 18px; display:flex; align-items:center; gap:14px; margin-bottom:16px;')}>
                <span style={s('font-size:22px;')}>🧠</span>
                <div style={s('flex:1; font-size:12.5px; line-height:1.5;')}><b style={{ color: '#25ADE3' }}>RAG Policy Engine.</b> Trước mỗi quyết định phân phối, AI Agent truy vấn kho văn bản còn hiệu lực. Chỉ đạo hành chính sẽ <b>ghi đè (override)</b> kịch bản mặc định của AI.</div>
                <span style={s('font-size:11px; background:rgba(37,173,227,.16); color:#25ADE3; padding:5px 11px; border-radius:20px; font-weight:600;')}>Ưu tiên cao nhất</span>
              </div>
              <div style={s('background:#fff; border:1px solid #E1E7EE; border-radius:14px; overflow:hidden;')}>
                <div style={s('display:grid; grid-template-columns:2.4fr 1fr 1.2fr 1.2fr 1fr; padding:11px 20px; background:#F7F9FB; font-size:10.5px; font-weight:700; color:#7C8896; text-transform:uppercase; letter-spacing:.05em;')}>
                  <span>Văn bản</span><span>Loại</span><span>Hiệu lực từ</span><span>Đến hết</span><span style={s('text-align:center;')}>Trạng thái</span>
                </div>
                {m.policies.map((p, i) => (
                  <div key={i} style={s('display:grid; grid-template-columns:2.4fr 1fr 1.2fr 1.2fr 1fr; align-items:center; padding:14px 20px; border-bottom:1px solid #F1F4F8;')}>
                    <span style={s('display:flex; align-items:center; gap:12px;')}><span style={s('font-size:20px;')}>📄</span><span><span style={s('display:block; font-size:13px; font-weight:600; color:#0F1E2A;')}>{p.title}</span><span style={s('display:block; font-size:10.5px; color:#9AA4B0;')}>{p.code} · {p.by}</span></span></span>
                    <span style={s('font-size:12px; color:#5A6675;')}>{p.type}</span>
                    <span style={s('font-size:12.5px; color:#5A6675; font-variant-numeric:tabular-nums;')}>{p.start}</span>
                    <span style={s('font-size:12.5px; color:#5A6675; font-variant-numeric:tabular-nums;')}>{p.end}</span>
                    <span style={s('text-align:center;')}><span style={s(p.pillStyle)}>{p.statusLabel}</span></span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ===== VIEW: CHANNELS / THỐNG KÊ ===== */}
          {view === 'channels' && (
            <div style={s('padding:22px 26px 34px;')}>
              <div style={s('display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom:16px;')}>
                {m.channels.map((ch, i) => (
                  <div key={i} style={s('background:#fff; border:1px solid #E1E7EE; border-radius:14px; padding:16px 18px;')}>
                    <div style={s('display:flex; align-items:center; gap:10px; margin-bottom:12px;')}><span style={s('font-size:22px;')}>{ch.icon}</span><span style={s('font-size:13.5px; font-weight:700;')}>{ch.name}</span></div>
                    <div style={s(`font-family:Georgia,serif; font-size:24px; font-weight:700; color:${ch.color};`)}>{ch.rateStr}</div>
                    <div style={s('font-size:10.5px; color:#8A95A2; margin-top:3px;')}>tiếp cận thành công</div>
                    <div style={s('display:flex; justify-content:space-between; margin-top:13px; padding-top:11px; border-top:1px solid #F1F4F8;')}>
                      <span style={s('font-size:11px; color:#7C8896;')}>Đã gửi<br /><b style={s('color:#0F1E2A; font-size:13px;')}>{ch.sentStr}</b></span>
                      <span style={s('font-size:11px; color:#7C8896; text-align:right;')}>Thất bại<br /><b style={s('color:#E23D3D; font-size:13px;')}>{ch.failedStr}</b></span>
                    </div>
                  </div>
                ))}
              </div>
              <div style={s('background:#fff; border:1px solid #E1E7EE; border-radius:14px; overflow:hidden;')}>
                <div style={s('padding:16px 20px; border-bottom:1px solid #EEF2F6; display:flex; align-items:center; justify-content:space-between;')}>
                  <div style={s('font-family:Georgia,serif; font-weight:700; font-size:16px;')}>Nhật ký phân phối tin nhắn · <span style={s('font-size:12px; color:#25ADE3;')}>{m.timeText}</span></div>
                  <span style={s('font-size:11px; color:#7C8896; display:flex; align-items:center; gap:6px;')}><span style={s('width:7px;height:7px;border-radius:50%;background:#1E9E6A; animation:gf-blink 2s infinite;')}></span>Cập nhật realtime</span>
                </div>
                <div style={s('display:grid; grid-template-columns:.8fr 1.4fr 1fr 1.3fr .9fr 1fr; padding:11px 20px; background:#F7F9FB; font-size:10.5px; font-weight:700; color:#7C8896; text-transform:uppercase; letter-spacing:.05em;')}>
                  <span>Thời gian</span><span>Địa bàn</span><span>Kênh</span><span>Ngôn ngữ / Dân tộc</span><span style={s('text-align:right;')}>Số nhận</span><span style={s('text-align:center;')}>Trạng thái</span>
                </div>
                {m.logs.map((l, i) => (
                  <div key={i} style={s('display:grid; grid-template-columns:.8fr 1.4fr 1fr 1.3fr .9fr 1fr; align-items:center; padding:12px 20px; border-bottom:1px solid #F1F4F8;')}>
                    <span style={s('font-size:12px; color:#5A6675; font-variant-numeric:tabular-nums;')}>{l.time}</span>
                    <span style={s('font-size:12.5px; font-weight:600; color:#0F1E2A;')}>{l.commune}</span>
                    <span style={s('font-size:12px; color:#5A6675;')}>{l.channelIcon} {l.channel}</span>
                    <span style={s('font-size:12px; color:#5A6675;')}>{l.ethnic}</span>
                    <span style={s('text-align:right; font-size:12.5px; font-variant-numeric:tabular-nums;')}>{l.recipientsStr}</span>
                    <span style={s('text-align:center;')}><span style={s(l.pillStyle)}>{l.statusLabel}</span></span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ===== VIEW: ROLES ===== */}
          {view === 'roles' && (
            <div style={s('padding:22px 26px 34px; max-width:900px;')}>
              <div style={s('background:#fff; border:1px solid #E1E7EE; border-radius:14px; padding:22px; margin-bottom:16px;')}>
                <div style={s('font-family:Georgia,serif; font-weight:700; font-size:16px; margin-bottom:4px;')}>Phân quyền theo cấp</div>
                <div style={s('font-size:12px; color:#7C8896; margin-bottom:18px;')}>Quyền hạn tự động thay đổi theo vai trò đăng nhập ở thanh bên.</div>
                {roleRows.map((r, i) => (
                  <div key={i} style={s(roleRowStyle(r.current))}>
                    <div style={s(`width:44px; height:44px; border-radius:11px; background:${r.bg}; display:flex; align-items:center; justify-content:center; font-size:20px; flex:0 0 44px;`)}>{r.icon}</div>
                    <div style={s('flex:1;')}>
                      <div style={s('font-size:14px; font-weight:700; color:#0F1E2A;')}>{r.name} {r.current && <span style={s('font-size:10px; background:#25ADE3; color:#0F1E2A; padding:2px 8px; border-radius:20px; margin-left:6px; font-weight:700;')}>Đang đăng nhập</span>}</div>
                      <div style={s('font-size:11.5px; color:#7C8896; margin-top:4px;')}>{r.perms}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </main>
      </div>

      {/* ============ COMMUNE DETAIL SLIDE-OVER ============ */}
      {detail && (
        <div style={s('position:fixed; inset:0; z-index:900;')}>
          <div onClick={() => setDetailId(null)} style={s('position:absolute; inset:0; background:rgba(15,30,42,.42);')}></div>
          <div style={s('position:absolute; top:0; right:0; height:100%; width:520px; max-width:92vw; background:#F5F8FB; box-shadow:-14px 0 40px rgba(15,30,42,.22); animation:gf-slidein .28s cubic-bezier(.22,.9,.3,1); display:flex; flex-direction:column;')}>
            <div style={s(`padding:20px 22px; color:#fff; display:flex; align-items:center; justify-content:space-between; background:${detail.headBg};`)}>
              <div style={s('display:flex; align-items:center; gap:13px;')}>
                <span style={s('font-size:30px;')}>{detail.icon}</span>
                <div>
                  <div style={s('font-family:Georgia,serif; font-size:20px; font-weight:700;')}>{detail.name}</div>
                  <div style={s('font-size:12px; opacity:.85; margin-top:2px;')}>{detail.district} · {detail.hazard}</div>
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
                  <div style={s('display:flex; gap:8px;')}>
                    <button onClick={() => showToast(`Đã gửi lại SMS cảnh báo tới Trưởng bản ${h.headman} — ${h.name}`, '✉️')} style={s('flex:1; font-size:11.5px; font-weight:600; color:#0F1E2A; background:#F0FAFE; border:1px solid #CBEBF9; border-radius:8px; padding:8px; cursor:pointer;')}>✉️ Gửi lại SMS</button>
                    <button onClick={() => showToast(`Đang kết nối cuộc gọi khẩn cấp tới ${h.headman} (${h.name})…`, '📞')} style={s('flex:1; font-size:11.5px; font-weight:600; color:#fff; background:#0F1E2A; border:none; border-radius:8px; padding:8px; cursor:pointer;')}>📞 Gọi khẩn cấp</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ============ UPLOAD MODAL ============ */}
      {uploadOpen && (
        <div style={s('position:fixed; inset:0; z-index:950; display:flex; align-items:center; justify-content:center;')}>
          <div onClick={() => setUploadOpen(false)} style={s('position:absolute; inset:0; background:rgba(15,30,42,.5);')}></div>
          <div style={s('position:relative; width:520px; max-width:94vw; background:#fff; border-radius:16px; overflow:hidden; animation:gf-fadeup .25s ease;')}>
            <div style={s('background:#0F1E2A; color:#fff; padding:18px 22px; display:flex; align-items:center; justify-content:space-between;')}>
              <div style={s('display:flex; align-items:center; gap:10px;')}><span style={s('font-size:20px;')}>📥</span><span style={s('font-family:Georgia,serif; font-size:16px; font-weight:700;')}>Upload văn bản chỉ đạo khẩn cấp</span></div>
              <button onClick={() => setUploadOpen(false)} style={s('width:32px; height:32px; border-radius:8px; border:none; background:rgba(255,255,255,.16); color:#fff; font-size:16px; cursor:pointer;')}>✕</button>
            </div>
            <div style={s('padding:22px;')}>
              <div style={s('border:2px dashed #CBD5E0; border-radius:12px; padding:30px; text-align:center; margin-bottom:18px; background:#F7F9FB;')}>
                <div style={s('font-size:32px; margin-bottom:8px;')}>📄</div>
                <div style={s('font-size:13px; font-weight:600; color:#0F1E2A;')}>Kéo thả file vào đây</div>
                <div style={s('font-size:11px; color:#8A95A2; margin-top:4px;')}>PDF, Word, Text · Tự động trích xuất Vector embeddings</div>
              </div>
              <div style={s('display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:6px;')}>
                <div><label style={s('font-size:11.5px; font-weight:600; color:#5A6675; display:block; margin-bottom:6px;')}>Ngày bắt đầu hiệu lực</label><input defaultValue="17/07/2026" style={s('width:100%; height:40px; border:1px solid #E1E7EE; border-radius:9px; padding:0 12px; font-family:inherit; font-size:13px; color:#0F1E2A;')} /></div>
                <div><label style={s('font-size:11.5px; font-weight:600; color:#5A6675; display:block; margin-bottom:6px;')}>Ngày kết thúc hiệu lực</label><input defaultValue="17/09/2026" style={s('width:100%; height:40px; border:1px solid #E1E7EE; border-radius:9px; padding:0 12px; font-family:inherit; font-size:13px; color:#0F1E2A;')} /></div>
              </div>
              <div style={s('background:#FFF7E8; border:1px solid #F3DFA8; border-radius:9px; padding:10px 13px; font-size:11px; color:#8A6D2B; margin-bottom:20px;')}>⏳ Nếu không nhập hạn, hệ thống mặc định hiệu lực tối đa <b>2 tháng</b> để tránh áp dụng quy định lỗi thời.</div>
              <div style={s('display:flex; gap:10px; justify-content:flex-end;')}>
                <button onClick={() => setUploadOpen(false)} style={s('font-size:13px; font-weight:600; color:#5A6675; background:#F0F3F7; border:none; border-radius:9px; padding:11px 20px; cursor:pointer;')}>Hủy</button>
                <button onClick={() => { setUploadOpen(false); showToast('Đã nạp văn bản vào Vector DB — RAG sẵn sàng override kịch bản AI', '🧠'); }} style={s('font-size:13px; font-weight:700; color:#0F1E2A; background:#25ADE3; border:none; border-radius:9px; padding:11px 22px; cursor:pointer;')}>Nạp vào Vector DB</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ============ TOAST ============ */}
      {toast && (
        <div style={s('position:fixed; bottom:26px; left:50%; transform:translateX(-50%); z-index:1000; background:#0F1E2A; color:#fff; padding:13px 20px; border-radius:11px; box-shadow:0 12px 34px rgba(15,30,42,.3); display:flex; align-items:center; gap:11px; animation:gf-toastin .3s ease;')}>
          <span style={s('font-size:17px;')}>{toastIcon}</span>
          <span style={s('font-size:13px; font-weight:500;')}>{toast}</span>
        </div>
      )}
    </div>
  );
}

// ---- small presentational helpers ----
function KpiCard({ k }) {
  return (
    <div style={s(k.cardStyle)}>
      <div style={s('display:flex; align-items:center; justify-content:space-between;')}>
        <span style={s('font-size:11px; color:#7C8896; font-weight:600;')}>{k.label}</span>
        <span style={s('font-size:15px;')}>{k.icon}</span>
      </div>
      <div style={s(`font-family:Georgia,serif; font-size:26px; font-weight:700; margin-top:9px; color:${k.valueColor}; line-height:1;`)}>{k.value}</div>
      <div style={s('font-size:10.5px; color:#8A95A2; margin-top:6px;')}>{k.sub}</div>
    </div>
  );
}

function Legend({ color, label, ml }) {
  return (
    <span style={s(`font-size:11px; display:flex; align-items:center; gap:5px; color:#5A6675;${ml ? ' margin-left:8px;' : ''}`)}>
      <span style={s(`width:10px;height:10px;border-radius:50%;background:${color};`)}></span>{label}
    </span>
  );
}

function PolicyStat({ label, value, color }) {
  return (
    <div style={s('background:#fff; border:1px solid #E1E7EE; border-radius:12px; padding:12px 18px; min-width:118px;')}>
      <div style={s('font-size:11px; color:#7C8896;')}>{label}</div>
      <div style={s(`font-family:Georgia,serif; font-size:23px; font-weight:700; color:${color};`)}>{value}</div>
    </div>
  );
}

function DetailStat({ label, value, color }) {
  return (
    <div style={s('background:#fff; border:1px solid #E1E7EE; border-radius:11px; padding:13px;')}>
      <div style={s('font-size:10.5px; color:#7C8896;')}>{label}</div>
      <div style={s(`font-family:Georgia,serif; font-size:21px; font-weight:700;${color ? ` color:${color};` : ''}`)}>{value}</div>
    </div>
  );
}
