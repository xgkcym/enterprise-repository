<template>
  <div class="admin-layout">
    <AdminSidebar />
    <div class="admin-main">
      <header class="admin-topbar">
        <div>
          <div class="admin-topbar-title">后台管理</div>
          <div class="admin-topbar-subtitle">Agent、监控与运行分析</div>
        </div>
        <div class="admin-topbar-badge">Admin Console</div>
      </header>
      <main class="admin-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import AdminSidebar from "../../components/admin/AdminSidebar.vue";
</script>

<style scoped>
.admin-layout {
  display: flex;
  min-height: 100vh;
  background: #edf3f9;
}

.admin-main {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-width: 0;
}

.admin-topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 18px 24px;
  background: rgba(255, 255, 255, 0.84);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(148, 163, 184, 0.18);
}

.admin-topbar-title {
  font-size: 22px;
  font-weight: 700;
  color: #17212b;
}

.admin-topbar-subtitle {
  margin-top: 4px;
  font-size: 13px;
  color: #64748b;
}

.admin-topbar-badge {
  border-radius: 999px;
  background: linear-gradient(135deg, #dbeafe 0%, #e0f2fe 100%);
  color: #1d4ed8;
  padding: 8px 14px;
  font-size: 12px;
  font-weight: 700;
}

.admin-content {
  /* flex: 1; */
  /* min-height: 0; */
  height: calc(100vh - 94px);
  overflow: auto;
}

@media (max-width: 960px) {
  .admin-layout {
    flex-direction: column;
  }

  .admin-topbar {
    padding: 14px 16px;
  }
}
</style>
