/**
 * Axios 请求封装
 *
 * 统一配置基础 URL、超时时间和响应拦截器，
 * 自动提取响应数据并处理错误提示。
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建 Axios 实例，基础路径指向后端 API
const request = axios.create({
  baseURL: '/api',
  timeout: 30000,  // 30 秒超时
})

// 响应拦截器
request.interceptors.response.use(
  // 成功响应：直接返回 data 字段，简化调用方代码
  (response) => response.data,
  // 错误响应：提取错误信息并弹出提示
  (error) => {
    const msg = error.response?.data?.detail || error.message || '请求失败'
    ElMessage.error(msg)
    return Promise.reject(error)
  }
)

export default request
