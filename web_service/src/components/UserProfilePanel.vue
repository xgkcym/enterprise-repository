<template>
  <el-dialog
    :model-value="modelValue"
    title="User Profile"
    width="640px"
    destroy-on-close
    @close="emit('update:modelValue', false)"
  >
    <el-form label-position="top" class="profile-form">
      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="Default answer style">
            <el-select v-model="form.answer_style" class="w-full">
              <el-option label="Concise" value="concise" />
              <el-option label="Standard" value="standard" />
              <el-option label="Detailed" value="detailed" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="Preferred language">
            <el-select v-model="form.preferred_language" class="w-full">
              <el-option label="Chinese" value="zh-CN" />
              <el-option label="English" value="en-US" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="Preferred topics">
        <el-select
          v-model="form.preferred_topics"
          multiple
          filterable
          allow-create
          default-first-option
          placeholder="Press Enter to add multiple topics"
          class="w-full"
        />
        <div class="helper-text">
          These topics are treated as weak hints during query rewriting and retrieval expansion.
        </div>
      </el-form-item>

      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="Show citations">
            <el-switch v-model="form.prefers_citations" />
            <div class="helper-text">
              When off, the UI will hide citations when possible while audit data remains available.
            </div>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="Allow web search">
            <el-switch v-model="form.allow_web_search" />
            <div class="helper-text">
              When on, live public-information questions may route to web search.
            </div>
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="Notes">
        <el-input
          v-model="form.profile_notes"
          type="textarea"
          :rows="4"
          maxlength="1000"
          show-word-limit
          placeholder="Optional role context, communication style, or long-term interests."
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="emit('update:modelValue', false)">Cancel</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">Save</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { reactive, watch } from "vue";

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  profile: {
    type: Object,
    default: () => ({
      answer_style: "standard",
      preferred_language: "zh-CN",
      preferred_topics: [],
      prefers_citations: true,
      allow_web_search: false,
      profile_notes: "",
    }),
  },
  saving: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["update:modelValue", "save"]);

const form = reactive({
  answer_style: "standard",
  preferred_language: "zh-CN",
  preferred_topics: [],
  prefers_citations: true,
  allow_web_search: false,
  profile_notes: "",
});

const syncForm = (profile) => {
  form.answer_style = profile?.answer_style || "standard";
  form.preferred_language = profile?.preferred_language || "zh-CN";
  form.preferred_topics = Array.isArray(profile?.preferred_topics) ? [...profile.preferred_topics] : [];
  form.prefers_citations = profile?.prefers_citations !== false;
  form.allow_web_search = !!profile?.allow_web_search;
  form.profile_notes = profile?.profile_notes || "";
};

watch(
  () => props.profile,
  (value) => {
    syncForm(value);
  },
  { immediate: true, deep: true }
);

watch(
  () => props.modelValue,
  (open) => {
    if (open) {
      syncForm(props.profile);
    }
  }
);

const handleSave = () => {
  emit("save", {
    answer_style: form.answer_style,
    preferred_language: form.preferred_language,
    preferred_topics: [...form.preferred_topics],
    prefers_citations: form.prefers_citations,
    allow_web_search: form.allow_web_search,
    profile_notes: form.profile_notes,
  });
};
</script>

<style scoped>
.profile-form :deep(.el-form-item) {
  margin-bottom: 18px;
}

.helper-text {
  margin-top: 6px;
  font-size: 12px;
  line-height: 1.5;
  color: #6b7280;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.w-full {
  width: 100%;
}
</style>
