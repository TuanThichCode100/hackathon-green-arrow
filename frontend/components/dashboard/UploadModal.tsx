import { FileArrowUp, X } from '@phosphor-icons/react';

export default function UploadModal({ setUploadOpen, showToast }: { setUploadOpen: (open: boolean) => void; showToast: (message: string, icon?: string) => void }) {
  return (
    <>
      <button className="slideover-backdrop" aria-label="Đóng" onClick={() => setUploadOpen(false)} />
      <aside className="slideover" role="dialog" aria-modal="true" aria-labelledby="upload-title">
        <header className="slideover-header">
          <div><p className="eyebrow">Kho ngữ cảnh</p><h2 id="upload-title" style={{ margin: 0 }}>Thêm văn bản chỉ đạo</h2></div>
          <button className="icon-button" onClick={() => setUploadOpen(false)} aria-label="Đóng"><X size={18} /></button>
        </header>
        <div className="slideover-body">
          <label className="data-section" style={{ display: 'grid', placeItems: 'center', minHeight: 190, cursor: 'pointer', textAlign: 'center', padding: 24 }}>
            <FileArrowUp size={30} />
            <strong>Chọn PDF, Word hoặc Text</strong>
            <span className="metric-label">Tối đa 20 MB. Tính năng tải thật cần endpoint document upload.</span>
            <input className="sr-only" type="file" accept=".pdf,.doc,.docx,.txt" />
          </label>
          <div style={{ display: 'grid', gap: 14, marginTop: 20 }}>
            <label><span className="metric-label">Ngày bắt đầu hiệu lực</span><input type="date" style={{ width: '100%', height: 40, marginTop: 6, border: '1px solid var(--line)', borderRadius: 10, padding: '0 10px' }} /></label>
            <label><span className="metric-label">Ngày kết thúc hiệu lực</span><input type="date" style={{ width: '100%', height: 40, marginTop: 6, border: '1px solid var(--line)', borderRadius: 10, padding: '0 10px' }} /></label>
          </div>
          <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end', marginTop: 24 }}>
            <button className="secondary-button" onClick={() => setUploadOpen(false)}>Hủy</button>
            <button className="primary-button" onClick={() => { setUploadOpen(false); showToast('Đã ghi nhận văn bản ở chế độ mô phỏng.'); }}>Ghi nhận</button>
          </div>
        </div>
      </aside>
    </>
  );
}
