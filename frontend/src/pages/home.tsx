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
      {/* ⭕ 完美的頂部深藍色 Header (整合了原本 Navbar 的功能) */}
      <div style={Styles.styles.header}>
        <span>Job scheduler System</span>
        
        {/* 右側按鈕區 */}
        <div>
          {user ? (
            <button className="btn btn-light btn-sm px-3" onClick={handleLogout} style={Styles.homeLoginLogoutStyles.style}>
              登出 ({user.id})
            </button>
          ) : (
            <button className="btn btn-light btn-sm px-3" onClick={() => navigate('/login')} style={Styles.homeLoginLogoutStyles.style}>
              登入 / 註冊
            </button>
          )}
        </div>
      </div>

      {/* 中央主要內容區 */}
      <div className="container mt-5">
        <div className="row text-center">
          
          {/* 開發者專區 */}
          <div className="col-md-6 mb-4">
            <div className="card p-5 shadow-sm" style={{ borderRadius: '12px', border: 'none' }}>
              <h3 style={{ fontWeight: 'bold', color: '#333' }}>開發者專區</h3>
              <button 
                onClick={() => navigate('/developer')} 
                className="btn btn-success mt-3 px-4"
                style={{ borderRadius: '20px', backgroundColor: '#198754', border: 'none' }}
              >
                進入開發者頁面
              </button>
            </div>
          </div>

          {/* 維運人員專區 */}
          <div className="col-md-6 mb-4">
            <div className="card p-5 shadow-sm" style={{ borderRadius: '12px', border: 'none' }}>
              <h3 style={{ fontWeight: 'bold', color: '#333' }}>維運人員專區</h3>
              <button 
                onClick={() => navigate('/operator')} 
                className="btn btn-warning mt-3 px-4"
                style={{ borderRadius: '20px', backgroundColor: '#ffc107', border: 'none', color: '#000' }}
              >
                進入維運人員頁面
              </button>
            </div>
          </div>

        </div>
      </div>
    </div>
  );

  // return (
  //   <div /*className="bg-light min-vh-100"*/>

  //     <div style={styles.header}>Job scheduler System</div>

  //     <nav className="navbar navbar-dark bg-dark p-3">
  //       <div className="container-fluid">
  //         {/* <span className="navbar-brand mb-0 h1">Job Management System</span> */}
  //         <span className="navbar-brand mb-0 h1">Job Management System</span>
  //         {user ? (
  //           <button className="btn btn-danger" onClick={handleLogout}>登出 ({user.id})</button>
  //         ) : (
  //           <button className="btn btn-primary" onClick={() => navigate('/login')}>登入/註冊</button>
  //         )}
  //       </div>
  //     </nav>

  //     <div className="container mt-5">
  //       <div className="row text-center">
  //         <div className="col-md-6">
  //           <div className="card p-5 shadow-sm">
  //             <h3>開發者專區</h3>
  //             <button onClick={() => navigate('/developer')} className="btn btn-success mt-3">進入開發者頁面</button>
  //           </div>
  //         </div>
  //         <div className="col-md-6">
  //           <div className="card p-5 shadow-sm">
  //             <h3>維運人員專區</h3>
  //             <button onClick={() => navigate('/operator')} className="btn btn-warning mt-3">進入維運人員頁面</button>
  //           </div>
  //         </div>
  //       </div>
  //     </div>
  //   </div>
  // );
};