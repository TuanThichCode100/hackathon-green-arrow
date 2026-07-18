// ---------------------------------------------------------------------------
// GreenForecast — domain data + model builders (pure, framework-agnostic)
// Ported from the HTML prototype. Replace the mock arrays / buildModel logic
// with real API calls (see README "API mapping") when wiring a backend.
// ---------------------------------------------------------------------------

export const COMMUNES = [
  { id: 'muong_nhe', name: 'Xã Mường Nhé', district: 'H. Mường Nhé', lat: 21.170, lng: 102.470, pop: 12400, recvNormal: 0.98, recvAlert: 0.62, alertStatus: 'alert', icon: '🌊', hazard: 'Lũ quét / Lũ ống',
    hamlets: [ { name: 'Bản Nậm Pố', pop: 2100, headman: 'Vàng A Của' }, { name: 'Bản Huổi Lếch', pop: 1750, headman: 'Lò Văn Pánh' }, { name: 'Bản Cà Là Pá', pop: 2600, headman: 'Sùng A Dơ' }, { name: 'Bản Nậm Kè', pop: 1500, headman: 'Giàng A Sính' } ],
    lost: [ { name: 'Hộ Vàng A Sơ (4 người)', lat: 21.155, lng: 102.455, phone: '0987 xxx 214' }, { name: 'Hộ Lò Thị Mai (3 người)', lat: 21.182, lng: 102.488, phone: '0912 xxx 770' } ] },
  { id: 'tua_chua', name: 'Xã Tủa Chùa', district: 'H. Tủa Chùa', lat: 21.930, lng: 103.380, pop: 11200, recvNormal: 0.98, recvAlert: 0.58, alertStatus: 'alert', icon: '🧊', hazard: 'Mưa đá / Ngập lũ',
    hamlets: [ { name: 'Bản Tả Sìn Thàng', pop: 3100, headman: 'Mùa A Kỷ' }, { name: 'Bản Sín Chải', pop: 2400, headman: 'Thào A Dế' }, { name: 'Bản Xá Nhè', pop: 2900, headman: 'Vừ A Lử' } ],
    lost: [ { name: 'Hộ Thào A Chá (5 người)', lat: 21.945, lng: 103.395, phone: '0965 xxx 018' } ] },
  { id: 'dien_bien_dong', name: 'Xã Điện Biên Đông', district: 'H. Điện Biên Đông', lat: 21.230, lng: 103.230, pop: 9400, recvNormal: 0.97, recvAlert: 0.64, alertStatus: 'alert', icon: '⛰️', hazard: 'Sạt lở đất',
    hamlets: [ { name: 'Bản Na Son', pop: 2200, headman: 'Lò Văn Muôn' }, { name: 'Bản Keo Lôm', pop: 1900, headman: 'Vàng A Tùng' }, { name: 'Bản Phì Nhừ', pop: 1700, headman: 'Sùng Seo Sáng' } ],
    lost: [ { name: 'Hộ Lò A Vư (2 người)', lat: 21.240, lng: 103.245, phone: '0938 xxx 552' } ] },
  { id: 'nam_po', name: 'Xã Nậm Pồ', district: 'H. Nậm Pồ', lat: 21.900, lng: 102.680, pop: 9800, recvNormal: 0.97, recvAlert: 0.71, alertStatus: 'watch', icon: '⛰️', hazard: 'Nguy cơ sạt lở',
    hamlets: [ { name: 'Bản Nà Hỳ', pop: 2500, headman: 'Poòng Văn Điêng' }, { name: 'Bản Chà Nưa', pop: 2100, headman: 'Lò Văn Xuân' }, { name: 'Bản Si Pa Phìn', pop: 2600, headman: 'Vàng A Nếnh' } ] },
  { id: 'muong_cha', name: 'Xã Mường Chà', district: 'H. Mường Chà', lat: 21.760, lng: 103.030, pop: 8600, recvNormal: 0.99, recvAlert: 0.80, alertStatus: 'watch', icon: '💨', hazard: 'Gió mạnh',
    hamlets: [ { name: 'Bản Sá Tổng', pop: 2200, headman: 'Lý A Sáu' }, { name: 'Bản Hừa Ngài', pop: 1800, headman: 'Giàng A Chớ' }, { name: 'Bản Pa Ham', pop: 2000, headman: 'Lò Văn Hoan' } ] },
  { id: 'tuan_giao', name: 'Xã Tuần Giáo', district: 'H. Tuần Giáo', lat: 21.580, lng: 103.420, pop: 15300, recvNormal: 0.99, recvAlert: 0.76, alertStatus: 'watch', icon: '⚡', hazard: 'Giông sét',
    hamlets: [ { name: 'Bản Quài Nưa', pop: 3400, headman: 'Lò Văn Panh' }, { name: 'Bản Chiềng Sinh', pop: 2900, headman: 'Cà Văn Inh' }, { name: 'Bản Tỏa Tình', pop: 2600, headman: 'Mùa A Sềnh' } ] },
  { id: 'muong_ang', name: 'Xã Mường Ảng', district: 'H. Mường Ảng', lat: 21.480, lng: 103.310, pop: 10100, recvNormal: 0.99, recvAlert: 0.91, alertStatus: 'watch', icon: '🌫️', hazard: 'Sương mù dày',
    hamlets: [ { name: 'Bản Ẳng Nưa', pop: 2800, headman: 'Lò Văn Pọm' }, { name: 'Bản Búng Lao', pop: 2500, headman: 'Quàng Văn Tọ' } ] },
  { id: 'muong_lay', name: 'Phường Mường Lay', district: 'TX. Mường Lay', lat: 22.030, lng: 103.150, pop: 4200, recvNormal: 0.98, recvAlert: 0.70, alertStatus: 'watch', icon: '🌊', hazard: 'Lũ ống',
    hamlets: [ { name: 'Tổ dân phố Na Lay', pop: 1500, headman: 'Điêu Chính Hoan' }, { name: 'Bản Chi Luông', pop: 1300, headman: 'Lò Văn Pín' } ] },
  { id: 'dien_bien', name: 'Xã Thanh Nưa', district: 'H. Điện Biên', lat: 21.300, lng: 102.980, pop: 13500, recvNormal: 0.99, recvAlert: 0.85, alertStatus: 'watch', icon: '🌊', hazard: 'Ngập cục bộ',
    hamlets: [ { name: 'Bản Pom Lót', pop: 3200, headman: 'Lò Văn Pâng' }, { name: 'Bản Hồng Lếnh', pop: 2900, headman: 'Cà Văn Dung' } ] },
  { id: 'dbp', name: 'TP. Điện Biên Phủ', district: 'Trung tâm tỉnh', lat: 21.386, lng: 103.017, pop: 60000, recvNormal: 0.99, recvAlert: 0.88, alertStatus: 'watch', icon: '🌪️', hazard: 'Giông lốc',
    hamlets: [ { name: 'Phường Mường Thanh', pop: 14000, headman: 'BQL Tổ 1' }, { name: 'Phường Nam Thanh', pop: 11000, headman: 'BQL Tổ 4' }, { name: 'Phường Thanh Trường', pop: 9500, headman: 'BQL Tổ 7' } ] },
];

// ---- helpers ----
export const fmt = (n) => Math.round(n).toLocaleString('vi-VN');
export const statusOf = (c, emergency) => (emergency ? c.alertStatus : 'safe');
export const statusMeta = (st) => {
  if (st === 'alert') return { label: 'Cảnh báo', color: '#E23D3D', bg: '#FDECEC' };
  if (st === 'watch') return { label: 'Theo dõi', color: '#B9832B', bg: '#FFF6E6' };
  return { label: 'An toàn', color: '#1E9E6A', bg: '#E7F6EF' };
};
export const rateColor = (r) => (r >= 0.9 ? '#1E9E6A' : r >= 0.7 ? '#E8A93B' : '#E23D3D');
export const pill = (color, bg) => `display:inline-block; font-size:10.5px; font-weight:700; color:${color}; background:${bg}; padding:3px 10px; border-radius:20px; margin-top:3px;`;

export const TIME_META = {
  today: { label: 'Hôm nay', factor: 1, text: 'hôm nay' },
  '24h': { label: '24 giờ', factor: 1.4, text: 'trong 24 giờ qua' },
  '7d': { label: '7 ngày', factor: 6.2, text: 'trong 7 ngày qua' },
  '30d': { label: '30 ngày', factor: 22, text: 'trong 30 ngày qua' },
};

export const VIEW_TITLES = {
  map: 'Bản đồ giám sát', overview: 'Tổng quan hệ thống', communes: 'Danh sách Xã',
  policy: 'Văn bản chỉ đạo (RAG)', channels: 'Thống kê', roles: 'Phân quyền',
  database: 'Quản lý Dữ liệu Dân cư'
};

export const NAV = [
  { key: 'map', icon: '🗺️', label: 'Bản đồ giám sát' },
  { key: 'overview', icon: '📊', label: 'Tổng quan' },
  { key: 'communes', icon: '🏘️', label: 'Danh sách Xã' },
  { key: 'policy', icon: '🧠', label: 'Văn bản chỉ đạo (RAG)' },
  { key: 'channels', icon: '📡', label: 'Thống kê' },
  { key: 'roles', icon: '🔐', label: 'Phân quyền' },
  { key: 'database', icon: '👥', label: 'Quản lý Dân cư' },
];

// ---- model builders ----
export function buildModel(emergency, timeRange) {
  const tf = TIME_META[timeRange].factor;

  const communes = COMMUNES.map((c) => {
    const st = statusOf(c, emergency);
    const meta = statusMeta(st);
    const rate = emergency ? c.recvAlert : c.recvNormal;
    const received = Math.round(c.pop * rate);
    const notReceived = c.pop - received;
    return {
      id: c.id, name: c.name, district: c.district, icon: c.icon, hazard: c.hazard,
      popStr: fmt(c.pop), receivedStr: fmt(received), notReceivedStr: fmt(notReceived),
      notReceivedColor: notReceived > c.pop * 0.15 ? '#E23D3D' : '#5A6675',
      rateStr: Math.round(rate * 100) + '%', rateColor: rateColor(rate),
      statusLabel: meta.label, pillStyle: pill(meta.color, meta.bg),
    };
  });

  const totalPop = COMMUNES.reduce((s, c) => s + c.pop, 0);
  const totalRecv = COMMUNES.reduce((s, c) => s + Math.round(c.pop * (emergency ? c.recvAlert : c.recvNormal)), 0);
  const totalNot = totalPop - totalRecv;
  const alertCount = COMMUNES.filter((c) => statusOf(c, emergency) === 'alert').length;
  const headmenTotal = COMMUNES.reduce((s, c) => s + (c.hamlets ? c.hamlets.length : 0), 0);
  const headmenConfirmed = emergency ? Math.round(headmenTotal * 0.72) : headmenTotal;

  const kpiCard = 'background:#fff; border:1px solid #E1E7EE; border-radius:14px; padding:15px 17px;';
  const kpiCardAlert = 'background:#fff; border:1px solid #F6C6C6; border-radius:14px; padding:15px 17px; box-shadow:0 0 0 1px #F6C6C6;';
  const kpis = [
    { label: 'Dân số vùng ảnh hưởng', icon: '👥', value: fmt(totalPop), sub: 'trên ' + COMMUNES.length + ' xã/phường giám sát', cardStyle: kpiCard, valueColor: '#0F1E2A' },
    { label: 'Đã nhận cảnh báo', icon: '✅', value: Math.round((totalRecv / totalPop) * 100) + '%', sub: fmt(totalRecv) + ' người', cardStyle: kpiCard, valueColor: '#1E9E6A' },
    { label: 'Chưa phản hồi', icon: '⚠️', value: fmt(totalNot), sub: emergency ? 'cần cử lực lượng tiếp cận' : 'trong ngưỡng an toàn', cardStyle: emergency ? kpiCardAlert : kpiCard, valueColor: emergency ? '#E23D3D' : '#5A6675' },
    { label: 'Trưởng bản xác nhận', icon: '📢', value: headmenConfirmed + '/' + headmenTotal, sub: 'đã nhận file Audio loa', cardStyle: kpiCard, valueColor: '#0F1E2A' },
    { label: emergency ? 'Cảnh báo đang mở' : 'Trạng thái hệ thống', icon: emergency ? '🚨' : '🟢', value: emergency ? String(alertCount) : 'Ổn định', sub: emergency ? 'xã ở mức Cảnh báo' : 'giám sát thường trực', cardStyle: emergency ? kpiCardAlert : kpiCard, valueColor: emergency ? '#E23D3D' : '#1E9E6A' },
  ];

  const chBase = [
    { name: 'Zalo OA', icon: '💬', color: '#1E9E6A', sent: emergency ? 128400 : 42100, rate: emergency ? 0.86 : 0.97 },
    { name: 'SMS Gateway', icon: '✉️', color: '#25ADE3', sent: emergency ? 141200 : 40800, rate: emergency ? 0.91 : 0.98 },
    { name: 'Auto-Call (tiếng dân tộc)', icon: '📞', color: '#E8A93B', sent: emergency ? 38600 : 6200, rate: emergency ? 0.74 : 0.88 },
    { name: 'Audio Loa phát thanh', icon: '📢', color: '#0F1E2A', sent: emergency ? 412 : 132, rate: emergency ? 0.95 : 0.99 },
  ];
  const channels = chBase.map((ch) => {
    const sent = Math.round(ch.sent * tf);
    const delivered = Math.round(sent * ch.rate);
    return { name: ch.name, icon: ch.icon, color: ch.color, sentStr: fmt(sent), deliveredStr: fmt(delivered), failedStr: fmt(sent - delivered), rateStr: Math.round(ch.rate * 100) + '%', pct: Math.round(ch.rate * 100) + '%' };
  });

  const eth = [ { name: 'Thái', pop: 38200 }, { name: 'Mông (H\u2019Mông)', pop: 31500 }, { name: 'Kinh', pop: 24800 }, { name: 'Khơ Mú', pop: 9600 }, { name: 'Dao', pop: 5100 }, { name: 'Hà Nhì / khác', pop: 5300 } ];
  const ethTotal = eth.reduce((s, e) => s + e.pop, 0);
  const ethnics = eth.map((e) => ({ name: e.name, popStr: fmt(e.pop), pct: Math.round((e.pop / ethTotal) * 100) + '%' }));

  const activities = emergency
    ? [
        { icon: '🚨', bg: '#FDECEC', text: 'AI Agent kích hoạt kịch bản Lũ quét cho H. Mường Nhé & Tủa Chùa', time: 'vừa xong' },
        { icon: '🧠', bg: '#F0FAFE', text: 'RAG override: áp dụng Công điện khẩn 04/CĐ — sơ tán dân sát bờ sông Nậm Rốm', time: '1 phút trước' },
        { icon: '📞', bg: '#FFF6E6', text: 'Tổng đài Auto-call phát cảnh báo tiếng Mông tới 38.600 thuê bao', time: '2 phút trước' },
        { icon: '📢', bg: '#EEF2F6', text: 'Sinh file Audio MP3 loa phát thanh cho 61 trưởng bản', time: '3 phút trước' },
        { icon: '📍', bg: '#FDECEC', text: 'Phát hiện 4 hộ chưa phản hồi tại Điện Biên Đông — đã đánh dấu tọa độ', time: '4 phút trước' },
      ]
    : [
        { icon: '🟢', bg: '#E7F6EF', text: 'Hệ thống giám sát thường trực — không có hình thái cực đoan', time: 'vừa xong' },
        { icon: '📄', bg: '#F0FAFE', text: 'Cập nhật danh bạ cư dân xã Tuần Giáo (thêm 214 nhân khẩu)', time: '22 phút trước' },
        { icon: '🧠', bg: '#F0FAFE', text: 'RAG index làm mới: 8 văn bản chỉ đạo còn hiệu lực', time: '1 giờ trước' },
        { icon: '✅', bg: '#E7F6EF', text: 'Bản tin dự báo tuần đã gửi thử nghiệm tới 42.100 thuê bao Zalo', time: '3 giờ trước' },
        { icon: '📢', bg: '#EEF2F6', text: 'Kiểm tra định kỳ hệ thống loa phát thanh 132 bản — hoạt động tốt', time: 'hôm qua' },
      ];

  const polBase = [
    { code: 'Công điện 04/CĐ-UBND', title: 'Sơ tán khẩn cấp dân cư sát bờ sông Nậm Rốm khi mưa lũ', type: 'Công điện', by: 'UBND Tỉnh', start: '15/07/2026', end: '15/08/2026', status: 'active' },
    { code: 'QĐ 118/QĐ-PCTT', title: 'Phương án ứng phó sạt lở đất mùa mưa 2026', type: 'Quyết định', by: 'Ban CH PCTT', start: '01/06/2026', end: '30/09/2026', status: 'active' },
    { code: 'HD 27/HD-BCH', title: 'Hướng dẫn phát thanh cảnh báo bằng tiếng dân tộc', type: 'Hướng dẫn', by: 'Sở TT&TT', start: '10/05/2026', end: '10/11/2026', status: 'active' },
    { code: 'TB 09/TB-UBND', title: 'Thông báo cấm đường ĐT143 khu vực đèo Pha Đin', type: 'Thông báo', by: 'UBND Huyện', start: '02/07/2026', end: '22/07/2026', status: 'expiring' },
    { code: 'CV 512/CV-NN', title: 'Cảnh báo rét hại vụ đông xuân (đã hết hiệu lực)', type: 'Công văn', by: 'Sở NN&PTNT', start: '01/01/2026', end: '31/03/2026', status: 'expired' },
  ];
  const polMeta = { active: { label: 'Còn hiệu lực', color: '#1E9E6A', bg: '#E7F6EF' }, expiring: { label: 'Sắp hết hạn', color: '#B9832B', bg: '#FFF6E6' }, expired: { label: 'Hết hiệu lực', color: '#9AA4B0', bg: '#EEF2F6' } };
  const policies = polBase.map((p) => ({ ...p, statusLabel: polMeta[p.status].label, pillStyle: pill(polMeta[p.status].color, polMeta[p.status].bg) }));

  const logBase = emergency
    ? [
        { time: '14:32:07', commune: 'Xã Mường Nhé', channel: 'Auto-Call', channelIcon: '📞', ethnic: 'Tiếng Mông', recipients: 12400 },
        { time: '14:31:55', commune: 'Xã Tủa Chùa', channel: 'SMS', channelIcon: '✉️', ethnic: 'Thái (không dấu)', recipients: 11200 },
        { time: '14:31:40', commune: 'Điện Biên Đông', channel: 'Zalo OA', channelIcon: '💬', ethnic: 'Tiếng Kinh', recipients: 9400 },
        { time: '14:31:22', commune: 'Xã Mường Nhé', channel: 'Audio Loa', channelIcon: '📢', ethnic: 'MP3 → Trưởng bản', recipients: 4 },
        { time: '14:30:58', commune: 'Xã Nậm Pồ', channel: 'SMS', channelIcon: '✉️', ethnic: 'Khơ Mú → fallback Kinh', recipients: 9800 },
        { time: '14:30:31', commune: 'Xã Tủa Chùa', channel: 'Auto-Call', channelIcon: '📞', ethnic: 'Tiếng Mông', recipients: 3200 },
        { time: '14:30:10', commune: 'Xã Tuần Giáo', channel: 'Zalo OA', channelIcon: '💬', ethnic: 'Thái', recipients: 15300 },
        { time: '14:29:44', commune: 'TP. Điện Biên Phủ', channel: 'SMS', channelIcon: '✉️', ethnic: 'Tiếng Kinh', recipients: 60000 },
      ]
    : [
        { time: '09:12:04', commune: 'Toàn tỉnh', channel: 'Zalo OA', channelIcon: '💬', ethnic: 'Đa ngôn ngữ', recipients: 42100 },
        { time: '09:11:30', commune: 'Xã Tuần Giáo', channel: 'SMS', channelIcon: '✉️', ethnic: 'Thái (không dấu)', recipients: 15300 },
        { time: '08:40:12', commune: 'Xã Mường Ảng', channel: 'Audio Loa', channelIcon: '📢', ethnic: 'MP3 định kỳ', recipients: 2 },
        { time: '08:15:55', commune: 'TP. Điện Biên Phủ', channel: 'Zalo OA', channelIcon: '💬', ethnic: 'Tiếng Kinh', recipients: 60000 },
        { time: '07:50:20', commune: 'Xã Nậm Pồ', channel: 'SMS', channelIcon: '✉️', ethnic: 'Tiếng Kinh', recipients: 9800 },
      ];
  const logs = logBase.map((l) => ({ ...l, recipientsStr: fmt(l.recipients), statusLabel: 'Đã gửi', pillStyle: pill('#25ADE3', '#EAF7FD') }));

  const activeCommunes = COMMUNES.filter((c) => statusOf(c, emergency) === 'alert').map((c) => c.name).filter((v, i, a) => a.indexOf(v) === i);
  const alertHeadline = 'Lũ quét & sạt lở tại ' + (activeCommunes.length ? activeCommunes.join(', ') : 'khu vực giám sát') + ' — ưu tiên sơ tán theo Công điện 04.';

  return {
    kpis, communes, channels, ethnics, activities, policies, logs,
    alertCount, alertHeadline,
    timeText: TIME_META[timeRange].text,
    policyActive: polBase.filter((p) => p.status === 'active').length,
    policyExpiring: polBase.filter((p) => p.status === 'expiring').length,
    policyExpired: polBase.filter((p) => p.status === 'expired').length,
  };
}

export function buildDetail(id, emergency) {
  const c = COMMUNES.find((x) => x.id === id);
  if (!c) return null;
  const st = statusOf(c, emergency);
  const rate = emergency ? c.recvAlert : c.recvNormal;
  const received = Math.round(c.pop * rate);
  const notReceived = c.pop - received;
  const hamlets = (c.hamlets || []).map((h, i) => {
    const hr = Math.min(1, Math.max(0.3, rate + (i % 2 === 0 ? 0.04 : -0.06)));
    const confirmed = !emergency || hr >= 0.75;
    return { name: h.name, headman: h.headman, rateStr: Math.round(hr * 100) + '%', rateColor: rateColor(hr), confirmLabel: confirmed ? 'đã xác nhận ✅' : 'CHƯA xác nhận ⚠️' };
  });
  const hasLost = !!(emergency && st === 'alert' && c.lost && c.lost.length);
  const headBg = st === 'alert' ? 'linear-gradient(135deg,#C42B2B,#E23D3D)' : st === 'watch' ? 'linear-gradient(135deg,#0F1E2A,#2A4A5E)' : 'linear-gradient(135deg,#0F1E2A,#1E9E6A)';
  return {
    id: c.id, icon: c.icon, name: c.name, hazard: emergency ? c.hazard : 'Không có cảnh báo',
    popStr: fmt(c.pop), receivedStr: fmt(received), notReceivedStr: fmt(notReceived),
    notReceivedColor: notReceived > c.pop * 0.15 ? '#E23D3D' : '#5A6675',
    rateStr: Math.round(rate * 100) + '%', rateColor: rateColor(rate),
    hamletCount: hamlets.length, hamlets,
    hasLost, lostCount: hasLost ? c.lost.length : 0,
    lost: hasLost ? c.lost.map((lp) => ({ name: lp.name, coord: lp.lat.toFixed(3) + ', ' + lp.lng.toFixed(3), phone: lp.phone })) : [],
    headBg,
  };
}
