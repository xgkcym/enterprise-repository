import { computed, ref } from "vue";

import { get_agent_monitor_overview, get_agent_monitor_runs } from "../../api/admin_monitor";

export function useAgentMonitor() {
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
  const loading = ref(false);

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
    tooltip: { trigger: "axis" },
    legend: { top: 8, textStyle: { color: "#445468" } },
    grid: { left: 36, right: 18, top: 48, bottom: 28 },
    xAxis: {
      type: "category",
      data: dailyTrend.value.map((item) => item.date),
      axisLabel: { color: "#607086" },
    },
    yAxis: [
      {
        type: "value",
        name: "数量",
        axisLabel: { color: "#607086" },
        splitLine: { lineStyle: { color: "#e5ebf3" } },
      },
      {
        type: "value",
        name: "失败率",
        min: 0,
        max: 100,
        axisLabel: { color: "#607086", formatter: "{value}%" },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: "请求数",
        type: "line",
        smooth: false,
        data: dailyTrend.value.map((item) => item.request_count),
        areaStyle: { opacity: 0.12 },
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
        label: { show: true, formatter: "{c}%" },
      },
    ],
  }));

  const tokenTrendOption = computed(() => ({
    color: ["#0f766e", "#7c3aed"],
    tooltip: { trigger: "axis" },
    legend: { top: 8, textStyle: { color: "#445468" } },
    grid: { left: 36, right: 18, top: 48, bottom: 28 },
    xAxis: {
      type: "category",
      data: dailyTrend.value.map((item) => item.date),
      axisLabel: { color: "#607086" },
    },
    yAxis: [
      {
        type: "value",
        name: "Tokens",
        axisLabel: { color: "#607086" },
        splitLine: { lineStyle: { color: "#e5ebf3" } },
      },
      {
        type: "value",
        name: "成本",
        axisLabel: {
          color: "#607086",
          formatter: (value) => `$${Number(value).toFixed(4)}`,
        },
        splitLine: { show: false },
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
        areaStyle: { opacity: 0.1 },
      },
    ],
  }));

  const actionOption = computed(() => ({
    color: chartPalette,
    tooltip: { trigger: "item" },
    legend: { bottom: 0, left: "center", textStyle: { color: "#445468" } },
    series: [
      {
        type: "pie",
        radius: ["42%", "72%"],
        center: ["50%", "42%"],
        itemStyle: { borderRadius: 10, borderColor: "#fff", borderWidth: 3 },
        label: { formatter: "{b}\n{c}" },
        data: actionDistribution.value.map((item) => ({ value: item.count, name: item.action })),
      },
    ],
  }));

  const modelOption = computed(() => ({
    color: ["#0f766e", "#1d4ed8", "#ea580c", "#9333ea", "#f43f5e"],
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    grid: { left: 24, right: 18, top: 20, bottom: 36 },
    xAxis: {
      type: "value",
      axisLabel: { color: "#607086" },
      splitLine: { lineStyle: { color: "#e5ebf3" } },
    },
    yAxis: {
      type: "category",
      axisLabel: { color: "#445468", width: 120, overflow: "truncate" },
      data: modelDistribution.value.map((item) => item.model),
    },
    series: [
      {
        type: "bar",
        barMaxWidth: 18,
        data: modelDistribution.value.map((item) => item.count),
        label: { show: true, position: "right", color: "#445468" },
      },
    ],
  }));

  const failReasonOption = computed(() => ({
    color: ["#dc2626"],
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    grid: { left: 24, right: 18, top: 20, bottom: 36 },
    xAxis: {
      type: "value",
      axisLabel: { color: "#607086" },
      splitLine: { lineStyle: { color: "#e5ebf3" } },
    },
    yAxis: {
      type: "category",
      axisLabel: { color: "#445468", width: 160, overflow: "truncate" },
      data: failReasonDistribution.value.map((item) => item.fail_reason),
    },
    series: [
      {
        type: "bar",
        barMaxWidth: 18,
        data: failReasonDistribution.value.map((item) => item.count),
        label: { show: true, position: "right", color: "#445468" },
      },
    ],
  }));

  const loadData = async () => {
    loading.value = true;
    try {
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
    } finally {
      loading.value = false;
    }
  };

  return {
    loading,
    overview,
    dailyTrend,
    actionDistribution,
    modelDistribution,
    failReasonDistribution,
    actionMetrics,
    topUsers,
    topSessions,
    runs,
    overviewCards,
    requestTrendOption,
    tokenTrendOption,
    actionOption,
    modelOption,
    failReasonOption,
    loadData,
    formatCost,
    formatRate,
    formatDateTime,
    stringifyPayload,
    extractOutputField,
  };
}
