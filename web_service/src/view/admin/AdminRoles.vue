<template>
  <div class="admin-page">
    <div class="admin-page-header">
      <div>
        <h1>角色管理</h1>
        <p>维护权限角色，并配置每个角色可以访问的部门范围。</p>
      </div>
      <div class="header-actions">
        <el-button @click="loadData">刷新</el-button>
        <el-button type="primary" @click="openCreateDialog">新增角色</el-button>
      </div>
    </div>

    <el-card shadow="hover">
      <el-table :data="roles" stripe>
        <el-table-column prop="role_id" label="编号" width="90" />
        <el-table-column prop="role_name" label="角色名称" min-width="180" />
        <el-table-column label="可访问部门" min-width="260">
          <template #default="{ row }">
            <div class="tag-wrap">
              <el-tag
                v-for="department in row.departments"
                :key="`${row.role_id}-${department.dept_id}`"
                size="small"
                effect="plain"
              >
                {{ department.dept_name }}
              </el-tag>
              <span v-if="!row.departments.length" class="muted-text">未分配部门</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="user_count" label="用户数" width="100" />
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEditDialog(row)">编辑</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogMode === 'create' ? '新增角色' : '编辑角色'" width="560px">
      <el-form label-position="top" :model="form">
        <el-form-item label="角色名称" required>
          <el-input v-model="form.role_name" placeholder="请输入角色名称" />
        </el-form-item>
        <el-form-item label="可访问部门">
          <el-select v-model="form.dept_ids" multiple collapse-tags class="w-full" placeholder="请选择部门">
            <el-option
              v-for="department in departments"
              :key="department.dept_id"
              :label="department.dept_name"
              :value="department.dept_id"
            />
          </el-select>
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
  create_admin_role,
  delete_admin_role,
  get_role_admin_meta,
  list_admin_roles,
  update_admin_role,
} from "../../api/role";

const roles = ref([]);
const departments = ref([]);
const dialogVisible = ref(false);
const dialogMode = ref("create");
const editingRoleId = ref(null);
const submitting = ref(false);
const form = ref({ role_name: "", dept_ids: [] });

const loadData = async () => {
  const [rolesRes, metaRes] = await Promise.all([list_admin_roles(), get_role_admin_meta()]);
  roles.value = rolesRes.data || [];
  departments.value = metaRes.data?.departments || [];
};

const openCreateDialog = () => {
  dialogMode.value = "create";
  editingRoleId.value = null;
  form.value = { role_name: "", dept_ids: [] };
  dialogVisible.value = true;
};

const openEditDialog = (role) => {
  dialogMode.value = "edit";
  editingRoleId.value = role.role_id;
  form.value = {
    role_name: role.role_name,
    dept_ids: [...(role.dept_ids || [])],
  };
  dialogVisible.value = true;
};

const submitForm = async () => {
  const roleName = form.value.role_name.trim();
  if (!roleName) {
    ElMessage.warning("请输入角色名称");
    return;
  }

  const payload = {
    role_name: roleName,
    dept_ids: form.value.dept_ids || [],
  };

  submitting.value = true;
  try {
    if (dialogMode.value === "create") {
      await create_admin_role(payload);
      ElMessage.success("角色创建成功");
    } else {
      await update_admin_role(editingRoleId.value, payload);
      ElMessage.success("角色更新成功");
    }
    dialogVisible.value = false;
    await loadData();
  } finally {
    submitting.value = false;
  }
};

const handleDelete = async (role) => {
  await ElMessageBox.confirm(`确定删除角色“${role.role_name}”吗？`, "提示", { type: "warning" });
  await delete_admin_role(role.role_id);
  ElMessage.success("角色已删除");
  await loadData();
};

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

.header-actions {
  display: flex;
  gap: 12px;
}

.tag-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.muted-text {
  color: #94a3b8;
  font-size: 13px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.w-full {
  width: 100%;
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
