import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { styles } from './Style';
import { type Role, type User } from '../types/types';

interface MockUser {
  id: string;
  password?: string;
  role: Role;
}

const COMPANY_DB: Record<string, MockUser> = {
  '001': { id: '001', role: 'developer' },
  '002': { id: '002', role: 'operator' }
};

const getMockDB = (): Record<string, MockUser> => {
    const db = localStorage.getItem('mock_db');
    if (!db) {
        localStorage.setItem('mock_db', JSON.stringify(COMPANY_DB));
        return COMPANY_DB;
    }
    return JSON.parse(db);
};

const saveMockDB = (db: Record<string, MockUser>) => {
    localStorage.setItem('mock_db', JSON.stringify(db));
};

type LoginStep = 'checkId' | 'registerPassword' | 'registerSuccess' | 'loginPassword' | 'loginSuccess';

export const Login = () => {
    const [step, setStep] = useState<LoginStep>('checkId');
    const [id, setId] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    useEffect(() => {
        const savedUser = localStorage.getItem('user');
        if (savedUser) {
            console.log('偵測到已登入狀態，自動跳轉。');
            navigate('/');
        }
    }, [navigate]);

    const checkIdHandler = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setLoading(true);

        const trimmedId = id.trim();
        setId(trimmedId);

        try {
            // const response = await fetch('/api/auth/check-id', {
            //     method: 'POST',
            //     headers: { 'Content-Type': 'application/json'},
            //     body: JSON.stringify({ trimmedId })
            // })

            // if(!response.ok) {
            //     throw new Error('can not find ID');
            // } 

            // const data = await response.json();

            // if(data.isRegistered) {
            //     setStep('loginPassword');
            // }
            // else {
            //     setStep('registerPassword');
            // }

            const db = getMockDB();
            const user = db[trimmedId];
            if (!user) {
                throw new Error('can not find ID');
            }
            if (user.password) {
                setStep('loginPassword');
            }
            else {
                setStep('registerPassword');
            }

        }
        catch (error) {
            alert('ID not found. Please try again.');
            console.error(error);
        }
        finally {
            setLoading(false);
        }
    };

    const registerPasswordHandler = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setLoading(true);

        try {
            // const response = await fetch('/api/auth/register-password', {
            //     method: 'POST',
            //     headers: { 'Content-Type': 'application/json'},
            //     body: JSON.stringify({ id, password })
            // })

            // if(!response.ok) {
            //     throw new Error('registration failed');
            // }
            const db = getMockDB();            
            if (!db[id]) {
                throw new Error('registration failed');
            }

            db[id].password = password;
            saveMockDB(db);

            setPassword('');
            setStep('registerSuccess');
        }
        catch (error) {
            alert('Registration failed. Please try again.');
            console.error(error);
        }
        finally {
            setLoading(false);
        }
    };

    const loginPasswordHandler = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setLoading(true);

        try {
            // const response = await fetch('/api/auth/login-password', {
            //     method: 'POST',
            //     headers: { 'Content-Type': 'application/json'},
            //     body: JSON.stringify({ id, password })
            // })

            // if(!response.ok) {
            //     throw new Error('password incorrect');
            // }

            // const data = await response.json();
            // localStorage.setItem('user', JSON.stringify(data));
            const db = getMockDB();            

            if (db[id].password !== password) {
                throw new Error('password incorrect');
            }

            const userData: User = {
                id: db[id].id,
                role: db[id].role
            }
            localStorage.setItem('user', JSON.stringify(userData));

            setStep('loginSuccess');
        }
        catch (error) {
            alert('Login failed. Please try again.');
            console.error(error);
        }
        finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (step === 'registerSuccess') {
            const timer = setTimeout(() => {
                setStep('loginPassword');
            }, 2000);

            return () => clearTimeout(timer);
        }
    }, [step]);

    useEffect(() => {
        if (step === 'loginSuccess') {
            const timer = setTimeout(() => {
                navigate('/');
            }, 3000);

            return () => clearTimeout(timer);
        }
    }, [step, navigate]);

    const backToIdHandler = () => {
        setPassword('');
        setStep('checkId');
    }

    return (
      <div style={{ minHeight: '100vh', backgroundColor: '#fff' }}>
        <style>{`
          .custom-btn {
            transition: filter 0.2s ease !important;
          }
          .custom-btn:hover {
            filter: brightness(0.88) !important; /* 滑鼠移入：亮度變為 88% (稍微變暗) */
          }
          .custom-btn:active {
            filter: brightness(0.75) !important; /* 滑鼠點擊：亮度變為 75% (更有點擊感) */
          }
        `}</style>

        <div style={styles.header}>Job scheduler System</div>

        <div style={styles.container}>

          {step === 'checkId' && (
            <form onSubmit={checkIdHandler} style={styles.buttonForm}>
              <h2 style={styles.title}>登入</h2>
              <input 
                type="text" 
                style={styles.input}
                placeholder="輸入員工編號"
                value={id} 
                onChange={(e) => setId(e.target.value)} 
                required 
              />
              <button type="submit" className="custom-btn" style={styles.primaryBtn} disabled={loading}>
                {loading ? '檢查中...' : '登入'}
              </button>
              <button type="button" className="custom-btn" style={styles.primaryBtn} onClick={() => navigate('/')} disabled={loading}>
                回首頁
              </button>
            </form>
          )}

          {step === 'registerPassword' && (
            <form onSubmit={registerPasswordHandler} style={styles.buttonForm}>
              <h2 style={styles.title}>Hi~ 員工{id}！歡迎使用 Job Scheduler System</h2>
              <p className="text-muted small mb-2">請設定您的新密碼</p>
              <input 
                type="password" 
                style={styles.input}
                placeholder="輸入新密碼"
                value={password} 
                onChange={(e) => setPassword(e.target.value)} 
                required 
              />
              <button type="submit" className="custom-btn" style={styles.primaryBtn} disabled={loading}>
                {loading ? '處理中...' : '確認'}
              </button>
              <button type="button" className="custom-btn" style={styles.primaryBtn} onClick={backToIdHandler} disabled={loading}>
                上一步
              </button>
              <button type="button" className="custom-btn" style={styles.primaryBtn} onClick={() => navigate('/')} disabled={loading}>
                回首頁
              </button>
            </form>
          )}

          {step === 'registerSuccess' && (
            <div style={{ textAlign: 'center', paddingTop: '40px' }}>
              <div style={{ display: 'inline-block', marginBottom: '20px' }}>
                <svg 
                  width="64" 
                  height="64" 
                  viewBox="0 0 64 64" 
                  fill="none" 
                  xmlns="http://www.w3.org/2000/svg"
                >
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
              <h3 style={{ color: '#198754', marginTop: '20px', fontWeight: 'bold' }}>密碼設定成功！</h3>
              <p style={{ color: '#a0a0a0', fontSize: '16px' }}>請再次輸入密碼登入系統</p>
            </div>
          )}

          {step === 'loginPassword' && (
            <form onSubmit={loginPasswordHandler} style={styles.buttonForm}>
              <h2 style={styles.title}>歡迎回來！員工 {id}</h2>
              <input 
                type="password" 
                style={styles.input}
                placeholder="輸入密碼"
                value={password} 
                onChange={(e) => setPassword(e.target.value)} 
                required 
              />
              <button type="submit" className="custom-btn" style={styles.primaryBtn} disabled={loading}>
                {loading ? '登入中...' : '確認'}
              </button>
              <button type="button" className="custom-btn" style={styles.primaryBtn} onClick={backToIdHandler} disabled={loading}>
                上一步
              </button>
              <button type="button" className="custom-btn" style={styles.primaryBtn} onClick={() => navigate('/')} disabled={loading}>
                回首頁
              </button>
            </form>
          )}

          {step === 'loginSuccess' && (
            <div style={{ textAlign: 'center', paddingTop: '40px' }}>
              <div className="spinner-border text-success" role="status" style={{ width: '3rem', height: '3rem' }}>
                <span className="visually-hidden">Loading...</span>
              </div>
              <h3 style={{ color: '#198754', marginTop: '20px', fontWeight: 'bold' }}>登入成功！</h3>
              <p style={{ color: '#a0a0a0', fontSize: '12px' }}>正在為您導向主頁，請稍候...</p>
            </div>
          )}
          
        </div>
      </div>
    );
}