<template>
  <div class="admin-page">
    <div class="admin-page-header">
      <div>
        <h1>文件管理</h1>
        <p>查看各部门上传的文件，并在需要时进行下载或删除。</p>
      </div>
      <div class="header-actions">
        <el-button @click="loadFiles">刷新</el-button>
      </div>
    </div>

    <el-card shadow="hover" class="filter-card">
      <div class="filter-row">
        <el-input v-model="filters.keyword" placeholder="按文件名搜索" clearable />
        <el-select v-model="filters.deptId" clearable placeholder="选择部门">
          <el-option
            v-for="department in departmentOptions"
            :key="department.dept_id"
            :label="department.dept_name"
            :value="department.dept_id"
          />
        </el-select>
        <el-select v-model="filters.state" clearable placeholder="选择状态">
          <el-option
            v-for="state in stateOptions"
            :key="state.value"
            :label="state.label"
            :value="state.value"
          />
        </el-select>
      </div>
    </el-card>

    <el-card shadow="hover">
      <el-table :data="filteredFiles" stripe>
        <el-table-column prop="file_id" label="编号" width="90" />
        <el-table-column prop="file_name" label="文件名" min-width="240" />
        <el-table-column prop="dept_name" label="所属部门" min-width="140" />
        <el-table-column prop="username" label="上传用户" min-width="140" />
        <el-table-column prop="file_type" label="类型" width="100" />
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.state)">
              {{ getStateLabel(row.state) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="创建时间" min-width="180" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleDownload(row)">下载</el-button>
            <el-button link type="danger" :disabled="row.state === '0'" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";

import { delete_admin_file, download_file, list_admin_files } from "../../api/file";

const files = ref([]);
const filters = ref({
  keyword: "",
  deptId: null,
  state: "",
});

const stateOptions = [
  { value: "0", label: "已删除" },
  { value: "1", label: "已就绪" },
  { value: "2", label: "处理中" },
  { value: "3", label: "待处理" },
  { value: "4", label: "失败" },
];

const getStateLabel = (state) => {
  const current = stateOptions.find((item) => item.value === state);
  return current?.label || state;
};

const departmentOptions = computed(() => {
  const map = new Map();
  files.value.forEach((file) => {
    if (!map.has(file.dept_id)) {
      map.set(file.dept_id, {
        dept_id: file.dept_id,
        dept_name: file.dept_name || `部门 ${file.dept_id}`,
      });
    }
  });
  return [...map.values()].sort((a, b) => a.dept_id - b.dept_id);
});

const filteredFiles = computed(() => {
  const keyword = filters.value.keyword.trim().toLowerCase();
  return files.value.filter((file) => {
    if (keyword && !String(file.file_name || "").toLowerCase().includes(keyword)) {
      return false;
    }
    if (filters.value.deptId && file.dept_id !== filters.value.deptId) {
      return false;
    }
    if (filters.value.state && file.state !== filters.value.state) {
      return false;
    }
    return true;
  });
});

const loadFiles = async () => {
  const res = await list_admin_files();
  files.value = res.data || [];
};

const statusTagType = (state) => {
  if (state === "1") return "success";
  if (state === "2") return "warning";
  if (state === "4") return "danger";
  return "info";
};

const handleDownload = async (file) => {
  await download_file(file.download_url, file.file_name);
};

const handleDelete = async (file) => {
  await ElMessageBox.confirm(`确定删除文件“${file.file_name}”吗？`, "提示", { type: "warning" });
  await delete_admin_file(file.file_id);
  ElMessage.success("文件已删除");
  await loadFiles();
};

onMounted(loadFiles);
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

.header-actions {
  display: flex;
  gap: 12px;
}

.filter-card {
  margin-bottom: 20px;
}

.filter-row {
  display: grid;
  grid-template-columns: 1.5fr 1fr 1fr;
  gap: 12px;
}

@media (max-width: 900px) {
  .filter-row {
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
