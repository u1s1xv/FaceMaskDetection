"""
视频源模块验证 —— 无需 HTTP 服务，直接测 CameraSource 与 FrameSlot。

为什么单独成一个脚本：
  摄像头和实时性都是"跑起来才知道对不对"的东西，靠肉眼看不出来。
  这里把关键语义固化成断言，改代码后一条命令就能回归。

用法：
    python server/tools/test_camera.py          # 只用虚拟摄像头（视频文件）
    python server/tools/test_camera.py --device 0   # 额外测真实摄像头

退出码 0 = 全部通过。
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "server"))

import camera  # noqa: E402

VIDEO = ROOT / "data" / "test_video" / "mask_demo.mp4"

PASS, FAIL = [], []


def check(name, ok, detail=""):
    (PASS if ok else FAIL).append(name)
    print("  %s  %s%s" % ("[OK]  " if ok else "[FAIL]", name, ("  " + detail) if detail else ""))


def ensure_video():
    if VIDEO.exists():
        return True
    print("  测试视频不存在，正在生成…")
    rc = subprocess.call([sys.executable, str(ROOT / "server" / "tools" / "make_test_video.py")])
    return rc == 0 and VIDEO.exists()


def wait_first_frame(cam, timeout=8.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        seq, frame, ts = cam.read_latest()
        if frame is not None:
            return frame, time.time() - (deadline - timeout)
        time.sleep(0.005)
    return None, timeout


def test_frame_slot():
    print("=== FrameSlot 语义 ===")
    slot = camera.FrameSlot()

    check("空槽位返回 None", slot.get()[1] is None)

    slot.put("A")
    check("首次写入可读到", slot.get()[1] == "A")
    check("无新帧时返回 None（不重复消费）", slot.get()[1] is None)

    slot.put("B")
    slot.put("C")
    seq, data, _ = slot.get()
    check("latest-frame-wins：读到最新的 C 而不是 B", data == "C", "读到 %s" % data)
    check("被覆盖的帧计入 dropped", slot.dropped == 1, "dropped=%d" % slot.dropped)

    check("peek 不消费", (slot.put("D"), slot.peek()[1] == "D", slot.get()[1] == "D")[1:3] == (True, True))


def test_video_source():
    print()
    print("=== 虚拟摄像头（视频文件）===")
    cam = camera.CameraSource(str(VIDEO), width=640, height=480)
    cam.start()
    frame, elapsed = wait_first_frame(cam)
    if frame is None:
        check("能取到首帧", False)
        cam.stop()
        return
    st = cam.stats()
    check("能取到首帧", True, "%.0f ms" % (elapsed * 1000))
    check("走 FFMPEG 后端（不是摄像头后端）", st["backend"] == "FFMPEG", st["backend"] or "?")
    check("分辨率正确", (frame.shape[1], frame.shape[0]) == (640, 480),
          "%dx%d" % (frame.shape[1], frame.shape[0]))
    check("识别出源帧率", abs(st["source_fps"] - 30.0) < 1.0, "%.1f" % st["source_fps"])

    # 采集节流：文件源应按源帧率放帧，而不是全速解码
    t = time.time()
    consumed = 0
    while time.time() - t < 4.0:
        if cam.read_latest()[1] is not None:
            consumed += 1
        time.sleep(0.001)
    st = cam.stats()
    cam.stop()
    check("按源帧率节流（≈30 FPS）", 24 <= st["fps"] <= 36, "%.1f FPS" % st["fps"])
    check("消费次数≈采集帧数（不重复推理同一帧）",
          consumed <= st["frames"] * 1.2, "消费 %d / 采集 %d" % (consumed, st["frames"]))


def test_slow_consumer():
    print()
    print("=== 慢消费者：帧应被覆盖而非排队 ===")
    cam = camera.CameraSource(str(VIDEO), width=640, height=480)
    cam.start()
    wait_first_frame(cam)
    t = time.time()
    n = 0
    while time.time() - t < 3.0:
        if cam.read_latest()[1] is not None:
            n += 1
        time.sleep(0.1)          # 模拟推理跟不上采集
    st = cam.stats()
    cam.stop()
    check("丢弃数显著大于 0（说明没在排队）",
          st["dropped"] > st["frames"] * 0.5,
          "采集 %d / 消费 %d / 丢弃 %d" % (st["frames"], n, st["dropped"]))


def test_invalid_source():
    print()
    print("=== 无效源应优雅失败 ===")
    cam = camera.CameraSource(99, width=640, height=480)
    cam.start()
    time.sleep(1.5)
    st = cam.stats()
    cam.stop()
    check("无效源不崩溃且无帧", st["frames"] == 0)
    check("记录了错误原因", bool(st["last_error"]), st["last_error"][:40])


def test_device(index):
    print()
    print("=== 真实摄像头（序号 %s）===" % index)
    cam = camera.CameraSource(str(index), width=640, height=480)
    cam.start()
    frame, _ = wait_first_frame(cam)
    if frame is None:
        check("真实摄像头可用", False, "取不到帧")
        cam.stop()
        return
    t = time.time()
    while time.time() - t < 4.0:
        cam.read_latest()
        time.sleep(0.001)
    st = cam.stats()
    cam.stop()
    check("真实摄像头可用", True, "后端 %s" % st["backend"])
    check("帧率合理（>=15 FPS）", st["fps"] >= 15, "%.1f FPS" % st["fps"])


def main():
    parser = argparse.ArgumentParser(description="视频源模块验证")
    parser.add_argument("--device", default=None,
                        help="额外测试的真实摄像头序号；不给则跳过")
    args = parser.parse_args()

    test_frame_slot()

    if not ensure_video():
        print("  [FAIL] 无法准备测试视频，跳过后续")
        return 1
    test_video_source()
    test_slow_consumer()
    test_invalid_source()

    if args.device is not None:
        test_device(args.device)

    print()
    print("通过 %d 项，失败 %d 项" % (len(PASS), len(FAIL)))
    for name in FAIL:
        print("  失败: %s" % name)
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
