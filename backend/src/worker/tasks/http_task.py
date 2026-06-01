import time
import requests

def run_http_task(payload: dict, timeout_threshold: int):
    """
    【真正的 HTTP 任務執行器】
    依據傳入的參數，發送真實的網路請求，並精準捕捉回應狀態與耗時
    """
    method = payload.get("method", "GET").upper()
    endpoint = payload.get("endpoint")
    headers = payload.get("headers", {})
    body = payload.get("body", {})

    start_time = time.time()
    try:
        # 發送真實的 HTTP 請求，並套用系統傳入的超時門檻
        response = requests.request(
            method=method,
            url=endpoint,
            headers=headers,
            json=body if method in ["POST", "PUT", "PATCH"] else None,
            timeout=timeout_threshold
        )
        
        duration = time.time() - start_time
        
        # 根據 HTTP 狀態碼映射系統狀態
        if 200 <= response.status_code < 300:
            return {
                "status": "Success",
                "duration": duration,
                "error_message": "",
                "log": f"HTTP {response.status_code} SUCCESS\nResponse: {response.text[:1000]}"
            }
        else:
            return {
                "status": "Failed",
                "duration": duration,
                "error_message": f"HTTP Status Error: {response.status_code}",
                "log": f"HTTP {response.status_code} FAILED\nResponse: {response.text[:1000]}"
            }

    except requests.Timeout:
        # 精準捕捉網路連線超時
        return {
            "status": "Timeout",
            "duration": time.time() - start_time,
            "error_message": "HTTP Request Timeout exceeded threshold",
            "log": f"Request to {endpoint} timed out."
        }
    except Exception as e:
        # 捕捉其他網路異常（如 DNS 解析失敗、斷線）
        return {
            "status": "Failed",
            "duration": time.time() - start_time,
            "error_message": f"Network Error: {str(e)}",
            "log": f"Failed to connect to {endpoint}. Exception: {str(e)}"
        }