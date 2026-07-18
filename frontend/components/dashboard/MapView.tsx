import React, { useEffect, useRef } from 'react';
import { s } from '@/lib/style';
import { KpiCard, Legend } from './Shared';
import { DashboardData } from './types';
import { statusOf } from '@/lib/data';

interface MapViewProps {
  m: DashboardData;
  emergency: boolean;
  setDetailId: (id: string | number) => void;
  view: string;
}

export default function MapView({ m, emergency, setDetailId, view }: MapViewProps) {
  const mapRef = useRef<any>(null);
  const layerRef = useRef<any>(null);
  const [mapReady, setMapReady] = React.useState(false);

  // 1. Initialize Map
  useEffect(() => {
    if (view !== 'map') return;
    let isCancelled = false;
    let timeoutId: any = null;

    import('leaflet').then((LModule) => {
      if (isCancelled) return;
      const L = LModule.default;

      if (!mapRef.current) {
        const el = document.getElementById('gf-map') as any;
        if (!el) return;

        if (el._leaflet_id) {
          el._leaflet_id = null;
        }

        const map = L.map(el, { zoomControl: true, attributionControl: false, fadeAnimation: false }).setView([21.55, 103.05], 9);
        mapRef.current = map;
        
        L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', { maxZoom: 18 }).addTo(map);
        
        const layer = L.layerGroup().addTo(map);
        layerRef.current = layer;

        timeoutId = setTimeout(() => { if (!isCancelled && mapRef.current) mapRef.current.invalidateSize(); }, 200);
        
        setMapReady(true);
      }
    });

    return () => {
      isCancelled = true;
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [view]);

  // 2. Stream Data to Map
  useEffect(() => {
    if (view !== 'map' || !mapReady || !layerRef.current) return;
    let isCancelled = false;

    import('leaflet').then((LModule) => {
      if (isCancelled) return;
      const L = LModule.default;
      const layer = layerRef.current;

      layer.clearLayers();

      (m?.communes || []).forEach((c: any) => {
        const st = statusOf(c, emergency);
        const color = st === 'alert' ? '#E23D3D' : st === 'watch' ? '#E8A93B' : '#1E9E6A';
        const rate = emergency ? (c.recvAlert || 0.6) : (c.recvNormal || 0.98); // Fallback for rate in MapView
        
        L.circle([c.lat, c.lng], {
          radius: c.pop > 30000 ? 9000 : c.pop > 12000 ? 7000 : 5500,
          color: '#E23D3D', weight: 1.5, opacity: 0.55, dashArray: '5 5', fillColor: '#E23D3D', fillOpacity: 0.05,
        }).addTo(layer);
        
        const marker = L.circleMarker([c.lat, c.lng], {
          radius: c.pop > 30000 ? 15 : c.pop > 12000 ? 12 : 9,
          fillColor: color, color: '#fff', weight: 2.5, fillOpacity: 0.9,
        }).addTo(layer);
        
        marker.bindTooltip(`<b>${c.name}</b><br>${Math.round(rate * 100)}% đã nhận`, { direction: 'top', offset: [0, -6] });
        marker.on('click', () => setDetailId(c.id));
        
        if (emergency && st === 'alert' && c.lost) {
          c.lost.forEach((lp: any) => {
            L.marker([lp.lat, lp.lng], { icon: L.divIcon({ className: '', html: '<div class="gf-lost-pin"></div>', iconSize: [16, 16], iconAnchor: [8, 8] }) })
              .addTo(layer)
              .bindTooltip(`📍 ${lp.name}<br>Chưa phản hồi`, { direction: 'top', offset: [0, -8] });
          });
        }
      });
    });

    return () => {
      isCancelled = true;
    };
  }, [view, emergency, m?.communes, setDetailId, mapReady]);

  useEffect(() => {
    if (view !== 'map') {
      if (mapRef.current) {
        mapRef.current.off();
        mapRef.current.remove();
        mapRef.current = null;
        layerRef.current = null;
      }
    }
  }, [view]);

  useEffect(() => {
    return () => {
      if (mapRef.current) {
        mapRef.current.off();
        mapRef.current.remove();
        mapRef.current = null;
        layerRef.current = null;
      }
    };
  }, []);

  return (
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
                  <div style={s('font-size:10.5px; color:#8A95A2;')}>{c.popStr} dân</div>
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
  );
}
