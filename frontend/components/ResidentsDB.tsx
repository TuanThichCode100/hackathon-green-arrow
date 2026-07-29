import { useEffect, useRef, useState } from 'react';
import { apiCreateResident, apiDeleteResident, apiImportResidents, apiUpdateResident, useResidents } from '../lib/api';

const ETHNICS = ['Kinh', 'Thái', 'Mông', 'Khơ Mú', 'Dao'];
const fieldStyle = { width: '100%', height: 40, border: '1px solid var(--line)', borderRadius: 10, padding: '0 12px', color: 'var(--ink)', background: 'var(--surface)' };
const buttonStyle = { minHeight: 40, padding: '8px 14px', borderRadius: 10, cursor: 'pointer', fontWeight: 650 };

function validateResident(data) {
  if (!data.name?.trim() || data.name.trim().length < 2) return 'Họ và tên cần có ít nhất 2 ký tự.';
  if (!/^0\d{9}$/.test(data.phone?.replace(/\s/g, ''))) return 'Số điện thoại phải có 10 chữ số và bắt đầu bằng 0.';
  if (!data.ethnic) return 'Vui lòng chọn dân tộc.';
  return null;
}

function parseCsv(source: string) {
  const rows: string[][] = [];
  let row: string[] = [], value = '', quoted = false;
  for (let index = 0; index < source.length; index += 1) {
    const char = source[index];
    if (char === '"' && quoted && source[index + 1] === '"') { value += char; index += 1; }
    else if (char === '"') quoted = !quoted;
    else if ((char === ',' || char === ';') && !quoted) { row.push(value.trim()); value = ''; }
    else if ((char === '\n' || char === '\r') && !quoted) {
      if (char === '\r' && source[index + 1] === '\n') index += 1;
      row.push(value.trim()); if (row.some(Boolean)) rows.push(row); row = []; value = '';
    } else value += char;
  }
  row.push(value.trim()); if (row.some(Boolean)) rows.push(row);
  return rows;
}

export default function ResidentsDB({ isProv, showToast, communesData }) {
  const [communeId, setCommuneId] = useState('');
  const [ethnic, setEthnic] = useState('');
  const [page, setPage] = useState(1);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [formData, setFormData] = useState({ name: '', phone: '', ethnic: 'Kinh', literate: true });
  const [formError, setFormError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  useEffect(() => { if (!isProv && communesData?.[0]?.id) setCommuneId(String(communesData[0].id)); }, [isProv, communesData]);
  const { data: response, isLoading, isError, mutate } = useResidents(communeId, ethnic, page, 50);
  const result = response?.data;
  const residents = result?.items ?? [];
  const totalPages = Math.max(1, Math.ceil((result?.total ?? 0) / (result?.limit ?? 50)));
  const selectedCommuneId = Number(communeId);
  const openModal = (resident = null) => { setEditingId(resident?.id ?? null); setFormData(resident ? { name: resident.name, phone: resident.phone, ethnic: resident.ethnic, literate: resident.literate } : { name: '', phone: '', ethnic: 'Kinh', literate: true }); setFormError(''); setIsModalOpen(true); };
  const handleSave = async () => {
    const error = validateResident(formData);
    if (error) { setFormError(error); return; }
    if (!editingId && !selectedCommuneId) { setFormError('Chọn xã/phường trước khi thêm dân cư.'); return; }
    try {
      const clean = { ...formData, name: formData.name.trim(), phone: formData.phone.replace(/\s/g, '') };
      if (editingId) await apiUpdateResident(editingId, clean); else await apiCreateResident({ ...clean, commune_id: selectedCommuneId });
      showToast(editingId ? 'Đã cập nhật dân cư.' : 'Đã thêm dân cư.'); setIsModalOpen(false); mutate();
    } catch (error) { setFormError(error instanceof Error ? error.message : 'Không thể lưu dữ liệu.'); }
  };
  const handleImport = async (event) => {
    const file = event.target.files?.[0]; event.target.value = '';
    if (!file) return;
    if (!file.name.toLowerCase().endsWith('.csv')) { showToast('Chỉ hỗ trợ tệp CSV.', 'error'); return; }
    if (!selectedCommuneId && isProv) { showToast('Chọn xã/phường trước khi import CSV.', 'warning'); return; }
    const rows = parseCsv(await file.text());
    if (rows.length < 2) { showToast('CSV cần có hàng tiêu đề và ít nhất một bản ghi.', 'error'); return; }
    const header = rows[0].map((item) => item.toLocaleLowerCase('vi-VN').replace(/[\s_]/g, ''));
    const indexOf = (...names: string[]) => header.findIndex((item) => names.includes(item));
    const nameIndex = indexOf('hoten', 'họvàtên', 'name'), phoneIndex = indexOf('sodienthoai', 'sđt', 'phone'), ethnicIndex = indexOf('dantoc', 'ethnic'), literateIndex = indexOf('bietchu', 'literate');
    if (nameIndex < 0 || phoneIndex < 0 || ethnicIndex < 0) { showToast('CSV phải có cột Họ tên, Số điện thoại và Dân tộc.', 'error'); return; }
    const records = rows.slice(1).map((row) => ({ commune_id: selectedCommuneId, name: row[nameIndex] ?? '', phone: (row[phoneIndex] ?? '').replace(/\s/g, ''), ethnic: row[ethnicIndex] ?? '', literate: literateIndex < 0 ? true : ['1', 'true', 'có', 'co', 'yes'].includes((row[literateIndex] ?? '').toLocaleLowerCase('vi-VN')) }));
    const invalid = records.find((record) => validateResident(record));
    if (invalid) { showToast(`CSV có dòng không hợp lệ, ví dụ: ${invalid.name || 'thiếu họ tên'}.`, 'error'); return; }
    try { const response = await apiImportResidents(records); showToast(`Đã import ${response.data.imported} bản ghi dân cư.`); setPage(1); mutate(); } catch (error) { showToast(error instanceof Error ? error.message : 'Không thể import CSV.', 'error'); }
  };
  return <div style={{ padding: '22px 26px' }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, marginBottom: 20, alignItems: 'end', flexWrap: 'wrap' }}><div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
      {isProv && <label><span className="metric-label">Xã/phường</span><select value={communeId} onChange={(event) => { setCommuneId(event.target.value); setPage(1); }} style={fieldStyle}><option value="">Chọn xã/phường</option>{communesData?.map((commune) => <option key={commune.id} value={commune.id}>{commune.name}</option>)}</select></label>}
      <label><span className="metric-label">Lọc theo dân tộc</span><select value={ethnic} onChange={(event) => { setEthnic(event.target.value); setPage(1); }} style={fieldStyle}><option value="">Tất cả dân tộc</option>{ETHNICS.map((item) => <option key={item}>{item}</option>)}</select></label></div>
      <div style={{ display: 'flex', gap: 10 }}><input ref={fileInputRef} type="file" accept=".csv,text/csv" onChange={handleImport} style={{ display: 'none' }} /><button onClick={() => fileInputRef.current?.click()} style={{ ...buttonStyle, background: 'var(--surface)', border: '1px solid var(--line)', color: 'var(--ink)' }}>Import CSV</button><button onClick={() => openModal()} style={{ ...buttonStyle, background: 'var(--accent)', color: 'var(--surface)', border: '1px solid var(--accent)' }}>Thêm dân cư</button></div></div>
    <p className="metric-label" style={{ margin: '-8px 0 16px' }}>CSV gồm các cột: Họ tên, Số điện thoại, Dân tộc, Biết chữ (Có/Không).</p>
    <div style={{ background: 'var(--surface)', border: '1px solid var(--line)', borderRadius: 14, overflow: 'auto' }}><table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', minWidth: 620 }}><thead><tr style={{ background: 'var(--surface-muted)' }}>{['Họ tên', 'Số điện thoại', 'Dân tộc', 'Biết chữ', 'Thao tác'].map((label) => <th key={label} style={{ padding: '12px 16px' }}>{label}</th>)}</tr></thead><tbody>{isLoading ? <tr><td colSpan={5} style={{ padding: 20, textAlign: 'center' }}>Đang tải dữ liệu...</td></tr> : isError ? <tr><td colSpan={5} style={{ padding: 20, textAlign: 'center' }}>Không thể tải dữ liệu. Hãy thử lại.</td></tr> : residents.length === 0 ? <tr><td colSpan={5} style={{ padding: 28, textAlign: 'center' }}>Chưa có dân cư. Hãy thêm mới hoặc import CSV.</td></tr> : residents.map((resident) => <tr key={resident.id} style={{ borderTop: '1px solid var(--line)' }}><td style={{ padding: '12px 16px' }}>{resident.name}</td><td style={{ padding: '12px 16px' }}>{resident.phone}</td><td style={{ padding: '12px 16px' }}>{resident.ethnic}</td><td style={{ padding: '12px 16px' }}>{resident.literate ? 'Có' : 'Không'}</td><td style={{ padding: '8px 16px' }}><button onClick={() => openModal(resident)} style={{ ...buttonStyle, minHeight: 32, padding: '4px 8px', border: '1px solid var(--line)', background: 'var(--surface)' }}>Sửa</button> <button onClick={async () => { if (confirm(`Xóa ${resident.name}?`)) { try { await apiDeleteResident(resident.id); showToast('Đã xóa dân cư.'); mutate(); } catch { showToast('Không thể xóa dân cư.', 'error'); } } }} style={{ ...buttonStyle, minHeight: 32, padding: '4px 8px', border: '1px solid var(--danger)', color: 'var(--danger)', background: 'var(--surface)' }}>Xóa</button></td></tr>)}</tbody></table></div>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 16 }}><button disabled={page === 1} onClick={() => setPage((current) => current - 1)} style={buttonStyle}>Trước</button><span className="metric-label">Trang {page} / {totalPages}</span><button disabled={page >= totalPages} onClick={() => setPage((current) => current + 1)} style={buttonStyle}>Sau</button></div>
    {isModalOpen && <div style={{ position: 'fixed', inset: 0, display: 'grid', placeItems: 'center', background: 'oklch(0.235 0.022 160 / .42)', zIndex: 100 }}><section role="dialog" aria-modal="true" aria-labelledby="resident-dialog-title" style={{ width: 'min(460px, calc(100vw - 32px))', background: 'var(--surface)', borderRadius: 14, padding: 24, boxShadow: '0 20px 60px oklch(0.235 0.022 160 / .22)' }}><h2 id="resident-dialog-title" style={{ margin: '0 0 20px', fontSize: 20 }}>{editingId ? 'Sửa thông tin dân cư' : 'Thêm dân cư'}</h2><div style={{ display: 'grid', gap: 14 }}><label><span className="metric-label">Họ và tên</span><input value={formData.name} onChange={(event) => setFormData({ ...formData, name: event.target.value })} placeholder="Ví dụ: Lò Văn Hùng" style={fieldStyle} autoFocus /></label><label><span className="metric-label">Số điện thoại</span><input value={formData.phone} onChange={(event) => setFormData({ ...formData, phone: event.target.value })} inputMode="tel" placeholder="Ví dụ: 0912 345 678" style={fieldStyle} /></label><label><span className="metric-label">Dân tộc</span><select value={formData.ethnic} onChange={(event) => setFormData({ ...formData, ethnic: event.target.value })} style={fieldStyle}>{ETHNICS.map((item) => <option key={item}>{item}</option>)}</select></label><label style={{ display: 'flex', alignItems: 'center', gap: 8 }}><input type="checkbox" checked={formData.literate} onChange={(event) => setFormData({ ...formData, literate: event.target.checked })} /> Biết chữ</label>{formError && <p role="alert" style={{ margin: 0, color: 'var(--danger)', fontSize: 13 }}>{formError}</p>}</div><div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 24 }}><button onClick={() => setIsModalOpen(false)} style={{ ...buttonStyle, border: '1px solid var(--line)', background: 'var(--surface)' }}>Hủy</button><button onClick={handleSave} style={{ ...buttonStyle, border: '1px solid var(--accent)', background: 'var(--accent)', color: 'var(--surface)' }}>Lưu</button></div></section></div>}
  </div>;
}
