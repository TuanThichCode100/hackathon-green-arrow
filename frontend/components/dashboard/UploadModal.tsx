import { useState } from 'react';
import { FileArrowUp, X, Spinner } from '@phosphor-icons/react';
import { API_BASE_URL } from '@/lib/api';

export default function UploadModal({ setUploadOpen, showToast }: { setUploadOpen: (open: boolean) => void; showToast: (message: string, icon?: string) => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [isUploading, setIsUploading] = useState(false);

  const handleUpload = async () => {
    if (!file || !title || !startDate || !endDate) {
      showToast('Vui lòng điền đủ thông tin và chọn file', 'warning');
      return;
    }
    
    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', title);
      formData.append('doc_type', 'Chỉ đạo');
      formData.append('issued_by', 'UBND Tỉnh');
      formData.append('start_date', startDate);
      formData.append('end_date', endDate);

      const token = window.localStorage.getItem('auth_token');
      const res = await fetch(`${API_BASE_URL}/api/documents/upload`, {
        method: 'POST',
        headers: {
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: formData,
      });

      if (!res.ok) throw new Error('Upload failed');
      
      showToast('Tải văn bản lên thành công và đã được mã hóa!');
      setUploadOpen(false);
      // Optional: reload window or mutate to fetch new docs
      setTimeout(() => window.location.reload(), 1500);
    } catch (err) {
      console.error(err);
      showToast('Lỗi khi tải văn bản lên. Vui lòng thử lại.', 'error');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <>
      <button className="slideover-backdrop" aria-label="Đóng" onClick={() => setUploadOpen(false)} />
      <aside className="slideover" role="dialog" aria-modal="true" aria-labelledby="upload-title">
        <header className="slideover-header">
          <div><p className="eyebrow">Kho ngữ cảnh</p><h2 id="upload-title" style={{ margin: 0 }}>Thêm văn bản chỉ đạo</h2></div>
          <button className="icon-button" onClick={() => setUploadOpen(false)} aria-label="Đóng"><X size={18} /></button>
        </header>
        <div className="slideover-body">
          <label className="data-section" style={{ display: 'grid', placeItems: 'center', minHeight: 120, cursor: 'pointer', textAlign: 'center', padding: 24, border: file ? '2px solid var(--ink)' : '2px dashed var(--border)', borderRadius: 12 }}>
            <FileArrowUp size={30} color={file ? 'var(--ink)' : 'var(--ink-muted)'} />
            <strong style={{ marginTop: 8 }}>{file ? file.name : 'Chọn PDF, Word hoặc Text'}</strong>
            <span className="metric-label" style={{ marginTop: 4 }}>Tối đa 20 MB. Dữ liệu sẽ được mã hóa AES-256.</span>
            <input className="sr-only" type="file" accept=".pdf,.doc,.docx,.txt" onChange={(e) => {
              if (e.target.files && e.target.files[0]) {
                setFile(e.target.files[0]);
                if (!title) setTitle(e.target.files[0].name.split('.')[0]);
              }
            }} />
          </label>
          <div style={{ display: 'grid', gap: 14, marginTop: 20 }}>
            <label>
              <span className="metric-label">Tên / Tiêu đề văn bản</span>
              <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Nhập tên văn bản..." style={{ width: '100%', height: 40, marginTop: 6, border: '1px solid var(--line)', borderRadius: 10, padding: '0 10px' }} />
            </label>
            <label>
              <span className="metric-label">Ngày bắt đầu hiệu lực</span>
              <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} style={{ width: '100%', height: 40, marginTop: 6, border: '1px solid var(--line)', borderRadius: 10, padding: '0 10px' }} />
            </label>
            <label>
              <span className="metric-label">Ngày kết thúc hiệu lực</span>
              <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} style={{ width: '100%', height: 40, marginTop: 6, border: '1px solid var(--line)', borderRadius: 10, padding: '0 10px' }} />
            </label>
          </div>
          <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end', marginTop: 24 }}>
            <button className="secondary-button" onClick={() => setUploadOpen(false)} disabled={isUploading}>Hủy</button>
            <button className="primary-button" onClick={handleUpload} disabled={isUploading}>
              {isUploading ? <><Spinner size={16} className="spin" /> Đang tải lên...</> : 'Tải lên mã hóa'}
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}
