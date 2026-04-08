<template>
  <aside class="admin-sidebar">
    <div class="admin-brand">
      <div class="admin-brand-badge">RA</div>
      <div>
        <div class="admin-brand-title">RAG Admin</div>
        <div class="admin-brand-subtitle">后台管理系统</div>
      </div>
    </div>

    <nav class="admin-nav">
      <button
        v-for="item in items"
        :key="item.path"
        class="admin-nav-item"
        :class="{ 'admin-nav-item-active': isActive(item.path) }"
        @click="go(item.path)"
      >
        <span class="admin-nav-icon">{{ item.icon }}</span>
        <span>{{ item.label }}</span>
      </button>
    </nav>

    <div class="admin-sidebar-footer">
      <button class="admin-chat-link" @click="go('/chat')">返回聊天</button>
    </div>
  </aside>
</template>

<script setup>
import { useRoute, useRouter } from "vue-router";

const router = useRouter();
const route = useRoute();

const items = [
  { label: "监控总览", path: "/admin/agent-overview", icon: "◫" },
  { label: "分析中心", path: "/admin/agent-analytics", icon: "◎" },
  { label: "运行明细", path: "/admin/agent-runs", icon: "▣" },
];

const go = (path) => {
  router.push(path);
};

const isActive = (path) => route.path === path;
</script>

<style scoped>
.admin-sidebar {
  display: flex;
  flex-direction: column;
  width: 248px;
  min-width: 248px;
  background: linear-gradient(180deg, #0f172a 0%, #172554 100%);
  color: #e2e8f0;
  padding: 20px 16px;
  border-right: 1px solid rgba(148, 163, 184, 0.16);
}

.admin-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-bottom: 18px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.16);
}

.admin-brand-badge {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #38bdf8 0%, #22c55e 100%);
  color: #082f49;
  font-weight: 800;
}

.admin-brand-title {
  font-size: 18px;
  font-weight: 700;
}

.admin-brand-subtitle {
  margin-top: 4px;
  font-size: 12px;
  color: #93c5fd;
}

.admin-nav {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-top: 18px;
}

.admin-nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  border: 0;
  border-radius: 14px;
  background: transparent;
  color: #cbd5e1;
  padding: 12px 14px;
  text-align: left;
  cursor: pointer;
  transition: background-color 0.2s ease, color 0.2s ease, transform 0.2s ease;
}

.admin-nav-item:hover {
  background: rgba(59, 130, 246, 0.16);
  color: #ffffff;
  transform: translateX(2px);
}

.admin-nav-item-active {
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.9) 0%, rgba(14, 165, 233, 0.7) 100%);
  color: #ffffff;
  box-shadow: 0 10px 30px rgba(14, 165, 233, 0.18);
}

.admin-nav-icon {
  width: 18px;
  text-align: center;
  opacity: 0.9;
}

.admin-sidebar-footer {
  margin-top: auto;
  padding-top: 18px;
  border-top: 1px solid rgba(148, 163, 184, 0.16);
}

.admin-chat-link {
  width: 100%;
  border: 1px solid rgba(148, 163, 184, 0.24);
  border-radius: 12px;
  background: rgba(15, 23, 42, 0.24);
  color: #e2e8f0;
  padding: 10px 12px;
  cursor: pointer;
}

@media (max-width: 960px) {
  .admin-sidebar {
    width: 100%;
    min-width: 0;
    padding: 16px;
  }
}
</style>
