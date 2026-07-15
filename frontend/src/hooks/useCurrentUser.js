import { ref, onMounted } from 'vue';
import { userInfo } from '@/api/user.js';
import { ElMessage } from 'element-plus';
import { useRouter } from 'vue-router';

export function useCurrentUser() {
    const user = ref(null);
    const loading = ref(false);
    const router = useRouter();

    const fetchUser = async () => {
        // 如果本地没有登录凭证，直接跳转登录页
        const loginUser = localStorage.getItem('loginUser');
        if (!loginUser) {
            await router.push('/');
            return;
        }

        loading.value = true;
        try {
            const result = await userInfo();
            if (result.code) {
                user.value = result.data;
            } else {
                ElMessage.error(result.msg || '获取用户信息失败');
                // Token 过期或无效时清除本地存储并跳转登录
                localStorage.removeItem('loginUser');
                await router.push('/');
            }
        } catch (error) {
            console.error('获取用户信息异常:', error);
            ElMessage.error('网络异常，请检查服务是否正常');
        } finally {
            loading.value = false;
        }
    };

    // 进入页面时自动获取
    onMounted(fetchUser);

    return {
        user,
        loading,
        fetchUser, // 暴露方法，支持手动刷新
    };
}