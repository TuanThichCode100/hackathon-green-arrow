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

type Risk = 'safe' | 'watch' | 'alert';
type FeatureInfo = { fid: number; name: string; district: string; risk: Risk; rate: number; linkedId?: string | number };

const fill: Record<Risk, string> = {
  safe: 'oklch(0.72 0.105 154)',
  watch: 'oklch(0.79 0.12 78)',
  alert: 'oklch(0.64 0.16 28)',
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

export default function MapView({ m, emergency, setDetailId, view }: Props) {
  const mapRef = useRef<any>(null);
  const layerRef = useRef<any>(null);
  const [selected, setSelected] = useState<FeatureInfo | null>(null);
  const [features, setFeatures] = useState<FeatureInfo[]>([]);
  const [mapError, setMapError] = useState<string | null>(null);

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
        minZoom: 8,
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
          const risk: Risk = emergency ? (fid % 9 < 2 ? 'alert' : fid % 3 === 0 ? 'watch' : 'safe') : 'safe';
          return { color: 'oklch(0.28 0.025 160)', weight: 0.8, opacity: 0.72, fillColor: fill[risk], fillOpacity: selected?.fid === fid ? 0.95 : 0.72 };
        },
        onEachFeature: (feature: any, layer: any) => {
          const fid = Number(feature?.properties?.FID || 0);
          const name = repairText(feature?.properties?.name || feature?.properties?.NAME_3) || `Địa bàn ${fid}`;
          const unitType = repairText(feature?.properties?.unit_type || feature?.properties?.TYPE_3).toLowerCase();
          const district = `${unitType || 'đơn vị'} mới từ 01/07/2025`;
          const linked = metricsByName.get(normalized(name));
          const risk: Risk = emergency ? (fid % 9 < 2 ? 'alert' : fid % 3 === 0 ? 'watch' : 'safe') : 'safe';
          const rate = linked ? Number.parseInt(linked.rateStr, 10) : emergency ? 61 + (fid % 36) : 94 + (fid % 6);
          const item = { fid, name, district, risk, rate, linkedId: linked?.id };
          info.push(item);
          layer.bindTooltip(`<strong>${name}</strong><br><span>${district}</span><br><span>Tiếp cận: ${rate}%</span>`, { className: 'commune-tooltip', sticky: true });
          layer.on({
            mouseover: (event: any) => event.target.setStyle({ weight: 2, fillOpacity: 0.9 }),
            mouseout: (event: any) => geoLayer.resetStyle(event.target),
            click: () => {
              setSelected(item);
              if (item.linkedId != null) setDetailId(item.linkedId);
            },
          });
        },
      }).addTo(map);

      layerRef.current = geoLayer;
      const bounds = geoLayer.getBounds();
      map.fitBounds(bounds, { padding: [28, 28] });
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

  const focusProvince = () => {
    if (mapRef.current && layerRef.current) mapRef.current.fitBounds(layerRef.current.getBounds(), { padding: [28, 28] });
  };

  return (
    <div className="map-screen">
      <section className="map-stage" aria-label="Bản đồ phân vùng rủi ro tỉnh Điện Biên">
        <div id="province-map" />
        <div className="map-toolbar"><MapPinArea size={18} weight="bold" /><strong>45 xã, phường Điện Biên · địa giới 2025</strong><button className="icon-button" onClick={focusProvince} aria-label="Hiển thị toàn tỉnh"><ArrowsOut size={17} /></button></div>
        <div className="map-source">Ranh giới tham chiếu được hợp nhất từ GADM 4.1 theo Nghị quyết 1661/NQ-UBTVQH15, hiệu lực từ 01/07/2025. Màu rủi ro hiện là dữ liệu mô phỏng, không phải cảnh báo chính thức.</div>
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
          </div>
        </div>
        <div className="panel-section"><span className="panel-kicker">Địa bàn ưu tiên</span></div>
        <div className="commune-list">
          {features.slice(0, 24).map((item) => (
            <button key={item.fid} className={`commune-row ${selected?.fid === item.fid ? 'selected' : ''}`} onClick={() => { setSelected(item); if (item.linkedId != null) setDetailId(item.linkedId); }}>
              <div><strong>{item.name}</strong><span>{item.district}</span></div>
              <div className="commune-rate mono">{item.rate}%<span>{item.risk === 'alert' ? 'Cảnh báo' : item.risk === 'watch' ? 'Theo dõi' : 'An toàn'}</span></div>
            </button>
          ))}
        </div>
      </aside>
    </div>
  );
}
