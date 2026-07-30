'use client';

import { useEffect, useState } from 'react';
import { ArrowCounterClockwise, Eye, FileText, Spinner, Trash, X } from '@phosphor-icons/react';
import { API_BASE_URL } from '@/lib/api';
import type { User } from './types';

type DocumentData = { id: number; code: string; document_number?: string; title: string; doc_type?: string; issued_by?: string; issued_date?: string; start_date?: string; end_date?: string; scope_type?: string; commune_ids?: number[]; llm_summary?: string; required_actions?: string; urgency?: string; upload_status: string; deleted_at?: string; deleted_by_name?: string };
type Access = { permitted: boolean; request_status?: 'pending' | 'approved' | 'rejected' | null };

export default function DocumentDetailModal({ documentId, communes, user, onClose, onChanged }: { documentId: number; communes: Array<{ id: number; name: string }>; user: User | null; onClose: () => void; onChanged: () => void }) {
  const [document, setDocument] = useState<DocumentData | null>(null);
  const [pdfUrl, setPdfUrl] = useState('');
  const [loadError, setLoadError] = useState('');
  const [requestState, setRequestState] = useState<'idle' | 'sending' | 'pending' | 'failed'>('idle');
  const [acting, setActing] = useState(false);
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
  const authHeaders = token ? { Authorization: `Bearer ${token}` } : {};

  const load = async () => {
    try {
      const documentResponse = await fetch(`${API_BASE_URL}/api/documents/${documentId}`, { headers: authHeaders });
      const documentBody = await documentResponse.json();
      if (!documentResponse.ok) throw new Error(documentBody.detail || 'Không thể tải văn bản.');
      setDocument(documentBody.data);
      if (documentBody.data.upload_status !== 'approved') return;
      const accessResponse = await fetch(`${API_BASE_URL}/api/documents/${documentId}/view-access`, { headers: authHeaders });
      const accessBody = await accessResponse.json();
      if (!accessResponse.ok) throw new Error(accessBody.detail || 'Không thể kiểm tra quyền xem.');
      const access: Access = accessBody.data;
      setRequestState(access.request_status === 'pending' ? 'pending' : 'idle');
      if (access.permitted) {
        const displayResponse = await fetch(`${API_BASE_URL}/api/documents/${documentId}/display`, { headers: authHeaders });
        if (!displayResponse.ok) throw new Error('Không thể mở bản hiển thị của văn bản.');
        setPdfUrl(URL.createObjectURL(await displayResponse.blob()));
      }
    } catch (reason) { setLoadError(reason instanceof Error ? reason.message : 'Không thể tải văn bản.'); }
  };
  useEffect(() => { load(); return () => { if (pdfUrl) URL.revokeObjectURL(pdfUrl); }; // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [documentId]);

  const requestView = async () => { setRequestState('sending'); try { const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}/view-requests`, { method: 'POST', headers: { 'Content-Type': 'application/json', ...authHeaders }, body: JSON.stringify({ reason: 'Đề nghị xem bản gốc để phục vụ công việc.' }) }); if (!response.ok) throw new Error(); setRequestState('pending'); } catch { setRequestState('failed'); window.setTimeout(() => setRequestState('idle'), 5000); } };
  const changeLifecycle = async (action: 'delete' | 'restore') => {
    const isDelete = action === 'delete';
    if (!confirm(isDelete ? 'Xóa văn bản này? Văn bản sẽ được giữ trong 30 ngày trước khi xóa hoàn toàn.' : 'Khôi phục văn bản này về danh sách đã duyệt?')) return;
    setActing(true);
    try { const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}/${action}`, { method: 'POST', headers: authHeaders }); const body = await response.json(); if (!response.ok) throw new Error(body.detail || 'Không thể cập nhật văn bản.'); onChanged(); onClose(); } catch (reason) { setLoadError(reason instanceof Error ? reason.message : 'Không thể cập nhật văn bản.'); } finally { setActing(false); }
  };
  const locality = document?.scope_type === 'communes' ? (document.commune_ids || []).map((id) => communes.find((commune) => commune.id === id)?.name || `Địa bàn #${id}`).join(', ') || 'Chưa xác định' : 'Toàn tỉnh';
  const deleted = document?.upload_status === 'deleted';

  return <div className="review-backdrop" role="presentation"><section className="document-detail" role="dialog" aria-modal="true" aria-labelledby="document-detail-title"><header className="document-review-header"><div><p className="eyebrow">Văn bản chỉ đạo</p><h2 id="document-detail-title">{document?.document_number || document?.code || 'Đang tải văn bản'}</h2></div><div className="document-header-actions">{user?.role === 'tinh' && document && (deleted ? <button className="secondary-button" disabled={acting} onClick={() => changeLifecycle('restore')}><ArrowCounterClockwise size={16} />Khôi phục</button> : <button className="secondary-button danger-button" disabled={acting} onClick={() => changeLifecycle('delete')}><Trash size={16} />Xóa</button>)}<button className="icon-button" onClick={onClose} aria-label="Đóng"><X size={18} /></button></div></header><div className="document-detail-body"><section className="document-original-pane" aria-label="Bản gốc văn bản">{deleted ? <div className="original-request-card"><Trash size={28} /><strong>Văn bản đã được xóa</strong><span>{document?.deleted_at ? `Được giữ đến hết 30 ngày kể từ ${new Date(document.deleted_at).toLocaleDateString('vi-VN')}.` : 'Tệp đang trong thời gian lưu giữ 30 ngày.'}</span></div> : pdfUrl ? <iframe title="Bản hiển thị văn bản" src={pdfUrl} className="document-pdf-frame" /> : <div className="original-request-card">{loadError ? <p className="form-error">{loadError}</p> : requestState === 'sending' ? <><Spinner size={24} className="spin" /><strong>Đang gửi yêu cầu</strong></> : requestState === 'pending' ? <><Eye size={24} /><strong>Đang chờ duyệt</strong><span>Yêu cầu xem bản gốc đã được gửi.</span></> : requestState === 'failed' ? <><strong>Gửi yêu cầu thất bại</strong><span>Vui lòng thử lại.</span></> : <><FileText size={28} /><strong>Bấm vào đây để gửi yêu cầu xem bản gốc</strong><span>Bản gốc chỉ hiển thị khi được cấp quyền.</span><button className="primary-button" onClick={requestView}>Gửi yêu cầu</button></>}</div>}</section><section className="document-metadata-pane">{document ? <><h3>{document.title}</h3>{deleted && <p className="deleted-note">Đã xóa bởi {document.deleted_by_name || 'cán bộ tỉnh'}; có thể khôi phục trong 30 ngày.</p>}<dl className="document-metadata"><div><dt>Loại văn bản</dt><dd>{document.doc_type || 'Chưa xác định'}</dd></div><div><dt>Cơ quan ban hành</dt><dd>{document.issued_by || 'Chưa xác định'}</dd></div><div><dt>Ngày ban hành</dt><dd>{document.issued_date || 'Chưa xác định'}</dd></div><div><dt>Hiệu lực</dt><dd>{document.start_date || 'Chưa xác định'}{document.end_date ? ` – ${document.end_date}` : ''}</dd></div><div><dt>Địa bàn áp dụng</dt><dd>{locality}</dd></div><div><dt>Mức độ khẩn</dt><dd>{document.urgency || 'Không xác định'}</dd></div></dl><div className="document-detail-copy"><h4>Tóm tắt chỉ đạo</h4><p>{document.llm_summary || 'Chưa có thông tin tóm tắt.'}</p><h4>Việc cần thực hiện</h4><p>{document.required_actions || 'Chưa có thông tin.'}</p></div></> : <div className="empty-state"><Spinner size={28} className="spin" /><p>Đang tải thông tin văn bản…</p></div>}</section></div></section></div>;
}
