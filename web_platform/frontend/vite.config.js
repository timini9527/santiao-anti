import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    host: '0.0.0.0',
    proxy: {
      // 代理测试执行与探测接口
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      // 代理 Allure 静态测试报告资源
      '/allure': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      }
    }
  },
  build: {
    // 打包直接输出至后端的托管目录中，便于一键运行与打包发布
    outDir: path.resolve(__dirname, '../backend/static'),
    emptyOutDir: true
  }
})
