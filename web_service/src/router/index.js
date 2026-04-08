import { createRouter, createWebHashHistory } from "vue-router";
import Chat from '../view/chat/Chat.vue'
import AdminLayout from "../view/admin/AdminLayout.vue";
import AgentAnalytics from "../view/admin/AgentAnalytics.vue";
import AgentOverview from "../view/admin/AgentOverview.vue";
import AgentRuns from "../view/admin/AgentRuns.vue";

const routes = [
  {
    path: '/',
    redirect: '/chat'
  },
  {
    path: '/chat',
    component: Chat
  },
  {
    path: "/admin",
    component: AdminLayout,
    redirect: "/admin/agent-overview",
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
    ],
  },
  {
    path: "/admin/agent-monitor",
    redirect: "/admin/agent-overview",
  }
];

const router = createRouter({
  history: createWebHashHistory(),
  routes,
});

export default router;
