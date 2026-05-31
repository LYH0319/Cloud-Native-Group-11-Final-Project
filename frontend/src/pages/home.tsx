import { useNavigate } from 'react-router-dom';
import Styles from './Style';
import { type User } from '../types/types';

export const Home = () => {
  const navigate = useNavigate();
  const userData = localStorage.getItem('user');
  const user: User | null = userData ? JSON.parse(userData) : null;

  const handleLogout = () => {
    alert('登出成功！');
    localStorage.removeItem('user');
    window.location.reload();
  };

  return (
    <div className="bg-light min-vh-100">
      <div style={Styles.styles.header}>
        <span>Job scheduler System</span>

        <div>
          {user ? (
            <button
              className="btn btn-light btn-sm px-3"
              onClick={handleLogout}
              style={Styles.homeLoginLogoutStyles.style}
            >
              登出 ({user.id})
            </button>
          ) : (
            <button
              className="btn btn-light btn-sm px-3"
              onClick={() => navigate('/login')}
              style={Styles.homeLoginLogoutStyles.style}
            >
              登入 / 註冊
            </button>
          )}
        </div>
      </div>

      <div className="container mt-5">
        <div className="row text-center">
          <div className="col-md-6 mb-4">
            <div className="card p-5 shadow-sm" style={{ borderRadius: '12px', border: 'none' }}>
              <h3 style={{ fontWeight: 'bold', color: '#333' }}>內部開發者專區</h3>
              <button
                onClick={() => navigate('/developer')}
                className="btn btn-success mt-3 px-4"
                style={{ borderRadius: '20px', backgroundColor: '#00A2E8', border: 'none' }}
              >
                進入內部開發者頁面
              </button>
            </div>
          </div>

          <div className="col-md-6 mb-4">
            <div className="card p-5 shadow-sm" style={{ borderRadius: '12px', border: 'none' }}>
              <h3 style={{ fontWeight: 'bold', color: '#333' }}>維運人員專區</h3>
              <button
                onClick={() => navigate('/operator')}
                className="btn btn-warning mt-3 px-4"
                style={{
                  borderRadius: '20px',
                  backgroundColor: '#00A2E8',
                  border: 'none',
                  color: 'white'
                }}
              >
                進入維運人員頁面
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
