import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { roleToBackend } from '../api';
import { type Role } from '../types/types';
import Styles from './Style';

export const TestCreateUser = () => {
  const [employeeId, setEmployeeId] = useState('');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('secret123');
  const [role, setRole] = useState<Role>('developer');
  const [message, setMessage] = useState('');
  const [isError, setIsError] = useState(false);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');
    setIsError(false);

    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          employee_id: employeeId.trim(),
          username: username.trim(),
          email: email.trim() || undefined,
          password,
          role: roleToBackend(role)
        })
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || '建立帳號失敗');
      }

      setIsError(false);
      setMessage(`建立成功，可以用員編 ${data.employee_id} 登入`);
      setEmployeeId('');
      setUsername('');
      setEmail('');
      setPassword('secret123');
      setRole('developer');
    } catch (error: unknown) {
      setIsError(true);
      setMessage(error instanceof Error ? error.message : '伺服器連線錯誤');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-light min-vh-100">
      <div style={Styles.styles.header}>
        <span>Job scheduler System</span>
        <button
          className="btn btn-light btn-sm px-3"
          onClick={() => navigate('/')}
          style={Styles.homeLoginLogoutStyles.style}
        >
          回登入頁
        </button>
      </div>

      <div style={{ padding: '40px', maxWidth: '560px', margin: '0 auto' }}>
        <h2>測試用新增帳號</h2>
        <p style={{ color: '#666' }}>這頁用來快速建立測試帳號，送到 /api/auth/register。</p>
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
          <input
            type="text"
            value={employeeId}
            onChange={(e) => setEmployeeId(e.target.value)}
            required
            placeholder="員工編號，例如 dev001"
            className="form-control"
          />
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            placeholder="姓名"
            className="form-control"
          />
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Email，可留空"
            className="form-control"
          />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={6}
            placeholder="密碼"
            className="form-control"
          />
          <select
            value={role}
            onChange={(e) => setRole(e.target.value as Role)}
            className="form-select"
          >
            <option value="developer">Developer</option>
            <option value="operator">Operator</option>
            <option value="admin">Admin</option>
          </select>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? '建立中...' : '建立測試帳號'}
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
