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
    const token = new URLSearchParams(window.location.search).get('reset_token');
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
      window.history.replaceState({}, document.title, window.location.pathname);
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
    <div className="login-page" style={loginStyles.pageContainer}>
      <style>{`
          .login-page,
          .login-shell,
          .login-white-gap,
          .login-frame {
            max-width: 100%;
          }

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

          @media (max-width: 900px) {
            .login-page {
              height: auto !important;
              min-height: 100svh !important;
              overflow-y: auto !important;
              align-items: stretch !important;
            }

            .login-shell {
              height: auto !important;
              min-height: 100svh !important;
              padding: 18px !important;
            }

            .login-white-gap {
              height: auto !important;
              min-height: calc(100svh - 36px) !important;
              padding: 14px !important;
            }

            .login-frame {
              height: auto !important;
              min-height: calc(100svh - 64px) !important;
              flex-direction: column !important;
              align-items: stretch !important;
              justify-content: center !important;
              gap: 24px !important;
              padding: 22px !important;
            }

            .login-brand-panel,
            .login-form-panel {
              width: 100% !important;
              height: auto !important;
            }

            .login-brand-box {
              width: 100% !important;
              height: auto !important;
              min-height: 130px !important;
              padding: 18px 12px !important;
              flex-direction: row !important;
              flex-wrap: wrap !important;
              gap: 8px 16px !important;
            }

            .login-brand-text {
              width: auto !important;
              margin: 0 !important;
              font-size: 34px !important;
              line-height: 1.1 !important;
            }

            .login-form-panel {
              justify-content: flex-start !important;
              padding-left: 0 !important;
              padding-right: 0 !important;
            }

            .login-title {
              font-size: 28px !important;
              line-height: 1.25 !important;
            }

            .login-input {
              font-size: 18px !important;
              padding: 13px 16px !important;
            }

            .login-actions {
              justify-content: stretch !important;
            }

            .login-actions .custom-btn {
              flex: 1 1 0;
              min-width: 0;
            }

            .login-forgot {
              position: static !important;
              margin-top: 18px !important;
              text-align: right !important;
            }
          }

          @media (max-width: 560px) {
            .login-shell {
              padding: 10px !important;
            }

            .login-white-gap {
              min-height: calc(100svh - 20px) !important;
              padding: 8px !important;
            }

            .login-frame {
              min-height: calc(100svh - 36px) !important;
              border-width: 5px !important;
              padding: 18px 14px !important;
              gap: 20px !important;
            }

            .login-brand-box {
              min-height: 96px !important;
              padding: 14px 10px !important;
              border-width: 4px !important;
              outline-width: 4px !important;
              gap: 6px 10px !important;
            }

            .login-brand-text {
              font-size: 25px !important;
            }

            .login-title {
              font-size: 24px !important;
              margin-bottom: 14px !important;
            }

            .login-subtitle,
            .login-success-text {
              font-size: 14px !important;
              line-height: 1.5 !important;
            }

            .login-input {
              font-size: 16px !important;
              padding: 12px 14px !important;
            }

            .login-actions {
              flex-direction: column-reverse !important;
              gap: 10px !important;
            }

            .login-actions .custom-btn,
            .login-success .custom-btn {
              width: 100% !important;
              box-sizing: border-box !important;
            }

            .custom-btn {
              font-size: 16px !important;
              padding: 11px 18px !important;
            }

            .login-forgot {
              text-align: center !important;
            }
          }
        `}</style>

      <div className="login-shell" style={loginStyles.outerBox}>
        <div className="login-white-gap" style={loginStyles.whiteGap}>
          <div className="login-frame" style={loginStyles.innerBorder}>
            {/* 左側：系統名稱區塊 */}
            <div className="login-brand-panel" style={loginStyles.leftPanel}>
              <div className="login-brand-box" style={loginStyles.leftBox}>
                {/* 改用 div 替代 h1，避免瀏覽器預設的 margin 撐開間距 */}
                <div className="login-brand-text" style={loginStyles.leftBoxText}>
                  Job
                </div>
                <div className="login-brand-text" style={loginStyles.leftBoxText}>
                  Scheduler
                </div>
                <div className="login-brand-text" style={loginStyles.leftBoxText}>
                  System
                </div>
              </div>
            </div>

            {/* 右側：動態表單區塊 */}
            <div className="login-form-panel" style={loginStyles.rightPanel}>
              {step === 'checkId' && (
                <form className="login-form" onSubmit={checkIdHandler} style={loginStyles.formContainer}>
                  <div className="login-title" style={loginStyles.title}>
                    歡迎使用
                  </div>
                  <input
                    type="text"
                    className="login-input"
                    style={loginStyles.input}
                    placeholder="輸入您的員工編號"
                    value={id}
                    onChange={(e) => setId(e.target.value)}
                    required
                  />

                  {errMessage && <div style={loginStyles.errorMsg}>{errMessage}</div>}

                  <div className="login-actions" style={loginStyles.buttonContainer}>
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
                <form
                  className="login-form"
                  onSubmit={registerPasswordHandler}
                  style={loginStyles.formContainer}
                >
                  <div className="login-title" style={{ ...loginStyles.title, fontSize: '24px' }}>
                    Hi~ 員工{id}！歡迎使用
                  </div>
                  <input
                    type="password"
                    className="login-input"
                    style={loginStyles.input}
                    placeholder="輸入您的新密碼"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />

                  {errMessage && <div style={loginStyles.errorMsg}>{errMessage}</div>}

                  <div className="login-actions" style={loginStyles.buttonContainer}>
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
                <div className="login-success" style={loginStyles.successContainer}>
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
                  <h3 className="login-title" style={loginStyles.successTitle}>
                    密碼設定成功！
                  </h3>
                  <p className="login-success-text" style={loginStyles.successText}>
                    請再次輸入密碼登入系統
                  </p>
                </div>
              )}

              {step === 'forgotPassword' && (
                <form
                  className="login-form"
                  onSubmit={forgotPasswordHandler}
                  style={loginStyles.formContainer}
                >
                  <div className="login-title" style={loginStyles.title}>
                    忘記密碼
                  </div>
                  <p className="login-subtitle" style={loginStyles.subtitle}>
                    請輸入員工編號，我們會將密碼重設連結寄到帳號綁定的 email。
                  </p>
                  <input
                    type="text"
                    className="login-input"
                    style={loginStyles.input}
                    placeholder="輸入您的員工編號"
                    value={id}
                    onChange={(e) => setId(e.target.value)}
                    required
                  />

                  {errMessage && <div style={loginStyles.errorMsg}>{errMessage}</div>}

                  <div className="login-actions" style={loginStyles.buttonContainer}>
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
                <div className="login-success" style={loginStyles.successContainer}>
                  <h3 className="login-title" style={loginStyles.successTitle}>
                    重設連結已寄出
                  </h3>
                  <p className="login-success-text" style={loginStyles.successText}>
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
                <form
                  className="login-form"
                  onSubmit={loginPasswordHandler}
                  style={loginStyles.formContainer}
                >
                  <div className="login-title" style={loginStyles.title}>
                    歡迎回來！員工 {id}
                  </div>
                  <input
                    type="password"
                    className="login-input"
                    style={loginStyles.input}
                    placeholder="輸入您的密碼"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />

                  {errMessage && <div style={loginStyles.errorMsg}>{errMessage}</div>}

                  <div className="login-actions" style={loginStyles.buttonContainer}>
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
                <form
                  className="login-form"
                  onSubmit={resetPasswordHandler}
                  style={loginStyles.formContainer}
                >
                  <div className="login-title" style={loginStyles.title}>
                    重新設定密碼
                  </div>
                  <p className="login-subtitle" style={loginStyles.subtitle}>
                    請輸入新的密碼，完成後即可回到登入頁。
                  </p>
                  <input
                    type="password"
                    className="login-input"
                    style={loginStyles.input}
                    placeholder="輸入您的新密碼"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />

                  {errMessage && <div style={loginStyles.errorMsg}>{errMessage}</div>}

                  <div className="login-actions" style={loginStyles.buttonContainer}>
                    <button
                      type="button"
                      className="custom-btn"
                      style={loginStyles.primaryBtn}
                      onClick={() => {
                        setPassword('');
                        setErrMessage('');
                        setResetToken('');
                        window.history.replaceState({}, document.title, window.location.pathname);
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
                <div className="login-success" style={loginStyles.successContainer}>
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
                  <h3 className="login-title" style={loginStyles.successTitle}>
                    密碼重設成功！
                  </h3>
                  <p className="login-success-text" style={loginStyles.successText}>
                    請使用新密碼重新登入...
                  </p>
                </div>
              )}

              {step === 'loginSuccess' && (
                <div className="login-success" style={loginStyles.successContainer}>
                  <h3 className="login-title" style={loginStyles.successTitle}>
                    登入成功！
                  </h3>
                  <p className="login-success-text" style={loginStyles.successText}>
                    正在為您導向主頁，請稍候...
                  </p>
                </div>
              )}
            </div>

            {/* 絕對定位的右下角「忘記密碼」區塊 */}
            {(step === 'checkId' || step === 'loginPassword') && (
              <div className="login-forgot" style={loginStyles.forgotPasswordContainer}>
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
