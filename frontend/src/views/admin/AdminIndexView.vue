<script setup>
import {onMounted, reactive, ref} from "vue";
import {useRouter} from "vue-router";
import {Bell, ChatSquare, Notebook, Refresh, Service, UserFilled} from "@element-plus/icons-vue";
import {getAllUsers} from "@/api/user.js";
import {getAllRoles} from "@/api/role.js";
import {getAllKnowledgeBases} from "@/api/knowledge_base.js";
import {getAllSessions} from "@/api/session.js";
import {getRecentAnnouncements} from "@/api/announcement.js";

const router = useRouter();
const loading = ref(false);
const loadFailed = ref(false);
const recentAnnouncements = ref([]);
const statistics = reactive({users: 0, roles: 0, knowledgeBases: 0, sessions: 0, announcements: 0});

const metricDefinitions = [
  {key: "users", label: "用户", icon: UserFilled, route: "admin-user"},
  {key: "roles", label: "角色", icon: Service, route: "admin-role"},
  {key: "knowledgeBases", label: "知识库", icon: Notebook, route: "admin-knowledgeBase"},
  {key: "sessions", label: "会话", icon: ChatSquare, route: "admin-session"},
  {key: "announcements", label: "公告", icon: Bell, route: "admin-announcement"}
];

const requireSuccessfulResponse = (response) => {
  if (response?.code !== 1) {
    throw new Error(response?.msg || "首页数据加载失败");
  }
  return response.data;
};

const loadDashboard = async () => {
  loading.value = true;
  loadFailed.value = false;

  try {
    const [userResponse, roleResponse, knowledgeBaseResponse, sessionResponse, announcementResponse] =
      await Promise.all([
        getAllUsers(1, 1),
        getAllRoles(1, 1),
        getAllKnowledgeBases(1, 1),
        getAllSessions(1, 1),
        getRecentAnnouncements(5)
      ]);

    const userData = requireSuccessfulResponse(userResponse);
    const roleData = requireSuccessfulResponse(roleResponse);
    const knowledgeBaseData = requireSuccessfulResponse(knowledgeBaseResponse);
    const sessionData = requireSuccessfulResponse(sessionResponse);
    const announcementData = requireSuccessfulResponse(announcementResponse);

    statistics.users = Number(userData.total) || 0;
    statistics.roles = Number(roleData.total) || 0;
    statistics.knowledgeBases = Number(knowledgeBaseData.total) || 0;
    statistics.sessions = Number(sessionData.total) || 0;
    statistics.announcements = Number(announcementData.total) || 0;
    recentAnnouncements.value = announcementData.list || [];
  } catch (error) {
    console.error("管理首页加载失败", error);
    loadFailed.value = true;
  } finally {
    loading.value = false;
  }
};

const navigateTo = async (routeName) => {
  await router.push({name: routeName});
};

const dateFormatter = new Intl.DateTimeFormat("zh-CN", {
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  hour12: false
});

const formatDate = (value) => {
  if (!value) return "-";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? String(value) : dateFormatter.format(date);
};

onMounted(loadDashboard);
</script>

<template>
  <div class="dashboard-page">
    <header class="dashboard-header">
      <h1>管理概览</h1>
      <el-button
        :icon="Refresh"
        circle
        :loading="loading"
        aria-label="刷新首页数据"
        title="刷新"
        @click="loadDashboard"
      />
    </header>

    <el-result v-if="loadFailed && !loading" icon="warning" title="首页数据加载失败">
      <template #extra>
        <el-button type="primary" @click="loadDashboard">重新加载</el-button>
      </template>
    </el-result>

    <template v-else>
      <section class="statistics-section" aria-labelledby="statistics-title">
        <h2 id="statistics-title">数据统计</h2>
        <div class="statistics-grid">
          <button
            v-for="metric in metricDefinitions"
            :key="metric.key"
            class="metric-item"
            type="button"
            :aria-label="`查看${metric.label}管理`"
            @click="navigateTo(metric.route)"
          >
            <span class="metric-icon"><component :is="metric.icon" /></span>
            <span class="metric-content">
              <el-skeleton v-if="loading" :rows="1" animated />
              <strong v-else>{{ statistics[metric.key] }}</strong>
              <span>{{ metric.label }}</span>
            </span>
          </button>
        </div>
      </section>

      <section class="announcement-section" aria-labelledby="recent-announcement-title">
        <div class="section-header">
          <h2 id="recent-announcement-title">最近公告</h2>
          <el-button type="primary" link @click="navigateTo('admin-announcement')">查看全部</el-button>
        </div>

        <el-skeleton v-if="loading" :rows="5" animated />
        <el-empty v-else-if="recentAnnouncements.length === 0" description="暂无公告" :image-size="72" />
        <div v-else class="announcement-list">
          <button
            v-for="announcement in recentAnnouncements"
            :key="announcement.id"
            class="announcement-item"
            type="button"
            @click="navigateTo('admin-announcement')"
          >
            <span class="announcement-main">
              <el-tag v-if="announcement.is_top" size="small" type="danger" effect="plain">置顶</el-tag>
              <span class="announcement-title">{{ announcement.title }}</span>
            </span>
            <time class="announcement-time" :datetime="announcement.create_time">
              {{ formatDate(announcement.create_time) }}
            </time>
          </button>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.dashboard-page {
  width: 100%;
  max-width: 1280px;
  margin: 0 auto;
}

.dashboard-header,
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.dashboard-header {
  min-height: 48px;
  margin-bottom: 18px;
  border-bottom: 1px solid #dcdfe6;
}

h1,
h2 {
  margin: 0;
  color: #303133;
  letter-spacing: 0;
}

h1 { font-size: 22px; }
h2 { font-size: 16px; }

.statistics-section { margin-bottom: 28px; }
.statistics-section h2 { margin-bottom: 12px; }

.statistics-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  overflow: hidden;
}

.metric-item {
  min-width: 0;
  min-height: 96px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  border: 0;
  border-right: 1px solid #ebeef5;
  background: #fff;
  color: inherit;
  text-align: left;
  cursor: pointer;
  transition: background-color 0.2s;
}

.metric-item:last-child { border-right: 0; }
.metric-item:hover,
.metric-item:focus-visible { background: #f5f7fa; }

.metric-item:focus-visible,
.announcement-item:focus-visible {
  outline: 2px solid #409eff;
  outline-offset: -2px;
}

.metric-icon {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  background: #ecf5ff;
  color: #337ecc;
}

.metric-icon :deep(svg) {
  width: 22px;
  height: 22px;
}

.metric-content {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.metric-content strong {
  font-size: 26px;
  line-height: 1;
  font-weight: 600;
  color: #303133;
}

.metric-content span {
  font-size: 14px;
  color: #606266;
}

.metric-content :deep(.el-skeleton__item) { width: 56px; }

.announcement-section { border-top: 1px solid #dcdfe6; }
.section-header { min-height: 52px; }

.announcement-list {
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  overflow: hidden;
}

.announcement-item {
  width: 100%;
  min-height: 52px;
  padding: 10px 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  border: 0;
  border-bottom: 1px solid #ebeef5;
  background: #fff;
  color: inherit;
  text-align: left;
  cursor: pointer;
  transition: background-color 0.2s;
}

.announcement-item:last-child { border-bottom: 0; }
.announcement-item:hover,
.announcement-item:focus-visible { background: #f5f7fa; }

.announcement-main {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.announcement-title {
  overflow: hidden;
  color: #303133;
  font-size: 14px;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.announcement-time {
  flex-shrink: 0;
  color: #909399;
  font-size: 13px;
}

@media (max-width: 900px) {
  .statistics-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .metric-item { border-right: 1px solid #ebeef5; border-bottom: 1px solid #ebeef5; }
  .metric-item:nth-child(2n) { border-right: 0; }
  .metric-item:last-child { grid-column: 1 / -1; border-right: 0; border-bottom: 0; }
}

@media (max-width: 480px) {
  .dashboard-header { margin-bottom: 14px; }
  h1 { font-size: 20px; }
  .statistics-section { margin-bottom: 22px; }
  .metric-item { min-height: 82px; padding: 12px; gap: 10px; }
  .metric-icon { width: 34px; height: 34px; }
  .metric-content strong { font-size: 22px; }
  .announcement-item { align-items: flex-start; flex-direction: column; gap: 6px; }
  .announcement-main { width: 100%; }
}
</style>
