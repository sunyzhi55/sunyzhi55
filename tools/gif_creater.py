"""
gif_creater.py
简要说明:
    基于一张图片生成带淡紫色神秘滤镜、微放大（zoom）与呼吸光晕文字效果的 GIF，
    适合用于 GitHub 主页展示封面或 README 插图。

用法:
    1. 将目标图片放在脚本同目录，或修改 `IMAGE_PATH` 为图片路径。
    2. 确认 `FONT_PATH` 指向系统中的可用字体（Windows: C:\\Windows\\Fonts\\）
    3. 需要安装依赖: `moviepy`, `imageio`, `numpy`，以及系统层面的 ImageMagick（用于 TextClip 渲染）
    4. 运行: `python gif_creater.py`，输出默认为 `volcano.gif`，可修改 `OUTPUT_NAME`。

参数可调项:
    - `FONT_SIZE`, `GLOW_COLOR`, `RESIZE_WIDTH`, `DURATION`, `FPS` 等在文件顶部配置区域。

注意:
    - 如果出现 ImageMagick 或字体错误，请安装 ImageMagick 并确认 `FONT_PATH` 有权限访问。
    - 本脚本用 `TextClip(method='caption')` 渲染单行文字框以避免字母下部被裁切。
"""

import numpy as np
import os
# 导入必要的类
from moviepy import ImageClip, TextClip, CompositeVideoClip, vfx

# ================= 配置区域 (请仔细检查) =================
IMAGE_PATH = "volcano.png"
OUTPUT_NAME = "volcano.gif"

# 三行文案（按需求展示在图片中央）
TEXT_LINES = [
    "Chaos is not the end",
    "It is the beginning of creation",
    "Stay curious. Stay explosive.",
]

# 【再次确认】字体路径
# 务必确认这个文件存在，否则会报 ImageMagick 错误
FONT_PATH = r"C:\Windows\Fonts\arial.ttf"
if not os.path.exists(FONT_PATH):
    # 尝试回退到普通 Arial
    FONT_PATH = r"C:\Windows\Fonts\arial.ttf"

FONT_SIZE = 56
TEXT_COLOR = "#FFFFFF"
GLOW_COLOR = "#9D00FF"
STROKE_WIDTH = 4

DURATION = 5.0
FPS = 15
RESIZE_WIDTH = 800


# =======================================================

def create_advanced_gif():
    print("1. 正在处理背景 (Zoom + 淡紫神秘滤镜)...")

    # --- 1. 背景处理 ---
    # 加载图片
    img_raw = ImageClip(IMAGE_PATH).with_duration(DURATION)

    # 先调整到目标宽度 (基准大小)
    img_base = img_raw.resized(width=RESIZE_WIDTH)

    # 记录基准尺寸，用于最后裁剪
    base_w, base_h = img_base.size

    # 【修复 Zoom】使用 lambda 函数实现动态放大
    # t 是当前时间，1 + 0.02*t 表示每秒放大 2%
    # 这会使图片实际尺寸变大，我们稍后通过 CompositeVideoClip 裁剪
    clip_bg_zoom = img_base.resized(lambda t: 1 + 0.02 * t)

    # 添加暗角 + 淡紫神秘滤镜
    def add_mystic_filter(image):
        # image: uint8, shape (h, w, c)
        h, w = image.shape[:2]
        channels = image.shape[2] if image.ndim == 3 else 1
        rgb = image[:, :, :3].astype(np.float32)

        # 1) 轻微调色：压一点绿色、抬蓝/红，整体偏淡紫
        rgb[:, :, 0] *= 1.05  # R
        rgb[:, :, 1] *= 0.92  # G
        rgb[:, :, 2] *= 1.15  # B
        rgb += np.array([10.0, 0.0, 18.0], dtype=np.float32)  # 紫色偏移

        # 2) 轻微对比度与 gamma（营造神秘感但不发黑）
        rgb = (rgb - 128.0) * 1.06 + 128.0
        rgb = np.clip(rgb, 0, 255)
        rgb = np.power(rgb / 255.0, 0.97) * 255.0

        # 3) 暗角 (Vignette)
        Y, X = np.ogrid[:h, :w]
        center_y, center_x = h / 2.0, w / 2.0
        max_dist = np.sqrt(center_x ** 2 + center_y ** 2)
        dist = np.sqrt((X - center_x) ** 2 + (Y - center_y) ** 2)
        mask = 1.0 - (dist / max_dist) ** 1.55
        mask = np.clip(mask, 0.0, 1.0)
        rgb = rgb * (mask[..., np.newaxis] * 0.88 + 0.12)

        out = image.copy()
        out[:, :, :3] = np.clip(rgb, 0, 255).astype(np.uint8)
        if channels == 4:
            out[:, :, 3] = image[:, :, 3]
        return out

    clip_bg_final = clip_bg_zoom.image_transform(add_mystic_filter)

    print("2. 正在生成居中文字 (带光晕与呼吸)...")

    # --- 2. 文字处理 ---
    # 定义呼吸函数：根据时间 t 返回透明度系数 (0.0 ~ 1.0)
    def get_pulse_alpha(t):
        # 正弦波呼吸：0.4 到 0.9 之间变化
        return 0.4 + 0.25 * (1 + np.sin(2 * np.pi * t / 2.5))

    # 生成逐行文字，整体在画面正中
    # 关键：使用 method='caption' + 固定行高，避免 'y' 等下伸部被裁切
    center_y = base_h / 2
    text_box_w = int(base_w * 0.92)
    line_box_h = int(FONT_SIZE * 1.75) + STROKE_WIDTH * 2 + 8
    line_gap = 10

    def make_line(text, color, stroke_color=None, stroke_width=0):
        return (TextClip(
            text=text,
            font_size=FONT_SIZE,
            font=FONT_PATH,
            color=color,
            stroke_color=stroke_color,
            stroke_width=stroke_width,
            method='caption',
            size=(text_box_w, line_box_h),
            text_align='center',
            horizontal_align='center',
            vertical_align='center',
        ).with_duration(DURATION))

    glow_lines = [
        make_line(line, GLOW_COLOR, stroke_color=GLOW_COLOR, stroke_width=STROKE_WIDTH)
        for line in TEXT_LINES
    ]
    main_lines = [make_line(line, TEXT_COLOR) for line in TEXT_LINES]

    # 统一按固定行高布局（caption 文字框高度一致，更稳）
    total_h = line_box_h * len(main_lines) + line_gap * (len(main_lines) - 1)
    start_y = center_y - total_h / 2

    txt_glow_clips = []
    txt_main_clips = []
    y = start_y
    for glow, main in zip(glow_lines, main_lines):
        txt_glow_clips.append(glow.with_position(('center', y)))
        txt_main_clips.append(main.with_position(('center', y)))
        y += line_box_h + line_gap

    # 【呼吸】对所有 glow 的 mask 做时间变化
    for i, g in enumerate(txt_glow_clips):
        if g.mask is not None:
            txt_glow_clips[i].mask = g.mask.transform(
                lambda get_frame, t: get_frame(t) * get_pulse_alpha(t)
            )

    # 让主体文字稍微淡入
    # 如果 vfx.CrossFadeIn 存在则用，不存在手动做
    try:
        txt_main_clips = [c.with_effects([vfx.CrossFadeIn(1.0)]) for c in txt_main_clips]
        txt_glow_clips = [c.with_effects([vfx.CrossFadeIn(1.0)]) for c in txt_glow_clips]
    except AttributeError:
        print("警告: CrossFadeIn 未找到，跳过淡入效果")

    print("3. 正在合成...")
    # --- 3. 合成 ---
    # 【关键】设置 size=img_base.size 强制裁剪
    # 因为背景图在不断变大，如果不固定 size，GIF 尺寸会乱动
    final_clip = CompositeVideoClip(
        [clip_bg_final.with_position("center"), *txt_glow_clips, *txt_main_clips],
        size=(base_w, base_h)
    )

    # --- 4. 导出 ---
    final_clip.write_gif(OUTPUT_NAME, fps=FPS)
    print(f"\n完成！已生成: {OUTPUT_NAME}")


if __name__ == "__main__":
    try:
        create_advanced_gif()
    except Exception as e:
        import traceback

        traceback.print_exc()
        print("\n=== 常见错误指引 ===")
        print("1. OSError: ... convert ... -> 请安装 ImageMagick")
        print("2. 字体相关错误 -> 再次检查 FONT_PATH 是否有效")