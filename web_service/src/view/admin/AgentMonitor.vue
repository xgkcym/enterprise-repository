<template>
  <div class="monitor-page">
    <div class="monitor-header">
      <div>
        <h1>Agent 监控面板</h1>
        <p>统计范围仅包含聊天链路 /agent/chat/stream</p>
      </div>
      <div class="monitor-actions">
        <el-button type="primary" @click="loadData">刷新</el-button>
      </div>
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

    <div class="panel-grid secondary-grid">
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

    <el-card shadow="hover">
      <template #header>最近运行明细</template>
      <el-table :data="runs" border size="small" row-key="run_id" height="320">
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="detail-grid">
              <div>
                <span class="detail-label">原始输入</span>
                <pre>{{ row.query || "-" }}</pre>
              </div>
              <div>
                <span class="detail-label">解析后查询</span>
                <pre>{{ row.resolved_query || "-" }}</pre>
              </div>
              <div>
                <span class="detail-label">执行查询</span>
                <pre>{{ row.working_query || "-" }}</pre>
              </div>
              <div>
                <span class="detail-label">路由原因</span>
                <pre>{{ row.reason || "-" }}</pre>
              </div>
              <div>
                <span class="detail-label">重写查询</span>
                <pre>{{ row.rewrite_query || "-" }}</pre>
              </div>
              <div>
                <span class="detail-label">扩展查询</span>
                <pre>{{ row.expand_query?.join("\n") || "-" }}</pre>
              </div>
              <div>
                <span class="detail-label">分解查询</span>
                <pre>{{ row.decompose_query?.join("\n") || "-" }}</pre>
              </div>
              <div>
                <span class="detail-label">失败原因</span>
                <pre>{{ row.fail_reason || "-" }}</pre>
              </div>
            </div>
            <div v-if="row.action_history?.length" class="mt-4" style="padding: 10px;">
              <div class="detail-label">执行时间线</div>
              <div class="space-y-2">
                <div
                  v-for="(item, historyIndex) in row.action_history"
                  :key="`${row.run_id}-history-${historyIndex}`"
                  class="history-card"
                >
                  <div class="history-head">
                    <div class="history-title">
                      <span
                        class="history-kind"
                        :class="item.kind === 'tool' ? 'history-kind-tool' : 'history-kind-reasoning'"
                      >
                        {{ item.kind === "tool" ? "工具" : "推理" }}
                      </span>
                      <strong>步骤 {{ historyIndex + 1 }}: {{ item.name || "-" }}</strong>
                    </div>
                    <div class="history-meta">
                      <span>{{ item.duration_ms ? `${item.duration_ms} ms` : "-" }}</span>
                      <span>状态：{{ item.status || "-" }}</span>
                    </div>
                  </div>
                  <div class="history-grid">
                    <div v-if="item.input" class="history-block">
                      <div class="history-label">输入</div>
                      <pre>{{ stringifyPayload(item.input) }}</pre>
                    </div>
                    <div v-if="item.output" class="history-block">
                      <div class="history-label">输出</div>
                      <pre>{{ stringifyPayload(item.output) }}</pre>
                    </div>
                  </div>
                  <div class="history-notes">
                    <span v-if="extractOutputField(item, 'reason')">原因：{{ extractOutputField(item, "reason") }}</span>
                    <span v-if="extractOutputField(item, 'message')">消息：{{ extractOutputField(item, "message") }}</span>
                    <span v-if="extractOutputField(item, 'fail_reason')">失败原因：{{ extractOutputField(item, "fail_reason") }}</span>
                  </div>
                  <div v-if="item.error" class="history-error">错误：{{ item.error }}</div>
                </div>
              </div>
            </div>
            <div v-else-if="row.trace?.length" class="mt-4" style="padding: 10px;">
              <div class="detail-label">执行轨迹</div>
              <div class="space-y-2">
                <div
                  v-for="(item, traceIndex) in row.trace"
                  :key="`${row.run_id}-trace-${traceIndex}`"
                  class="history-card"
                >
                  <div class="history-head">
                    <div class="history-title">
                      <strong>步骤 {{ item.step || traceIndex + 1 }}: {{ item.event_name || item.event || "-" }}</strong>
                    </div>
                    <div class="history-meta">
                      <span>{{ item.duration_ms ? `${item.duration_ms} ms` : "-" }}</span>
                      <span>状态：{{ item.status || "-" }}</span>
                    </div>
                  </div>
                  <div class="history-notes">
                    <span v-if="item.message">消息：{{ item.message }}</span>
                    <span v-if="item.fail_reason">失败原因：{{ item.fail_reason }}</span>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="时间" min-width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="action" label="Action" min-width="120" />
        <el-table-column prop="status" label="状态" min-width="90" />
        <el-table-column prop="duration_ms" label="耗时(ms)" min-width="100" />
        <el-table-column prop="total_tokens" label="Tokens" min-width="100" />
        <el-table-column label="估算成本(USD)" min-width="130">
          <template #default="{ row }">
            {{ formatCost(row.estimated_cost_usd) }}
          </template>
        </el-table-column>
        <el-table-column label="回答预览" min-width="280">
          <template #default="{ row }">
            <span>{{ row.answer_preview || "-" }}</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";

import { get_agent_monitor_overview, get_agent_monitor_runs } from "../../api/admin_monitor";
import EChartPanel from "../../components/admin/EChartPanel.vue";

const overview = ref({
  today_request_count: 0,
  today_active_users: 0,
  today_active_sessions: 0,
  today_new_sessions: 0,
  today_total_tokens: 0,
  today_estimated_cost_usd: 0,
  avg_duration_ms: 0,
  avg_tokens_per_request: 0,
  avg_session_message_count: 0,
  max_session_message_count: 0,
  fail_rate: 0,
});
const dailyTrend = ref([]);
const actionDistribution = ref([]);
const modelDistribution = ref([]);
const failReasonDistribution = ref([]);
const actionMetrics = ref([]);
const topUsers = ref([]);
const topSessions = ref([]);
const runs = ref([]);

const formatCost = (value) => Number(value || 0).toFixed(6);
const formatRate = (value) => `${(Number(value || 0) * 100).toFixed(2)}%`;
const formatDateTime = (value) => {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
    timeZone: "Asia/Shanghai",
  }).format(date);
};
const stringifyPayload = (payload) => {
  if (!payload) return "-";
  if (typeof payload === "string") return payload;
  try {
    return JSON.stringify(payload, null, 2);
  } catch (error) {
    return String(payload);
  }
};
const extractOutputField = (item, field) => {
  const output = item?.output;
  if (!output || typeof output !== "object") return "";
  return output[field] || "";
};

const overviewCards = computed(() => [
  { label: "今日请求量", value: overview.value.today_request_count || 0 },
  { label: "今日活跃用户", value: overview.value.today_active_users || 0 },
  { label: "今日活跃会话", value: overview.value.today_active_sessions || 0 },
  { label: "今日新建会话", value: overview.value.today_new_sessions || 0 },
  { label: "今日 Tokens", value: overview.value.today_total_tokens || 0 },
  { label: "今日估算成本", value: `$${formatCost(overview.value.today_estimated_cost_usd)}` },
  { label: "平均响应耗时", value: `${overview.value.avg_duration_ms || 0} ms` },
  { label: "平均每次 Tokens", value: overview.value.avg_tokens_per_request || 0 },
  { label: "会话平均轮数", value: overview.value.avg_session_message_count || 0 },
  { label: "单会话最高轮数", value: overview.value.max_session_message_count || 0 },
  { label: "失败率", value: formatRate(overview.value.fail_rate) },
]);

const chartPalette = ["#1d4ed8", "#0f766e", "#ea580c", "#7c3aed", "#dc2626", "#0891b2"];

const requestTrendOption = computed(() => ({
  color: ["#1d4ed8", "#dc2626", "#f59e0b"],
  tooltip: {
    trigger: "axis",
  },
  legend: {
    top: 8,
    textStyle: {
      color: "#445468",
    },
  },
  grid: {
    left: 36,
    right: 18,
    top: 48,
    bottom: 28,
  },
  xAxis: {
    type: "category",
    data: dailyTrend.value.map((item) => item.date),
    axisLabel: {
      color: "#607086",
    },
  },
  yAxis: [
    {
      type: "value",
      name: "数量",
      axisLabel: {
        color: "#607086",
      },
      splitLine: {
        lineStyle: {
          color: "#e5ebf3",
        },
      },
    },
    {
      type: "value",
      name: "失败率",
      min: 0,
      max: 100,
      axisLabel: {
        color: "#607086",
        formatter: "{value}%",
      },
      splitLine: {
        show: false,
      },
    },
  ],
  series: [
    {
      name: "请求数",
      type: "line",
      smooth: false,
      data: dailyTrend.value.map((item) => item.request_count),
      areaStyle: {
        opacity: 0.12,
      },
    },
    {
      name: "失败数",
      type: "bar",
      barMaxWidth: 18,
      data: dailyTrend.value.map((item) => item.failed_count),
    },
    {
      name: "失败率",
      type: "line",
      smooth: false,
      yAxisIndex: 1,
      data: dailyTrend.value.map((item) => {
        const requestCount = Number(item.request_count || 0);
        const failedCount = Number(item.failed_count || 0);
        return requestCount ? Number(((failedCount / requestCount) * 100).toFixed(2)) : 0;
      }),
      label: {
        show: true,
        formatter: "{c}%",
      },
    },
  ],
}));

const tokenTrendOption = computed(() => ({
  color: ["#0f766e", "#7c3aed"],
  tooltip: {
    trigger: "axis",
  },
  legend: {
    top: 8,
    textStyle: {
      color: "#445468",
    },
  },
  grid: {
    left: 36,
    right: 18,
    top: 48,
    bottom: 28,
  },
  xAxis: {
    type: "category",
    data: dailyTrend.value.map((item) => item.date),
    axisLabel: {
      color: "#607086",
    },
  },
  yAxis: [
    {
      type: "value",
      name: "Tokens",
      axisLabel: {
        color: "#607086",
      },
      splitLine: {
        lineStyle: {
          color: "#e5ebf3",
        },
      },
    },
    {
      type: "value",
      name: "成本",
      axisLabel: {
        color: "#607086",
        formatter: (value) => `$${Number(value).toFixed(4)}`,
      },
      splitLine: {
        show: false,
      },
    },
  ],
  series: [
    {
      name: "Tokens",
      type: "bar",
      barMaxWidth: 24,
      data: dailyTrend.value.map((item) => item.total_tokens),
    },
    {
      name: "估算成本",
      type: "line",
      smooth: false,
      yAxisIndex: 1,
      data: dailyTrend.value.map((item) => Number(item.estimated_cost_usd || 0)),
      areaStyle: {
        opacity: 0.1,
      },
    },
  ],
}));

const actionOption = computed(() => ({
  color: chartPalette,
  tooltip: {
    trigger: "item",
  },
  legend: {
    bottom: 0,
    left: "center",
    textStyle: {
      color: "#445468",
    },
  },
  series: [
    {
      type: "pie",
      radius: ["42%", "72%"],
      center: ["50%", "42%"],
      itemStyle: {
        borderRadius: 10,
        borderColor: "#fff",
        borderWidth: 3,
      },
      label: {
        formatter: "{b}\n{c}",
      },
      data: actionDistribution.value.map((item) => ({
        value: item.count,
        name: item.action,
      })),
    },
  ],
}));

const modelOption = computed(() => ({
  color: ["#0f766e", "#1d4ed8", "#ea580c", "#9333ea", "#f43f5e"],
  tooltip: {
    trigger: "axis",
    axisPointer: {
      type: "shadow",
    },
  },
  grid: {
    left: 24,
    right: 18,
    top: 20,
    bottom: 36,
  },
  xAxis: {
    type: "value",
    axisLabel: {
      color: "#607086",
    },
    splitLine: {
      lineStyle: {
        color: "#e5ebf3",
      },
    },
  },
  yAxis: {
    type: "category",
    axisLabel: {
      color: "#445468",
      width: 120,
      overflow: "truncate",
    },
    data: modelDistribution.value.map((item) => item.model),
  },
  series: [
    {
      type: "bar",
      barMaxWidth: 18,
      data: modelDistribution.value.map((item) => item.count),
      label: {
        show: true,
        position: "right",
        color: "#445468",
      },
    },
  ],
}));

const failReasonOption = computed(() => ({
  color: ["#dc2626"],
  tooltip: {
    trigger: "axis",
    axisPointer: {
      type: "shadow",
    },
  },
  grid: {
    left: 24,
    right: 18,
    top: 20,
    bottom: 36,
  },
  xAxis: {
    type: "value",
    axisLabel: {
      color: "#607086",
    },
    splitLine: {
      lineStyle: {
        color: "#e5ebf3",
      },
    },
  },
  yAxis: {
    type: "category",
    axisLabel: {
      color: "#445468",
      width: 160,
      overflow: "truncate",
    },
    data: failReasonDistribution.value.map((item) => item.fail_reason),
  },
  series: [
    {
      type: "bar",
      barMaxWidth: 18,
      data: failReasonDistribution.value.map((item) => item.count),
      label: {
        show: true,
        position: "right",
        color: "#445468",
      },
    },
  ],
}));

const loadData = async () => {
  const [overviewRes, runsRes] = await Promise.all([
    get_agent_monitor_overview(),
    get_agent_monitor_runs({ limit: 20 }),
  ]);

  overview.value = overviewRes.data?.overview || overview.value;
  dailyTrend.value = overviewRes.data?.daily_trend || [];
  actionDistribution.value = overviewRes.data?.action_distribution || [];
  modelDistribution.value = overviewRes.data?.model_distribution || [];
  failReasonDistribution.value = overviewRes.data?.fail_reason_distribution || [];
  actionMetrics.value = overviewRes.data?.action_metrics || [];
  topUsers.value = overviewRes.data?.top_users || [];
  topSessions.value = overviewRes.data?.top_sessions || [];
  runs.value = runsRes.data || [];
};

onMounted(loadData);
</script>

<style scoped>
.monitor-page {
  padding: 24px;
}

.monitor-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 20px;
}

.monitor-header h1 {
  margin: 0 0 8px;
  font-size: 28px;
  color: #1f2a37;
}

.monitor-header p {
  margin: 0;
  color: #526071;
}

.monitor-actions {
  display: flex;
  gap: 12px;
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
  margin-bottom: 20px;
}

.secondary-grid {
  margin-top: -4px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 12px;
  padding: 8px;
}

.detail-label {
  display: block;
  margin-bottom: 6px;
  font-size: 12px;
  color: #6b7a8c;
}

.detail-grid pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  padding: 10px 12px;
  border-radius: 10px;
  background: #f7f9fc;
  color: #243243;
  font-size: 12px;
  line-height: 1.5;
}

.history-card {
  border: 1px solid #e5ebf3;
  border-radius: 12px;
  background: #f8fbff;
  padding: 12px;
}

.history-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.history-title {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #243243;
}

.history-kind {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 600;
}

.history-kind-tool {
  background: #dbeafe;
  color: #1d4ed8;
}

.history-kind-reasoning {
  background: #fef3c7;
  color: #b45309;
}

.history-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #64748b;
}

.history-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 12px;
  margin-top: 12px;
}

.history-block {
  border-radius: 10px;
  background: #ffffff;
  padding: 10px 12px;
}

.history-label {
  margin-bottom: 6px;
  font-size: 11px;
  font-weight: 600;
  color: #94a3b8;
}

.history-block pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 12px;
  line-height: 1.5;
  color: #334155;
}

.history-error {
  margin-top: 10px;
  font-size: 12px;
  color: #dc2626;
}

.history-notes {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 10px;
  font-size: 12px;
  color: #64748b;
}

@media (max-width: 1100px) {
  .panel-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .monitor-page {
    padding: 16px;
  }

  .monitor-header {
    flex-direction: column;
  }

  .monitor-actions {
    width: 100%;
  }
}
</style>
