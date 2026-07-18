import React from 'react';
import { s } from '@/lib/style';

interface UploadModalProps {
  setUploadOpen: (open: boolean) => void;
  showToast: (msg: string, icon?: string) => void;
}

export default function UploadModal({ setUploadOpen, showToast }: UploadModalProps) {
  return (
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
          <div style={s('background:#FFF7E8; border:1px solid #F3DFA8; border-radius:9px; padding:10px 13px; font-size:11px; color:#8A6D2B; margin-bottom:20px;')}>
            Văn bản tải lên sẽ được ưu tiên cao nhất, Agent sẽ tự động điều chỉnh khu vực và thông điệp cảnh báo.
          </div>
          <div style={s('display:flex; justify-content:flex-end; gap:10px;')}>
            <button onClick={() => setUploadOpen(false)} style={s('font-size:13px; font-weight:600; color:#5A6675; background:#EEF2F6; border:none; border-radius:9px; padding:11px 20px; cursor:pointer;')}>Hủy</button>
            <button onClick={() => { setUploadOpen(false); showToast('Đã nạp văn bản vào Vector DB — RAG sẵn sàng override kịch bản AI', '🧠'); }} style={s('font-size:13px; font-weight:700; color:#0F1E2A; background:#25ADE3; border:none; border-radius:9px; padding:11px 22px; cursor:pointer;')}>Nạp vào Vector DB</button>
          </div>
        </div>
      </div>
    </div>
  );
}
