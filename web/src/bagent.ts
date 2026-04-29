/**
 * bagent 前端 SDK（Vue 3）
 *
 * - 通过 WebSocket 连后端 /ws/{threadId}，token 走 Sec-WebSocket-Protocol（bearer.<token>）。
 * - 注册一组 UI action handler，agent 调用 UI tool 时这边会被触发。
 * - 暴露 sendMessage(text) / messages 给聊天组件用。
 */
import { ref, onUnmounted, type Ref } from "vue";

export type ActionHandler = (args: any) => any | Promise<any>;
export type ActionRegistry = Record<string, ActionHandler>;

export interface ChatMessage {
  role: "user" | "assistant";
  text: string;
}

export interface UseBagentOptions {
  wsBase: string;            // e.g. "ws://localhost:8080"
  threadId: string;          // 同一用户同一会话用稳定 id（一个 tab 一个）
  token: string;             // 用户 token，走子协议传递
  actions: ActionRegistry;
}

export function useBagent(opts: UseBagentOptions) {
  const messages: Ref<ChatMessage[]> = ref([]);
  const connected = ref(false);
  let ws: WebSocket | null = null;
  let stopped = false;
  let retry = 0;

  function connect() {
    const url = `${opts.wsBase.replace(/\/$/, "")}/ws/${encodeURIComponent(opts.threadId)}`;
    // 子协议必须是合法 token（无空格、不带 ":"），bearer.<token> 直接给 token 用
    ws = new WebSocket(url, [`bearer.${opts.token}`]);

    ws.onopen = () => {
      connected.value = true;
      retry = 0;
    };

    ws.onclose = () => {
      connected.value = false;
      if (!stopped) {
        retry = Math.min(retry + 1, 6);
        setTimeout(connect, 500 * 2 ** retry);  // 指数退避，最长约 32s
      }
    };

    ws.onerror = () => { /* onclose 会跟着触发，重连逻辑统一在那 */ };

    ws.onmessage = async (ev) => {
      const msg = JSON.parse(ev.data);
      switch (msg.type) {
        case "assistant_message":
          messages.value.push({ role: "assistant", text: msg.text });
          break;
        case "action": {
          const handler = opts.actions[msg.name];
          let payload: any;
          if (!handler) {
            payload = { type: "action_result", id: msg.id, ok: false, error: `no handler for ${msg.name}` };
          } else {
            try {
              const data = await handler(msg.args);
              payload = { type: "action_result", id: msg.id, ok: true, data: data ?? {} };
            } catch (e: any) {
              payload = { type: "action_result", id: msg.id, ok: false, error: String(e?.message ?? e) };
            }
          }
          ws?.send(JSON.stringify(payload));
          break;
        }
        case "pong":
          break;
        default:
          console.warn("unknown server message", msg);
      }
    };
  }

  function sendMessage(text: string) {
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    messages.value.push({ role: "user", text });
    ws.send(JSON.stringify({ type: "user_message", text }));
  }

  connect();

  onUnmounted(() => {
    stopped = true;
    ws?.close();
  });

  return { messages, connected, sendMessage };
}
