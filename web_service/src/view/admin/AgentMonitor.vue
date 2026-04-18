<template>
  <div class="monitor-legacy-page">
    <el-card shadow="hover" class="legacy-card">
      <div class="legacy-title">运行监控已拆分为三个页面</div>
      <p class="legacy-text">为了让数据更清晰，现在可以分别查看总览、分析中心和运行记录。</p>
      <div class="legacy-actions">
        <el-button type="primary" @click="go('/admin/agent-overview')">进入总览</el-button>
        <el-button @click="go('/admin/agent-analytics')">进入分析中心</el-button>
        <el-button @click="go('/admin/agent-runs')">进入运行记录</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { useRouter } from "vue-router";

const router = useRouter();

const go = (path) => {
  router.push(path);
};
</script>

<style scoped>
.monitor-legacy-page {
  padding: 24px;
}

.legacy-card {
  max-width: 720px;
}

.legacy-title {
  font-size: 24px;
  font-weight: 700;
  color: #17212b;
}

.legacy-text {
  margin: 12px 0 0;
  color: #526071;
  line-height: 1.7;
}

.legacy-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 20px;
}

@media (max-width: 768px) {
  .monitor-legacy-page {
    padding: 16px;
  }
}
</style>
