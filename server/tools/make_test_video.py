"""
从已爬取的口罩图片合成一段测试视频，用作"虚拟摄像头"。

为什么需要它：
  1. 自动化验证不能依赖真实摄像头 —— 换台机器就跑不了，也没法在 CI 里跑
  2. 演示时不必真对着摄像头
  3. 视频内容可复现，便于对比不同版本的行为

输出到 data/test_video/（该目录已 gitignore，需要时重新生成即可）。

用法：
    python server/tools/make_test_video.py [--out 路径] [--seconds 30]
"""

import argparse
import os
import sys
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parent.parent.parent
IMAGES_DIR = ROOT / "yoloserver" / "data" / "crawled" / "images"
DEFAULT_OUT = ROOT / "data" / "test_video" / "mask_demo.mp4"

WIDTH, HEIGHT, FPS = 640, 480, 30


def collect_images(limit=60):
    """挑图片源。优先小的，避免合成时反复缩放超大图。"""
    if not IMAGES_DIR.is_dir():
        raise SystemExit("找不到图片目录: %s" % IMAGES_DIR)
    files = [p for p in IMAGES_DIR.iterdir()
             if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp")]
    files.sort(key=lambda p: p.stat().st_size)
    if not files:
        raise SystemExit("图片目录里没有可用图片: %s" % IMAGES_DIR)
    return files[:limit]


def letterbox(image, width, height):
    """等比缩放 + 补边，避免把图片拉变形（变形会让检测效果失真）。"""
    h, w = image.shape[:2]
    scale = min(width / w, height / h)
    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
    resized = cv2.resize(image, (nw, nh), interpolation=cv2.INTER_AREA)
    canvas = cv2.copyMakeBorder(
        resized,
        (height - nh) // 2, height - nh - (height - nh) // 2,
        (width - nw) // 2, width - nw - (width - nw) // 2,
        cv2.BORDER_CONSTANT, value=(32, 32, 32),
    )
    return canvas


def main():
    parser = argparse.ArgumentParser(description="合成测试视频")
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--seconds", type=float, default=30.0)
    parser.add_argument("--loop-images", action="store_true", default=True)
    args = parser.parse_args()

    files = collect_images()
    total_frames = int(args.seconds * FPS)
    per_image = max(1, total_frames // len(files))
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    writer = cv2.VideoWriter(str(out_path), cv2.VideoWriter_fourcc(*"mp4v"),
                             FPS, (WIDTH, HEIGHT))
    if not writer.isOpened():
        raise SystemExit("无法创建视频写入器，检查 OpenCV 的 mp4v 支持")

    written = 0
    for path in files:
        img = cv2.imread(str(path))
        if img is None:
            continue
        frame = letterbox(img, WIDTH, HEIGHT)
        # 叠一行很小的来源标注，方便在视频里分辨当前是第几张图
        cv2.putText(frame, path.name[:44], (8, HEIGHT - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (180, 180, 180), 1, cv2.LINE_AA)
        for _ in range(per_image):
            writer.write(frame)
            written += 1
            if written >= total_frames:
                break
        if written >= total_frames:
            break

    writer.release()
    size_mb = out_path.stat().st_size / 1024 / 1024
    print("已生成: %s" % out_path)
    print("  %d 帧 / %.1f 秒 / %dx%d @ %d FPS / %.2f MB"
          % (written, written / FPS, WIDTH, HEIGHT, FPS, size_mb))
    print("  用了 %d 张源图，每张 %d 帧" % (len(files), per_image))


if __name__ == "__main__":
    sys.exit(main())
