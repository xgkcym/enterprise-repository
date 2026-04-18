import { createRouter, createWebHashHistory } from "vue-router";

import AdminLayout from "../view/admin/AdminLayout.vue";
import AgentAnalytics from "../view/admin/AgentAnalytics.vue";
import AgentOverview from "../view/admin/AgentOverview.vue";
import AgentRuns from "../view/admin/AgentRuns.vue";
import AdminDepartments from "../view/admin/AdminDepartments.vue";
import AdminFiles from "../view/admin/AdminFiles.vue";
import AdminRoles from "../view/admin/AdminRoles.vue";
import AdminUsers from "../view/admin/AdminUsers.vue";
import Chat from "../view/chat/Chat.vue";

const getStoredUserInfo = () => {
  try {
    const raw = localStorage.getItem("userInfo");
    return raw ? JSON.parse(raw) : null;
  } catch (error) {
    return null;
  }
};

const isAdminUser = () => {
  const userInfo = getStoredUserInfo();
  return userInfo?.user_type === "admin" || userInfo?.is_admin === true;
};

const routes = [
  {
    path: "/",
    redirect: "/chat",
  },
  {
    path: "/chat",
    component: Chat,
  },
  {
    path: "/admin",
    component: AdminLayout,
    redirect: "/admin/agent-overview",
    meta: { requiresAdmin: true },
    children: [
      {
        path: "agent-overview",
        component: AgentOverview,
      },
      {
        path: "agent-analytics",
        component: AgentAnalytics,
      },
      {
        path: "agent-runs",
        component: AgentRuns,
      },
      {
        path: "users",
        component: AdminUsers,
      },
      {
        path: "departments",
        component: AdminDepartments,
      },
      {
        path: "roles",
        component: AdminRoles,
      },
      {
        path: "files",
        component: AdminFiles,
      },
    ],
  },
  {
    path: "/admin/agent-monitor",
    redirect: "/admin/agent-overview",
  },
];

const router = createRouter({
  history: createWebHashHistory(),
  routes,
});

router.beforeEach((to) => {
  if (!to.meta?.requiresAdmin) {
    return true;
  }

  if (isAdminUser()) {
    return true;
  }

  return "/chat";
});

export default router;
