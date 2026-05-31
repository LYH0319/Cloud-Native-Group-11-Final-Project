import { defineConfig } from 'vite';
import react, { reactCompilerPreset } from '@vitejs/plugin-react';
import babel from '@rolldown/plugin-babel';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), babel({ presets: [reactCompilerPreset()] })],
  server: {
    proxy: {
      // 當前端請求開頭為 /api 時，轉發到後端伺服器
      '/api': {
        target: 'http://127.0.0.1:8000', // 👈 這裡請改成你 Python 後端實際運行的網址與 Port
        changeOrigin: true
        // 如果你後端路由本來就有包含 /api (如 @router.post("/api/auth/check-id"))，這行就不用寫
        // rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
});
