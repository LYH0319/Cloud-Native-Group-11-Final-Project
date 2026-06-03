import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiFetch, getStoredUser, roleFromBackend, roleToBackend } from '../api';
import { type BackendUser, type Role } from '../types/types';
import Styles from './Style';

export const Admin = () => {
  const [users, setUsers] = useState<BackendUser[]>([]);
  const [employeeId, setEmployeeId] = useState('');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('secret123');
  const [role, setRole] = useState<Role>('developer');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [isError, setIsError] = useState(false);
  const navigate = useNavigate();
  const currentUser = getStoredUser();

  const loadUsers = useCallback(async () => {
    try {
      const response = await apiFetch('/auth/users');
      if (response.status === 401 || response.status === 403) {
        localStorage.removeItem('user');
        navigate('/');
        return;
      }
      const data = (await response.json()) as BackendUser[];
      setUsers(data);
    } catch (error) {
      console.error(error);
      setIsError(true);
      setMessage('無法取得帳號清單');
    }
  }, [navigate]);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');
    setIsError(false);

    try {
      const response = await apiFetch('/auth/register', {
        method: 'POST',
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
        throw new Error(data.detail || '新增失敗');
      }

      setIsError(false);
      setMessage(`成功建立員工，編號: ${data.employee_id}`);
      setEmployeeId('');
      setUsername('');
      setEmail('');
      setPassword('secret123');
      setRole('developer');
      loadUsers();
    } catch (error: unknown) {
      setIsError(true);
      setMessage(error instanceof Error ? error.message : '伺服器連線錯誤');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (user: BackendUser) => {
    if (user.employee_id === currentUser?.employeeId) {
      alert('不能刪除目前登入的帳號');
      return;
    }
    if (!window.confirm(`確定要刪除 ${user.employee_id} 嗎？`)) {
      return;
    }

    try {
      const response = await apiFetch(`/auth/users/${user.user_id}`, {
        method: 'DELETE'
      });
      if (!response.ok) {
        let detail = '刪除失敗';
        try {
          detail = (await response.json()).detail || detail;
        } catch {
          // 204 responses do not contain JSON.
        }
        throw new Error(detail);
      }
      setIsError(false);
      setMessage(`已刪除帳號 ${user.employee_id}`);
      loadUsers();
    } catch (error: unknown) {
      setIsError(true);
      setMessage(error instanceof Error ? error.message : '伺服器連線錯誤');
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
              alert('登出成功');
              localStorage.removeItem('user');
              navigate('/');
            }}
            style={Styles.homeLoginLogoutStyles.style}
          >
            登出
          </button>

          <h2 className="fs-5 m-0 font-weight-bold">管理帳號介面</h2>
        </div>
      </div>

      <div className="container py-4">
        <div className="row g-4">
          <div className="col-lg-5">
            <h2>新增帳號</h2>
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
                placeholder="員工編號"
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
                placeholder="初始密碼，至少 6 碼"
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

              <button type="submit" disabled={loading} className="btn btn-primary">
                {loading ? '處理中...' : '確認新增帳號'}
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

          <div className="col-lg-7">
            <div className="d-flex justify-content-between align-items-center mb-2">
              <h2 className="m-0">帳號清單</h2>
              <button className="btn btn-outline-secondary btn-sm" onClick={loadUsers}>
                重新整理
              </button>
            </div>
            <div className="table-responsive bg-white shadow-sm rounded">
              <table className="table table-hover mb-0">
                <thead>
                  <tr>
                    <th>員工編號</th>
                    <th>姓名</th>
                    <th>角色</th>
                    <th>Email</th>
                    <th style={{ width: '90px' }}>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((user) => (
                    <tr key={user.user_id}>
                      <td>{user.employee_id}</td>
                      <td>{user.username}</td>
                      <td>{roleFromBackend(user.role)}</td>
                      <td>{user.email || '-'}</td>
                      <td>
                        <button
                          className="btn btn-outline-danger btn-sm"
                          onClick={() => handleDelete(user)}
                          disabled={user.employee_id === 'admin'}
                        >
                          刪除
                        </button>
                      </td>
                    </tr>
                  ))}
                  {users.length === 0 && (
                    <tr>
                      <td colSpan={5} className="text-center text-muted py-4">
                        目前沒有帳號資料
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
