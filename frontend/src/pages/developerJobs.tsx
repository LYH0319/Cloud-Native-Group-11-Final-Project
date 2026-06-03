import { useNavigate } from 'react-router-dom';
import Styles from './Style';
import { JobMonitor } from './JobMonitor';

export const DeveloperJobs = () => {
  const navigate = useNavigate();

  return (
    <div className="bg-light min-vh-100">
      <div style={Styles.styles.header}>
        <span>Job scheduler System</span>
        <div className="d-flex flex-column align-items-end">
          <button
            className="btn btn-light btn-sm px-3 mb-2"
            onClick={() => navigate('/developer')}
            style={Styles.homeLoginLogoutStyles.style}
          >
            返回
          </button>
          <h2 className="fs-5 m-0 font-weight-bold">內部開發者專區</h2>
        </div>
      </div>
      <JobMonitor scope="developer" />
    </div>
  );
};
