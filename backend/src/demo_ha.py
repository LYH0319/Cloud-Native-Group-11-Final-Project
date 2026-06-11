import requests
import time
from datetime import datetime

# 請確認這是你們 Load Balancer (VM1) 轉發到後端的 API 網址
# 假設 /api/health 是後端的健康檢查路由
TARGET_URL = "http://192.168.10.4:8000/api/health"

success_count = 0
fail_count = 0

print(f"🚀 開始對 {TARGET_URL} 進行連續壓測...")
print("-" * 50)

try:
    while True:
        try:
            # 設定 timeout 為 2 秒，如果超過就視為失敗
            response = requests.get(TARGET_URL, timeout=2)
            if response.status_code == 200:
                success_count += 1
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ 請求成功 (200 OK) | 累積成功: {success_count}")
            else:
                fail_count += 1
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ 狀態碼異常 ({response.status_code}) | 累積失敗: {fail_count}")
        
        except requests.exceptions.RequestException as e:
            fail_count += 1
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ 連線失敗 (Nginx 正在切換節點或後端全掛) | 累積失敗: {fail_count}")
        
        time.sleep(2.0) # 每 2.0 秒打一次，避免把 VM 灌爆

except KeyboardInterrupt:
    print("\n" + "=" * 50)
    print(f"🛑 壓測結束。總結報告：")
    print(f"總請求數: {success_count + fail_count}")
    print(f"✅ 成功: {success_count}")
    print(f"❌ 失敗: {fail_count}")
    print("=" * 50)