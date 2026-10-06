"""
大模型分析客户端 —— 从 django_frontend/api_views.py 的 LLM 部分移植。

相对原版的改动：
  1. API Key 不再硬编码（原 api_views.py:24 写了真实 sk- 密钥并随代码入库），
     改为从环境变量 SILICONFLOW_API_KEY 读取。
  2. 没有配置 Key 时进入 mock 模式，产出确定性的流式文本，
     这样客户端和流式解析逻辑在没有密钥的环境下也能开发和自测。
  3. 用生成器逐块吐出，交由 HTTP 层封装成 SSE。
"""

import json
import logging
import os
import time

logger = logging.getLogger(__name__)

SILICONFLOW_BASE_URL = os.environ.get(
    "SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1/chat/completions")

# 模型白名单：只允许调用这几个，避免任意模型名透传给上游
AVAILABLE_MODELS = [
    "Qwen/QwQ-32B",
    "Qwen/Qwen2.5-7B-Instruct",
    "Qwen/Qwen2.5-14B-Instruct",
    "deepseek-ai/DeepSeek-V2.5",
]
DEFAULT_MODEL = "Qwen/QwQ-32B"

SYSTEM_PROMPT = "你是一个口罩佩戴合规性分析助手。请基于给定的检测统计数据给出简洁、专业的中文分析报告。"


def api_key_configured():
    return bool(os.environ.get("SILICONFLOW_API_KEY"))


def build_context(record, prompt):
    """把一条检测记录拼成给大模型的中文上下文。"""
    counts = record.get("counts") or {}
    lines = [
        f"文件名：{record.get('file_name', '未知')}",
        f"图像尺寸：{record.get('image_width', 0)}×{record.get('image_height', 0)}",
        f"检测目标总数：{record.get('total_detections', 0)}",
        f"正确佩戴口罩：{record.get('with_mask_count', 0)}",
        f"未佩戴口罩：{record.get('without_mask_count', 0)}",
        f"佩戴不规范：{record.get('incorrect_mask_count', 0)}",
        f"推理耗时：{record.get('processing_time', 0):.3f} 秒",
    ]
    if counts:
        lines.append("按类别统计：" + json.dumps(counts, ensure_ascii=False))
    lines.append("")
    lines.append("用户要求：" + (prompt or "请分析本次检测结果并给出改进建议。"))
    return "\n".join(lines)


def _mock_stream(prompt, record):
    """无密钥时的确定性输出，用于跑通客户端流式解析。"""
    total = record.get("total_detections", 0)
    without = record.get("without_mask_count", 0)
    incorrect = record.get("incorrect_mask_count", 0)
    with_mask = record.get("with_mask_count", 0)

    compliance = (with_mask / total * 100.0) if total else 0.0
    if without == 0 and incorrect == 0:
        level = "合规"
    elif without == 0:
        level = "基本合规，存在佩戴不规范"
    else:
        level = "不合规"

    text = (
        "【模拟分析模式】当前未配置 SILICONFLOW_API_KEY，以下为本地生成的示例报告。\n\n"
        f"一、总体结论\n本次共检出 {total} 个目标，其中正确佩戴 {with_mask} 个、"
        f"未佩戴 {without} 个、佩戴不规范 {incorrect} 个，合规率 {compliance:.1f}%。"
        f"综合判定为：{level}。\n\n"
        "二、风险提示\n"
    )
    if without > 0:
        text += f"- 存在 {without} 个未佩戴口罩目标，属于高风险项，建议立即纠正。\n"
    if incorrect > 0:
        text += f"- 存在 {incorrect} 个佩戴不规范目标，建议现场复查佩戴方式。\n"
    if without == 0 and incorrect == 0:
        text += "- 未发现违规项，现场管理良好。\n"
    text += "\n三、改进建议\n"
    text += "1. 对未佩戴人员开展现场提醒并记录。\n"
    text += "2. 定期复核门禁与作业区域的视频抽查频次。\n"
    text += "3. 如需真实大模型分析，请配置环境变量 SILICONFLOW_API_KEY 后重启服务。\n"

    # 按小片段吐出，模拟真实流式响应的节奏
    for i in range(0, len(text), 12):
        yield text[i:i + 12]
        time.sleep(0.01)


def stream_analysis(record, prompt, model):
    """生成器：逐块产出文本片段。"""
    if model not in AVAILABLE_MODELS:
        raise ValueError(f"模型不在白名单内: {model}")

    key = os.environ.get("SILICONFLOW_API_KEY")
    if not key:
        logger.info("未配置 API Key，进入模拟分析模式")
        yield from _mock_stream(prompt, record)
        return

    import requests  # 仅在真正调用时导入，避免无密钥环境缺包

    context = build_context(record, prompt)
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": context},
        ],
        "max_tokens": 4000,
        "temperature": 0.7,
        "stream": True,
    }
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    with requests.post(SILICONFLOW_BASE_URL, json=payload, headers=headers,
                       stream=True, timeout=120) as resp:
        resp.raise_for_status()
        for raw in resp.iter_lines(decode_unicode=True):
            if not raw or not raw.startswith("data:"):
                continue
            data = raw[5:].strip()
            if data == "[DONE]":
                break
            try:
                chunk = json.loads(data)
            except ValueError:
                continue
            choices = chunk.get("choices") or []
            if not choices:
                continue
            delta = choices[0].get("delta") or {}
            piece = delta.get("content")
            if piece:
                yield piece
