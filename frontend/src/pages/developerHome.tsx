import { useNavigate } from 'react-router-dom';
import Styles from './Style';
import { showNotification } from '../components/NotificationCenter';

export const DeveloperHome = () => {
  const navigate = useNavigate();
  const actionCardStyle = {
    minHeight: '280px',
    borderRadius: '12px',
    border: 'none',
    display: 'flex',
    flexDirection: 'column' as const,
    justifyContent: 'center'
  };
  const actionTitleStyle = {
    minHeight: '96px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: 'bold',
    color: '#333'
  };
  const actionButtonStyle = {
    width: 'min(100%, 260px)',
    borderRadius: '20px',
    backgroundColor: '#00A2E8',
    border: 'none',
    color: 'white'
  };

  return (
    <div className="bg-light min-vh-100">
      <div style={Styles.styles.header}>
        <span>Job scheduler System</span>
        <div className="d-flex flex-column align-items-end">
          <button
            className="btn btn-light btn-sm px-3 mb-2"
            onClick={() => {
              localStorage.removeItem('user');
              showNotification('已登出', 'success');
              navigate('/');
            }}
            style={Styles.homeLoginLogoutStyles.style}
          >
            登出
          </button>
          <h2 className="fs-5 m-0 font-weight-bold">內部開發者專區</h2>
        </div>
      </div>

      <div className="container mt-5">
        <div className="row text-center align-items-stretch">
          <div className="col-md-4 mb-4 d-flex">
            <div className="card p-5 shadow-sm w-100" style={actionCardStyle}>
              <h3 style={actionTitleStyle}>新增 RESTful API 任務</h3>
              <button
                onClick={() => navigate('/developer/RESTfulAPI')}
                className="btn btn-success mt-3 px-4 mx-auto"
                style={actionButtonStyle}
              >
                新增
              </button>
            </div>
          </div>

          <div className="col-md-4 mb-4 d-flex">
            <div className="card p-5 shadow-sm w-100" style={actionCardStyle}>
              <h3 style={actionTitleStyle}>新增 Shell Script 任務</h3>
              <button
                onClick={() => navigate('/developer/ShellScript')}
                className="btn btn-warning mt-3 px-4 mx-auto"
                style={actionButtonStyle}
              >
                新增
              </button>
            </div>
          </div>

          <div className="col-md-4 mb-4 d-flex">
            <div className="card p-5 shadow-sm w-100" style={actionCardStyle}>
              <h3 style={actionTitleStyle}>我的 Job</h3>
              <button
                onClick={() => navigate('/developer/jobs')}
                className="btn btn-info mt-3 px-4 mx-auto"
                style={actionButtonStyle}
              >
                查看
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
