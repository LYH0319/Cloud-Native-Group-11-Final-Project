import { useState } from 'react';
import { type User, type JobBody } from '../types/types';

export const Developer = () => {
  const [method, setMethod] = useState('POST');
  const [endpoint, setEndpoint] = useState('');
  const [jsonBody, setJsonBody] = useState('');

  const user: User = JSON.parse(localStorage.getItem('user') || '{}');

  const handleSubmit = async () => {
    try {
      const parsedBody: JobBody = JSON.parse(jsonBody);
      const payload = {
        method,
        endpoint,
        headers: { "Content-Type": "application/json" },
        body: parsedBody
      };

      const res = await fetch('http://localhost:8000/api/jobs', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'x-emp-id': user.id 
        },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      alert(data.message || '建立成功');
    } catch (err) {
      alert('JSON 格式錯誤或連線失敗！');
    }
  };

  return (
    <div className="p-4">
      <h2>開發者控制台</h2>
      <hr />
      <h4>註冊新 Job</h4>
      <div className="row">
        <div className="col-md-6">
          <input type="text" className="form-control mb-2" placeholder="Method (ex: POST)" value={method} onChange={e => setMethod(e.target.value)} />
          <input type="text" className="form-control mb-2" placeholder="Endpoint (ex: /v1/run)" value={endpoint} onChange={e => setEndpoint(e.target.value)} />
          <textarea 
            className="form-control mb-2" 
            rows={6} 
            placeholder={`填入 JobBody JSON，例如:\n{\n  "command": "echo hello",\n  "schedule": "0 0 * * *",\n  "retry_policy": 3,\n  "timeout_seconds": 60\n}`}
            value={jsonBody}
            onChange={e => setJsonBody(e.target.value)}
          />
          <button onClick={handleSubmit} className="btn btn-success">註冊 Job</button>
        </div>
      </div>
    </div>
  );
};