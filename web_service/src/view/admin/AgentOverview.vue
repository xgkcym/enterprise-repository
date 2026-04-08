<template>
  <div class="admin-page">
    <div class="admin-page-header">
      <div>
        <h1>监控总览</h1>
        <p>聚合展示聊天链路的核心运行指标与趋势。</p>
      </div>
      <el-button type="primary" :loading="loading" @click="loadData">刷新</el-button>
    </div>

    <div class="metric-grid">
      <el-card v-for="card in overviewCards" :key="card.label" shadow="hover" class="metric-card">
        <div class="metric-label">{{ card.label }}</div>
        <div class="metric-value">{{ card.value }}</div>
      </el-card>
    </div>

    <div class="panel-grid">
      <el-card shadow="hover">
        <template #header>近 7 天请求与失败率</template>
        <EChartPanel :option="requestTrendOption" height="320px" />
      </el-card>

      <el-card shadow="hover">
        <template #header>近 7 天 Token 趋势</template>
        <EChartPanel :option="tokenTrendOption" height="320px" />
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from "vue";

import EChartPanel from "../../components/admin/EChartPanel.vue";
import { useAgentMonitor } from "./useAgentMonitor";

const { loading, overviewCards, requestTrendOption, tokenTrendOption, loadData } = useAgentMonitor();

onMounted(loadData);
</script>

<style scoped>
.admin-page {
  padding: 24px;
}

.admin-page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 20px;
}

.admin-page-header h1 {
  margin: 0 0 8px;
  font-size: 28px;
  color: #1f2a37;
}

.admin-page-header p {
  margin: 0;
  color: #526071;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.metric-card {
  border: 0;
}

.metric-label {
  font-size: 13px;
  color: #607086;
}

.metric-value {
  margin-top: 12px;
  font-size: 28px;
  font-weight: 700;
  color: #17212b;
}

.panel-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

@media (max-width: 1100px) {
  .panel-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .admin-page {
    padding: 16px;
  }

  .admin-page-header {
    flex-direction: column;
  }
}
</style>
