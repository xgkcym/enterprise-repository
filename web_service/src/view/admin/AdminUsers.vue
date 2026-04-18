<template>
  <div class="admin-page">
    <div class="admin-page-header">
      <div>
        <h1>用户管理</h1>
        <p>`user_type` 用于区分管理员和普通用户，`role_id` 与 `dept_id` 继续负责部门权限控制。</p>
      </div>
      <div class="header-actions">
        <el-button @click="loadData">刷新</el-button>
        <el-button type="primary" :disabled="!canCreateUser" @click="openCreateDialog">新建用户</el-button>
      </div>
    </div>

    <el-alert
      v-if="!permissionRoles.length || !departments.length"
      type="warning"
      :closable="false"
      show-icon
      title="部门或权限角色尚未配置，暂时无法创建新用户。"
      class="mb-4"
    />

    <el-card shadow="hover" class="summary-card">
      <div class="summary-grid">
        <div class="summary-item">
          <span class="summary-label">用户总数</span>
          <span class="summary-value">{{ users.length }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">管理员</span>
          <span class="summary-value">{{ adminCount }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">普通用户</span>
          <span class="summary-value">{{ normalUserCount }}</span>
        </div>
      </div>
    </el-card>

    <el-card shadow="hover">
      <el-table :data="users" stripe>
        <el-table-column prop="username" label="用户名" min-width="140" />
        <el-table-column label="用户类型" width="120">
          <template #default="{ row }">
            <el-tag :type="row.is_admin ? 'danger' : 'info'">
              {{ getUserTypeLabel(row.user_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="role_name" label="权限角色" min-width="150" />
        <el-table-column prop="dept_name" label="默认部门" min-width="150" />
        <el-table-column prop="create_time" label="创建时间" min-width="180" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEditDialog(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogMode === 'create' ? '新建用户' : '编辑用户'" width="560px">
      <el-form label-position="top" :model="form">
        <el-form-item label="用户名" required>
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="用户类型" required>
          <el-select v-model="form.user_type" class="w-full">
            <el-option
              v-for="item in localizedUserTypeOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
          <div class="field-tip">
            {{ currentUserTypeDescription }}
          </div>
        </el-form-item>
        <el-form-item label="权限角色" required>
          <el-select v-model="form.role_id" class="w-full">
            <el-option
              v-for="item in permissionRoles"
              :key="item.role_id"
              :label="`${item.role_name} (#${item.role_id})`"
              :value="item.role_id"
            />
          </el-select>
          <div class="field-tip">这里继续沿用原有的 `role_id` 做部门权限控制。</div>
        </el-form-item>
        <el-form-item label="默认部门" required>
          <el-select v-model="form.dept_id" class="w-full">
            <el-option
              v-for="item in departments"
              :key="item.dept_id"
              :label="item.dept_name"
              :value="item.dept_id"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="dialogMode === 'create' ? '密码' : '重置密码'">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            :placeholder="dialogMode === 'create' ? '至少 6 位字符' : '留空则保持不变'"
          />
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
import { computed, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";

import {
  create_admin_user,
  get_admin_user_meta,
  list_admin_users,
  update_admin_user,
} from "../../api/user";

const users = ref([]);
const departments = ref([]);
const permissionRoles = ref([]);
const userTypeOptions = ref([]);
const dialogVisible = ref(false);
const dialogMode = ref("create");
const editingUserId = ref(null);
const submitting = ref(false);
const form = ref({
  username: "",
  password: "",
  dept_id: null,
  role_id: null,
  user_type: "user",
});

const userTypeTextMap = {
  admin: {
    label: "管理员",
    description: "管理员可以进入聊天界面和管理界面。",
  },
  user: {
    label: "普通用户",
    description: "普通用户只能进入聊天界面。",
  },
};

const getUserTypeLabel = (value) => userTypeTextMap[value]?.label || value || "-";

const localizedUserTypeOptions = computed(() =>
  (userTypeOptions.value.length ? userTypeOptions.value : [{ value: "admin" }, { value: "user" }]).map((item) => ({
    ...item,
    label: userTypeTextMap[item.value]?.label || item.label || item.value,
    description: userTypeTextMap[item.value]?.description || item.description || "",
  }))
);

const adminCount = computed(() => users.value.filter((item) => item.is_admin).length);
const normalUserCount = computed(() => users.value.length - adminCount.value);
const canCreateUser = computed(() => departments.value.length > 0 && permissionRoles.value.length > 0);
const currentUserTypeDescription = computed(() => {
  const current = localizedUserTypeOptions.value.find((item) => item.value === form.value.user_type);
  return current?.description || "";
});

const buildDefaultForm = () => ({
  username: "",
  password: "",
  dept_id: departments.value[0]?.dept_id ?? null,
  role_id: permissionRoles.value[0]?.role_id ?? null,
  user_type: "user",
});

const loadMeta = async () => {
  const res = await get_admin_user_meta();
  departments.value = res.data?.departments || [];
  permissionRoles.value = res.data?.permission_roles || [];
  userTypeOptions.value = res.data?.user_types || [];
};

const loadUsers = async () => {
  const res = await list_admin_users();
  users.value = res.data || [];
};

const loadData = async () => {
  await Promise.all([loadMeta(), loadUsers()]);
};

const openCreateDialog = () => {
  dialogMode.value = "create";
  editingUserId.value = null;
  form.value = buildDefaultForm();
  dialogVisible.value = true;
};

const openEditDialog = (user) => {
  dialogMode.value = "edit";
  editingUserId.value = user.id;
  form.value = {
    username: user.username,
    password: "",
    dept_id: user.dept_id,
    role_id: user.role_id,
    user_type: user.user_type || "user",
  };
  dialogVisible.value = true;
};

const submitForm = async () => {
  if (!form.value.username.trim()) {
    ElMessage.warning("请输入用户名");
    return;
  }
  if (!form.value.role_id || !form.value.dept_id) {
    ElMessage.warning("请选择权限角色和默认部门");
    return;
  }
  if (dialogMode.value === "create" && (!form.value.password || form.value.password.length < 6)) {
    ElMessage.warning("新用户密码至少需要 6 位");
    return;
  }

  const payload = {
    username: form.value.username.trim(),
    dept_id: form.value.dept_id,
    role_id: form.value.role_id,
    user_type: form.value.user_type,
  };

  if (form.value.password) {
    payload.password = form.value.password;
  }

  submitting.value = true;
  try {
    if (dialogMode.value === "create") {
      await create_admin_user(payload);
      ElMessage.success("用户创建成功");
    } else {
      await update_admin_user(editingUserId.value, payload);
      ElMessage.success("用户更新成功");
    }
    dialogVisible.value = false;
    await loadUsers();
  } finally {
    submitting.value = false;
  }
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

.summary-card {
  margin-bottom: 20px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.summary-item {
  padding: 14px 16px;
  border-radius: 16px;
  background: linear-gradient(135deg, #f8fafc 0%, #eef6ff 100%);
}

.summary-label {
  display: block;
  font-size: 13px;
  color: #607086;
}

.summary-value {
  display: block;
  margin-top: 10px;
  font-size: 28px;
  font-weight: 700;
  color: #17212b;
}

.field-tip {
  margin-top: 6px;
  font-size: 12px;
  color: #64748b;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.mb-4 {
  margin-bottom: 16px;
}

.w-full {
  width: 100%;
}
</style>
