/**
 * 默认 UI action 实现。把这个对象传给 useBagent({ actions })。
 *
 * 每个 handler 的输入是后端 UI tool 传来的 args，输出是 ack 数据（可空）。
 * 抛异常会变成 ok:false 的 action_result，agent 那边能看到错误原因。
 */
import type { Router } from "vue-router";

export interface ConfirmDialog {
  open(prompt: string): Promise<boolean>;  // 由你自己的弹窗组件实现
}

export interface FormBus {
  prefill(formId: string, data: Record<string, unknown>): void;
}

export function buildActions(deps: {
  router: Router;
  confirm: ConfirmDialog;
  forms: FormBus;
  supplierDetailPath?: (code: string) => string;
}) {
  const supplierPath = deps.supplierDetailPath ?? ((code) => `/suppliers/${encodeURIComponent(code)}`);

  return {
    navigate_to: ({ path }: { path: string }) => {
      deps.router.push(path);
    },

    open_supplier_detail: ({ code }: { code: string }) => {
      deps.router.push(supplierPath(code));
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
      deps.forms.prefill(form_id, data);
    },

    confirm_with_user: async ({ prompt }: { prompt: string }) => {
      const confirmed = await deps.confirm.open(prompt);
      return { confirmed };
    },
  };
}
