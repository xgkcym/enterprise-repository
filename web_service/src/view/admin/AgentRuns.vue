<template>
  <div class="admin-page">
    <div class="admin-page-header">
      <div>
        <h1>运行详情</h1>
        <p>查看每次运行的查询演化、动作历史、令牌消耗以及用户偏好影响。</p>
      </div>
      <el-button type="primary" :loading="loading" @click="loadData">刷新</el-button>
    </div>

    <el-card shadow="hover">
      <template #header>最近运行</template>
      <el-table :data="runs" border size="small" row-key="run_id" max-height="calc(100vh - 340px)">
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="detail-grid">
              <div>
                <span class="detail-label">原始问题</span>
                <pre>{{ row.query || "-" }}</pre>
              </div>
              <div>
                <span class="detail-label">解析后问题</span>
                <pre>{{ row.resolved_query || "-" }}</pre>
              </div>
              <div>
                <span class="detail-label">工作问题</span>
                <pre>{{ row.working_query || "-" }}</pre>
              </div>
              <div>
                <span class="detail-label">路由原因</span>
                <pre>{{ row.reason || "-" }}</pre>
              </div>
              <div>
                <span class="detail-label">改写问题</span>
                <pre>{{ row.rewrite_query || "-" }}</pre>
              </div>
              <div>
                <span class="detail-label">扩展问题</span>
                <pre>{{ row.expand_query?.join("\n") || "-" }}</pre>
              </div>
              <div>
                <span class="detail-label">拆解问题</span>
                <pre>{{ row.decompose_query?.join("\n") || "-" }}</pre>
              </div>
              <div>
                <span class="detail-label">失败原因</span>
                <pre>{{ row.fail_reason || "-" }}</pre>
              </div>
            </div>

            <div
              v-if="row.preferred_topics_usage?.available_topics?.length || row.user_profile?.preferred_topics?.length"
              class="profile-impact-panel"
            >
              <div class="detail-label">关注主题影响</div>
              <div class="impact-grid">
                <div class="impact-card">
                  <div class="impact-title">已配置主题</div>
                  <div class="impact-tags">
                    <span
                      v-for="topic in row.user_profile?.preferred_topics || row.preferred_topics_usage?.available_topics || []"
                      :key="topic"
                      class="impact-tag"
                    >
                      {{ topic }}
                    </span>
                  </div>
                </div>
                <div class="impact-card">
                  <div class="impact-title">本次是否使用</div>
                  <div class="impact-value">{{ row.preferred_topics_usage?.used ? "是" : "否" }}</div>
                </div>
                <div class="impact-card">
                  <div class="impact-title">引导查询数</div>
                  <div class="impact-value">{{ row.preferred_topics_usage?.guidance_query_count || 0 }}</div>
                </div>
                <div class="impact-card">
                  <div class="impact-title">应用步骤</div>
                  <div class="impact-tags">
                    <span
                      v-for="step in row.preferred_topics_usage?.applied_steps || []"
                      :key="step"
                      class="impact-tag impact-tag-step"
                    >
                      {{ step }}
                    </span>
                    <span v-if="!(row.preferred_topics_usage?.applied_steps || []).length" class="impact-empty">-</span>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="row.action_history?.length" class="timeline-wrap">
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
                      <strong>步骤 {{ historyIndex + 1 }}：{{ item.name || "-" }}</strong>
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
                    <span v-if="extractOutputField(item, 'fail_reason')">
                      失败原因：{{ extractOutputField(item, "fail_reason") }}
                    </span>
                  </div>
                  <div v-if="item.error" class="history-error">错误：{{ item.error }}</div>
                </div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" min-width="180">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column prop="action" label="动作" min-width="120" />
        <el-table-column prop="status" label="状态" min-width="90" />
        <el-table-column prop="duration_ms" label="耗时（ms）" min-width="110" />
        <el-table-column prop="total_tokens" label="令牌数" min-width="100" />
        <el-table-column label="预估成本（USD）" min-width="150">
          <template #default="{ row }">{{ formatCost(row.estimated_cost_usd) }}</template>
        </el-table-column>
        <el-table-column label="回答预览" min-width="280">
          <template #default="{ row }">{{ row.answer_preview || "-" }}</template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted } from "vue";

import { useAgentMonitor } from "./useAgentMonitor";

const { loading, runs, loadData, formatCost, formatDateTime, stringifyPayload, extractOutputField } =
  useAgentMonitor();

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

.profile-impact-panel {
  margin: 4px 8px 0;
  padding: 12px;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  background: linear-gradient(135deg, #f8fafc, #f0fdf4);
}

.impact-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}

.impact-card {
  padding: 12px;
  border-radius: 10px;
  background: #ffffff;
  border: 1px solid #e5ebf3;
}

.impact-title {
  margin-bottom: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
}

.impact-value {
  font-size: 24px;
  font-weight: 700;
  color: #14532d;
}

.impact-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.impact-tag {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 12px;
  color: #92400e;
  background: #fffbeb;
}

.impact-tag-step {
  color: #166534;
  background: #ecfdf5;
}

.impact-empty {
  font-size: 12px;
  color: #94a3b8;
}

.timeline-wrap {
  margin-top: 16px;
  padding: 10px;
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
  color: #475569;
}
</style>
