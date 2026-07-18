import {createRouter, createWebHistory} from 'vue-router'
import LoginView from "@/views/LoginView.vue";
import ChatView from "@/views/chat/ChatView.vue";
import AdminLayoutView from "@/views/admin/AdminLayoutView.vue";
import UserLayoutView from "@/views/user/UserLayoutView.vue";
import UserMyView from "@/views/user/UserMyView.vue";
import AdminAnnouncementView from "@/views/admin/AdminAnnouncementView.vue";
import AdminSessionView from "@/views/admin/AdminSessionView.vue";
import AdminKnowledgeBaseView from "@/views/admin/AdminKnowledgeBaseView.vue";
import AdminUserView from "@/views/admin/AdminUserView.vue";
import AdminRoleView from "@/views/admin/AdminRoleView.vue";
import UserKnowledgeBaseView from "@/views/user/UserKnowledgeBaseView.vue";
import UserAnnouncementView from "@/views/user/UserAnnouncementView.vue";
import UserRoleView from "@/views/user/UserRoleView.vue";
import UserSessionView from "@/views/user/UserSessionView.vue";

const routes = [
    {path: '/', name: 'login', component: LoginView},
    {path: '/login', name: 'loginView', component: LoginView},
    {path: "/chat", name: 'chat', component: ChatView},
    {
        path: "/admin",
        name: "admin",
        component: AdminLayoutView,
        redirect: "/admin/my",
        children: [
            {path: "announcement", name: "admin-announcement", component: AdminAnnouncementView},
            {path: "knowledgeBase", name: "admin-knowledgeBase", component: AdminKnowledgeBaseView},
            {path: "role", name: "admin-role", component: AdminRoleView},
            {path: "session", name: "admin-session", component: AdminSessionView},
            {path: "user", name: "admin-user", component: AdminUserView}
        ]
    },
    {
        path: "/user",
        name: "user",
        component: UserLayoutView,
        redirect: "/user/my",
        children: [
            {path: "my", name: "user-my", component: UserMyView},
            {path: "announcement", name: "user-announcement", component: UserAnnouncementView},
            {path: "knowledgeBase", name: "user-knowledgeBase", component: UserKnowledgeBaseView},
            {path: "role", name: "user-role", component: UserRoleView},
            {path: "session", name: "user-session", component: UserSessionView}
        ]
    }
]

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes
})

export default router