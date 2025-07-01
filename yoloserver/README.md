# YOLOServer - 口罩检测服务端

## 项目简介

YOLOServer是一个基于YOLO（You Only Look Once）深度学习模型的口罩检测服务端项目。该项目专注于检测图像或视频中的人员是否正确佩戴口罩，支持三种检测类别：

- **正确戴口罩** (with_mask)
- **未戴口罩** (without_mask)  
- **错误戴口罩** (mask_weared_incorrect)

## 功能特性

### 🎯 核心功能
- **模型训练**: 支持自定义数据集训练YOLO模型
- **模型验证**: 提供完整的模型性能评估功能
- **实时推理**: 支持图像、视频、摄像头实时检测
- **结果美化**: 支持中文标签和圆角边框的美化显示
- **批量处理**: 支持批量图像和视频处理

### 🛠️ 技术特性
- 基于Ultralytics YOLO框架
- 支持GPU/CPU自动切换
- 完整的日志记录系统
- 灵活的配置管理（YAML + 命令行）
- 多种数据格式转换（COCO、Pascal VOC）
- 性能监控和设备信息记录

## 项目结构

```
yoloserver/
├── configs/                    # 配置文件目录
│   ├── data.yaml              # 数据集配置
│   └── train.yaml             # 训练配置
├── data/                      # 数据目录
│   ├── train/                 # 训练数据
│   ├── val/                   # 验证数据
│   ├── test/                  # 测试数据
│   ├── raw/                   # 原始数据
│   └── crawled/               # 爬虫数据
├── models/                    # 模型目录
│   ├── checkpoints/           # 训练好的模型
│   └── pretrained/            # 预训练模型
├── runs/                      # 运行结果
│   ├── train/                 # 训练结果
│   ├── val/                   # 验证结果
│   └── detect/                # 检测结果
├── logs/                      # 日志文件
├── scripts/                   # 核心脚本
│   ├── yolo_train.py          # 模型训练
│   ├── yolo_val.py            # 模型验证
│   ├── yolo_infer.py          # 模型推理
│   └── yolo_trans.py          # 数据转换
├── utils/                     # 工具模块
│   ├── paths.py               # 路径配置
│   ├── config_utils.py        # 配置管理
│   ├── data_utils.py          # 数据处理
│   ├── logging_utils.py       # 日志管理
│   ├── beautify.py            # 结果美化
│   └── data_converters/       # 数据格式转换
└── initialize_project.py      # 项目初始化
```

## 快速开始

### 1. 环境准备

```bash
# 创建虚拟环境
conda create -n FMD python=3.8+
conda activate FMD

# 安装依赖
pip install ultralytics opencv-python pillow pyyaml
```

### 2. 项目初始化

```bash
# 初始化项目结构
python initialize_project.py
```

### 3. 数据准备

将原始数据放置到相应目录：
- 原始图像: `data/raw/images/`
- 原始标注: `data/raw/original_annotations/`
- 爬虫数据: `data/crawled/`

### 4. 数据转换

```bash
# 转换COCO格式数据
python scripts/yolo_trans.py --format coco --input data/raw/original_annotations/

# 转换Pascal VOC格式数据
python scripts/yolo_trans.py --format pascal_voc --input data/raw/original_annotations/
```

## 使用指南

### 模型训练

```bash
# 基础训练
python scripts/yolo_train.py --data data.yaml --epochs 200 --batch 16

# 使用预训练模型
python scripts/yolo_train.py --weights yolo11n-seg.pt --data data.yaml --epochs 200

# 使用YAML配置文件
python scripts/yolo_train.py --use_yaml True
```

### 模型验证

```bash
# 验证训练好的模型
python scripts/yolo_val.py --weights best.pt --data data.yaml

# 在测试集上验证
python scripts/yolo_val.py --weights best.pt --split test
```

### 模型推理

```bash
# 图像推理
python scripts/yolo_infer.py --weights best.pt --source image.jpg

# 视频推理
python scripts/yolo_infer.py --weights best.pt --source video.mp4

# 摄像头实时推理
python scripts/yolo_infer.py --weights best.pt --source 0

# 批量推理
python scripts/yolo_infer.py --weights best.pt --source images_folder/
```

## 配置说明

### 数据配置 (data.yaml)

```yaml
path: /path/to/dataset
train: train/images
val: val/images  
test: test/images
nc: 3
names: [mask_weared_incorrect, with_mask, without_mask]
```

### 训练配置 (train.yaml)

主要参数：
- `epochs`: 训练轮数 (默认: 200)
- `batch`: 批次大小 (默认: 16)
- `imgsz`: 图像尺寸 (默认: 640)
- `device`: 设备选择 (默认: 自动检测)
- `patience`: 早停耐心值 (默认: 20)

## 工具模块

### 路径管理 (paths.py)
统一管理项目中所有路径配置，包括数据目录、模型目录、日志目录等。

### 配置管理 (config_utils.py)
- 支持YAML配置文件加载
- 命令行参数与YAML参数合并
- 参数优先级：命令行 > YAML > 默认值

### 数据处理 (data_utils.py)
- 支持COCO和Pascal VOC格式转换
- 自动数据集划分
- 数据验证和统计

### 日志管理 (logging_utils.py)
- 结构化日志记录
- 自动日志文件命名
- 支持多种编码格式

### 结果美化 (beautify.py)
- 中文标签显示
- 圆角边框绘制
- 自适应字体大小
- 高质量可视化输出

## 输出结果

### 训练结果
- 模型权重文件: `models/checkpoints/`
- 训练日志: `logs/train/`
- 训练曲线: `runs/train/`

### 验证结果
- 验证报告: `runs/val/`
- 性能指标: 精确度、召回率、mAP等
- 混淆矩阵和PR曲线

### 推理结果
- 检测图像: `runs/detect/`
- 美化结果: `runs/detect/beautified/`
- 检测框坐标: `runs/detect/labels/`
- 裁剪图像: `runs/detect/crops/`

## 性能优化

### 训练优化
- 使用混合精度训练 (AMP)
- 矩形训练 (rect=True) 适合小目标
- AdamW优化器
- 自动批次大小调整

### 推理优化
- GPU加速推理
- 批量处理
- 流式处理大视频
- 多线程数据加载

## 常见问题

### Q: 如何选择合适的模型？
A: 推荐使用yolo11n-seg.pt作为预训练模型，平衡了速度和精度。

### Q: 训练时显存不足怎么办？
A: 减小batch size，推荐8G显存使用batch=8-16。

### Q: 如何提高检测精度？
A: 增加训练数据、调整损失权重、使用数据增强。

## 许可证

本项目遵循相应的开源许可证。

## 贡献

欢迎提交Issue和Pull Request来改进项目。

---

**作者**: 雨霓同学  
**项目**: 基于YOLO的口罩检测系统
