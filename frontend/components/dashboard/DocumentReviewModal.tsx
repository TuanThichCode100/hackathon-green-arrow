'use client';

import { useEffect, useState } from 'react';
import { CheckCircle, FileText, Spinner, X } from '@phosphor-icons/react';
import { API_BASE_URL } from '@/lib/api';

const emptyDraft = { document_number: '', title: '', doc_type: '', issued_by: '', issued_date: '', start_date: '', end_date: '', llm_summary: '', required_actions: '', urgency: '', scope_type: 'province', commune_ids: [] as number[], show_original_to_province: false };
type ReviewStatus = 'processing' | 'ready' | 'failed';

export default function DocumentReviewModal({ documentId, onClose, onDone, communes }: { documentId: number; onClose: () => void; onDone: () => void; communes: Array<{ id: number; name: string }> }) {
  const [draft, setDraft] = useState<any>(emptyDraft);
  const [evidence, setEvidence] = useState<any>({});
  const [aiMessage, setAiMessage] = useState('');
  const [previewPdfUrl, setPreviewPdfUrl] = useState('');
  const [error, setError] = useState('');
  const [saveAction, setSaveAction] = useState<'draft' | 'approve' | null>(null);
  const [success, setSuccess] = useState('');
  const [reviewStatus, setReviewStatus] = useState<ReviewStatus>('processing');
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
  const headers = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const loadPreview = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}/preview`, { headers: token ? { Authorization: `Bearer ${token}` } : {} });
        const body = await response.json();
        if (response.status === 202) { if (!cancelled) { setReviewStatus('processing'); timer = setTimeout(loadPreview, 2000); } return; }
        if (!response.ok) throw new Error(body.detail || 'Không thể tạo bản xem trước.');
        if (!cancelled) { setDraft({ ...emptyDraft, ...body.data.draft }); setEvidence(body.data.evidence || {}); setAiMessage(body.data.ai_analysis?.message || ''); setReviewStatus('ready'); }
      } catch (reason) { if (!cancelled) { setReviewStatus('failed'); setError(reason instanceof Error ? reason.message : 'Không thể tạo bản xem trước.'); } }
    };
    loadPreview();
    return () => { cancelled = true; if (timer) clearTimeout(timer); };
  }, [documentId, token]);

  useEffect(() => {
    if (reviewStatus !== 'ready') return;
    let objectUrl = '';
    fetch(`${API_BASE_URL}/api/documents/${documentId}/preview-display`, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
      .then(async (response) => { if (!response.ok) throw new Error(); return response.blob(); })
      .then((blob) => { objectUrl = URL.createObjectURL(blob); setPreviewPdfUrl(objectUrl); })
      .catch(() => setPreviewPdfUrl(''));
    return () => { if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [documentId, reviewStatus, token]);

  const set = (key: string, value: any) => setDraft((current: any) => ({ ...current, [key]: value }));
  const save = async (approve = false) => {
    setSuccess('');
    if (approve && !draft.start_date) {
      setError('Cần xác nhận Hiệu lực từ ngày trước khi xác nhận văn bản.');
      document.getElementById('effective-start-date')?.focus();
      return;
    }
    const action = approve ? 'approve' : 'draft';
    setSaveAction(action); setError('');
    try { const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}/${approve ? 'approve' : 'preview'}`, { method: approve ? 'POST' : 'PUT', headers, body: JSON.stringify(draft) }); const body = await response.json(); if (!response.ok) throw new Error(body.detail || 'Không thể lưu bản xem trước.'); if (approve) onDone(); else { setEvidence(body.data.evidence || evidence); setSuccess('Đã lưu bản nháp. Bạn có thể tiếp tục chỉnh sửa hoặc xác nhận văn bản.'); } } catch (reason) { setError(reason instanceof Error ? reason.message : 'Không thể lưu thông tin.'); } finally { setSaveAction(null); }
  };
  const cancel = async () => { if (!confirm('Thoát và không lưu bản nháp này?')) return; await fetch(`${API_BASE_URL}/api/documents/${documentId}/cancel`, { method: 'POST', headers: token ? { Authorization: `Bearer ${token}` } : {} }); onClose(); };
  const source = (key: string) => evidence[key] ? <small className="document-evidence">Nguồn: trang {evidence[key].page}, “{evidence[key].quote}”</small> : null;

  return <div className="review-backdrop" role="presentation"><section className="document-review document-review-wide" role="dialog" aria-modal="true" aria-labelledby="review-title"><header className="document-review-header"><div><p className="eyebrow">Bản nháp cần xác nhận</p><h2 id="review-title">Kiểm tra thông tin văn bản</h2></div><button className="icon-button" onClick={cancel} aria-label="Thoát và không lưu"><X size={18} /></button></header><div className="document-review-body">
    {reviewStatus === 'processing' && <div className="empty-state" role="status"><Spinner size={28} className="spin" /><p>Hệ thống đang trích xuất thông tin từ văn bản…</p><small>Trang này sẽ tự động hiển thị bản xem trước khi hoàn tất.</small></div>}
    {error && <p className="form-error" role="alert">{error}</p>}{success && <p className="form-success" role="status">{success}</p>}
    {reviewStatus === 'ready' && <div className="review-split"><section className="review-source-pane">{previewPdfUrl ? <iframe title="Bản hiển thị tệp đã tải lên" className="document-pdf-frame" src={previewPdfUrl} /> : <div className="original-request-card"><FileText size={28} /><strong>Đang chuẩn bị bản hiển thị của tệp</strong></div>}</section><section className="review-form-pane">{aiMessage && <p className="form-error" role="status">{aiMessage}</p>}<div className="review-grid">
      <label>Số/ký hiệu<input value={draft.document_number || ''} onChange={(event) => set('document_number', event.target.value)} />{source('document_number')}</label><label>Loại văn bản<input value={draft.doc_type || ''} onChange={(event) => set('doc_type', event.target.value)} />{source('doc_type')}</label><label className="review-wide">Tiêu đề<input value={draft.title || ''} onChange={(event) => set('title', event.target.value)} />{source('title')}</label><label>Cơ quan ban hành<input value={draft.issued_by || ''} onChange={(event) => set('issued_by', event.target.value)} />{source('issued_by')}</label><label>Ngày ban hành<input type="date" value={draft.issued_date || ''} onChange={(event) => set('issued_date', event.target.value)} />{source('issued_date')}</label><label>Hiệu lực từ *<input id="effective-start-date" required aria-invalid={!draft.start_date} type="date" value={draft.start_date || ''} onChange={(event) => { set('start_date', event.target.value); if (event.target.value) setError(''); }} />{!draft.start_date && <small className="field-hint">Cần nhập trước khi xác nhận văn bản.</small>}</label><label>Hết hiệu lực<input type="date" value={draft.end_date || ''} onChange={(event) => set('end_date', event.target.value)} /></label><label>Mức độ khẩn<input value={draft.urgency || ''} placeholder="Ví dụ: Khẩn" onChange={(event) => set('urgency', event.target.value)} /></label><label className="review-wide">Tóm tắt chỉ đạo<textarea value={draft.llm_summary || ''} placeholder="Nội dung tóm tắt để cán bộ kiểm tra và bổ sung." onChange={(event) => set('llm_summary', event.target.value)} /></label><label className="review-wide">Hành động yêu cầu<textarea value={draft.required_actions || ''} placeholder="Các việc cần thực hiện; cán bộ có thể bổ sung trực tiếp." onChange={(event) => set('required_actions', event.target.value)} /></label>
    </div><fieldset className="scope-picker"><legend>Địa bàn áp dụng</legend><label><input type="radio" checked={draft.scope_type === 'province'} onChange={() => set('scope_type', 'province')} /> Toàn tỉnh</label><label><input type="radio" checked={draft.scope_type === 'communes'} onChange={() => set('scope_type', 'communes')} /> Các xã/phường cụ thể</label>{draft.scope_type === 'communes' && <div className="commune-checks">{communes.map((commune) => <label key={commune.id}><input type="checkbox" checked={draft.commune_ids.includes(commune.id)} onChange={() => set('commune_ids', draft.commune_ids.includes(commune.id) ? draft.commune_ids.filter((id: number) => id !== commune.id) : [...draft.commune_ids, commune.id])} /> {commune.name}</label>)}</div>}</fieldset><label className="original-toggle"><input type="checkbox" checked={draft.show_original_to_province} onChange={(event) => set('show_original_to_province', event.target.checked)} /> Hiển thị bản gốc của tài liệu cho cán bộ tỉnh</label></section></div>}
  </div>{reviewStatus === 'ready' && <footer className="document-review-footer"><button className="secondary-button" disabled={saveAction !== null} onClick={() => save(false)}>{saveAction === 'draft' ? 'Đang lưu bản nháp…' : 'Lưu bản nháp'}</button><button className="primary-button" disabled={saveAction !== null} onClick={() => save(true)}><CheckCircle size={17} />{saveAction === 'approve' ? 'Đang xác nhận…' : 'Xác nhận văn bản'}</button></footer>}</section></div>;
}
