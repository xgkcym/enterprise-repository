<template>
  <div class="flex-1 flex flex-col bg-gray-50">
    <div class="p-4 border-b border-gray-200 bg-white flex items-center justify-between">
      <div class="flex items-center">
        <h3 class="font-semibold text-lg">{{ sessionTitle || "智能检索对话" }}</h3>
        <span class="ml-2 px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">已连接</span>
      </div>

      <div class="flex items-center space-x-3">
        <button
          v-if="!isLogin"
          class="px-4 py-1.5 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors flex items-center"
          @click="showLoginModal = true"
        >
          <i class="fas fa-user-circle mr-2"></i>
          <span>登录</span>
        </button>

        <div v-else class="flex items-center space-x-2">
          <span class="text-sm font-medium text-gray-700 truncate max-w-[100px]">
            {{ userInfo.username || "未知用户" }}
          </span>
          <div class="relative">
            <button class="text-gray-500 hover:text-primary transition-colors" @click="showUserMenu = !showUserMenu">
              <i class="fas fa-caret-down"></i>
            </button>
            <div
              v-if="showUserMenu"
              class="absolute right-0 top-full mt-2 w-40 bg-white rounded-lg shadow-lg border border-gray-100 z-10"
            >
              <div class="py-2">
                <button class="w-full text-left px-4 py-2 text-sm text-red-500 hover:bg-gray-100" @click="logout">
                  <i class="fas fa-sign-out-alt mr-2"></i>退出登录
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div ref="chatContainer" class="flex-1 p-6 overflow-y-auto chat-height space-y-6">
      <div class="flex flex-col items-start">
        <div class="flex items-center mb-1">
          <div class="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-white">
            <i class="fas fa-robot"></i>
          </div>
          <span class="ml-2 text-sm font-medium">智能助手</span>
        </div>
        <div class="bg-white p-4 rounded-lg rounded-tl-none shadow-sm max-w-3xl">
          <p class="text-gray-700">你好，我可以基于你有权限访问的知识库文档，结合 Agent 流程为你回答问题。</p>
        </div>
      </div>

      <div
        v-for="message in messages"
        :key="message.message_id"
        class="flex flex-col"
        :class="{ 'items-end': isUserMessage(message), 'items-start': !isUserMessage(message) }"
      >
        <div class="flex items-center mb-1 gap-2">
          <template v-if="isUserMessage(message)">
            <span class="text-sm font-medium">我</span>
            <div class="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-gray-700">
              <i class="fas fa-user"></i>
            </div>
          </template>
          <template v-else>
            <div class="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-white">
              <i class="fas fa-robot"></i>
            </div>
            <span class="text-sm font-medium">智能助手</span>
          </template>
        </div>

        <div
          class="p-4 rounded-lg shadow-sm max-w-3xl"
          :class="{
            'rounded-tr-none bg-primary/10': isUserMessage(message),
            'rounded-tl-none bg-white': !isUserMessage(message),
          }"
        >
          <p class="text-gray-700 whitespace-pre-wrap">{{ message.content }}</p>

          <div v-if="!isUserMessage(message) && message.citations && message.citations.length" class="mt-3 pt-3 border-t border-gray-100">
            <div class="text-xs font-medium text-gray-500 mb-2">引用来源</div>
            <div class="flex flex-wrap gap-2">
              <span v-for="citation in message.citations" :key="citation" class="px-2 py-1 bg-gray-100 rounded text-xs text-gray-600">
                {{ citation }}
              </span>
            </div>
          </div>

          <div v-if="message.status === 'streaming'" class="mt-2 text-xs text-primary flex items-center gap-2">
            <span class="inline-block w-2 h-2 rounded-full bg-primary animate-pulse"></span>
            正在生成
          </div>
        </div>
      </div>
    </div>

    <div class="p-4 border-t border-gray-200 bg-white">
      <div class="flex flex-col space-y-3">
        <div class="relative">
          <textarea
            v-model="inputMessage"
            class="w-full p-3 pr-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary resize-none h-20"
            :placeholder="isLogin ? '请输入你的问题...' : '请先登录后再开始对话'"
            :disabled="!isLogin || isStreaming"
            @keydown.enter.exact.prevent="emitSend"
          ></textarea>
        </div>

        <div class="flex justify-between items-center">
          <div class="text-xs text-gray-400">{{ isStreaming ? "Agent 正在处理中..." : "支持流式回答与历史会话切换" }}</div>
          <button
            class="px-6 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="!isLogin || isStreaming || !inputMessage.trim()"
            @click="emitSend"
          >
            <span>{{ isStreaming ? "生成中" : "发送" }}</span>
            <i class="fas fa-paper-plane ml-2"></i>
          </button>
        </div>
      </div>
    </div>

    <teleport to="body">
      <div v-if="showLoginModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg w-full max-w-sm p-6">
          <h3 class="text-lg font-semibold text-center mb-4">用户登录</h3>

          <div class="space-y-4">
            <input
              v-model="loginForm.username"
              type="text"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50"
              placeholder="请输入用户名"
            />
            <input
              v-model="loginForm.password"
              type="password"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50"
              placeholder="请输入密码"
            />
          </div>

          <div class="flex space-x-2 mt-4">
            <button class="flex-1 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors" @click="showLoginModal = false">取消</button>
            <button class="flex-1 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors" @click="handleLogin">登录</button>
          </div>
        </div>
      </div>
    </teleport>
  </div>
</template>

<script setup>
import { nextTick, ref, watch } from "vue";

import { user_login } from "../api/user";

const props = defineProps({
  messages: {
    type: Array,
    default: () => [],
  },
  isLogin: {
    type: Boolean,
    default: false,
  },
  userInfo: {
    type: Object,
    default: () => ({ username: "" }),
  },
  isStreaming: {
    type: Boolean,
    default: false,
  },
  sessionTitle: {
    type: String,
    default: "智能检索对话",
  },
});

const emit = defineEmits(["login-success", "logout", "send-message"]);

const inputMessage = ref("");
const showLoginModal = ref(false);
const showUserMenu = ref(false);
const chatContainer = ref(null);
const loginForm = ref({
  username: "EdenXie",
  password: "123456",
});

const scrollToBottom = async () => {
  await nextTick();
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
  }
};

const isUserMessage = (message) => message.role === "user";

const emitSend = () => {
  const query = inputMessage.value.trim();
  if (!query || !props.isLogin || props.isStreaming) return;
  emit("send-message", query);
  inputMessage.value = "";
};

const handleLogin = () => {
  user_login(loginForm.value).then((res) => {
    if (res.code === 200) {
      localStorage.setItem("token", res.data.access_token);
      localStorage.setItem("userInfo", JSON.stringify(res.data.user));
      showLoginModal.value = false;
      showUserMenu.value = false;
      emit("login-success", { user: res.data.user });
    }
  });
};

const logout = () => {
  showUserMenu.value = false;
  localStorage.removeItem("token");
  localStorage.removeItem("userInfo");
  emit("logout");
};

watch(
  () => props.messages,
  () => {
    scrollToBottom();
  },
  { deep: true }
);
</script>
