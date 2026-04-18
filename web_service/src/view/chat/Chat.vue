<template>
  <div class="font-inter bg-gray-50 text-dark antialiased">
    <div class="flex h-screen overflow-hidden">
      <Sidebar
        :sessions="sessions"
        :current-session-id="currentSessionId"
        :is-login="isLogin"
        @new-chat="handleNewChat"
        @select-session="handleSelectSession"
        @delete-session="handleDeleteSession"
      />
      <ChatWindow
        :messages="messages"
        :is-login="isLogin"
        :user-info="userInfo"
        :user-profile="userProfile"
        :is-streaming="isStreaming"
        :is-saving-profile="isSavingProfile"
        :session-title="currentSessionTitle"
        :output-level="outputLevel"
        @login-success="handleLoginSuccess"
        @logout="handleLogout"
        @save-profile="handleProfileSave"
        @update:output-level="handleOutputLevelChange"
        @send-message="handleSendMessage"
      />
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";

import { delete_chat_session, get_chat_messages, list_chat_sessions, stream_agent_chat } from "../../api/chat";
import { get_user_profile, update_user_profile } from "../../api/user";
import ChatWindow from "../../components/ChatWindow.vue";
import Sidebar from "../../components/Sidebar.vue";

const defaultUserProfile = () => ({
  answer_style: "standard",
  preferred_language: "zh-CN",
  preferred_topics: [],
  prefers_citations: true,
  allow_web_search: false,
  profile_notes: "",
});

const sessions = ref([]);
const currentSessionId = ref("");
const messages = ref([]);
const isStreaming = ref(false);
const isSavingProfile = ref(false);
const isLogin = ref(!!localStorage.getItem("token"));
const userProfile = ref(defaultUserProfile());
const outputLevel = ref(localStorage.getItem("agentOutputLevel") || "standard");
const userInfo = ref(
  localStorage.getItem("userInfo")
    ? JSON.parse(localStorage.getItem("userInfo"))
    : { username: "", user_type: "user", is_admin: false }
);

const currentSessionTitle = computed(() => {
  const current = sessions.value.find((item) => item.session_id === currentSessionId.value);
  return current?.title || "新会话";
});

const normalizeMessage = (message) => ({
  message_id:
    message.message_id || `message-${Date.now()}-${Math.random().toString(16).slice(2)}`,
  role: message.role || "assistant",
  content: message.content || "",
  citations: message.citations || [],
  report_summary: message.report_summary || null,
  status: message.status || "completed",
  created_at: message.created_at || new Date().toISOString(),
});

const loadUserProfile = async () => {
  if (!isLogin.value) {
    userProfile.value = defaultUserProfile();
    return;
  }

  const res = await get_user_profile();
  const profile = res.data || defaultUserProfile();
  userProfile.value = {
    ...defaultUserProfile(),
    ...profile,
    preferred_topics: Array.isArray(profile.preferred_topics) ? profile.preferred_topics : [],
  };

  if (!localStorage.getItem("agentOutputLevel")) {
    outputLevel.value = userProfile.value.answer_style || "standard";
  }
};

const upsertSession = (session) => {
  if (!session?.session_id) return;
  const index = sessions.value.findIndex((item) => item.session_id === session.session_id);
  if (index >= 0) {
    sessions.value[index] = { ...sessions.value[index], ...session };
  } else {
    sessions.value.unshift(session);
  }
  sessions.value = [...sessions.value].sort((a, b) =>
    (b.updated_at || "").localeCompare(a.updated_at || "")
  );
};

const handleSelectSession = async (sessionId) => {
  if (!sessionId || !isLogin.value) return;
  const res = await get_chat_messages(sessionId);
  currentSessionId.value = sessionId;
  messages.value = (res.data?.messages || []).map(normalizeMessage);
};

const loadSessions = async ({ preferSessionId = "" } = {}) => {
  if (!isLogin.value) return;
  const res = await list_chat_sessions();
  sessions.value = res.data || [];

  const targetSessionId =
    preferSessionId || currentSessionId.value || sessions.value[0]?.session_id || "";

  if (!targetSessionId) {
    return;
  }

  const exists = sessions.value.some((item) => item.session_id === targetSessionId);
  if (!exists) {
    currentSessionId.value = "";
    messages.value = [];
    return;
  }

  if (currentSessionId.value !== targetSessionId || !messages.value.length) {
    await handleSelectSession(targetSessionId);
  }
};

const handleNewChat = () => {
  currentSessionId.value = "";
  messages.value = [];
};

const handleDeleteSession = async (sessionId) => {
  await delete_chat_session(sessionId);
  sessions.value = sessions.value.filter((item) => item.session_id !== sessionId);

  if (currentSessionId.value === sessionId) {
    const nextSessionId = sessions.value[0]?.session_id || "";
    if (nextSessionId) {
      await handleSelectSession(nextSessionId);
    } else {
      handleNewChat();
    }
  }
};

const handleLoginSuccess = async ({ user }) => {
  isLogin.value = true;
  userInfo.value = user || { username: "", user_type: "user", is_admin: false };
  await loadUserProfile();
  await loadSessions();
};

const handleLogout = () => {
  isLogin.value = false;
  userInfo.value = { username: "", user_type: "user", is_admin: false };
  userProfile.value = defaultUserProfile();
  sessions.value = [];
  handleNewChat();
};

const handleOutputLevelChange = (value) => {
  outputLevel.value = value || "standard";
  localStorage.setItem("agentOutputLevel", outputLevel.value);
};

const handleProfileSave = async (payload) => {
  isSavingProfile.value = true;
  try {
    const res = await update_user_profile(payload);
    const profile = res.data || payload;
    userProfile.value = {
      ...defaultUserProfile(),
      ...profile,
      preferred_topics: Array.isArray(profile.preferred_topics) ? profile.preferred_topics : [],
    };
    outputLevel.value = userProfile.value.answer_style || "standard";
    localStorage.setItem("agentOutputLevel", outputLevel.value);
    ElMessage.success("偏好设置已更新");
  } finally {
    isSavingProfile.value = false;
  }
};

const ensureAssistantMessage = (messageId) => {
  const index = messages.value.findIndex((item) => item.message_id === messageId);
  if (index >= 0) {
    return index;
  }
  messages.value.push(
    normalizeMessage({
      message_id: messageId,
      role: "assistant",
      content: "",
      status: "streaming",
    })
  );
  return messages.value.length - 1;
};

const handleSendMessage = async (query) => {
  if (!query?.trim() || isStreaming.value) return;

  isStreaming.value = true;
  messages.value.push(
    normalizeMessage({
      role: "user",
      content: query.trim(),
    })
  );

  let assistantMessageId = "";
  try {
    await stream_agent_chat({
      query: query.trim(),
      sessionId: currentSessionId.value || undefined,
      outputLevel: outputLevel.value,
      onEvent: ({ event, data }) => {
        if (event === "session_created") {
          upsertSession(data);
          currentSessionId.value = data.session_id;
          return;
        }

        if (event === "message_started") {
          assistantMessageId = data.message_id;
          ensureAssistantMessage(assistantMessageId);
          messages.value[ensureAssistantMessage(assistantMessageId)].report_summary = {
            status: "streaming",
            action: "",
            reason: "",
            output_level: data.output_level || outputLevel.value,
            trace: [],
            action_history: [],
          };
          return;
        }

        if (event === "token") {
          const index = ensureAssistantMessage(data.message_id || assistantMessageId);
          messages.value[index].content += data.content || "";
          messages.value[index].status = "streaming";
          return;
        }

        if (event === "message_completed") {
          const finalMessage = normalizeMessage({
            ...data.message,
            report_summary: data.report_summary || null,
          });
          const index = ensureAssistantMessage(finalMessage.message_id);
          messages.value[index] = finalMessage;
          currentSessionId.value = data.session_id || currentSessionId.value;
          return;
        }

        if (event === "error") {
          const targetId = assistantMessageId || `assistant-error-${Date.now()}`;
          const index = ensureAssistantMessage(targetId);
          messages.value[index].content = data.message || "请求失败，请重试。";
          messages.value[index].status = "failed";
        }
      },
    });
  } finally {
    isStreaming.value = false;
    await loadSessions({ preferSessionId: currentSessionId.value });
  }
};

onMounted(async () => {
  if (isLogin.value) {
    await loadUserProfile();
    await loadSessions();
  }
});
</script>
