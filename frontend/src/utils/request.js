import axios from 'axios'
import {ElMessage} from "element-plus"
import router from "@/router/index"

//创建axios实例对象
const request = axios.create({
    baseURL: '/api',
    timeout: 600000
})

// axios的请求 request 拦截器 - 获取localStorage中的token, 在请求头中增加Authorization请求头
request.interceptors.request.use(
    (config) => {
        const loginUser = JSON.parse(localStorage.getItem('loginUser'))
        if (loginUser && loginUser.token) {
            // 修改此处：使用标准的 Authorization 头，并添加 Bearer 前缀
            config.headers.Authorization = `Bearer ${loginUser.token}`
        }
        return config
    },
    (error) => { //失败回调
        return Promise.reject(error)
    }
)

//axios的响应 response 拦截器
request.interceptors.response.use(
    (response) => { //成功回调
        return response.data
    },
    (error) => { //失败回调
        if (error.response.status === 401) {
            ElMessage.error('登录超时，请重新登录')
            router.push('/user/login')
        } else {
            ElMessage.error('接口访问异常')
        }
        return Promise.reject(error)
    }
)

export default request