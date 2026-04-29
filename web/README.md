# bagent web SDK (Vue 3)

把这三个文件拷进你们的 Vue 项目（或发成包），然后在外层布局里挂上 `<ChatWidget>`。

## 文件

- `bagent.ts` — `useBagent()` composable：建 WebSocket、处理消息、把 UI action 派发到 handler。
- `actions.ts` — 默认 UI action 实现：路由跳转、高亮、表单预填、确认弹窗。`buildActions(deps)` 让你注入自己的 `router` / `confirm` / `forms`。
- `ChatWidget.vue` — 最小可用的聊天侧栏样例。

## 用法

```vue
<script setup lang="ts">
import ChatWidget from "@/bagent/ChatWidget.vue";
import { useUserStore } from "@/stores/user";

const user = useUserStore();
</script>

<template>
  <ChatWidget
    ws-base="ws://localhost:8080"
    :thread-id="`u_${user.id}`"
    :token="user.token"
  />
</template>
```

## 协议（和后端约定）

**子协议鉴权**：浏览器发起 WebSocket 时把 `bearer.<token>` 放在 `Sec-WebSocket-Protocol` 里。后端原样回 echo 后才算建联。

**消息**：

```ts
// 浏览器 → 后端
{ type: "user_message", text: "..." }
{ type: "action_result", id: "<cmd_id>", ok: true,  data: {...} }
{ type: "action_result", id: "<cmd_id>", ok: false, error: "..." }

// 后端 → 浏览器
{ type: "assistant_message", text: "..." }
{ type: "action", id: "<cmd_id>", name: "navigate_to", args: {...} }
```

## 表单预填

`prefill_form` 默认派发一个 `bagent:prefill` CustomEvent。在你的表单组件里监听它：

```ts
window.addEventListener("bagent:prefill", (e: any) => {
  const { formId, data } = e.detail;
  if (formId !== "supplier-edit") return;
  Object.assign(formState, data);
});
```

不喜欢 event bus 就在 `buildActions({ forms: ... })` 里换成 Pinia store。
