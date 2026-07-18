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
    const rows = text.split('\n').map(r => r.trim()).filter(r => r.length > 0);
    if (rows.length <= 1) {
       showToast('File trống hoặc không có dữ liệu', '❌');
       return;
    }
    
    const records = [];
    for (let i = 1; i < rows.length; i++) {
      const cols = rows[i].split(',');
      if (cols.length >= 3) {
        records.push({
          commune_id: isProv && communeId ? parseInt(communeId) : (communesData[0]?.id || 1),
          name: cols[0].trim(),
          phone: cols[1].trim(),
          ethnic: cols[2].trim(),
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
          <select value={ethnic} onChange={e => setEthnic(e.target.value)} style={s('padding:8px 12px; border-radius:8px; border:1px solid #E1E7EE; outline:none;')}>
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
            📥 Import CSV
          </button>
          <button onClick={() => openModal()} style={s('padding:8px 16px; border-radius:8px; background:#1E9E6A; border:none; color:#fff; font-weight:600; cursor:pointer;')}>
            + Thêm mới
          </button>
        </div>
      </div>

      {/* Table */}
      <div style={s('background:#fff; border:1px solid #E1E7EE; border-radius:12px; overflow:hidden;')}>
        <table style={s('width:100%; border-collapse:collapse; text-align:left; font-size:13px;')}>
          <thead>
            <tr style={s('background:#F7F9FB; border-bottom:1px solid #E1E7EE; color:#7C8896;')}>
              <th style={s('padding:12px 16px; font-weight:600;')}>Họ tên</th>
              <th style={s('padding:12px 16px; font-weight:600;')}>SĐT (Nhận SMS/Gọi)</th>
              <th style={s('padding:12px 16px; font-weight:600;')}>Dân tộc</th>
              <th style={s('padding:12px 16px; font-weight:600;')}>Biết chữ (SMS)</th>
              <th style={s('padding:12px 16px; font-weight:600; text-align:right;')}>Thao tác</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td colSpan={5} style={s('padding:30px; text-align:center; color:#7C8896;')}>Đang tải dữ liệu...</td></tr>
            ) : isError ? (
              <tr><td colSpan={5} style={s('padding:30px; text-align:center; color:#E23D3D;')}>Lỗi tải dữ liệu</td></tr>
            ) : !data || data.items.length === 0 ? (
              <tr><td colSpan={5} style={s('padding:30px; text-align:center; color:#7C8896;')}>Chưa có dữ liệu</td></tr>
            ) : (
              data.items.map(r => (
                <tr key={r.id} style={s('border-bottom:1px solid #EEF2F6;')}>
                  <td style={s('padding:12px 16px; font-weight:600; color:#0F1E2A;')}>{r.name}</td>
                  <td style={s('padding:12px 16px; font-family:monospace;')}>{r.phone}</td>
                  <td style={s('padding:12px 16px;')}>
                    <span style={s('background:#EAF7FD; color:#25ADE3; padding:3px 8px; border-radius:4px; font-weight:600;')}>{r.ethnic}</span>
                  </td>
                  <td style={s('padding:12px 16px;')}>
                    {r.literate ? <span style={s('color:#1E9E6A;')}>✅ Có</span> : <span style={s('color:#E23D3D;')}>❌ Không (Chỉ gọi)</span>}
                  </td>
                  <td style={s('padding:12px 16px; text-align:right;')}>
                    <button onClick={() => openModal(r)} style={s('background:none; border:none; color:#25ADE3; cursor:pointer; font-weight:600; margin-right:12px;')}>Sửa</button>
                    <button onClick={() => handleDelete(r.id)} style={s('background:none; border:none; color:#E23D3D; cursor:pointer; font-weight:600;')}>Xóa</button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Modal */}
      {isModalOpen && (
        <div style={s('position:fixed; top:0; left:0; right:0; bottom:0; background:rgba(15,30,42,.6); display:flex; align-items:center; justify-content:center; z-index:1000;')}>
          <div style={s('background:#fff; width:400px; border-radius:14px; overflow:hidden; box-shadow:0 10px 30px rgba(0,0,0,.15);')}>
            <div style={s('padding:18px 24px; border-bottom:1px solid #EEF2F6; font-size:16px; font-weight:700;')}>
              {editingId ? 'Sửa thông tin' : 'Thêm mới hộ dân'}
            </div>
            <div style={s('padding:24px; display:flex; flex-direction:column; gap:16px;')}>
              <div>
                <label style={s('display:block; font-size:12px; font-weight:600; margin-bottom:6px;')}>Họ tên <span style={{color:'red'}}>*</span></label>
                <input value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} placeholder="Nguyễn Văn A" style={s('width:100%; height:40px; border:1px solid #E1E7EE; border-radius:8px; padding:0 12px; outline:none; font-family:inherit; box-sizing:border-box;')} />
              </div>
              <div>
                <label style={s('display:block; font-size:12px; font-weight:600; margin-bottom:6px;')}>Số điện thoại <span style={{color:'red'}}>*</span></label>
                <input value={formData.phone} onChange={e => setFormData({...formData, phone: e.target.value})} placeholder="0912345678" style={s('width:100%; height:40px; border:1px solid #E1E7EE; border-radius:8px; padding:0 12px; outline:none; font-family:inherit; box-sizing:border-box;')} />
              </div>
              <div>
                <label style={s('display:block; font-size:12px; font-weight:600; margin-bottom:6px;')}>Dân tộc <span style={{color:'red'}}>*</span></label>
                <select value={formData.ethnic} onChange={e => setFormData({...formData, ethnic: e.target.value})} style={s('width:100%; height:40px; border:1px solid #E1E7EE; border-radius:8px; padding:0 12px; outline:none; font-family:inherit; box-sizing:border-box;')}>
                  <option value="Kinh">Kinh</option>
                  <option value="Thái">Thái</option>
                  <option value="Mông">Mông (H'Mông)</option>
                  <option value="Khơ Mú">Khơ Mú</option>
                  <option value="Dao">Dao</option>
                </select>
              </div>
              <div style={s('display:flex; align-items:center; gap:8px; margin-top:8px;')}>
                <input type="checkbox" id="literate" checked={formData.literate} onChange={e => setFormData({...formData, literate: e.target.checked})} />
                <label htmlFor="literate" style={s('font-size:13px; cursor:pointer;')}>Hộ dân có người biết đọc tiếng phổ thông (Để nhận SMS thay vì gọi điện)</label>
              </div>
            </div>
            <div style={s('padding:16px 24px; background:#F7F9FB; border-top:1px solid #EEF2F6; display:flex; justify-content:flex-end; gap:10px;')}>
              <button onClick={() => setIsModalOpen(false)} style={s('padding:8px 16px; border-radius:8px; background:#fff; border:1px solid #E1E7EE; cursor:pointer; font-weight:600;')}>Hủy</button>
              <button onClick={handleSave} style={s('padding:8px 16px; border-radius:8px; background:#1E9E6A; border:none; color:#fff; cursor:pointer; font-weight:600;')}>Lưu dữ liệu</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
