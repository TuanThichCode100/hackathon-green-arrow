import { useState, useRef, useEffect } from 'react';
import { useResidents, apiCreateResident, apiUpdateResident, apiDeleteResident, apiImportResidents } from '../lib/api';

// Utilities for inline styling
const s = (str) => {
  const obj = {};
  str.split(';').forEach(pair => {
    if (!pair.trim()) return;
    const [k, v] = pair.split(':');
    obj[k.trim().replace(/-./g, x => x[1].toUpperCase())] = v.trim();
  });
  return obj;
};

const validateResident = (data) => {
  const errors = [];
  if (!data.name || data.name.trim().length < 2) errors.push("Tên không hợp lệ (ít nhất 2 ký tự).");
  if (/[^a-zA-ZÀ-ỹ\s]/.test(data.name)) errors.push("Tên không được chứa ký tự đặc biệt.");
  if (!/^0\d{9}$/.test(data.phone)) errors.push("SĐT phải gồm 10 chữ số và bắt đầu bằng 0.");
  if (!data.ethnic) errors.push("Vui lòng chọn Dân tộc.");
  return errors;
};

export default function ResidentsDB({ isProv, showToast, communesData }) {
  const [communeId, setCommuneId] = useState('');
  const [ethnic, setEthnic] = useState('');
  const [page, setPage] = useState(1);
  
  // Set default commune if user is Commune level
  useEffect(() => {
    if (!isProv && communesData?.length > 0) {
      setCommuneId(communesData[0].id); // Mặc định gán cho xã đầu tiên (mock cho việc cán bộ xã)
    }
  }, [isProv, communesData]);

  const { data, isLoading, isError, mutate } = useResidents(communeId, ethnic, page, 50);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({ name: '', phone: '', ethnic: 'Kinh', literate: true });
  
  const fileInputRef = useRef(null);

  const openModal = (resident = null) => {
    if (resident) {
      setEditingId(resident.id);
      setFormData({ name: resident.name, phone: resident.phone, ethnic: resident.ethnic, literate: resident.literate });
    } else {
      setEditingId(null);
      setFormData({ name: '', phone: '', ethnic: 'Kinh', literate: true });
    }
    setIsModalOpen(true);
  };

  const handleSave = async () => {
    if (!isProv && !communeId) {
      showToast('Lỗi: Bạn chưa được phân bổ Xã.', '❌');
      return;
    }
    
    const errors = validateResident(formData);
    if (errors.length > 0) {
      showToast(errors[0], '❌');
      return;
    }

    const payload = {
      ...formData,
      commune_id: isProv && communeId ? parseInt(communeId) : (communesData[0]?.id || 1),
    };

    try {
      showToast('Đang lưu dữ liệu...', '⏳');
      if (editingId) {
        await apiUpdateResident(editingId, formData);
        showToast('Cập nhật thành công', '✅');
      } else {
        await apiCreateResident(payload);
        showToast('Thêm mới thành công', '✅');
      }
      setIsModalOpen(false);
      mutate();
    } catch (e) {
      showToast('Lỗi khi lưu dữ liệu', '❌');
    }
  };

  const handleDelete = async (id) => {
    if (confirm("Bạn có chắc chắn muốn xóa dữ liệu này?")) {
      try {
        await apiDeleteResident(id);
        showToast('Đã xóa thành công', '✅');
        mutate();
      } catch (e) {
        showToast('Lỗi khi xóa', '❌');
      }
    }
  };

  const handleImport = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    if (!file.name.endsWith('.csv')) {
      showToast('Chỉ hỗ trợ file CSV', '❌');
      return;
    }

    const text = await file.text();
    
    // Parser CSV chuẩn xử lý nháy kép
    const parseCSV = (str) => {
      const arr = [];
      let quote = false;
      let row = 0, col = 0;
      for (let c = 0; c < str.length; c++) {
        let cc = str[c], nc = str[c+1];
        arr[row] = arr[row] || [];
        arr[row][col] = arr[row][col] || '';
        if (cc === '"' && quote && nc === '"') { arr[row][col] += cc; ++c; continue; }
        if (cc === '"') { quote = !quote; continue; }
        if (cc === ',' && !quote) { ++col; continue; }
        if (cc === '\r' && nc === '\n' && !quote) { ++row; col = 0; ++c; continue; }
        if (cc === '\n' && !quote) { ++row; col = 0; continue; }
        if (cc === '\r' && !quote) { ++row; col = 0; continue; }
        arr[row][col] += cc;
      }
      return arr.filter(r => r.length > 1 || (r.length === 1 && r[0].trim() !== ''));
    };

    const rows = parseCSV(text);
    if (rows.length <= 1) {
       showToast('File trống hoặc không có dữ liệu', '❌');
       return;
    }
    
    const records = [];
    // Skip header (i=1)
    for (let i = 1; i < rows.length; i++) {
      const cols = rows[i];
      if (cols.length >= 3) {
        records.push({
          commune_id: isProv && communeId ? parseInt(communeId) : (communesData[0]?.id || 1),
          name: (cols[0] || '').trim(),
          phone: (cols[1] || '').trim(),
          ethnic: (cols[2] || '').trim(),
          literate: cols[3] ? (cols[3].trim() === '1' || cols[3].trim().toLowerCase() === 'true') : true
        });
      }
    }

    try {
      showToast(`Đang nhập ${records.length} bản ghi...`, '⏳');
      await apiImportResidents(records);
      showToast('Import thành công', '✅');
      mutate();
    } catch (err) {
      showToast('Lỗi khi Import CSV', '❌');
    }
    
    e.target.value = null;
  };

  const totalPages = data ? Math.ceil(data.total / data.limit) : 1;

  return (
    <div style={s('padding:22px 26px;')}>
      {/* Filters & Actions */}
      <div style={s('display:flex; justify-content:space-between; margin-bottom:20px; align-items:center;')}>
        <div style={s('display:flex; gap:12px;')}>
          {isProv && (
            <select value={communeId} onChange={e => setCommuneId(e.target.value)} style={s('padding:8px 12px; border-radius:8px; border:1px solid #E1E7EE; outline:none;')}>
              <option value="">-- Tất cả các Xã --</option>
              {communesData?.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          )}
          <select value={ethnic} onChange={e => { setEthnic(e.target.value); setPage(1); }} style={s('padding:8px 12px; border-radius:8px; border:1px solid #E1E7EE; outline:none;')}>
            <option value="">-- Mọi dân tộc --</option>
            <option value="Kinh">Kinh</option>
            <option value="Thái">Thái</option>
            <option value="Mông">Mông (H'Mông)</option>
            <option value="Khơ Mú">Khơ Mú</option>
            <option value="Dao">Dao</option>
          </select>
        </div>
        
        <div style={s('display:flex; gap:10px;')}>
          <input type="file" accept=".csv" ref={fileInputRef} onChange={handleImport} style={{ display: 'none' }} />
          <button onClick={() => fileInputRef.current.click()} style={s('padding:8px 16px; border-radius:8px; background:#fff; border:1px solid #E1E7EE; color:#0F1E2A; font-weight:600; cursor:pointer;')}>
            Import CSV
          </button>
          <button onClick={() => openModal()} style={s('padding:8px 16px; border-radius:8px; background:#0EA5E9; border:none; color:#fff; font-weight:600; cursor:pointer;')}>
            + Thêm Cư dân
          </button>
        </div>
      </div>

      {/* Table */}
      <div style={s('background:#fff; border-radius:12px; border:1px solid #E1E7EE; overflow:hidden;')}>
        <table style={s('width:100%; border-collapse:collapse; text-align:left;')}>
          <thead>
            <tr style={s('background:#F8FAFC; border-bottom:1px solid #E1E7EE;')}>
              <th style={s('padding:12px 16px; color:#64748B; font-weight:600; font-size:14px;')}>Họ tên</th>
              <th style={s('padding:12px 16px; color:#64748B; font-weight:600; font-size:14px;')}>SĐT</th>
              <th style={s('padding:12px 16px; color:#64748B; font-weight:600; font-size:14px;')}>Dân tộc</th>
              <th style={s('padding:12px 16px; color:#64748B; font-weight:600; font-size:14px;')}>Biết chữ</th>
              <th style={s('padding:12px 16px; color:#64748B; font-weight:600; font-size:14px;')}>Hành động</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? <tr><td colSpan={5} style={s('padding:16px; text-align:center;')}>Đang tải...</td></tr> : 
             (data?.data || []).map(r => (
              <tr key={r.id} style={s('border-bottom:1px solid #F1F5F9;')}>
                <td style={s('padding:12px 16px;')}>{r.name}</td>
                <td style={s('padding:12px 16px;')}>{r.phone}</td>
                <td style={s('padding:12px 16px;')}>{r.ethnic}</td>
                <td style={s('padding:12px 16px;')}>{r.literate ? 'Có' : 'Không'}</td>
                <td style={s('padding:12px 16px; display:flex; gap:8px;')}>
                  <button onClick={() => openModal(r)} style={s('padding:4px 8px; border-radius:4px; border:1px solid #E1E7EE; cursor:pointer;')}>Sửa</button>
                  <button onClick={() => handleDelete(r.id)} style={s('padding:4px 8px; border-radius:4px; border:1px solid #FECDD3; color:#E11D48; cursor:pointer;')}>Xóa</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div style={s('display:flex; justify-content:space-between; align-items:center; margin-top:20px;')}>
        <button disabled={page === 1} onClick={() => setPage(p => p - 1)} style={s('padding:8px 16px; border-radius:8px; border:1px solid #E1E7EE; cursor:pointer; background:#fff;')}>Trước</button>
        <span style={s('font-size:14px; color:#64748B;')}>Trang {page} / {totalPages}</span>
        <button disabled={page >= totalPages} onClick={() => setPage(p => p + 1)} style={s('padding:8px 16px; border-radius:8px; border:1px solid #E1E7EE; cursor:pointer; background:#fff;')}>Sau</button>
      </div>

      {/* Modal */}
      {isModalOpen && (
        <div style={s('position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); display:flex; align-items:center; justify-content:center; z-index:100;')}>
          <div style={s('background:#fff; padding:24px; border-radius:12px; width:400px;')}>
            <h3 style={s('margin-top:0; margin-bottom:20px; color:#0F1E2A;')}>{editingId ? 'Sửa Cư dân' : 'Thêm Cư dân'}</h3>
            <div style={s('display:flex; flex-direction:column; gap:12px; margin-bottom:20px;')}>
              <input type="text" placeholder="Họ tên" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} style={s('padding:8px 12px; border-radius:8px; border:1px solid #E1E7EE; outline:none;')} />
              <input type="text" placeholder="Số điện thoại" value={formData.phone} onChange={e => setFormData({...formData, phone: e.target.value})} style={s('padding:8px 12px; border-radius:8px; border:1px solid #E1E7EE; outline:none;')} />
              <select value={formData.ethnic} onChange={e => setFormData({...formData, ethnic: e.target.value})} style={s('padding:8px 12px; border-radius:8px; border:1px solid #E1E7EE; outline:none;')}>
                <option value="Kinh">Kinh</option>
                <option value="Thái">Thái</option>
                <option value="Mông">Mông</option>
                <option value="Khơ Mú">Khơ Mú</option>
                <option value="Dao">Dao</option>
              </select>
              <label style={s('display:flex; align-items:center; gap:8px;')}>
                <input type="checkbox" checked={formData.literate} onChange={e => setFormData({...formData, literate: e.target.checked})} />
                Biết chữ
              </label>
            </div>
            <div style={s('display:flex; justify-content:flex-end; gap:10px;')}>
              <button onClick={() => setIsModalOpen(false)} style={s('padding:8px 16px; border-radius:8px; border:1px solid #E1E7EE; background:#fff; cursor:pointer;')}>Hủy</button>
              <button onClick={handleSave} style={s('padding:8px 16px; border-radius:8px; background:#0EA5E9; border:none; color:#fff; cursor:pointer;')}>Lưu</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
