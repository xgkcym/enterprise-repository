<template>
  <div class="w-80 bg-white border-r border-gray-200 flex flex-col">
    <div class="p-4 border-b border-gray-200">
      <h2 class="text-lg font-semibold text-primary">RAG 检索助手</h2>
    </div>

    <div class="flex-1 overflow-y-auto p-2 sidebar-height">
      <div class="mb-2">
        <div
          class="accordion-header flex items-center justify-between p-3 bg-secondary rounded-lg cursor-pointer hover:bg-gray-200 transition-colors"
          @click="toggleAccordion('files')"
        >
          <div class="flex items-center">
            <i class="fas fa-folder-open mr-2 text-primary"></i>
            <span class="font-medium">上传文件</span>
          </div>
          <i
            class="fas fa-chevron-down text-xs transition-transform duration-300"
            :class="{ 'rotate-180': isFilesExpanded }"
          ></i>
        </div>

        <div v-if="isFilesExpanded" class="mt-2 pl-2">
          <div v-if="isLogin" class="mb-3 px-2">
            <div class="text-xs text-gray-500 mb-1">上传到部门</div>
            <select
              v-model="selectedDeptId"
              class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-primary/40"
            >
              <option :value="null" disabled>请选择部门</option>
              <option
                v-for="department in uploadDepartments"
                :key="department.dept_id"
                :value="department.dept_id"
              >
                {{ department.dept_name }}
              </option>
            </select>
            <div v-if="!uploadDepartments.length" class="mt-2 text-xs text-amber-600">
              当前账号没有可上传的部门权限
            </div>
          </div>

          <div id="fileList" class="space-y-2">
            <div v-if="!fileList.length" class="text-gray-500 text-sm italic pl-6">暂无上传文件</div>

            <div v-else class="space-y-2">
              <div v-for="folder in fileList" :key="folder.dept_id" class="border-l-2 border-gray-200 pl-4">
                <div
                  class="flex items-center justify-between p-2 rounded hover:bg-gray-100 cursor-pointer"
                  @click="toggleFolder(folder.dept_id)"
                >
                  <div class="flex items-center">
                    <i
                      class="fas mr-2 text-accent"
                      :class="expandedFolders.includes(folder.dept_id) ? 'fa-folder-open' : 'fa-folder'"
                    ></i>
                    <span class="text-sm font-medium">{{ folder.dept_name || `部门 ${folder.dept_id}` }}</span>
                    <span class="ml-2 text-xs text-gray-500">({{ folder.children.length }} 个文件)</span>
                  </div>
                  <i
                    class="fas fa-chevron-down text-xs transition-transform duration-300"
                    :class="{ 'rotate-180': expandedFolders.includes(folder.dept_id) }"
                  ></i>
                </div>

                <div
                  v-if="expandedFolders.includes(folder.dept_id)"
                  class="space-y-1 mt-1 pl-4 border-l-2 border-gray-100"
                >
                  <button
                    v-for="file in folder.children"
                    :key="file.file_id || file.file_name"
                    class="w-full p-2 rounded hover:bg-gray-100 flex items-center text-left"
                    @click="handleDownload(file)"
                  >
                    <i class="fas mr-2 text-accent" :class="getFileIcon(file.file_type)"></i>
                    <div class="truncate">
                      <div class="text-sm font-medium truncate">{{ file.file_name }}</div>
                    </div>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="mb-2">
        <div class="flex items-center gap-2">
          <div
            class="accordion-header flex-1 flex items-center justify-between p-3 bg-secondary rounded-lg cursor-pointer hover:bg-gray-200 transition-colors"
            @click="toggleAccordion('history')"
          >
            <div class="flex items-center">
              <i class="fas fa-history mr-2 text-primary"></i>
              <span class="font-medium">聊天历史</span>
            </div>
            <i
              class="fas fa-chevron-down text-xs transition-transform duration-300"
              :class="{ 'rotate-180': isHistoryExpanded }"
            ></i>
          </div>

          <button
            class="px-3 py-3 rounded-lg bg-primary text-white hover:bg-primary/90 transition-colors"
            @click="$emit('new-chat')"
          >
            <i class="fas fa-plus"></i>
          </button>
        </div>

        <div v-if="isHistoryExpanded" class="mt-2 pl-2">
          <div v-if="!sessions.length" class="text-gray-500 text-sm italic pl-3">暂无历史会话</div>
          <div v-else class="space-y-2">
            <div
              v-for="history in sessions"
              :key="history.session_id"
              class="p-2 rounded cursor-pointer flex items-center justify-between"
              :class="currentSessionId === history.session_id ? 'bg-primary/10 border border-primary/20' : 'hover:bg-gray-100'"
              @click="$emit('select-session', history.session_id)"
            >
              <div class="flex items-center truncate min-w-0">
                <i class="fas fa-comment-dots mr-2 text-accent"></i>
                <span class="truncate text-sm">{{ history.title }}</span>
              </div>
              <button
                class="text-gray-400 hover:text-red-500 text-xs ml-2"
                @click.stop="confirmDelete(history.session_id)"
              >
                <i class="fas fa-trash-alt"></i>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="p-4 border-t border-gray-200 bg-white">
      <div class="grid grid-cols-2 gap-3">
        <label
          class="flex flex-col items-center justify-center p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-primary hover:bg-primary/5 transition-colors cursor-pointer"
          :class="{ 'opacity-50 cursor-not-allowed': !isLogin || !uploadDepartments.length }"
        >
          <input
            type="file"
            @change="handleFolderUpload"
            webkitdirectory
            directory
            multiple
            class="hidden"
            :disabled="!isLogin || !uploadDepartments.length"
          />
          <i class="fas fa-folder-plus text-2xl text-primary mb-2"></i>
          <span class="text-sm font-medium">上传文件夹</span>
        </label>

        <label
          class="flex flex-col items-center justify-center p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-primary hover:bg-primary/5 transition-colors cursor-pointer"
          :class="{ 'opacity-50 cursor-not-allowed': !isLogin || !uploadDepartments.length }"
        >
          <input
            type="file"
            @change="handleFileUpload"
            multiple
            class="hidden"
            :disabled="!isLogin || !uploadDepartments.length"
          />
          <i class="fas fa-file-upload text-2xl text-primary mb-2"></i>
          <span class="text-sm font-medium">上传文件</span>
        </label>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from "vue";
import { ElMessage } from "element-plus";

import { download_file, get_file, get_upload_departments, upload_file } from "../api/file";

const props = defineProps({
  sessions: {
    type: Array,
    default: () => [],
  },
  currentSessionId: {
    type: String,
    default: "",
  },
  isLogin: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["new-chat", "select-session", "delete-session"]);

const isFilesExpanded = ref(true);
const isHistoryExpanded = ref(false);
const fileList = ref([]);
const expandedFolders = ref([]);
const uploadDepartments = ref([]);
const selectedDeptId = ref(null);

const toggleAccordion = (type) => {
  if (type === "files") {
    isFilesExpanded.value = !isFilesExpanded.value;
  } else {
    isHistoryExpanded.value = !isHistoryExpanded.value;
  }
};

const toggleFolder = (deptId) => {
  const index = expandedFolders.value.indexOf(deptId);
  if (index > -1) {
    expandedFolders.value.splice(index, 1);
  } else {
    expandedFolders.value.push(deptId);
  }
};

const getFileIcon = (fileType) => {
  if (!fileType) return "fa-file";
  if (fileType.includes("pdf")) return "fa-file-pdf";
  if (fileType.includes("doc")) return "fa-file-word";
  if (fileType.includes("xls") || fileType.includes("csv")) return "fa-file-excel";
  if (["png", "jpg", "jpeg", "bmp", "gif"].some((item) => fileType.includes(item))) return "fa-file-image";
  return "fa-file";
};

const queryFileList = async () => {
  if (!props.isLogin) {
    fileList.value = [];
    return;
  }

  const res = await get_file();
  if (res.code !== 200) return;

  const grouped = [];
  (res.data || []).forEach((file) => {
    const index = grouped.findIndex((item) => item.dept_id === file.dept_id);
    if (index >= 0) {
      grouped[index].children.push(file);
    } else {
      grouped.push({
        dept_id: file.dept_id,
        dept_name: file.dept_name,
        children: [file],
      });
    }
  });
  fileList.value = grouped;
};

const queryUploadDepartments = async () => {
  if (!props.isLogin) {
    uploadDepartments.value = [];
    selectedDeptId.value = null;
    return;
  }

  const res = await get_upload_departments();
  if (res.code !== 200) return;

  uploadDepartments.value = res.data || [];
  if (!uploadDepartments.value.some((department) => department.dept_id === selectedDeptId.value)) {
    selectedDeptId.value = uploadDepartments.value[0]?.dept_id ?? null;
  }
};

const handleFilesUpload = (files) => {
  if (!props.isLogin) {
    ElMessage.warning("请先登录");
    return;
  }
  if (!files.length) return;
  if (!selectedDeptId.value) {
    ElMessage.warning("请选择上传部门");
    return;
  }

  const requests = Array.from(files).map((file) => {
    const formData = new FormData();
    formData.append("file", file, file.name);
    formData.append("dept_id", selectedDeptId.value);
    return upload_file(formData);
  });

  Promise.all(requests)
    .then(async () => {
      ElMessage.success("上传任务已提交");
      await queryFileList();
    })
    .catch((err) => console.error("上传文件失败:", err));
};

const handleFolderUpload = (event) => {
  handleFilesUpload(event.target.files);
  event.target.value = "";
};

const handleFileUpload = (event) => {
  handleFilesUpload(event.target.files);
  event.target.value = "";
};

const handleDownload = async (file) => {
  if (!file?.download_url && !file?.file_path) {
    ElMessage.warning("该文件暂无可用下载地址");
    return;
  }
  try {
    await download_file(file.download_url || file.file_path, file.file_name);
  } catch (error) {
    console.error("下载文件失败:", error);
  }
};

const confirmDelete = (sessionId) => {
  if (window.confirm("确认删除这个会话吗？")) {
    emit("delete-session", sessionId);
  }
};

watch(
  () => props.isLogin,
  async (loggedIn) => {
    if (!loggedIn) {
      fileList.value = [];
      uploadDepartments.value = [];
      selectedDeptId.value = null;
      return;
    }
    await queryUploadDepartments();
    await queryFileList();
  },
  { immediate: true }
);
</script>
