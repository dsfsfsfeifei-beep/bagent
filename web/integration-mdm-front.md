# 在 cloud-mdm-front 里集成 bagent

把 bagent 聊天侧栏 + 页面操作能力嵌入 `cloud-mdm-front`（Vue 3 + Vite + Element Plus + Pinia + vue-router）。

## 核心约定

- **sid 来源**：`URLSearchParams.get("sid")`，与 `services/api-base.ts` 一致。ChatWidget 把这个 sid 作为 WebSocket 子协议传给 bagent 后端，bagent 再透传给 SRM。
- **bagent 后端地址**：通过新增环境变量 `VITE_BAGENT_WS_BASE` 配置（默认 `ws://localhost:8080`）。dev 不走 Vite proxy，直连。
- **跨组件协调**：新增 `useAgentIntentStore`（Pinia）。ChatWidget 写意图 → 业务组件 watch 后执行（打开 Drawer / 预填表单）。**不要用全局 event bus**，否则跨页面就乱。
- **不可逆动作**：bagent 已强制 agent 在调用 `push_supplier_to_fol` 前调用 `confirm_with_user`，前端用 `ElMessageBox.confirm` 实现即可。

## 改动清单

### 1. 环境变量

**`.env.dev`**

```env
VITE_BAGENT_WS_BASE=ws://localhost:8080
```

**`.env.test` / `.env.prod`** —— 按部署填实际地址（`wss://...`）。

### 2. 新增：`src/stores/agent-intent.ts`

承载"agent 想让页面干什么"的共享意图。业务组件 watch 它，自己决定怎么响应。

```ts
import { defineStore } from "pinia";
import { ref } from "vue";

export const useAgentIntentStore = defineStore("agent-intent", () => {
  // 让供应商列表打开某个编码的详情抽屉
  const pendingSupplierDetailCode = ref<string | null>(null);
  // 让供应商表单预填一组字段
  const pendingSupplierFormPrefill = ref<Record<string, unknown> | null>(null);

  function openSupplierDetail(code: string) {
    pendingSupplierDetailCode.value = code;
  }
  function clearSupplierDetail() {
    pendingSupplierDetailCode.value = null;
  }

  function prefillSupplierForm(data: Record<string, unknown>) {
    pendingSupplierFormPrefill.value = data;
  }
  function clearSupplierFormPrefill() {
    pendingSupplierFormPrefill.value = null;
  }

  return {
    pendingSupplierDetailCode,
    pendingSupplierFormPrefill,
    openSupplierDetail,
    clearSupplierDetail,
    prefillSupplierForm,
    clearSupplierFormPrefill,
  };
});
```

### 3. 新增：`src/components/agent/useBagent.ts`

和 [bagent 仓库的 web/src/bagent.ts](src/bagent.ts) 一致，复制即可。要点：

- WebSocket 子协议 `bearer.<sid>` 鉴权（前后端约定）
- 接收 `assistant_message` / `action`，对 `action` 调用前端注册的 handler 后回 `action_result`
- 指数退避重连
- `messages` / `connected` / `sendMessage` 暴露给聊天 UI

完整代码见 [bagent/web/src/bagent.ts](src/bagent.ts)（无需改动）。

### 4. 新增：`src/components/agent/actions.ts`

对接到本项目的 router、Element Plus、agent-intent store。

```ts
import { ElMessage, ElMessageBox } from "element-plus";
import type { Router } from "vue-router";

import { useAgentIntentStore } from "@/stores/agent-intent";

export function buildActions(deps: { router: Router }) {
  const intent = useAgentIntentStore();

  return {
    navigate_to: ({ path }: { path: string }) => {
      deps.router.push(path);
    },

    open_supplier_detail: async ({ code }: { code: string }) => {
      // 不在供应商页就先跳过去；intent store 设好后由 SupplierManagementView 接管
      if (deps.router.currentRoute.value.path !== "/vendors") {
        await deps.router.push("/vendors");
      }
      intent.openSupplierDetail(code);
    },

    highlight_element: ({ selector }: { selector: string }) => {
      const el = document.querySelector<HTMLElement>(selector);
      if (!el) throw new Error(`element not found: ${selector}`);
      el.scrollIntoView({ behavior: "smooth", block: "center" });
      const prev = el.style.boxShadow;
      el.style.transition = "box-shadow 0.3s";
      el.style.boxShadow = "0 0 0 3px rgba(255, 196, 0, 0.9)";
      setTimeout(() => { el.style.boxShadow = prev; }, 2500);
    },

    prefill_form: ({ form_id, data }: { form_id: string; data: Record<string, unknown> }) => {
      // 当前只有一个表单，未来可按 form_id 路由到不同 store
      if (form_id !== "supplier-form") {
        ElMessage.warning(`未识别的表单 ${form_id}`);
        return;
      }
      intent.prefillSupplierForm(data);
    },

    confirm_with_user: async ({ prompt }: { prompt: string }) => {
      try {
        await ElMessageBox.confirm(prompt, "请确认", {
          confirmButtonText: "确认",
          cancelButtonText: "取消",
          type: "warning",
        });
        return { confirmed: true };
      } catch {
        return { confirmed: false };
      }
    },
  };
}
```

### 5. 新增：`src/components/agent/ChatWidget.vue`

```vue
<script setup lang="ts">
import { computed, ref } from "vue";
import { useRouter } from "vue-router";
import { useBagent } from "./useBagent";
import { buildActions } from "./actions";

const router = useRouter();

// sid 与业务 service 同源
const sid = computed(
  () => new URLSearchParams(window.location.search).get("sid") || ""
);
// thread_id：用 sid 的前 12 位拼当前用户标识；如果以后有 user store 再换
const threadId = computed(() => `mdm_${sid.value.slice(0, 12) || "anon"}`);
const wsBase = import.meta.env.VITE_BAGENT_WS_BASE || "ws://localhost:8080";

const open = ref(true);
const input = ref("");

const actions = buildActions({ router });
const { messages, connected, sendMessage } = useBagent({
  wsBase,
  threadId: threadId.value,
  token: sid.value,
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
  <button v-if="!open" class="agent-fab" @click="open = true" title="打开助手">
    AI
  </button>

  <aside v-else class="agent-panel">
    <header>
      供应商助手
      <span :class="{ dot: true, on: connected }" />
      <button class="x" @click="open = false">×</button>
    </header>
    <ul>
      <li v-for="(m, i) in messages" :key="i" :class="m.role">
        <pre>{{ m.text }}</pre>
      </li>
    </ul>
    <form @submit.prevent="submit">
      <input v-model="input" placeholder="例：SUP001 为什么没推到 FOL" />
      <button :disabled="!connected">发送</button>
    </form>
  </aside>
</template>

<style scoped>
.agent-fab {
  position: fixed; right: 16px; bottom: 16px; z-index: 999;
  width: 48px; height: 48px; border-radius: 50%;
  background: #2563eb; color: #fff; border: none; cursor: pointer; font-weight: 600;
  box-shadow: 0 4px 12px rgba(0,0,0,.15);
}
.agent-panel {
  position: fixed; right: 0; top: 0; bottom: 0; width: 380px; z-index: 999;
  display: flex; flex-direction: column; background: #fff;
  border-left: 1px solid #e5e7eb; box-shadow: -4px 0 12px rgba(0,0,0,.05);
}
header { padding: 10px 12px; border-bottom: 1px solid #eee; display: flex; align-items: center; gap: 8px; font-weight: 600; }
.dot { width: 8px; height: 8px; border-radius: 50%; background: #bbb; }
.dot.on { background: #16a34a; }
.x { margin-left: auto; background: none; border: none; font-size: 18px; cursor: pointer; color: #666; }
ul { flex: 1; overflow: auto; list-style: none; padding: 8px 12px; margin: 0; }
li { margin: 6px 0; }
li.user pre { background: #eef2ff; padding: 6px 10px; border-radius: 8px; align-self: flex-end; }
li.assistant pre { background: #f3f4f6; padding: 6px 10px; border-radius: 8px; }
pre { white-space: pre-wrap; margin: 0; font: inherit; }
form { display: flex; padding: 8px; border-top: 1px solid #eee; gap: 8px; }
input { flex: 1; padding: 6px 8px; border: 1px solid #d1d5db; border-radius: 6px; }
form button { padding: 6px 12px; border: none; background: #2563eb; color: #fff; border-radius: 6px; cursor: pointer; }
form button:disabled { background: #9ca3af; cursor: not-allowed; }
</style>
```

### 6. 修改：`src/layouts/AppLayout.vue`

在 `app-shell` 末尾挂上 ChatWidget。

```vue
<script setup lang="ts">
// ...原有 import...
import ChatWidget from "@/components/agent/ChatWidget.vue";
</script>

<template>
  <div class="app-shell">
    <aside class="app-sidebar"><!-- 原有 --></aside>
    <div class="app-main"><!-- 原有 --></div>
    <ChatWidget />
  </div>
</template>
```

### 7. 修改：`src/views/supplier/SupplierManagementView.vue`

watch agent intent store，自动筛选并打开 Drawer。

```ts
import { watch } from "vue";
import { useAgentIntentStore } from "@/stores/agent-intent";

const intent = useAgentIntentStore();

watch(
  () => intent.pendingSupplierDetailCode,
  async (code) => {
    if (!code) return;
    try {
      // 1. 用 supplierNumber 精确过滤；按现有 filterBar 接口调
      filterBar.value?.setFilter?.({ supplierNumber: code });
      await refresh();      // 现有的列表刷新方法
      // 2. 找到对应行，沿用现有 loadDetail
      const row = rows.value.find((r) => r.supplierNumber === code);
      if (row) await loadDetail(row.id);
      else ElMessage.warning(`未找到供应商 ${code}`);
    } finally {
      intent.clearSupplierDetail();
    }
  },
  { immediate: true }
);
```

> 上面 `filterBar.value?.setFilter` / `refresh` / `rows` / `loadDetail` 全部用现有页面里的同名变量。具体名字以现网代码为准；如果当前是 `searchForm.supplierNumber = code; handleSearch()` 之类的写法，照搬即可。

### 8. 修改：`src/views/supplier/components/SupplierFormDialog.vue`

watch prefill 意图，对话框打开时把字段塞进 form。

```ts
import { watch } from "vue";
import { useAgentIntentStore } from "@/stores/agent-intent";

const intent = useAgentIntentStore();

watch(
  () => intent.pendingSupplierFormPrefill,
  (data) => {
    if (!data) return;
    // 安全合并：只覆盖白名单字段，避免 agent 误传
    const allowed = [
      "supplierNumber", "supplierName", "supplierShortName",
      "sourceSystem", "supplierStatus", "supplierType",
      "supplierUsci", "legalRepresentative",
      "settlementCurrency", "paymentTerm", "remark",
    ];
    for (const k of allowed) {
      if (k in data) (form as any)[k] = data[k as keyof typeof data];
    }
    intent.clearSupplierFormPrefill();
  },
  { immediate: true }
);
```

> 如果对话框默认是关着的，建议在 watcher 里也把它打开（`dialogVisible.value = true`），让 agent 调 `prefill_form` 后用户立刻能看到表单。

## 验证步骤

1. **bagent 后端起来**：仓库根目录 `uv run uvicorn src.server:app --port 8080`
2. **前端起来**：`cloud-mdm-front` 里 `npm run dev`，访问 `http://localhost:5173/?sid=<真实 sid>`
3. **冒烟用例**（按顺序问）：
   - "SUP001 是什么" → 期望 agent 调 `search_suppliers` / `get_supplier_by_number`，回中文摘要
   - "打开 SUP001 的详情" → 期望页面跳到 `/vendors`，自动按编码过滤，Drawer 弹开
   - "SUP001 为什么没推到 FOL" → 期望 agent 调 `query_interface_logs(business_no="SUP001", target_system="FOL", success_flag="N")`，必要时再 `get_interface_log_detail`
   - "重新推一次 SUP001 到 FOL" → 期望先弹 ElMessageBox 确认框，确认后才真正调 `push_supplier_to_fol`
   - 高亮：找一个有 `data-testid` 的元素让 agent 高亮，验证 `highlight_element` 路径

## 排错

| 现象 | 检查点 |
|---|---|
| WebSocket 连不上 / 1006 | `VITE_BAGENT_WS_BASE` 是否正确；浏览器控制台是否提示子协议拒绝；bagent 后端是否拿到 `bearer.<sid>` |
| `open_supplier_detail` 跳页面但 Drawer 不开 | SupplierManagementView 的 watcher 是否注册成功；`rows` / `filterBar` 名字是否与现网一致；`loadDetail` 是否被调用 |
| `prefill_form` 没反应 | SupplierFormDialog 是否被挂载（关闭状态下 watch 不会触发，看是否要在 watch 里同时打开 dialog） |
| sid 拿不到 | URL 没带 `?sid=`；和业务 service 是同一来源，业务接口正常时这里也应正常 |
| agent 反复重试 / 报错"接口失败 code=xxx" | 看 bagent 日志，确认是 SRM 真返回的错（说明接口/字段对不上，要改 [bagent/src/schemas.py](../src/schemas.py) 或 [_endpoints.py](../src/tools/_endpoints.py)） |

## 后续可选增强

- 把当前路由 / 当前选中的 supplier_id 通过 `user_message` 的额外 metadata 传给 agent，让它"知道用户站在哪个页面"，回答更贴
- 给 `highlight_element` 增加白名单（只允许 `[data-agent-target]` 选择器），防止 agent 乱点
- 把 ChatWidget 拆到独立的 `@longsys/bagent-vue` npm 包里，多个前端复用
- 把 sid 从 URL 改成走 cookie / pinia 后，`useBagent` 调用处统一改一行即可
