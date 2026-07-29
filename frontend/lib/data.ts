// Runtime presentation helpers shared by the API-to-UI mapping.
// Operational data must come from backend endpoints, never this module.

export const fmt = (value: unknown) => Number.isFinite(value) ? Math.round(value as number).toLocaleString('vi-VN') : '—';

export const statusMeta = (status: string) => {
  if (status === 'alert') return { label: 'Cảnh báo', color: '#E23D3D', bg: '#FDECEC' };
  if (status === 'watch') return { label: 'Theo dõi', color: '#B9832B', bg: '#FFF6E6' };
  if (status === 'unverified') return { label: 'Chưa xác thực', color: '#64748B', bg: '#F1F5F9' };
  return { label: 'An toàn', color: '#1E9E6A', bg: '#E7F6EF' };
};

export const rateColor = (rate: number) => (rate >= 0.9 ? '#1E9E6A' : rate >= 0.7 ? '#E8A93B' : '#E23D3D');

export const pill = (color: string, background: string) => `display:inline-block; font-size:10.5px; font-weight:700; color:${color}; background:${background}; padding:3px 10px; border-radius:20px; margin-top:3px;`;

export const TIME_META: Record<string, { label: string; factor: number; text: string }> = {
  today: { label: 'Hôm nay', factor: 1, text: 'hôm nay' },
  '24h': { label: '24 giờ', factor: 1.4, text: 'trong 24 giờ qua' },
  '7d': { label: '7 ngày', factor: 6.2, text: 'trong 7 ngày qua' },
  '30d': { label: '30 ngày', factor: 22, text: 'trong 30 ngày qua' },
};
