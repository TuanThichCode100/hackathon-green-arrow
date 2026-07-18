import './globals.css';

export const metadata = {
  title: 'GreenForecast — CRM Cảnh báo Thời tiết',
  description: 'Hệ thống CRM giám sát & cảnh báo thời tiết cực đoan cho cán bộ tỉnh Điện Biên (DBWAS).',
};

export default function RootLayout({ children }) {
  return (
    <html lang="vi">
      <body>{children}</body>
    </html>
  );
}
