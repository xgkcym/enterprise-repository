<template>
  <div class="admin-page">
    <div class="admin-page-header">
      <div>
        <h1>分析中心</h1>
        <p>按动作、模型、失败原因、用户与会话维度分析系统负担。</p>
      </div>
      <el-button type="primary" :loading="loading" @click="loadData">刷新</el-button>
    </div>

    <div class="panel-grid">
      <el-card shadow="hover">
        <template #header>Action 分布</template>
        <EChartPanel v-if="actionDistribution.length" :option="actionOption" height="320px" />
        <el-empty v-else description="暂无数据" />
      </el-card>

      <el-card shadow="hover">
        <template #header>模型分布</template>
        <EChartPanel v-if="modelDistribution.length" :option="modelOption" height="320px" />
        <el-empty v-else description="暂无数据" />
      </el-card>

      <el-card shadow="hover">
        <template #header>失败原因分布</template>
        <EChartPanel v-if="failReasonDistribution.length" :option="failReasonOption" height="320px" />
        <el-empty v-else description="暂无失败数据" />
      </el-card>

      <el-card shadow="hover">
        <template #header>用户请求排行</template>
        <el-table :data="topUsers" size="small" border height="320">
          <el-table-column prop="user_id" label="用户ID" min-width="120" />
          <el-table-column prop="count" label="请求数" min-width="90" />
          <el-table-column prop="total_tokens" label="Tokens" min-width="100" />
          <el-table-column prop="avg_duration_ms" label="平均耗时" min-width="100" />
          <el-table-column label="失败率" min-width="90">
            <template #default="{ row }">{{ formatRate(row.fail_rate) }}</template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <div class="panel-grid panel-grid-secondary">
      <el-card shadow="hover">
        <template #header>Action 效能</template>
        <el-table :data="actionMetrics" size="small" border height="320">
          <el-table-column prop="action" label="Action" min-width="120" />
          <el-table-column prop="count" label="次数" min-width="80" />
          <el-table-column label="成功率" min-width="90">
            <template #default="{ row }">{{ formatRate(row.success_rate) }}</template>
          </el-table-column>
          <el-table-column prop="avg_duration_ms" label="平均耗时" min-width="100" />
          <el-table-column prop="avg_total_tokens" label="平均Tokens" min-width="110" />
          <el-table-column label="平均成本" min-width="110">
            <template #default="{ row }">${{ formatCost(row.avg_estimated_cost_usd) }}</template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-card shadow="hover">
        <template #header>会话负担排行</template>
        <el-table :data="topSessions" size="small" border height="320">
          <el-table-column prop="session_id" label="会话ID" min-width="180" />
          <el-table-column prop="count" label="请求数" min-width="80" />
          <el-table-column prop="total_tokens" label="Tokens" min-width="100" />
          <el-table-column prop="avg_duration_ms" label="平均耗时" min-width="100" />
          <el-table-column label="失败率" min-width="90">
            <template #default="{ row }">{{ formatRate(row.fail_rate) }}</template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from "vue";

import EChartPanel from "../../components/admin/EChartPanel.vue";
import { useAgentMonitor } from "./useAgentMonitor";

const {
  loading,
  actionDistribution,
  modelDistribution,
  failReasonDistribution,
  actionMetrics,
  topUsers,
  topSessions,
  actionOption,
  modelOption,
  failReasonOption,
  loadData,
  formatCost,
  formatRate,
} = useAgentMonitor();

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

.panel-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.panel-grid-secondary {
  margin-top: -4px;
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
