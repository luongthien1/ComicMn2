import React from 'react';
import { useNavigation } from '../../hooks/useNavigation';

export const MainContent: React.FC = () => {
  const { navigationState } = useNavigation();

  return (
    <div className="flex-1 bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        {navigationState.breadcrumb.length > 0 && (
          <nav className="mb-6">
            <ol className="flex items-center space-x-2 text-sm text-gray-500">
              <li>Trang chủ</li>
              {navigationState.breadcrumb.map((crumb, index) => (
                <React.Fragment key={index}>
                  <li>/</li>
                  <li className={index === navigationState.breadcrumb.length - 1 ? 'text-gray-900 font-medium' : ''}>
                    {crumb}
                  </li>
                </React.Fragment>
              ))}
            </ol>
          </nav>
        )}

        <div className="bg-white rounded-lg shadow-sm p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-6">
            {navigationState.breadcrumb.length > 0
              ? navigationState.breadcrumb[navigationState.breadcrumb.length - 1]
              : 'Chào mừng đến với Admin Panel'
            }
          </h1>

          {navigationState.activeItem ? (
            <div className="space-y-4">
              <p className="text-gray-600">
                Bạn đang xem nội dung của: <strong>{navigationState.breadcrumb.join(' > ')}</strong>
              </p>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="font-semibold text-blue-900 mb-2">Thông tin trang</h3>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>ID: {navigationState.activeItem}</li>
                  <li>Đường dẫn: {navigationState.breadcrumb.join(' > ')}</li>
                  <li>Cấp độ: {navigationState.breadcrumb.length}</li>
                </ul>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">
                <div className="bg-gradient-to-br from-blue-500 to-blue-600 text-white p-6 rounded-lg">
                  <h3 className="text-lg font-semibold mb-2">Tổng quan</h3>
                  <p className="text-blue-100">Nội dung tổng quan cho trang này</p>
                </div>

                <div className="bg-gradient-to-br from-green-500 to-green-600 text-white p-6 rounded-lg">
                  <h3 className="text-lg font-semibold mb-2">Thống kê</h3>
                  <p className="text-green-100">Các số liệu thống kê quan trọng</p>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">👋</div>
              <h2 className="text-2xl font-semibold text-gray-700 mb-4">
                Chào mừng bạn đến với Admin Panel
              </h2>
              <p className="text-gray-500 max-w-md mx-auto">
                Hãy chọn một mục từ sidebar để bắt đầu quản lý hệ thống của bạn.
                Sidebar hỗ trợ nhiều cấp menu với animation mượt mà.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
