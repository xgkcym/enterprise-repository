<template>
  <div class="admin-page">
    <div class="admin-page-header">
      <div>
        <h1>部门管理</h1>
        <p>维护业务部门，供用户、文件和角色权限映射使用。</p>
      </div>
      <div class="header-actions">
        <el-button @click="loadDepartments">刷新</el-button>
        <el-button type="primary" @click="openCreateDialog">新增部门</el-button>
      </div>
    </div>

    <el-card shadow="hover">
      <el-table :data="departments" stripe>
        <el-table-column prop="dept_id" label="编号" width="90" />
        <el-table-column prop="dept_name" label="部门名称" min-width="220" />
        <el-table-column prop="user_count" label="用户数" width="100" />
        <el-table-column prop="role_count" label="角色映射数" width="140" />
        <el-table-column prop="file_count" label="文件数" width="100" />
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEditDialog(row)">编辑</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogMode === 'create' ? '新增部门' : '编辑部门'" width="480px">
      <el-form label-position="top" :model="form">
        <el-form-item label="部门名称" required>
          <el-input v-model="form.dept_name" placeholder="请输入部门名称" />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="submitting" @click="submitForm">保存</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";

import {
  create_admin_department,
  delete_admin_department,
  list_admin_departments,
  update_admin_department,
} from "../../api/role";

const departments = ref([]);
const dialogVisible = ref(false);
const dialogMode = ref("create");
const editingDeptId = ref(null);
const submitting = ref(false);
const form = ref({ dept_name: "" });

const loadDepartments = async () => {
  const res = await list_admin_departments();
  departments.value = res.data || [];
};

const openCreateDialog = () => {
  dialogMode.value = "create";
  editingDeptId.value = null;
  form.value = { dept_name: "" };
  dialogVisible.value = true;
};

const openEditDialog = (department) => {
  dialogMode.value = "edit";
  editingDeptId.value = department.dept_id;
  form.value = { dept_name: department.dept_name };
  dialogVisible.value = true;
};

const submitForm = async () => {
  const deptName = form.value.dept_name.trim();
  if (!deptName) {
    ElMessage.warning("请输入部门名称");
    return;
  }

  submitting.value = true;
  try {
    if (dialogMode.value === "create") {
      await create_admin_department({ dept_name: deptName });
      ElMessage.success("部门创建成功");
    } else {
      await update_admin_department(editingDeptId.value, { dept_name: deptName });
      ElMessage.success("部门更新成功");
    }
    dialogVisible.value = false;
    await loadDepartments();
  } finally {
    submitting.value = false;
  }
};

const handleDelete = async (department) => {
  await ElMessageBox.confirm(`确定删除部门“${department.dept_name}”吗？`, "提示", { type: "warning" });
  await delete_admin_department(department.dept_id);
  ElMessage.success("部门已删除");
  await loadDepartments();
};

onMounted(loadDepartments);
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

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
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
