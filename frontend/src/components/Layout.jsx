import { Outlet, Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../utils/authStore';
import { LogOut, Settings, Home, Upload, FileText } from 'lucide-react';

export default function Layout() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="flex h-screen bg-gray-900 text-gray-100">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-800 shadow-xl">
        <div className="p-6 border-b border-gray-700">
          <h1 className="text-2xl font-bold text-purple-500">private-converter</h1>
          <p className="text-gray-400 text-sm">File Conversion Service</p>
        </div>

        <nav className="mt-6">
          <Link
            to="/dashboard"
            className="flex items-center gap-3 px-6 py-3 rounded-lg hover:bg-gray-700 transition-colors"
          >
            <Home size={20} />
            <span>Dashboard</span>
          </Link>

          <Link
            to="/convert"
            className="flex items-center gap-3 px-6 py-3 rounded-lg hover:bg-gray-700 transition-colors"
          >
            <Upload size={20} />
            <span>Convert</span>
          </Link>

          <Link
            to="/jobs"
            className="flex items-center gap-3 px-6 py-3 rounded-lg hover:bg-gray-700 transition-colors"
          >
            <FileText size={20} />
            <span>My Jobs</span>
          </Link>

          {user?.role === 'admin' && (
            <>
              <hr className="my-4 border-gray-700" />
              <div className="px-6 py-2 text-xs font-semibold text-gray-500 uppercase">
                Admin
              </div>
              <Link
                to="/admin"
                className="flex items-center gap-3 px-6 py-3 rounded-lg hover:bg-gray-700 transition-colors"
              >
                <Settings size={20} />
                <span>Dashboard</span>
              </Link>
              <Link
                to="/admin/users"
                className="flex items-center gap-3 px-6 py-3 rounded-lg hover:bg-gray-700 transition-colors"
              >
                <span>Users</span>
              </Link>
              <Link
                to="/admin/audit-logs"
                className="flex items-center gap-3 px-6 py-3 rounded-lg hover:bg-gray-700 transition-colors"
              >
                <span>Audit Logs</span>
              </Link>
              <Link
                to="/admin/settings"
                className="flex items-center gap-3 px-6 py-3 rounded-lg hover:bg-gray-700 transition-colors"
              >
                <Settings size={20} />
                <span>Settings</span>
              </Link>
            </>
          )}
        </nav>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="bg-gray-800 shadow-sm border-b border-gray-700">
          <div className="px-6 py-4 flex justify-between items-center">
            <div>
              <p className="text-gray-400 text-sm">Logged in as</p>
              <p className="font-semibold text-gray-100">{user?.email}</p>
            </div>
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              <LogOut size={20} />
              <span>Logout</span>
            </button>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-auto p-6 bg-gray-900">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
