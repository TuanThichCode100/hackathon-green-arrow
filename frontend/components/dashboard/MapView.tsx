'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { ArrowsOut, MapPinArea, Path, Warning } from '@phosphor-icons/react';
import type { DashboardData } from './types';

interface Props {
  m: DashboardData;
  emergency: boolean;
  setDetailId: (id: string | number) => void;
  view: string;
}

type Risk = 'safe' | 'watch' | 'alert' | 'unverified';
type FeatureInfo = { fid: number; name: string; district: string; risk: Risk; rate: number | null; linkedId?: string | number };

const fill: Record<Risk, string> = {
  safe: 'oklch(0.72 0.105 154)',
  watch: 'oklch(0.79 0.12 78)',
  alert: 'oklch(0.64 0.16 28)',
  unverified: 'oklch(0.78 0.012 255)',
};

function repairText(value: unknown) {
  if (typeof value !== 'string') return '';
  const cp1252 = '€‚ƒ„…†‡ˆ‰Š‹ŒŽ‘’“”•–—˜™š›œžŸ';
  let result = value;
  for (let pass = 0; pass < 3 && /[ÃÄÆáºá»]/.test(result); pass += 1) {
    try {
      const bytes = Uint8Array.from(Array.from(result).map((char) => {
        const code = char.charCodeAt(0);
        const cpIndex = cp1252.indexOf(char);
        return cpIndex >= 0 ? 0x80 + cpIndex : code & 255;
      }));
      const decoded = new TextDecoder('utf-8', { fatal: true }).decode(bytes);
      if (decoded === result) break;
      result = decoded;
    } catch {
      break;
    }
  }
  return result;
}

function normalized(value: string) {
  return value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/^(xa|phuong|thi tran|tp)\s+/i, '').toLowerCase().trim();
}

function editDistance(a: string, b: string) {
  const row = Array.from({ length: b.length + 1 }, (_, index) => index);
  for (let i = 1; i <= a.length; i += 1) {
    let previous = row[0];
    row[0] = i;
    for (let j = 1; j <= b.length; j += 1) {
      const next = row[j];
      row[j] = Math.min(row[j] + 1, row[j - 1] + 1, previous + (a[i - 1] === b[j - 1] ? 0 : 1));
      previous = next;
    }
  }
  return row[b.length];
}

export default function MapView({ m, emergency, setDetailId, view }: Props) {
  const mapRef = useRef<any>(null);
  const layerRef = useRef<any>(null);
  const layersByFid = useRef(new Map<number, any>());
  const [selected, setSelected] = useState<FeatureInfo | null>(null);
  const [features, setFeatures] = useState<FeatureInfo[]>([]);
  const [mapError, setMapError] = useState<string | null>(null);
  const [query, setQuery] = useState('');
  const [activeRisk, setActiveRisk] = useState<Risk | 'all'>('all');
  const listRows = useRef(new Map<number, HTMLButtonElement>());

  const metricsByName = useMemo(() => {
    const result = new Map<string, any>();
    m.communes.forEach((commune) => result.set(normalized(commune.name), commune));
    return result;
  }, [m.communes]);

  useEffect(() => {
    if (view !== 'map') return;
    let cancelled = false;

    Promise.all([
      import('leaflet'),
      fetch('/dien-bien-communes.geojson').then((response) => {
        if (!response.ok) throw new Error('Không tải được dữ liệu ranh giới');
        return response.json();
      }),
    ]).then(([leafletModule, geojson]) => {
      if (cancelled) return;
      const L = leafletModule.default;
      const container = document.getElementById('province-map');
      if (!container) return;

      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }

      const map = L.map(container, {
        attributionControl: false,
        zoomControl: true,
        minZoom: 5,
        maxZoom: 12,
        zoomSnap: 0.25,
      });
      mapRef.current = map;

      const info: FeatureInfo[] = [];
      const geoLayer = L.geoJSON(geojson, {
        style: (feature: any) => {
          const fid = Number(feature?.properties?.FID || 0);
          const name = repairText(feature?.properties?.NAME_3);
          const linked = metricsByName.get(normalized(name));
          const risk: Risk = linked?.statusLabel === 'Cảnh báo' ? 'alert' : linked?.statusLabel === 'Theo dõi' ? 'watch' : linked?.statusLabel === 'An toàn' ? 'safe' : 'unverified';
          return { color: 'oklch(0.28 0.025 160)', weight: 0.8, opacity: 0.72, fillColor: fill[risk], fillOpacity: 0.72 };
        },
        onEachFeature: (feature: any, layer: any) => {
          const fid = Number(feature?.properties?.FID || 0);
          const name = repairText(feature?.properties?.name || feature?.properties?.NAME_3) || `Địa bàn ${fid}`;
          const unitType = repairText(feature?.properties?.unit_type || feature?.properties?.TYPE_3).toLowerCase();
          const district = `${unitType || 'đơn vị'} mới từ 01/07/2025`;
          const linked = metricsByName.get(normalized(name));
          const risk: Risk = linked?.statusLabel === 'Cảnh báo' ? 'alert' : linked?.statusLabel === 'Theo dõi' ? 'watch' : linked?.statusLabel === 'An toàn' ? 'safe' : 'unverified';
          const rate = linked?.rateStr && linked.rateStr !== '—' ? Number.parseInt(linked.rateStr, 10) : null;
          const item = { fid, name, district, risk, rate, linkedId: linked?.id };
          info.push(item);
          layersByFid.current.set(fid, layer);
          layer.bindTooltip(`<strong>${name}</strong><br><span>${district}</span><br><span>${rate === null ? 'Chưa xác thực' : `Tiếp cận: ${rate}%`}</span>`, { className: 'commune-tooltip', sticky: true });
          layer.on({
            mouseover: (event: any) => event.target.setStyle({ weight: 2, fillOpacity: 0.9 }),
            mouseout: (event: any) => geoLayer.resetStyle(event.target),
            click: () => {
              selectItem(item);
            },
          });
        },
      }).addTo(map);

      layerRef.current = geoLayer;
      const bounds = geoLayer.getBounds();
      window.setTimeout(() => map.fitBounds(bounds, { padding: [28, 28] }), 0);
      map.setMaxBounds(bounds.pad(0.04));
      setFeatures(info.sort((a, b) => b.risk.localeCompare(a.risk) || a.name.localeCompare(b.name, 'vi')));
      window.setTimeout(() => map.invalidateSize(), 0);
    }).catch((error) => setMapError(error instanceof Error ? error.message : 'Không thể khởi tạo bản đồ'));

    return () => {
      cancelled = true;
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, [view, emergency, metricsByName, setDetailId]);

  const counts = useMemo(() => ({
    alert: features.filter((item) => item.risk === 'alert').length,
    watch: features.filter((item) => item.risk === 'watch').length,
  }), [features]);

  const visibleFeatures = useMemo(() => {
    const keyword = normalized(query);
    const filtered = activeRisk === 'all' ? features : features.filter((item) => item.risk === activeRisk);
    if (!keyword) return filtered;
    const exact = filtered.filter((item) => normalized(item.name).split(' ').every((token) => token.includes(keyword) || keyword.includes(token)) || normalized(item.name).includes(keyword));
    if (exact.length) return exact;
    return filtered.filter((item) => editDistance(normalized(item.name), keyword) <= 2);
  }, [activeRisk, features, query]);

  const focusProvince = () => {
    if (mapRef.current && layerRef.current) mapRef.current.fitBounds(layerRef.current.getBounds(), { padding: [28, 28] });
  };

  const selectItem = (item: FeatureInfo) => {
    const previous = selected && layersByFid.current.get(selected.fid);
    if (previous) layerRef.current?.resetStyle(previous);
    const layer = layersByFid.current.get(item.fid);
    if (layer) {
      layer.setStyle({ weight: 2.8, color: 'oklch(0.18 0.03 160)', fillOpacity: 0.92 });
      const bounds = layer.getBounds();
      if (!mapRef.current.getBounds().contains(bounds)) mapRef.current.flyToBounds(bounds, { padding: [48, 48], duration: 0.25 });
    }
    setSelected(item);
    window.setTimeout(() => listRows.current.get(item.fid)?.scrollIntoView({ block: 'nearest', behavior: 'smooth' }), 0);
  };

  return (
    <div className="map-screen">
      <section className="map-stage" aria-label="Bản đồ phân vùng rủi ro tỉnh Điện Biên">
        <div id="province-map" />
        <div className="map-toolbar"><MapPinArea size={18} weight="bold" /><strong>45 xã, phường Điện Biên · địa giới 2025</strong><button className="icon-button" onClick={focusProvince} aria-label="Hiển thị toàn tỉnh"><ArrowsOut size={17} /></button></div>
        <div className="map-source">Ranh giới tham chiếu được hợp nhất từ GADM 4.1 theo Nghị quyết 1661/NQ-UBTVQH15, hiệu lực từ 01/07/2025. Màu thể hiện dữ liệu đã xác thực; vùng xám cần được cập nhật.</div>
        {mapError && <div className="empty-state"><Warning size={28} /><p>{mapError}</p></div>}
      </section>

      <aside className="map-panel">
        <div className="panel-section">
          <span className="panel-kicker">{emergency ? 'Phiên mô phỏng khẩn cấp' : 'Giám sát thường trực'}</span>
          <h2 className="panel-title">{selected?.name || 'Toàn tỉnh Điện Biên'}</h2>
          <div className="risk-summary">
            <div className="risk-metric"><span className="metric-label">Cảnh báo</span><strong className="metric-value mono">{counts.alert}</strong></div>
            <div className="risk-metric"><span className="metric-label">Theo dõi</span><strong className="metric-value mono">{counts.watch}</strong></div>
          </div>
          <div className="legend-list">
            <div className="legend-row"><span className="legend-swatch" style={{ background: fill.safe }} /><span>An toàn</span><span>Ổn định</span></div>
            <div className="legend-row"><span className="legend-swatch" style={{ background: fill.watch }} /><span>Theo dõi</span><span>Cần quan sát</span></div>
            <div className="legend-row"><span className="legend-swatch" style={{ background: fill.alert }} /><span>Cảnh báo</span><span>Ưu tiên xử lý</span></div>
            <div className="legend-row"><span className="legend-swatch" style={{ background: fill.unverified }} /><span>Chưa xác thực</span><span>Chưa đủ dữ liệu</span></div>
          </div>
          {selected?.linkedId != null && <button className="secondary-button" style={{ marginTop: 16 }} onClick={() => setDetailId(selected.linkedId!)}>Xem chi tiết</button>}
        </div>
        <div className="panel-section"><span className="panel-kicker">Địa bàn</span><input className="commune-search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="VD: Điện Biên Phủ" aria-label="Tìm kiếm xã, phường" /><div className="map-filter-row">{(['all', 'alert', 'watch', 'safe', 'unverified'] as const).map((risk) => <button key={risk} className={activeRisk === risk ? 'active' : ''} onClick={() => setActiveRisk(risk)}>{risk === 'all' ? 'Tất cả' : risk === 'alert' ? 'Cảnh báo' : risk === 'watch' ? 'Theo dõi' : risk === 'safe' ? 'An toàn' : 'Chưa xác thực'}</button>)}</div></div>
        <div className="commune-list">
          {visibleFeatures.map((item) => (
            <button key={item.fid} ref={(node) => { if (node) listRows.current.set(item.fid, node); }} className={`commune-row ${selected?.fid === item.fid ? 'selected' : ''}`} onClick={() => selectItem(item)}>
              <div><strong>{item.name}</strong><span>{item.district}</span></div>
              <div className="commune-rate mono">{item.rate === null ? '—' : `${item.rate}%`}<span>{item.risk === 'alert' ? 'Cảnh báo' : item.risk === 'watch' ? 'Theo dõi' : item.risk === 'safe' ? 'An toàn' : 'Chưa xác thực'}</span></div>
            </button>
          ))}
        </div>
      </aside>
    </div>
  );
}
