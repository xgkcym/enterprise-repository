<template>
  <aside class="admin-sidebar">
    <div class="admin-brand">
      <div class="admin-brand-badge">RA</div>
      <div>
        <div class="admin-brand-title">RAG 管理后台</div>
        <div class="admin-brand-subtitle">系统控制台</div>
      </div>
    </div>

    <nav class="admin-nav">
      <section class="admin-nav-group">
        <button
          class="admin-group-trigger"
          :class="{ 'admin-group-trigger-active': hasActiveChild(monitorItems) }"
          @click="isMonitorOpen = !isMonitorOpen"
        >
          <div class="admin-group-trigger-main">
            <span class="admin-nav-icon">
              <i class="fas fa-gauge-high"></i>
            </span>
            <span>运行监控</span>
          </div>
          <i
            class="fas fa-chevron-down admin-group-chevron"
            :class="{ 'admin-group-chevron-open': isMonitorOpen }"
          ></i>
        </button>

        <div v-if="isMonitorOpen" class="admin-group-children">
          <button
            v-for="item in monitorItems"
            :key="item.path"
            class="admin-nav-item admin-nav-item-child"
            :class="{ 'admin-nav-item-active': isActive(item.path) }"
            @click="go(item.path)"
          >
            <span class="admin-nav-icon">
              <i :class="item.icon"></i>
            </span>
            <span>{{ item.label }}</span>
          </button>
        </div>
      </section>

      <section class="admin-nav-group">
        <button
          class="admin-group-trigger"
          :class="{ 'admin-group-trigger-active': hasActiveChild(systemItems) }"
          @click="isSystemOpen = !isSystemOpen"
        >
          <div class="admin-group-trigger-main">
            <span class="admin-nav-icon">
              <i class="fas fa-screwdriver-wrench"></i>
            </span>
            <span>系统管理</span>
          </div>
          <i
            class="fas fa-chevron-down admin-group-chevron"
            :class="{ 'admin-group-chevron-open': isSystemOpen }"
          ></i>
        </button>

        <div v-if="isSystemOpen" class="admin-group-children">
          <button
            v-for="item in systemItems"
            :key="item.path"
            class="admin-nav-item admin-nav-item-child"
            :class="{ 'admin-nav-item-active': isActive(item.path) }"
            @click="go(item.path)"
          >
            <span class="admin-nav-icon">
              <i :class="item.icon"></i>
            </span>
            <span>{{ item.label }}</span>
          </button>
        </div>
      </section>
    </nav>

    <div class="admin-sidebar-footer">
      <button class="admin-chat-link" @click="go('/chat')">返回对话界面</button>
    </div>
  </aside>
</template>

<script setup>
import { ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

const router = useRouter();
const route = useRoute();

const monitorItems = [
  { label: "总览", path: "/admin/agent-overview", icon: "fas fa-chart-line" },
  { label: "分析", path: "/admin/agent-analytics", icon: "fas fa-chart-pie" },
  { label: "运行记录", path: "/admin/agent-runs", icon: "fas fa-list-check" },
];

const systemItems = [
  { label: "用户管理", path: "/admin/users", icon: "fas fa-users-cog" },
  { label: "部门管理", path: "/admin/departments", icon: "fas fa-building" },
  { label: "角色管理", path: "/admin/roles", icon: "fas fa-user-shield" },
  { label: "文件管理", path: "/admin/files", icon: "fas fa-folder-tree" },
];

const isMonitorOpen = ref(true);
const isSystemOpen = ref(true);

const go = (path) => {
  router.push(path);
};

const isActive = (path) => route.path === path;

const hasActiveChild = (items) => items.some((item) => isActive(item.path));

watch(
  () => route.path,
  () => {
    if (hasActiveChild(monitorItems)) {
      isMonitorOpen.value = true;
    }
    if (hasActiveChild(systemItems)) {
      isSystemOpen.value = true;
    }
  },
  { immediate: true }
);
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

.admin-nav-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.admin-group-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  border: 0;
  border-radius: 14px;
  background: rgba(148, 163, 184, 0.08);
  color: #e2e8f0;
  padding: 12px 14px;
  cursor: pointer;
  transition: background-color 0.2s ease, color 0.2s ease;
}

.admin-group-trigger:hover {
  background: rgba(59, 130, 246, 0.16);
}

.admin-group-trigger-active {
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.35) 0%, rgba(14, 165, 233, 0.22) 100%);
}

.admin-group-trigger-main {
  display: flex;
  align-items: center;
  gap: 10px;
}

.admin-group-chevron {
  font-size: 12px;
  transition: transform 0.2s ease;
}

.admin-group-chevron-open {
  transform: rotate(180deg);
}

.admin-group-children {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-left: 12px;
  border-left: 1px solid rgba(148, 163, 184, 0.22);
  margin-left: 10px;
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

.admin-nav-item-child {
  padding: 10px 12px;
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
