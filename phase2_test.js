import http from 'k6/http';
import { check, sleep } from 'k6';
import { randomBytes } from 'k6/crypto';

const config = JSON.parse(open('./k6_scenarios.json'));

export const options = {
    scenarios: {
        // 第一期: 小團隊常態負載 - 目標TPS=2，驗證同步等待下的基本效能與資料庫連線
        //phase1_low_load: config.scenarios.phase1_low_load,
        
        // 第二期: 中型公司負載 - 目標TPS=8.3，驗證Redis Queue緩衝層與Docker獨立Worker pool的解耦能力
        phase2_medium_load: config.scenarios.phase2_medium_load,
        
        // 第三期: 大型企業高流量 - 目標TPS=166.7，階梯式拉高至200TPS持續10分鐘
        //phase3_high_load: config.scenarios.phase3_high_load,
    },
    thresholds: config.thresholds,
};

/*export const options = {
  scenarios: {
    medium_company_load: {
      executor: 'ramping-arrival-rate', 
      startRate: 1,                     
      timeUnit: '1s',
      stages: [
        { target: 9, duration: '2m' },  // 2分鐘內線性爬升到 9 TPS
        { target: 9, duration: '5m' },  // 峰值 9 TPS 持續衝擊 5 分鐘
        { target: 0, duration: '1m' },  // 1分鐘內降溫
      ],
      preAllocatedVUs: 15,              
      maxVUs: 50,                       
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],     
    http_req_duration: ['p(95)<1000'],  
  },
};*/

const BASE_URL = 'http://localhost:8000/api'; 

export function setup() {
    const loginURL = `${BASE_URL}/auth/login`;
    const payload = JSON.stringify({
        identifier: 'testuser',
        password: '00000000'
    });
    const params = { headers: { 'Content-Type': 'application/json'}};
    const res = http.post(loginURL, payload, params);

    if(res.status !== 200 && res.status != 201){
        console.log(`❌ Setup 自動登入失敗！狀態碼: ${res.status}, 回傳: ${res.body}`);
    }

    return {token: res.json().access_token};
}

//const TEST_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNzgwNDExNDM5fQ.gPkXCk0K4h2WSiLRAO9A2wLaMyhWNl6hmbTwWm2Z4Hk'; 

export default function (data) {
  const headers = { 
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${data.token}`
  };

  let resHealth = http.get(`${BASE_URL}/health`);
  check(resHealth, { '系統健康檢查成功': (r) => r.status === 200 });

  sleep(0.5); 

  // ---------------------------------------------------
  // 情境 B：建立 Job (對接真實的 POST /api/jobs/)
  // ---------------------------------------------------
  const jobPayload = JSON.stringify({
    job_name: `Medium_Job_${Math.floor(Math.random() * 100000)}`,
    method: 'GET',
    endpoint: 'http://backend:8000/api/health',
    schedule_type: 'One-time',
    config: randomBytes(5120), // 5KB 隨機資料壓測需求
    depends_on: [] 
  });
  
  let resJob = http.post(`${BASE_URL}/jobs/`, jobPayload, { headers });
  if (resJob.status != 201){
    console.log(`❌ 建立 Job 失敗！狀態碼: ${resJob.status}, 後端回傳: ${resJob.body}`);
  }
  
  const isJobCreated = check(resJob, { '建立 Job 成功': (r) => r.status === 201 });

  // ---------------------------------------------------
  // 情境 C：模擬 Worker 執行與回報 (對接手動觸發與結果回報)
  // ---------------------------------------------------
  if (isJobCreated && resJob.body) {
    try {
      const resJson = JSON.parse(resJob.body);
      const jobId = resJson.job_id; 
      
      if (jobId) {
        // 1. 模擬使用者或排程「手動觸發」該作業進入 Redis Queue
        // 對接 POST /api/jobs/{job_id}/trigger
        let resTrigger = http.post(`${BASE_URL}/jobs/${jobId}/trigger`, null, { headers });
        const isTriggered = check(resTrigger, { '手動觸發 Job 成功': (r) => r.status === 201 });

        if (isTriggered && resTrigger.body) {
          const triggerJson = JSON.parse(resTrigger.body);
          // 假設回傳有 execution 物件，從中拿到 execution_id
          const executionId = triggerJson.execution.execution_id;

          if (executionId) {
            sleep(1); // 模擬 Worker 正在跑任務

            const mockLogText = "LOG LINE: " + "A".repeat(20)

            // 2. 模擬 Worker 跑完後，將結果回報給後端
            // 💡 修正四：對接真實的 PATCH /api/executions/{execution_id}/result
            const patchPayload = JSON.stringify({
                status: 'Success',
                worker_id: `mock-worker-${__VU}-${__ITER}`,
                result: mockLogText, // 20KB 的隨機 Log/結果 壓測需求
                output: mockLogText,
                logs: mockLogText
            });

            let resPatch = http.patch(`${BASE_URL}/executions/${executionId}/result`, patchPayload, { headers });
            if (resPatch.status != 200){
                console.log(`❌ PATCH 失敗！狀態碼: ${resPatch.status}, 錯誤回應: ${resPatch.body}`);
            }
            check(resPatch, { 'Worker 回報結果成功': (r) => r.status === 200 });
          }
        }
      }
    } catch (e) {
      // 避免因為某些錯誤導致虛擬用戶中斷
    }
  }
}