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
          <i class="fas fa-chevron-down text-xs transition-transform duration-300" :class="{ 'rotate-180': isFilesExpanded }"></i>
        </div>

        <div v-if="isFilesExpanded" class="mt-2 pl-2">
          <div id="fileList" class="space-y-2">
            <div v-if="!fileList.length" class="text-gray-500 text-sm italic pl-6">暂无上传文件</div>

            <div v-else class="space-y-2">
              <div v-for="folder in fileList" :key="folder.dept_id" class="border-l-2 border-gray-200 pl-4">
                <div class="flex items-center justify-between p-2 rounded hover:bg-gray-100 cursor-pointer" @click="toggleFolder(folder.dept_id)">
                  <div class="flex items-center">
                    <i class="fas mr-2 text-accent" :class="expandedFolders.includes(folder.dept_id) ? 'fa-folder-open' : 'fa-folder'"></i>
                    <span class="text-sm font-medium">{{ folder.dept_name || `部门 ${folder.dept_id}` }}</span>
                    <span class="ml-2 text-xs text-gray-500">({{ folder.children.length }} 个文件)</span>
                  </div>
                  <i class="fas fa-chevron-down text-xs transition-transform duration-300" :class="{ 'rotate-180': expandedFolders.includes(folder.dept_id) }"></i>
                </div>

                <div v-if="expandedFolders.includes(folder.dept_id)" class="space-y-1 mt-1 pl-4 border-l-2 border-gray-100">
                  <div v-for="file in folder.children" :key="file.id || file.file_name" class="p-2 rounded hover:bg-gray-100 flex items-center">
                    <i class="fas mr-2 text-accent" :class="getFileIcon(file.type)"></i>
                    <div class="truncate">
                      <div class="text-sm font-medium truncate">{{ file.file_name }}</div>
                    </div>
                  </div>
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
            <i class="fas fa-chevron-down text-xs transition-transform duration-300" :class="{ 'rotate-180': isHistoryExpanded }"></i>
          </div>

          <button class="px-3 py-3 rounded-lg bg-primary text-white hover:bg-primary/90 transition-colors" @click="$emit('new-chat')">
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
              <button class="text-gray-400 hover:text-red-500 text-xs ml-2" @click.stop="confirmDelete(history.session_id)">
                <i class="fas fa-trash-alt"></i>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="p-4 border-t border-gray-200 bg-white">
      <div class="grid grid-cols-2 gap-3">
        <label class="flex flex-col items-center justify-center p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-primary hover:bg-primary/5 transition-colors cursor-pointer">
          <input type="file" @change="handleFolderUpload" webkitdirectory directory multiple class="hidden" />
          <i class="fas fa-folder-plus text-2xl text-primary mb-2"></i>
          <span class="text-sm font-medium">上传文件夹</span>
        </label>

        <label class="flex flex-col items-center justify-center p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-primary hover:bg-primary/5 transition-colors cursor-pointer">
          <input type="file" @change="handleFileUpload" multiple class="hidden" />
          <i class="fas fa-file-upload text-2xl text-primary mb-2"></i>
          <span class="text-sm font-medium">上传文件</span>
        </label>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";

import { get_file, upload_file } from "../api/file";

defineProps({
  sessions: {
    type: Array,
    default: () => [],
  },
  currentSessionId: {
    type: String,
    default: "",
  },
});

const emit = defineEmits(["new-chat", "select-session", "delete-session"]);

const isFilesExpanded = ref(true);
const isHistoryExpanded = ref(false);
const fileList = ref([]);
const expandedFolders = ref([]);

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
  if (fileType.includes("word")) return "fa-file-word";
  if (fileType.includes("excel")) return "fa-file-excel";
  if (fileType.includes("image")) return "fa-file-image";
  return "fa-file";
};

const queryFileList = () => {
  get_file().then((res) => {
    if (res.code === 200) {
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
    }
  });
};

const handleFilesUpload = (files) => {
  if (!files.length) return;
  const requests = Array.from(files).map((file, index) => {
    const formData = new FormData();
    formData.append("file", file, file.name);
    formData.append("user_id", 1);
    formData.append("dept_id", index % 3 + 1);
    return upload_file(formData);
  });

  Promise.all(requests)
    .then(() => queryFileList())
    .catch((err) => console.error("上传文件失败:", err));
};

const handleFolderUpload = (event) => {
  handleFilesUpload(event.target.files);
};

const handleFileUpload = (event) => {
  handleFilesUpload(event.target.files);
};

const confirmDelete = (sessionId) => {
  if (window.confirm("确认删除这个会话吗？")) {
    emit("delete-session", sessionId);
  }
};

onMounted(() => {
  queryFileList();
});
</script>
