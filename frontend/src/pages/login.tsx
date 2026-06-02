import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { loginStyles } from './Style';
import { type Role, type User } from '../types/types';

type LoginStep =
  | 'checkId'
  | 'registerPassword'
  | 'registerSuccess'
  | 'loginPassword'
  | 'loginSuccess'
  | 'resetPassword'
  | 'resetSuccess';

export const Login = () => {
  const [step, setStep] = useState<LoginStep>('checkId');
  const [id, setId] = useState('');
  const [password, setPassword] = useState('');
  const [counter, setCounter] = useState(0);
  const [errMessage, setErrMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const savedUser = localStorage.getItem('user');
    if (savedUser) {
      console.log('偵測到已登入狀態，自動跳轉。');
      const user: User = JSON.parse(savedUser);
      if (user.role === 'developer') {
        navigate('/developer');
      } else if (user.role === 'operator') {
        navigate('/operator');
      } else if (user.role === 'admin') {
        navigate('/admin');
      }
    }
  }, [navigate]);

  const backToIdHandler = () => {
    setPassword('');
    setCounter(0);
    setErrMessage('');
    setStep('checkId');
  };

  const backToHomeHandler = () => {
    setCounter(0);
    setId('');
    setPassword('');
    setErrMessage('');
    setStep('checkId');
    navigate('/');
  };

  const checkIdHandler = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setErrMessage('');

    const trimmedId = id.trim();
    setId(trimmedId);

    try {
      const response = await fetch('/api/auth/check-id', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ employee_id: trimmedId })
      });

      if (!response.ok) {
        throw new Error('Can not find ID');
      }

      const data = await response.json();

      if (data.isRegistered) {
        setStep('loginPassword');
      } else {
        setStep('registerPassword');
      }
      setCounter(0);
    } catch (error) {
      setErrMessage('查無此員工編號！請重新輸入');
      setId('');
      console.error(error);
      setCounter((prev) => prev + 1);
    } finally {
      setLoading(false);
    }
  };

  const registerPasswordHandler = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setErrMessage('');

    try {
      const response = await fetch('/api/auth/register-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ employee_id: id, password })
      });

      if (!response.ok) {
        throw new Error('Registration failed');
      }

      setPassword('');
      setStep('registerSuccess');
      setCounter(0);
    } catch (error) {
      setErrMessage('註冊失敗！請再試一次');
      setPassword('');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const loginPasswordHandler = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setErrMessage('');

    try {
      const response = await fetch('/api/auth/login-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ employee_id: id, password })
      });

      if (!response.ok) {
        throw new Error('Password incorrect');
      }

      const userData = await response.json();
      localStorage.setItem('user', JSON.stringify(userData));

      setStep('loginSuccess');
      setCounter(0);
    } catch (error) {
      if (counter >= 2) {
        setErrMessage('是不是忘記密碼了？可以點擊忘記密碼重新設定');
      } else {
        setErrMessage('密碼錯誤！請重新輸入');
      }
      setPassword('');
      console.error(error);
      setCounter((prev) => prev + 1);
    } finally {
      setLoading(false);
    }
  };

  const resetPasswordHandler = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setErrMessage('');

    try {
      const response = await fetch('/api/auth/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ employee_id: id, new_password: password })
      });

      if (!response.ok) {
        throw new Error('Reset password failed');
      }

      setPassword('');
      setStep('resetSuccess');
      setCounter(0);
    } catch (error) {
      setErrMessage('重設密碼失敗！請再試一次');
      setPassword('');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (step === 'registerSuccess' || step === 'resetSuccess') {
      const timer = setTimeout(() => {
        setStep('loginPassword');
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [step]);

  useEffect(() => {
    if (step === 'loginSuccess') {
      const timer = setTimeout(() => {
        const savedUser = localStorage.getItem('user');
        if (savedUser) {
          const user: User = JSON.parse(savedUser);
          if (user.role === 'developer') navigate('/developer');
          else if (user.role === 'operator') navigate('/operator');
          else if (user.role === 'admin') navigate('/admin');
        }
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [step, navigate]);

  return (
    <div style={loginStyles.pageContainer}>
      <style>{`
          .custom-btn {
            transition: filter 0.2s ease, transform 0.1s ease;
          }
          .custom-btn:hover:not(:disabled) { filter: brightness(1.2); }
          .custom-btn:active:not(:disabled) { transform: scale(0.97); }
          .custom-btn:disabled { opacity: 0.6; cursor: not-allowed; }
          
          .link-btn {
            background: none;
            border: none;
            color: #0f117a;
            text-decoration: none; 
            font-size: 16px;       /* 稍微放大，符合圖中比例 */
            font-weight: bold;     /* 改為粗體 */
            cursor: pointer;
            padding: 0;
            transition: opacity 0.2s ease;
          }
          .link-btn:hover { text-decoration: underline; opacity: 0.8; }
        `}</style>

      <div style={loginStyles.outerBox}>
        <div style={loginStyles.whiteGap}>
          <div style={loginStyles.innerBorder}>
            {/* 左側：系統名稱區塊 */}
            <div style={loginStyles.leftPanel}>
              <div style={loginStyles.leftBox}>
                {/* 改用 div 替代 h1，避免瀏覽器預設的 margin 撐開間距 */}
                <div style={loginStyles.leftBoxText}>Job</div>
                <div style={loginStyles.leftBoxText}>Scheduler</div>
                <div style={loginStyles.leftBoxText}>System</div>
              </div>
            </div>

            {/* 右側：動態表單區塊 */}
            <div style={loginStyles.rightPanel}>
              {step === 'checkId' && (
                <form onSubmit={checkIdHandler} style={loginStyles.formContainer}>
                  <div style={loginStyles.title}>歡迎使用</div>
                  <input
                    type="text"
                    style={loginStyles.input}
                    placeholder="輸入您的員工編號"
                    value={id}
                    onChange={(e) => setId(e.target.value)}
                    required
                  />

                  {errMessage && <div style={loginStyles.errorMsg}>{errMessage}</div>}

                  <div style={loginStyles.buttonContainer}>
                    <button
                      type="submit"
                      className="custom-btn"
                      style={loginStyles.primaryBtn}
                      disabled={loading}
                    >
                      {loading ? '檢查中' : '下一步'}
                    </button>
                  </div>
                </form>
              )}

              {step === 'registerPassword' && (
                <form onSubmit={registerPasswordHandler} style={loginStyles.formContainer}>
                  <div style={{ ...loginStyles.title, fontSize: '24px' }}>
                    Hi~ 員工{id}！歡迎使用
                  </div>
                  <input
                    type="password"
                    style={loginStyles.input}
                    placeholder="輸入您的新密碼"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />

                  {errMessage && <div style={loginStyles.errorMsg}>{errMessage}</div>}

                  <div style={loginStyles.buttonContainer}>
                    <button
                      type="button"
                      className="custom-btn"
                      style={loginStyles.primaryBtn}
                      onClick={backToIdHandler}
                      disabled={loading}
                    >
                      上一步
                    </button>
                    <button
                      type="submit"
                      className="custom-btn"
                      style={loginStyles.primaryBtn}
                      disabled={loading}
                    >
                      {loading ? '處理中...' : '下一步'}
                    </button>
                  </div>
                </form>
              )}

              {step === 'registerSuccess' && (
                <div style={loginStyles.successContainer}>
                  <div style={loginStyles.successIcon}>
                    <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
                      <circle cx="32" cy="32" r="32" fill="#198754" />
                      <path
                        d="M18 32L28 42L46 22"
                        stroke="white"
                        strokeWidth="5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  </div>
                  <h3 style={loginStyles.successTitle}>密碼設定成功！</h3>
                  <p style={loginStyles.successText}>請再次輸入密碼登入系統</p>
                </div>
              )}

              {step === 'loginPassword' && (
                <form onSubmit={loginPasswordHandler} style={loginStyles.formContainer}>
                  <div style={loginStyles.title}>歡迎回來！員工 {id}</div>
                  <input
                    type="password"
                    style={loginStyles.input}
                    placeholder="輸入您的密碼"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />

                  {errMessage && <div style={loginStyles.errorMsg}>{errMessage}</div>}

                  <div style={loginStyles.buttonContainer}>
                    <button
                      type="button"
                      className="custom-btn"
                      style={loginStyles.primaryBtn}
                      onClick={backToIdHandler}
                      disabled={loading}
                    >
                      上一步
                    </button>
                    <button
                      type="submit"
                      className="custom-btn"
                      style={loginStyles.primaryBtn}
                      disabled={loading}
                    >
                      {loading ? '登入中...' : '下一步'}
                    </button>
                  </div>
                </form>
              )}

              {step === 'resetPassword' && (
                <form onSubmit={resetPasswordHandler} style={loginStyles.formContainer}>
                  <div style={loginStyles.title}>
                    重新設定員工 <strong>{id}</strong> 的密碼
                  </div>
                  <input
                    type="password"
                    style={loginStyles.input}
                    placeholder="輸入您的新密碼"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />

                  {errMessage && <div style={loginStyles.errorMsg}>{errMessage}</div>}

                  <div style={loginStyles.buttonContainer}>
                    <button
                      type="button"
                      className="custom-btn"
                      style={loginStyles.primaryBtn}
                      onClick={() => {
                        setPassword('');
                        setErrMessage('');
                        setStep('loginPassword');
                        setCounter(0);
                      }}
                      disabled={loading}
                    >
                      上一步
                    </button>
                    <button
                      type="submit"
                      className="custom-btn"
                      style={loginStyles.primaryBtn}
                      disabled={loading}
                    >
                      {loading ? '重設中...' : '下一步'}
                    </button>
                  </div>
                </form>
              )}

              {step === 'resetSuccess' && (
                <div style={loginStyles.successContainer}>
                  <div style={loginStyles.successIcon}>
                    <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
                      <circle cx="32" cy="32" r="32" fill="#198754" />
                      <path
                        d="M18 32L28 42L46 22"
                        stroke="white"
                        strokeWidth="5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  </div>
                  <h3 style={loginStyles.successTitle}>密碼重設成功！</h3>
                  <p style={loginStyles.successText}>請使用新密碼重新登入...</p>
                </div>
              )}

              {step === 'loginSuccess' && (
                <div style={loginStyles.successContainer}>
                  <h3 style={loginStyles.successTitle}>登入成功！</h3>
                  <p style={loginStyles.successText}>正在為您導向主頁，請稍候...</p>
                </div>
              )}
            </div>

            {/* 絕對定位的右下角「忘記密碼」區塊 */}
            {(step === 'checkId' || step === 'loginPassword') && (
              <div style={loginStyles.forgotPasswordContainer}>
                <button
                  type="button"
                  className="link-btn"
                  onClick={() => {
                    if (!id) {
                      setErrMessage('請先輸入員工編號，再點擊忘記密碼');
                      return;
                    }
                    setPassword('');
                    setErrMessage('');
                    setStep('resetPassword');
                  }}
                >
                  忘記密碼?
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
