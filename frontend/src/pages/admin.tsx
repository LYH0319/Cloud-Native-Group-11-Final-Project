import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Styles from './Style';

export const Admin = () => {
  const [employeeId, setEmployeeId] = useState('');
  const [username, setUsername] = useState('');
  const [role, setRole] = useState('developer');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [isError, setIsError] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');
    setIsError(false);

    try {
      const response = await fetch('/api/admin/create-user', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          employee_id: employeeId.trim(),
          username: username.trim(),
          role: role
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || '新增失敗');
      }

      // 新增成功，清空輸入框
      setIsError(false);
      setMessage(`成功建立員工！編號: ${data.employee_id}`);
      setEmployeeId('');
      setUsername('');
      setRole('developer');
    } catch (error: any) {
      setIsError(true);
      setMessage(error.message || '伺服器連線錯誤');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-light min-vh-100">
      <div style={Styles.styles.header}>
        <span>Job scheduler System</span>

        <div className="d-flex flex-column align-items-end">
          <button
            className="btn btn-light btn-sm px-3 mb-2"
            onClick={() => {
              alert('登出成功！');
              localStorage.removeItem('user');
              navigate('/');
            }}
            style={Styles.homeLoginLogoutStyles.style}
          >
            登出
          </button>

          <h2 className="fs-5 m-0 font-weight-bold">管理者專區</h2>
        </div>
      </div>

      <div style={{ padding: '40px', maxWidth: '500px', margin: '0 auto' }}>
        <h2>管理員後台 - 新增員工職位</h2>

        <form
          onSubmit={handleSubmit}
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '15px',
            backgroundColor: 'white',
            padding: '20px',
            borderRadius: '8px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
          }}
        >
          <div>
            <label style={{ display: 'block', marginBottom: '5px' }}>員工編號：</label>
            <input
              type="text"
              value={employeeId}
              onChange={(e) => setEmployeeId(e.target.value)}
              required
              placeholder="例如: 003"
              style={{
                width: '100%',
                padding: '8px',
                backgroundColor: 'white',
                color: 'black',
                border: '1px solid #b5b5b5'
              }}
            />
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '5px' }}>賦予職位：</label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              style={{ width: '100%', padding: '8px', backgroundColor: 'white', color: 'black' }}
            >
              <option value="developer">Developer (開發人員)</option>
              <option value="operator">Operator (操作人員)</option>
            </select>
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              padding: '10px',
              background: '#0f117a',
              color: 'white',
              border: 'none',
              cursor: 'pointer'
            }}
          >
            {loading ? '處理中...' : '確認新增員工'}
          </button>
        </form>

        {message && (
          <div
            style={{
              marginTop: '20px',
              padding: '10px',
              backgroundColor: isError ? '#f8d7da' : '#d1e7dd',
              color: isError ? '#842029' : '#0f5132',
              borderRadius: '4px'
            }}
          >
            {message}
          </div>
        )}
      </div>
    </div>
  );
};
