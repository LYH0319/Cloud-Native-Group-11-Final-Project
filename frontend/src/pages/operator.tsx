import { useNavigate } from 'react-router-dom';
import { JobMonitor } from './JobMonitor';
import { homeLoginLogoutStyles, operatorStyles } from './Style';
import { showNotification } from '../components/NotificationCenter';

export const Operator = () => {
  const navigate = useNavigate();

  return (
    <div className="bg-light min-vh-100">
      <div style={operatorStyles.header}>
        <span>Job scheduler System</span>
        <div className="d-flex flex-column align-items-end">
          <button
            className="btn btn-light btn-sm px-3 mb-2"
            onClick={() => {
              localStorage.removeItem('user');
              showNotification('已登出', 'success');
              navigate('/');
            }}
            style={homeLoginLogoutStyles.style}
          >
            登出
          </button>
          <h2 className="fs-5 m-0 font-weight-bold">維運人員專區</h2>
        </div>
      </div>
      <JobMonitor scope="operator" />
    </div>
  );
};
