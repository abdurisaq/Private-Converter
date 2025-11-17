import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import { Routes, Route, Navigate,useNavigate } from 'react-router-dom';
import './App.css'
import useAuthStore from './utils/authStore'
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import { LogOut, Settings, Home, Upload, FileText } from 'lucide-react';

function App() {
  const [count, setCount] = useState(0)
  const { access, refresh, user,logout } = useAuthStore();
  const navigate = useNavigate();
  const handleLogout = () => {
    logout();
    navigate('/login');
  };
  const PrivateRoute = ({ children, adminOnly = false }) => {
    if (!access) {
      return <Navigate to="/login" replace />;
    }
    if (adminOnly && user?.role !== 'admin') {
      return <Navigate to="/dashboard" replace />;
    }
    return children;
  };

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route
        path="/dashboard"
        element={
            <>
          <div>
            <a href="https://vite.dev" target="_blank">
              <img src={viteLogo} className="logo" alt="Vite logo" />
            </a>
            <a href="https://react.dev" target="_blank">
              <img src={reactLogo} className="logo react" alt="React logo" />
            </a>
          </div>
          <h1>Vite + React</h1>
          <div className="card">
            <button onClick={() => setCount((count) => count + 1)}>
              count is {count}
            </button>
            <p>
              Edit <code>src/App.jsx</code> and save to test HMR
            </p>
          </div>
          <p className="read-the-docs">
            Click on the Vite and React logos to learn more
          </p>
          <div className="p-8">
          <h1 className="text-2xl font-bold">Vite + Django Skeleton</h1>
        </div>
        <button
              onClick={handleLogout}
              className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
            >
              <LogOut size={20} />
              <span>Logout</span>
            </button>
        </>
        }
      />
    </Routes>
  )
}

export default App



{/* <>
      <div>
        <a href="https://vite.dev" target="_blank">
          <img src={viteLogo} className="logo" alt="Vite logo" />
        </a>
        <a href="https://react.dev" target="_blank">
          <img src={reactLogo} className="logo react" alt="React logo" />
        </a>
      </div>
      <h1>Vite + React</h1>
      <div className="card">
        <button onClick={() => setCount((count) => count + 1)}>
          count is {count}
        </button>
        <p>
          Edit <code>src/App.jsx</code> and save to test HMR
        </p>
      </div>
      <p className="read-the-docs">
        Click on the Vite and React logos to learn more
      </p>
      <div className="p-8">
      <h1 className="text-2xl font-bold">Vite + Django Skeleton</h1>
    </div>
    </> */}