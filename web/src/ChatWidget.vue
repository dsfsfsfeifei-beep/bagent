<script setup lang="ts">
/**
 * 极简聊天侧栏。生产里换成你们自己的 UI 组件库即可。
 * 关键是：useBagent + buildActions 的接线方式，不在样式。
 */
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useBagent } from "./bagent";
import { buildActions } from "./actions";

const props = defineProps<{
  wsBase: string;
  threadId: string;
  token: string;
}>();

const router = useRouter();
const input = ref("");

// 简单的 confirm 实现：用浏览器原生 confirm。生产里换成你们的 Modal。
const confirm = {
  open: async (prompt: string) => window.confirm(prompt),
};

// 简单的 form bus：派发 CustomEvent，由具体表单组件监听。
const forms = {
  prefill(formId: string, data: Record<string, unknown>) {
    window.dispatchEvent(new CustomEvent("bagent:prefill", { detail: { formId, data } }));
  },
};

const actions = buildActions({ router, confirm, forms });
const { messages, connected, sendMessage } = useBagent({
  wsBase: props.wsBase,
  threadId: props.threadId,
  token: props.token,
  actions,
});

function submit() {
  const t = input.value.trim();
  if (!t) return;
  sendMessage(t);
  input.value = "";
}
</script>

<template>
  <div class="bagent">
    <header>供应商助手 <span :class="{ dot: true, on: connected }" /></header>
    <ul>
      <li v-for="(m, i) in messages" :key="i" :class="m.role">
        <pre>{{ m.text }}</pre>
      </li>
    </ul>
    <form @submit.prevent="submit">
      <input v-model="input" placeholder="问点什么…" />
      <button :disabled="!connected">发送</button>
    </form>
  </div>
</template>

<style scoped>
.bagent { display:flex; flex-direction:column; height:100%; border-left:1px solid #e5e5e5; }
header { padding:8px 12px; border-bottom:1px solid #eee; display:flex; align-items:center; gap:8px; }
.dot { width:8px; height:8px; border-radius:50%; background:#bbb; }
.dot.on { background:#3c3; }
ul { flex:1; overflow:auto; list-style:none; padding:8px; margin:0; }
li { margin:6px 0; }
li.user pre { background:#eef; padding:6px 8px; border-radius:6px; }
li.assistant pre { background:#f4f4f4; padding:6px 8px; border-radius:6px; }
pre { white-space:pre-wrap; margin:0; font-family:inherit; }
form { display:flex; padding:8px; border-top:1px solid #eee; gap:8px; }
input { flex:1; padding:6px 8px; }
</style>
