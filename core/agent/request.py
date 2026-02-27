import json
import logging
import socket
import time
import requests
from typing import List, Dict, Optional, Iterator

logger = logging.getLogger(__name__)


def chat_complete(
    base_url: str,
    api_key: str,
    model: str,
    system: Optional[str],
    history: List[Dict[str, str]],
    question: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None
) -> Iterator[str]:
    """
    流式调用 OpenAI 兼容 API
    :param base_url: API 基础地址
    :param api_key: API 密钥
    :param model: 模型名称
    :param system: 系统提示词
    :param history: 历史消息列表
    :param question: 用户问题
    :param temperature: 温度参数
    :param max_tokens: 最大 token 数
    :return: 逐块返回文本的迭代器
    """
    url = base_url.rstrip("/") + "/chat/completions"
    messages: List[Dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.extend(history)
    if question:
        messages.append({"role": "user", "content": question})

    payload = {"model": model, "messages": messages, "stream": True}
    if temperature is not None:
        payload["temperature"] = temperature
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        "Accept-Encoding": "identity",
        "Cache-Control": "no-cache"
    }

    # 重试逻辑：覆盖网络异常和可重试的 HTTP 状态码
    max_retries = 3
    resp = None
    last_error = None
    _RETRYABLE_STATUS = {429, 500, 502, 503, 504}

    for attempt in range(max_retries + 1):
        try:
            resp = requests.post(
                url, json=payload, headers=headers,
                stream=True, timeout=(15, 180)
            )
            # 可重试的 HTTP 状态码
            if resp.status_code in _RETRYABLE_STATUS and attempt < max_retries:
                wait = min(2 ** attempt, 10)
                logger.warning(f"HTTP {resp.status_code}, 第 {attempt+1} 次重试, 等待 {wait}s")
                resp.close()
                resp = None
                time.sleep(wait)
                continue
            break
        except requests.exceptions.Timeout as e:
            last_error = f"请求超时: {e}"
        except requests.exceptions.ConnectionError as e:
            # 包含 SSLError、ProxyError 等子类
            last_error = f"连接失败: {e}"
        except requests.exceptions.RequestException as e:
            # 包含 ChunkedEncodingError 等其他子类
            last_error = f"请求异常: {e}"
        except OSError as e:
            last_error = f"系统网络错误: {e}"

        if attempt < max_retries:
            wait = min(2 ** attempt, 10)
            logger.warning(f"{last_error}, 第 {attempt+1} 次重试, 等待 {wait}s")
            time.sleep(wait)
        else:
            raise RuntimeError(f"{last_error} (已重试 {max_retries} 次)")

    if resp is None:
        raise RuntimeError(f"请求失败: {last_error or '无法建立连接'}")

    # TCP_NODELAY 优化
    try:
        sock = resp.raw._fp.fp.raw._sock
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    except Exception:
        pass  # 非关键优化，静默忽略

    if resp.status_code != 200:
        try:
            error = resp.json()
            msg = error.get("error", {}).get("message", str(error))
        except (json.JSONDecodeError, ValueError):
            msg = resp.text[:500] if resp.text else f"HTTP {resp.status_code}"
        except Exception:
            msg = f"HTTP {resp.status_code} (响应解析失败)"
        resp.close()
        raise RuntimeError(f"API 错误 ({resp.status_code}): {msg}")

    resp.raw.decode_content = False

    try:
        yield from _parse_sse_stream(resp)
    finally:
        resp.close()


def _parse_sse_stream(resp) -> Iterator[str]:
    """解析 SSE 流，使用缓冲读取提升性能，增强异常容错"""
    buffer = b""
    consecutive_errors = 0
    max_consecutive_errors = 5

    while True:
        try:
            chunk = resp.raw.read(4096)
        except requests.exceptions.ChunkedEncodingError as e:
            logger.warning(f"SSE 流传输中断: {e}")
            break
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"SSE 流连接断开: {e}")
            break
        except OSError as e:
            logger.warning(f"SSE 流读取系统错误: {e}")
            break
        except Exception as e:
            logger.warning(f"SSE 流读取未知错误: {type(e).__name__}: {e}")
            break

        if not chunk:
            break

        consecutive_errors = 0  # 成功读取，重置错误计数
        buffer += chunk

        while b"\n" in buffer:
            line, buffer = buffer.split(b"\n", 1)
            line = line.strip(b"\r")
            if not line:
                continue
            if not line.startswith(b"data:"):
                continue
            data = line[5:].strip()
            if data == b"[DONE]":
                return
            try:
                data_text = data.decode("utf-8", errors="replace")
            except Exception as e:
                logger.warning(f"SSE 流解码失败 (忽略此块): {e}")
                continue
            try:
                obj = json.loads(data_text)
            except (json.JSONDecodeError, ValueError) as e:
                consecutive_errors += 1
                if consecutive_errors >= max_consecutive_errors:
                    logger.error(f"SSE JSON 连续解析失败 {consecutive_errors} 次，终止流")
                    return
                logger.debug(f"SSE JSON解析失败 (忽略): {e}")
                continue
            consecutive_errors = 0
            choices = obj.get("choices") or []
            if not choices:
                continue
            delta = choices[0].get("delta") or {}
            content = delta.get("content")
            if content:
                yield content
