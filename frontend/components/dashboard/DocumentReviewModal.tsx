'use client';

import { useEffect, useState } from 'react';
import { CheckCircle, X } from '@phosphor-icons/react';
import { API_BASE_URL } from '@/lib/api';

const emptyDraft = { document_number: '', title: '', doc_type: '', issued_by: '', issued_date: '', start_date: '', end_date: '', llm_summary: '', required_actions: '', urgency: '', scope_type: 'province', commune_ids: [], show_original_to_province: false };

export default function DocumentReviewModal({ documentId, onClose, onDone, communes }: { documentId: number; onClose: () => void; onDone: () => void; communes: Array<{ id: number; name: string }> }) {
  const [draft, setDraft] = useState<any>(emptyDraft);
  const [evidence, setEvidence] = useState<any>({});
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
  const headers = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  useEffect(() => { fetch(`${API_BASE_URL}/api/documents/${documentId}/preview`, { headers: token ? { Authorization: `Bearer ${token}` } : {} }).then(async (res) => { const body = await res.json(); if (!res.ok) throw new Error(body.detail); setDraft({ ...emptyDraft, ...body.data.draft }); setEvidence(body.data.evidence || {}); }).catch((err) => setError(err.message)); }, [documentId]);
  const set = (key, value) => setDraft((current) => ({ ...current, [key]: value }));
  const save = async (approve = false) => { setSaving(true); setError(''); try { const res = await fetch(`${API_BASE_URL}/api/documents/${documentId}/${approve ? 'approve' : 'preview'}`, { method: approve ? 'POST' : 'PUT', headers, body: JSON.stringify(draft) }); const body = await res.json(); if (!res.ok) throw new Error(body.detail || 'Không thể lưu bản xem trước'); if (approve) onDone(); else setEvidence(body.data.evidence || evidence); } catch (err) { setError(err instanceof Error ? err.message : 'Không thể lưu'); } finally { setSaving(false); } };
  const cancel = async () => { if (!confirm('Thoát và không lưu bản nháp này?')) return; await fetch(`${API_BASE_URL}/api/documents/${documentId}/cancel`, { method: 'POST', headers: token ? { Authorization: `Bearer ${token}` } : {} }); onDone(); };
  const source = (key) => evidence[key] ? <small className="document-evidence">Nguồn: trang {evidence[key].page}, “{evidence[key].quote}”</small> : null;
  return <div className="review-backdrop" role="presentation"><section className="document-review" role="dialog" aria-modal="true" aria-labelledby="review-title"><header className="document-review-header"><div><p className="eyebrow">Bản nháp cần xác nhận</p><h2 id="review-title">Kiểm tra thông tin văn bản</h2></div><button className="icon-button" onClick={cancel} aria-label="Thoát và không lưu"><X size={18} /></button></header><div className="document-review-body">
    {error && <p className="form-error" role="alert">{error}</p>}
    <div className="review-grid">
      <label>Số/ký hiệu<input value={draft.document_number || ''} onChange={(e) => set('document_number', e.target.value)} />{source('document_number')}</label>
      <label>Loại văn bản<input value={draft.doc_type || ''} onChange={(e) => set('doc_type', e.target.value)} />{source('doc_type')}</label>
      <label className="review-wide">Tiêu đề<input value={draft.title || ''} onChange={(e) => set('title', e.target.value)} />{source('title')}</label>
      <label>Cơ quan ban hành<input value={draft.issued_by || ''} onChange={(e) => set('issued_by', e.target.value)} />{source('issued_by')}</label>
      <label>Ngày ban hành<input type="date" value={draft.issued_date || ''} onChange={(e) => set('issued_date', e.target.value)} />{source('issued_date')}</label>
      <label>Hiệu lực từ<input type="date" value={draft.start_date || ''} onChange={(e) => set('start_date', e.target.value)} /></label><label>Hết hiệu lực<input type="date" value={draft.end_date || ''} onChange={(e) => set('end_date', e.target.value)} /></label>
      <label>Mức độ khẩn<input value={draft.urgency || ''} placeholder="Ví dụ: Khẩn" onChange={(e) => set('urgency', e.target.value)} /></label>
      <label className="review-wide">Tóm tắt chỉ đạo<textarea value={draft.llm_summary || ''} onChange={(e) => set('llm_summary', e.target.value)} /></label>
      <label className="review-wide">Hành động yêu cầu<textarea value={draft.required_actions || ''} onChange={(e) => set('required_actions', e.target.value)} /></label>
    </div>
    <fieldset className="scope-picker"><legend>Địa bàn áp dụng</legend><label><input type="radio" checked={draft.scope_type === 'province'} onChange={() => set('scope_type', 'province')} /> Toàn tỉnh</label><label><input type="radio" checked={draft.scope_type === 'communes'} onChange={() => set('scope_type', 'communes')} /> Các xã/phường cụ thể</label>{draft.scope_type === 'communes' && <div className="commune-checks">{communes.map((commune) => <label key={commune.id}><input type="checkbox" checked={draft.commune_ids.includes(commune.id)} onChange={() => set('commune_ids', draft.commune_ids.includes(commune.id) ? draft.commune_ids.filter((id) => id !== commune.id) : [...draft.commune_ids, commune.id])} /> {commune.name}</label>)}</div>}</fieldset>
    <label className="original-toggle"><input type="checkbox" checked={draft.show_original_to_province} onChange={(e) => set('show_original_to_province', e.target.checked)} /> Hiển thị bản gốc của tài liệu cho cán bộ tỉnh</label>
  </div><footer className="document-review-footer"><button className="secondary-button" disabled={saving} onClick={() => save(false)}>Lưu bản nháp</button><button className="primary-button" disabled={saving} onClick={() => save(true)}><CheckCircle size={17} />{saving ? 'Đang lưu…' : 'Xác nhận văn bản'}</button></footer></section></div>;
}
