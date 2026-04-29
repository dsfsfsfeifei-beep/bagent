"""HTTP 适配层。

约定：
- SRM 接口走 url 传 sid 鉴权（来自用户 token），其它鉴权方式以后再加。
- 失败统一转 RuntimeError，让 LangGraph 把错误信息回传给 LLM 处理。
- 业务层只看 RespMsg.data；code != "0" 当成失败。
"""
from typing import Any

import httpx

from ..settings import settings


class ApiError(RuntimeError):
    pass


def _unwrap(resp_json: dict, *, path: str) -> Any:
    """统一处理 RespMsg{code,msg,data}。"""
    if not isinstance(resp_json, dict):
        raise ApiError(f"{path} returned non-object response")
    code = str(resp_json.get("code"))
    if code != "0":
        raise ApiError(f"{path} failed: code={code} msg={resp_json.get('msg')}")
    return resp_json.get("data")


def _params_with_sid(sid: str, extra: dict | None = None) -> dict:
    p = {"sid": sid}
    if extra:
        p.update(extra)
    return p


def srm_post(path: str, sid: str, body: dict | None = None, params: dict | None = None) -> Any:
    url = f"{settings.srm_base_url.rstrip('/')}{path}"
    r = httpx.post(
        url,
        params=_params_with_sid(sid, params),
        json=body or {},
        timeout=settings.http_timeout,
    )
    r.raise_for_status()
    return _unwrap(r.json(), path=path)


def srm_get(path: str, sid: str, params: dict | None = None) -> Any:
    url = f"{settings.srm_base_url.rstrip('/')}{path}"
    r = httpx.get(
        url,
        params=_params_with_sid(sid, params),
        timeout=settings.http_timeout,
    )
    r.raise_for_status()
    return _unwrap(r.json(), path=path)
