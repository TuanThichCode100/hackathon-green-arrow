import {
  BellRinging, BookOpenText, Broadcast, Buildings, ChartLineUp, Database, MapTrifold,
  SignIn, SignOut, ShieldCheck, TreeStructure,
} from '@phosphor-icons/react';
import type { ComponentType } from 'react';
import type { User } from './types';

interface Props {
  user: User | null;
  view: string;
  setView: (view: string) => void;
  emergency: boolean;
  onLogout: () => void;
  onLoginRequest: () => void;
  handleToggleEmergency: () => void;
}

const items: Array<{ key: string; label: string; mobileLabel?: string; icon: ComponentType<any>; protected?: boolean }> = [
  { key: 'map', label: 'Bản đồ rủi ro', mobileLabel: 'Bản đồ', icon: MapTrifold },
  { key: 'overview', label: 'Tổng quan', icon: ChartLineUp },
  { key: 'communes', label: 'Địa bàn', icon: Buildings },
  { key: 'channels', label: 'Phân phối', icon: Broadcast },
  { key: 'policy', label: 'Văn bản chỉ đạo', mobileLabel: 'Văn bản', icon: BookOpenText },
  { key: 'database', label: 'Dữ liệu dân cư', icon: Database, protected: true },
  { key: 'roles', label: 'Phân quyền', icon: ShieldCheck, protected: true },
  { key: 'feedback', label: 'Phản ánh thông tin', icon: BellRinging, protected: true },
];

export default function Sidebar({ user, view, setView, emergency, onLogout, onLoginRequest, handleToggleEmergency }: Props) {
  return (
    <aside className="rail">
      <div className="brand">
        <div className="brand-mark"><TreeStructure size={20} weight="bold" /></div>
        <div><strong>GreenForecast</strong><span>Điều hành cảnh báo Điện Biên</span></div>
      </div>
      <nav className="rail-nav" aria-label="Điều hướng chính">
        {items.filter((item) => !item.protected || user).map((item) => {
          const Icon = item.icon;
          return (
            <button key={item.key} className="nav-button" aria-current={view === item.key ? 'page' : undefined} onClick={() => setView(item.key)} title={item.label}>
              <Icon size={19} weight={view === item.key ? 'bold' : 'regular'} />
              <span className="nav-label">{item.label}</span>
              <span className="nav-label-mobile">{item.mobileLabel || item.label}</span>
            </button>
          );
        })}
      </nav>
      <div className="rail-spacer" />
      {user && (
        <div className="system-mode">
          <div className="mode-row">
            <div><div className="mode-label">{emergency ? 'Điều phối khẩn cấp' : 'Giám sát thường trực'}</div><div className="mode-copy">{emergency ? 'Cần xác minh trước khi phát' : 'Dữ liệu được theo dõi liên tục'}</div></div>
            <button className={`toggle ${emergency ? 'on' : ''}`} aria-label="Chuyển chế độ khẩn cấp" aria-pressed={emergency} onClick={handleToggleEmergency} />
          </div>
        </div>
      )}
      <div className="rail-account">
        <div className="avatar">{user?.name?.slice(0, 2).toUpperCase() || 'DB'}</div>
        <div className="account-copy"><strong>{user?.name || 'Chế độ quan sát'}</strong><span>{user ? (user.role === 'tinh' ? 'Cán bộ tỉnh' : 'Cán bộ xã') : 'Chưa đăng nhập'}</span></div>
        <button className="icon-button" onClick={user ? onLogout : onLoginRequest} aria-label={user ? 'Đăng xuất' : 'Đăng nhập'}>
          {user ? <SignOut size={17} /> : <SignIn size={17} />}
        </button>
      </div>
    </aside>
  );
}
