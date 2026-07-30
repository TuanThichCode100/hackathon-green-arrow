'use client';

import { useEffect, useState } from 'react';
import { Eye, FileText, Spinner, X } from '@phosphor-icons/react';
import { API_BASE_URL } from '@/lib/api';

type DocumentData = { id: number; document_number?: string; code: string; title: string; doc_type?: string; issued_by?: string; issued_date?: string; start_date?: string; end_date?: string; scope_type?: string; commune_ids?: number[]; llm_summary?: string; required_actions?: string; urgency?: string; original_filename?: string };
type Access = { permitted: boolean; request_status?: 'pending' | 'approved' | 'rejected' | null; view_expires_at?: string | null };

export default function DocumentDetailModal({ documentId, communes, onClose }: { documentId: number; communes: Array<{ id: number; name: string }>; onClose: () => void }) {
  const [document, setDocument] = useState<DocumentData | null>(null);
  const [access, setAccess] = useState<Access | null>(null);
  const [pdfUrl, setPdfUrl] = useState('');
  const [loadError, setLoadError] = useState('');
  const [requestState, setRequestState] = useState<'idle' | 'sending' | 'pending' | 'failed'>('idle');
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
  const authHeaders = token ? { Authorization: `Bearer ${token}` } : {};

  const load = async () => {
    try {
      const [documentResponse, accessResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/api/documents/${documentId}`, { headers: authHeaders }),
        fetch(`${API_BASE_URL}/api/documents/${documentId}/view-access`, { headers: authHeaders }),
      ]);
      const documentBody = await documentResponse.json();
      const accessBody = await accessResponse.json();
      if (!documentResponse.ok || !accessResponse.ok) throw new Error(documentBody.detail || accessBody.detail || 'Không thể tải văn bản.');
      setDocument(documentBody.data);
      setAccess(accessBody.data);
      setRequestState(accessBody.data.request_status === 'pending' ? 'pending' : 'idle');
      if (accessBody.data.permitted) {
        const displayResponse = await fetch(`${API_BASE_URL}/api/documents/${documentId}/display`, { headers: authHeaders });
        if (!displayResponse.ok) throw new Error('Không thể mở bản hiển thị của văn bản.');
        const blob = await displayResponse.blob();
        setPdfUrl(URL.createObjectURL(blob));
      }
    } catch (reason) {
      setLoadError(reason instanceof Error ? reason.message : 'Không thể tải văn bản.');
    }
  };

  useEffect(() => {
    load();
    return () => { if (pdfUrl) URL.revokeObjectURL(pdfUrl); };
    // Blob URLs are intentionally replaced only after a new access check.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [documentId]);

  const requestView = async () => {
    setRequestState('sending');
    try {
      const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}/view-requests`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', ...authHeaders },
        body: JSON.stringify({ reason: 'Đề nghị xem bản gốc để phục vụ công việc.' }),
      });
      if (!response.ok) throw new Error();
      setRequestState('pending');
    } catch {
      setRequestState('failed');
      window.setTimeout(() => setRequestState('idle'), 5000);
    }
  };

  const locality = document?.scope_type === 'communes'
    ? (document.commune_ids || []).map((id) => communes.find((commune) => commune.id === id)?.name || `Địa bàn #${id}`).join(', ') || 'Chưa xác định'
    : 'Toàn tỉnh';

  return <div className="review-backdrop" role="presentation"><section className="document-detail" role="dialog" aria-modal="true" aria-labelledby="document-detail-title"><header className="document-review-header"><div><p className="eyebrow">Văn bản chỉ đạo</p><h2 id="document-detail-title">{document?.document_number || document?.code || 'Đang tải văn bản'}</h2></div><button className="icon-button" onClick={onClose} aria-label="Đóng"><X size={18} /></button></header><div className="document-detail-body">
    <section className="document-original-pane" aria-label="Bản gốc văn bản">
      {pdfUrl ? <iframe title="Bản hiển thị văn bản" src={pdfUrl} className="document-pdf-frame" /> : <div className="original-request-card">{loadError ? <p className="form-error">{loadError}</p> : requestState === 'sending' ? <><Spinner size={24} className="spin" /><strong>Đang gửi yêu cầu</strong></> : requestState === 'pending' ? <><Eye size={24} /><strong>Đang chờ duyệt</strong><span>Yêu cầu xem bản gốc đã được gửi.</span></> : requestState === 'failed' ? <><strong>Gửi yêu cầu thất bại</strong><span>Vui lòng thử lại.</span></> : <><FileText size={28} /><strong>Bấm vào đây để gửi yêu cầu xem bản gốc</strong><span>Bản gốc chỉ hiển thị khi được cấp quyền.</span><button className="primary-button" onClick={requestView}>Gửi yêu cầu</button></>}</div>}
    </section>
    <section className="document-metadata-pane">
      {document ? <><h3>{document.title}</h3><dl className="document-metadata"><div><dt>Loại văn bản</dt><dd>{document.doc_type || 'Chưa xác định'}</dd></div><div><dt>Cơ quan ban hành</dt><dd>{document.issued_by || 'Chưa xác định'}</dd></div><div><dt>Ngày ban hành</dt><dd>{document.issued_date || 'Chưa xác định'}</dd></div><div><dt>Hiệu lực</dt><dd>{document.start_date || 'Chưa xác định'}{document.end_date ? ` – ${document.end_date}` : ''}</dd></div><div><dt>Địa bàn áp dụng</dt><dd>{locality}</dd></div><div><dt>Mức độ khẩn</dt><dd>{document.urgency || 'Không xác định'}</dd></div></dl><div className="document-detail-copy"><h4>Tóm tắt chỉ đạo</h4><p>{document.llm_summary || 'Chưa có thông tin tóm tắt.'}</p><h4>Việc cần thực hiện</h4><p>{document.required_actions || 'Chưa có thông tin.'}</p></div></> : <div className="empty-state"><Spinner size={28} className="spin" /><p>Đang tải thông tin văn bản…</p></div>}
    </section>
  </div></section></div>;
}
