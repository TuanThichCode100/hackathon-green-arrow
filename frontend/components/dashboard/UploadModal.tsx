import { useState } from 'react';
import { FileArrowUp, X, Spinner } from '@phosphor-icons/react';
import { API_BASE_URL } from '@/lib/api';

export default function UploadModal({ setUploadOpen, showToast, onUploaded }: { setUploadOpen: (open: boolean) => void; showToast: (message: string, icon?: string) => void; onUploaded: (documentId: number) => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const handleUpload = async () => {
    if (!file) return showToast('Chọn một tệp để tiếp tục.', 'warning');
    if (file.size > 20 * 1024 * 1024) return showToast('Tệp vượt quá giới hạn 20 MB.', 'error');
    setIsUploading(true);
    try {
      const formData = new FormData(); formData.append('file', file);
      const token = window.localStorage.getItem('auth_token');
      const res = await fetch(`${API_BASE_URL}/api/documents/upload`, { method: 'POST', headers: token ? { Authorization: `Bearer ${token}` } : {}, body: formData });
      const body = await res.json(); if (!res.ok) throw new Error(body.detail || 'Không thể tải văn bản lên');
      showToast('Đã nhận tệp. Hệ thống đang đọc và tạo bản xem trước.'); setUploadOpen(false); onUploaded(body.data.id);
    } catch (err) { showToast(err instanceof Error ? err.message : 'Không thể tải văn bản lên.', 'error'); } finally { setIsUploading(false); }
  };
  return <><button className="slideover-backdrop" aria-label="Đóng" onClick={() => setUploadOpen(false)} /><aside className="slideover" role="dialog" aria-modal="true" aria-labelledby="upload-title"><header className="slideover-header"><div><p className="eyebrow">Kho văn bản</p><h2 id="upload-title" style={{ margin: 0 }}>Thêm văn bản chỉ đạo</h2></div><button className="icon-button" onClick={() => setUploadOpen(false)} aria-label="Đóng"><X size={18} /></button></header><div className="slideover-body"><label className="data-section" style={{ display: 'grid', placeItems: 'center', minHeight: 160, cursor: 'pointer', textAlign: 'center', padding: 24, border: file ? '2px solid var(--accent)' : '2px dashed var(--line)', borderRadius: 12 }}><FileArrowUp size={30} color={file ? 'var(--accent)' : 'var(--ink-muted)'} /><strong style={{ marginTop: 8 }}>{file ? file.name : 'Chọn văn bản để phân tích'}</strong><span className="metric-label" style={{ marginTop: 4 }}>PDF, DOCX, TXT, JPG hoặc PNG · tối đa 20 MB</span><input className="sr-only" type="file" accept=".pdf,.docx,.txt,.jpg,.jpeg,.png" onChange={(e) => setFile(e.target.files?.[0] || null)} /></label><p className="metric-label" style={{ marginTop: 18 }}>Tệp được mã hóa. Thông tin chỉ được đưa vào hệ thống sau khi bạn xem và xác nhận bản trích xuất.</p><div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end', marginTop: 24 }}><button className="secondary-button" onClick={() => setUploadOpen(false)} disabled={isUploading}>Hủy</button><button className="primary-button" onClick={handleUpload} disabled={isUploading}>{isUploading ? <><Spinner size={16} className="spin" />Đang xử lý…</> : 'Tải lên và phân tích'}</button></div></div></aside></>;
}
