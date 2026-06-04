import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { loginStyles } from './Style';
import { getStoredUser, storeUserFromTokenResponse } from '../api';
import { type User, type TokenResponse } from '../types/types';

type LoginStep =
  | 'checkId'
  | 'forgotPassword'
  | 'forgotSent'
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
  const [resetToken, setResetToken] = useState('');
  const [counter, setCounter] = useState(0);
  const [errMessage, setErrMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const token = new URLSearchParams(globalThis.location.search).get('reset_token');
    if (token) {
      setResetToken(token);
      setStep('resetPassword');
      return;
    }

    const savedUser = getStoredUser();
    if (savedUser) {
      console.log('偵測到已登入狀態，自動跳轉。');
      const user: User = savedUser;
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

      const userData = (await response.json()) as TokenResponse;
      storeUserFromTokenResponse(userData);

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

  const forgotPasswordHandler = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setErrMessage('');

    const trimmedId = id.trim();
    setId(trimmedId);

    try {
      const response = await fetch('/api/auth/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ employee_id: trimmedId })
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Can not find ID');
      }

      if (data.status === 'missing_email') {
        setErrMessage('此帳號未綁定 email，請聯絡管理員重設密碼');
        return;
      }

      setStep('forgotSent');
    } catch (error) {
      setErrMessage(error instanceof Error ? error.message : '忘記密碼流程失敗，請稍後再試');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const resetPasswordHandler = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setErrMessage('');

    if (!resetToken) {
      setErrMessage('重設連結無效，請重新申請忘記密碼');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch('/api/auth/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: resetToken, new_password: password })
      });

      if (!response.ok) {
        throw new Error('Reset password failed');
      }

      const data = await response.json();
      if (data.employee_id) {
        setId(data.employee_id);
      }
      setPassword('');
      setStep('resetSuccess');
      setCounter(0);
      globalThis.history.replaceState({}, document.title, globalThis.location.pathname);
    } catch (error) {
      setErrMessage('重設密碼失敗！請確認連結是否過期，或重新申請一次');
      setPassword('');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (step === 'registerSuccess' || step === 'resetSuccess') {
      const timer = setTimeout(() => {
        setStep(id ? 'loginPassword' : 'checkId');
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [id, step]);

  useEffect(() => {
    if (step === 'loginSuccess') {
      const timer = setTimeout(() => {
        const savedUser = getStoredUser();
        if (savedUser) {
          const user: User = savedUser;
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

              {step === 'forgotPassword' && (
                <form onSubmit={forgotPasswordHandler} style={loginStyles.formContainer}>
                  <div style={loginStyles.title}>忘記密碼</div>
                  <p style={loginStyles.subtitle}>
                    請輸入員工編號，我們會將密碼重設連結寄到帳號綁定的 email。
                  </p>
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
                      {loading ? '處理中...' : '寄送連結'}
                    </button>
                  </div>
                </form>
              )}

              {step === 'forgotSent' && (
                <div style={loginStyles.successContainer}>
                  <h3 style={loginStyles.successTitle}>重設連結已寄出</h3>
                  <p style={loginStyles.successText}>
                    請到帳號綁定的 email 收信，並使用信中的連結重設密碼。
                  </p>
                  <button
                    type="button"
                    className="custom-btn"
                    style={{ ...loginStyles.primaryBtn, marginTop: '20px' }}
                    onClick={backToIdHandler}
                  >
                    回登入頁
                  </button>
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
                  <div style={loginStyles.title}>重新設定密碼</div>
                  <p style={loginStyles.subtitle}>請輸入新的密碼，完成後即可回到登入頁。</p>
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
                        setResetToken('');
                        globalThis.history.replaceState(
                          {},
                          document.title,
                          globalThis.location.pathname
                        );
                        setStep(id ? 'loginPassword' : 'checkId');
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
                    setPassword('');
                    setErrMessage('');
                    setStep('forgotPassword');
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
