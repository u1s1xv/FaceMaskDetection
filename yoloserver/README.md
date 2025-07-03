# YOLOServer - 口罩检测服务端

基于YOLO12深度学习模型的口罩检测服务端，提供完整的模型训练、验证、推理和数据处理功能。

## 模块概述

YOLOServer是FaceMaskDetection项目的核心AI服务模块，专注于检测图像或视频中的人员是否正确佩戴口罩。系统支持三种检测类别：

- **正确戴口罩** (with_mask) - 绿色标注
- **未戴口罩** (without_mask) - 红色标注
- **错误戴口罩** (mask_weared_incorrect) - 黄色标注

### 核心功能

#### 模型训练
- 支持自定义数据集训练YOLO12模型
- 多种预训练模型支持（YOLO12n、YOLO12s、YOLO12m、YOLO12l、YOLO12x）
- 混合精度训练（AMP）优化
- 自动批次大小调整
- 早停机制和学习率调度

#### 模型验证
- 完整的模型性能评估功能
- 支持多种评估指标（mAP、精确度、召回率）
- 混淆矩阵和PR曲线生成
- 测试集、验证集分离验证

#### 实时推理
- 支持图像、视频、摄像头实时检测
- GPU/CPU自动切换和优化
- 批量处理和流式处理
- 多线程数据加载

#### 结果美化
- 支持中文标签显示
- 圆角边框和自适应字体
- 高质量可视化输出
- 自定义颜色和样式配置

#### 数据处理
- 多种数据格式转换（COCO、Pascal VOC）
- 自动数据集划分和验证
- 数据增强和预处理
- 数据质量检查和清理

### 技术特性
- 基于Ultralytics YOLO框架
- 完整的日志记录和性能监控系统
- 灵活的配置管理（YAML + 命令行）
- 设备信息自动检测和记录
- 模块化设计，易于扩展和维护

## 项目结构

```
yoloserver/
├── configs/                    # 配置文件目录
│   ├── data.yaml              # 数据集配置文件
│   ├── train.yaml             # 训练配置文件
│   ├── val.yaml               # 验证配置文件
│   └── infer.yaml             # 推理配置文件
├── data/                      # 数据目录
│   ├── train/                 # 训练数据集
│   │   ├── images/            # 训练图像
│   │   └── labels/            # 训练标签
│   ├── val/                   # 验证数据集
│   │   ├── images/            # 验证图像
│   │   └── labels/            # 验证标签
│   ├── test/                  # 测试数据集
│   │   ├── images/            # 测试图像
│   │   └── labels/            # 测试标签
│   ├── raw/                   # 原始数据
│   │   ├── images/            # 原始图像文件
│   │   └── original_annotations/ # 原始标注文件
│   └── crawled/               # 爬虫采集数据
│       ├── images/            # 爬虫图像
│       └── original_annotations/ # 爬虫标注
├── models/                    # 模型目录
│   ├── checkpoints/           # 训练完成的模型文件
│   └── pretrained/            # 预训练模型文件
├── runs/                      # 运行结果目录
│   ├── train/                 # 训练结果和日志
│   ├── val/                   # 验证结果和报告
│   ├── detect/                # 推理检测结果
│   └── infer/                 # 推理输出结果
├── logs/                      # 系统日志文件
├── scripts/                   # 核心执行脚本
│   ├── yolo_train.py          # 模型训练脚本
│   ├── yolo_val.py            # 模型验证脚本
│   ├── yolo_infer.py          # 模型推理脚本
│   ├── yolo_trans.py          # 数据格式转换脚本
│   └── yolo_validate.py       # 数据集验证脚本
├── utils/                     # 工具模块库
│   ├── __init__.py            # 模块初始化
│   ├── paths.py               # 路径配置管理
│   ├── config_utils.py        # 配置文件处理
│   ├── configs.py             # 默认配置定义
│   ├── data_utils.py          # 数据处理工具
│   ├── logging_utils.py       # 日志管理工具
│   ├── beautify.py            # 结果美化工具
│   ├── system_utils.py        # 系统信息工具
│   ├── performance_utils.py   # 性能监控工具
│   ├── result_utils.py        # 结果处理工具
│   ├── datainfo_utils.py      # 数据信息工具
│   ├── infer_frame.py         # 单帧推理处理
│   └── data_converters/       # 数据格式转换器
│       ├── coco_converter.py  # COCO格式转换
│       └── voc_converter.py   # Pascal VOC格式转换
└── initialize_project.py      # 项目结构初始化脚本
```

## 安装和环境配置

### 环境要求
- **Python**: 3.8+
- **操作系统**: Windows/Linux/macOS
- **内存**: 建议8GB以上（训练时建议16GB+）
- **GPU**: 支持CUDA的NVIDIA GPU（可选，但强烈推荐）
- **存储**: 至少5GB可用空间

### 1. 环境准备

```bash
# 创建虚拟环境
conda create -n FMD python=3.8+
conda activate FMD

# 安装核心依赖
pip install ultralytics>=8.0.0
pip install opencv-python>=4.7.0
pip install pillow>=9.0.0
pip install pyyaml>=6.0
pip install numpy>=1.21.0
pip install torch torchvision torchaudio  # 根据CUDA版本选择

# 安装其他工具依赖
pip install psutil cpuinfo matplotlib seaborn
```

### 2. 项目初始化

```bash
# 进入yoloserver目录
cd yoloserver

# 初始化项目结构（创建必要的目录）
python initialize_project.py
```

### 3. 验证安装

```bash
# 检查YOLO安装
python -c "from ultralytics import YOLO; print('YOLO安装成功')"

# 检查GPU可用性
python -c "import torch; print(f'CUDA可用: {torch.cuda.is_available()}')"

# 检查项目结构
python -c "from utils.paths import *; print('路径配置正确')"
```

### 4. 数据准备

#### 4.1 数据目录结构
将原始数据按以下结构放置：
```
data/
├── raw/
│   ├── images/                    # 原始图像文件
│   └── original_annotations/      # 原始标注文件（COCO/VOC格式）
└── crawled/
    ├── images/                    # 爬虫采集的图像
    └── original_annotations/      # 爬虫标注文件
```

#### 4.2 数据格式转换
```bash
# 转换COCO格式数据到YOLO格式
python scripts/yolo_trans.py --format coco --input data/raw/original_annotations/

# 转换Pascal VOC格式数据到YOLO格式
python scripts/yolo_trans.py --format pascal_voc --input data/raw/original_annotations/

# 验证数据集完整性
python scripts/yolo_validate.py --data configs/data.yaml
```

## 详细使用方法

### 模型训练

#### 基础训练命令
```bash
# 使用默认配置训练
python scripts/yolo_train.py --data configs/data.yaml --epochs 200 --batch 16

# 使用预训练模型进行迁移学习
python scripts/yolo_train.py --weights YOLO12n-seg.pt --data configs/data.yaml --epochs 200

# 使用YAML配置文件训练（推荐）
python scripts/yolo_train.py --use_yaml True
```

#### 高级训练选项
```bash
# 多GPU训练
python scripts/yolo_train.py --data configs/data.yaml --device 0,1,2,3

# 混合精度训练（节省显存）
python scripts/yolo_train.py --data configs/data.yaml --amp True

# 自定义图像尺寸
python scripts/yolo_train.py --data configs/data.yaml --imgsz 1280

# 启用数据增强
python scripts/yolo_train.py --data configs/data.yaml --augment True

# 设置早停机制
python scripts/yolo_train.py --data configs/data.yaml --patience 50
```

#### 训练监控
```bash
# 查看训练日志
tail -f logs/train_*.log

# 使用TensorBoard监控（如果安装）
tensorboard --logdir runs/train
```

### 模型验证

#### 基础验证命令
```bash
# 验证训练好的模型
python scripts/yolo_val.py --weights models/checkpoints/best.pt --data configs/data.yaml

# 在测试集上验证
python scripts/yolo_val.py --weights models/checkpoints/best.pt --split test

# 使用YAML配置文件验证
python scripts/yolo_val.py --use_yaml True
```

#### 详细验证选项
```bash
# 保存验证结果
python scripts/yolo_val.py --weights best.pt --save_json True --save_txt True

# 生成混淆矩阵和PR曲线
python scripts/yolo_val.py --weights best.pt --plots True

# 指定验证图像尺寸
python scripts/yolo_val.py --weights best.pt --imgsz 640

# 调整置信度和IOU阈值
python scripts/yolo_val.py --weights best.pt --conf 0.25 --iou 0.45
```

### 模型推理

#### 基础推理命令
```bash
# 单张图像推理
python scripts/yolo_infer.py --weights models/checkpoints/best.pt --source path/to/image.jpg

# 视频文件推理
python scripts/yolo_infer.py --weights models/checkpoints/best.pt --source path/to/video.mp4

# 摄像头实时推理
python scripts/yolo_infer.py --weights models/checkpoints/best.pt --source 0

# 批量图像推理
python scripts/yolo_infer.py --weights models/checkpoints/best.pt --source path/to/images_folder/
```

#### 高级推理选项
```bash
# 启用美化显示（中文标签、圆角边框）
python scripts/yolo_infer.py --weights best.pt --source image.jpg --beautify True

# 保存检测结果
python scripts/yolo_infer.py --weights best.pt --source image.jpg --save True --save_txt True

# 调整检测参数
python scripts/yolo_infer.py --weights best.pt --source image.jpg --conf 0.5 --iou 0.4

# 指定输出目录
python scripts/yolo_infer.py --weights best.pt --source image.jpg --project runs/custom --name my_detection

# 实时显示结果
python scripts/yolo_infer.py --weights best.pt --source 0 --show True
```

#### 推理结果说明
推理完成后，结果保存在 `runs/infer/` 目录下：
- **原始检测图像**: 带有检测框的图像
- **美化检测图像**: 使用中文标签和圆角边框的高质量图像
- **检测坐标文件**: TXT格式的检测框坐标和置信度
- **裁剪图像**: 检测到的目标裁剪图像

## 配置文件说明

### 数据配置 (configs/data.yaml)

```yaml
# 数据集根路径
path: C:\FaceMaskDetection\yoloserver\data

# 训练、验证、测试数据路径
train: C:\FaceMaskDetection\yoloserver\data\train\images
val: C:\FaceMaskDetection\yoloserver\data\val\images
test: C:\FaceMaskDetection\yoloserver\data\test\images

# 类别数量
nc: 3

# 类别名称（按索引顺序）
names: [mask_weared_incorrect, with_mask, without_mask]
```

### 训练配置 (configs/train.yaml)

```yaml
# 基本训练参数
epochs: 200              # 训练轮数
batch: 16                # 批次大小
imgsz: 640               # 输入图像尺寸
device: ''               # 设备选择（''为自动检测）

# 模型参数
model: 'YOLO12n-seg.pt'  # 预训练模型路径
data: 'configs/data.yaml' # 数据配置文件

# 优化器设置
optimizer: 'AdamW'       # 优化器类型
lr0: 0.01               # 初始学习率
momentum: 0.937         # 动量
weight_decay: 0.0005    # 权重衰减

# 训练策略
patience: 20            # 早停耐心值
save_period: 10         # 模型保存间隔
amp: True               # 混合精度训练
rect: True              # 矩形训练
augment: True           # 数据增强

# 输出设置
project: 'runs/train'   # 输出项目目录
name: 'exp'             # 实验名称
exist_ok: False         # 是否覆盖已存在的实验
```

### 验证配置 (configs/val.yaml)

```yaml
# 基本验证参数
data: 'configs/data.yaml' # 数据配置文件
imgsz: 640               # 验证图像尺寸
batch: 16                # 验证批次大小
device: ''               # 设备选择

# 检测参数
conf: 0.001             # 置信度阈值
iou: 0.7                # IOU阈值
max_det: 300            # 最大检测数量

# 输出设置
save_json: False        # 保存JSON结果
save_txt: True          # 保存TXT结果
save_conf: True         # 保存置信度
save_crop: True         # 保存裁剪图像
plots: True             # 生成图表

# 验证设置
split: 'val'            # 验证集分割
rect: True              # 矩形验证
half: True              # 半精度推理
```

### 推理配置 (configs/infer.yaml)

```yaml
# 基本推理参数
source: '0'             # 数据源（图像/视频/摄像头）
device: ''              # 设备选择
imgsz: 640              # 推理图像尺寸
batch: 1                # 推理批次大小

# 检测参数
conf: 0.25              # 置信度阈值
iou: 0.7                # IOU阈值
max_det: 300            # 最大检测数量
classes: null           # 指定检测类别
agnostic_nms: False     # 类别无关NMS

# 输出设置
project: 'runs/infer'   # 输出项目目录
name: 'predict'         # 预测名称
save: False             # 保存结果图像
save_txt: False         # 保存检测坐标
save_conf: False        # 保存置信度
save_crop: False        # 保存裁剪图像

# 显示设置
show: False             # 实时显示
show_labels: True       # 显示标签
show_conf: True         # 显示置信度
show_boxes: True        # 显示检测框
line_width: 8           # 线宽

# 美化设置（自定义参数）
beautify: True          # 启用美化
use_chinese: True       # 使用中文标签
font_size: 22           # 字体大小
label_padding_x: 30     # 标签水平内边距
label_padding_y: 18     # 标签垂直内边距
corner_radius: 8        # 圆角半径
```

## 工具模块介绍

### 路径管理 (utils/paths.py)
统一管理项目中所有路径配置，确保跨平台兼容性：
```python
from utils.paths import *

# 主要路径常量
YOLO_SERVER_ROOT      # yoloserver根目录
DATA_ROOT             # 数据根目录
MODELS_ROOT           # 模型根目录
LOGS_ROOT             # 日志根目录
RUNS_ROOT             # 运行结果根目录
```

### 配置管理 (utils/config_utils.py)
提供灵活的配置文件管理功能：
- **YAML配置加载**: 支持嵌套配置和变量替换
- **参数合并**: 命令行参数与YAML参数智能合并
- **参数优先级**: 命令行 > YAML > 默认值
- **配置验证**: 自动验证配置参数的有效性

```python
from utils.config_utils import load_config, merge_configs

# 加载配置文件
config = load_config('configs/train.yaml')

# 合并命令行参数
final_config = merge_configs(config, args)
```

### 数据处理 (utils/data_utils.py)
完整的数据处理工具集：
- **格式转换**: COCO、Pascal VOC到YOLO格式
- **数据集划分**: 自动按比例划分训练/验证/测试集
- **数据验证**: 检查标注文件完整性和格式正确性
- **数据统计**: 生成数据集统计报告

```python
from utils.data_utils import convert_dataset, split_dataset, validate_dataset

# 转换数据格式
convert_dataset('coco', 'data/raw/annotations.json', 'data/converted/')

# 划分数据集
split_dataset('data/all/', train_ratio=0.7, val_ratio=0.2, test_ratio=0.1)
```

### 日志管理 (utils/logging_utils.py)
结构化的日志记录系统：
- **多级日志**: DEBUG、INFO、WARNING、ERROR、CRITICAL
- **文件输出**: 自动创建带时间戳的日志文件
- **格式化输出**: 统一的日志格式和编码
- **性能监控**: 记录训练和推理性能指标

```python
from utils.logging_utils import setup_logger

# 设置日志记录器
logger = setup_logger('train', 'logs/train.log')
logger.info('开始训练模型')
```

### 结果美化 (utils/beautify.py)
高质量的检测结果可视化：
- **中文标签**: 支持中文类别名称显示
- **圆角边框**: 美观的圆角矩形检测框
- **自适应字体**: 根据图像尺寸自动调整字体大小
- **颜色配置**: 可自定义的类别颜色映射

```python
from utils.beautify import beautify_detection_result

# 美化检测结果
beautified_image = beautify_detection_result(
    image, detections,
    use_chinese=True,
    corner_radius=8
)
```

### 系统工具 (utils/system_utils.py)
系统信息和性能监控：
- **硬件检测**: 自动检测GPU、CPU、内存信息
- **性能监控**: 实时监控资源使用情况
- **设备管理**: 智能选择最优计算设备

```python
from utils.system_utils import get_device_info, monitor_performance

# 获取设备信息
device_info = get_device_info()
print(f"GPU: {device_info['gpu']}, 内存: {device_info['memory']}")
```

### 数据转换器 (utils/data_converters/)
专业的数据格式转换工具：

#### COCO转换器 (coco_converter.py)
```python
from utils.data_converters.coco_converter import COCOConverter

converter = COCOConverter()
converter.convert('annotations.json', 'output_dir/')
```

#### VOC转换器 (voc_converter.py)
```python
from utils.data_converters.voc_converter import VOCConverter

converter = VOCConverter()
converter.convert('annotations_dir/', 'output_dir/')
```

## 数据处理和格式转换

### 支持的数据格式
- **YOLO格式**: 原生支持的标注格式
- **COCO格式**: 通过转换器支持
- **Pascal VOC格式**: 通过转换器支持

### 数据转换示例
```bash
# COCO格式转换
python scripts/yolo_trans.py --format coco --input data/raw/annotations.json --output data/converted/

# Pascal VOC格式转换
python scripts/yolo_trans.py --format pascal_voc --input data/raw/xml_annotations/ --output data/converted/

# 数据集验证
python scripts/yolo_validate.py --data configs/data.yaml --check_labels True
```

### 数据集划分
```bash
# 自动划分数据集（7:2:1比例）
python -c "
from utils.data_utils import split_dataset
split_dataset('data/all_images/', train_ratio=0.7, val_ratio=0.2, test_ratio=0.1)
"
```

## 输出结果说明

### 训练结果目录结构
```
runs/train/exp/
├── weights/
│   ├── best.pt              # 最佳模型权重
│   ├── last.pt              # 最后一轮权重
│   └── epoch_*.pt           # 各轮次权重
├── results.png              # 训练曲线图
├── confusion_matrix.png     # 混淆矩阵
├── F1_curve.png            # F1曲线
├── P_curve.png             # 精确度曲线
├── R_curve.png             # 召回率曲线
├── PR_curve.png            # PR曲线
└── args.yaml               # 训练参数记录
```

### 验证结果目录结构
```
runs/val/exp/
├── confusion_matrix.png     # 混淆矩阵
├── F1_curve.png            # F1曲线
├── labels.jpg              # 标签分布图
├── predictions.json        # 预测结果JSON
├── val_batch*.jpg          # 验证批次可视化
└── results.txt             # 详细验证结果
```

### 推理结果目录结构
```
runs/infer/predict/
├── image1.jpg              # 原始检测结果
├── image1_beautified.jpg   # 美化检测结果
├── labels/
│   └── image1.txt          # 检测框坐标
├── crops/
│   ├── with_mask/          # 正确戴口罩裁剪图
│   ├── without_mask/       # 未戴口罩裁剪图
│   └── mask_weared_incorrect/ # 错误戴口罩裁剪图
└── results.json            # 检测结果汇总
```

## 性能优化建议

### 训练性能优化
1. **硬件优化**
   ```bash
   # 使用多GPU训练
   python scripts/yolo_train.py --device 0,1,2,3

   # 启用混合精度训练
   python scripts/yolo_train.py --amp True
   ```

2. **数据加载优化**
   ```bash
   # 增加数据加载线程
   python scripts/yolo_train.py --workers 8

   # 启用矩形训练（减少padding）
   python scripts/yolo_train.py --rect True
   ```

3. **内存优化**
   ```bash
   # 自动调整批次大小
   python scripts/yolo_train.py --batch -1

   # 减少图像尺寸
   python scripts/yolo_train.py --imgsz 416
   ```

### 推理性能优化
1. **模型优化**
   ```bash
   # 使用TensorRT优化（需要安装TensorRT）
   python scripts/yolo_infer.py --weights best.pt --engine True

   # 半精度推理
   python scripts/yolo_infer.py --weights best.pt --half True
   ```

2. **批量处理**
   ```bash
   # 批量推理
   python scripts/yolo_infer.py --weights best.pt --batch 8

   # 流式处理大视频
   python scripts/yolo_infer.py --weights best.pt --stream True
   ```

3. **设备选择**
   ```bash
   # 指定GPU设备
   python scripts/yolo_infer.py --weights best.pt --device 0

   # CPU推理（低功耗场景）
   python scripts/yolo_infer.py --weights best.pt --device cpu
   ```

### 内存和存储优化
- **定期清理**: 自动清理临时文件和过期日志
- **模型压缩**: 使用模型剪枝和量化技术
- **数据压缩**: 使用高效的图像压缩格式
- **缓存管理**: 合理配置数据加载缓存

## 故障排除

### 常见问题及解决方案

#### 1. 训练相关问题

**问题**: 训练过程中出现CUDA内存不足
```
RuntimeError: CUDA out of memory
```
**解决方案**:
```bash
# 减少批次大小
python scripts/yolo_train.py --batch 8

# 减少图像尺寸
python scripts/yolo_train.py --imgsz 416

# 启用梯度累积
python scripts/yolo_train.py --accumulate 2
```

**问题**: 训练数据加载失败
```
FileNotFoundError: No such file or directory
```
**解决方案**:
```bash
# 检查数据配置文件
python scripts/yolo_validate.py --data configs/data.yaml

# 验证数据路径
python -c "from utils.paths import *; print(f'数据根目录: {DATA_ROOT}')"

# 重新初始化项目结构
python initialize_project.py
```

**问题**: 模型收敛缓慢或不收敛
**解决方案**:
```bash
# 调整学习率
python scripts/yolo_train.py --lr0 0.001

# 使用预训练模型
python scripts/yolo_train.py --weights YOLO12n-seg.pt

# 增加训练轮数
python scripts/yolo_train.py --epochs 300

# 检查数据质量
python scripts/yolo_validate.py --data configs/data.yaml --check_labels True
```

#### 2. 推理相关问题

**问题**: 推理结果质量差
**解决方案**:
```bash
# 调整置信度阈值
python scripts/yolo_infer.py --conf 0.5

# 调整IOU阈值
python scripts/yolo_infer.py --iou 0.4

# 使用更大的图像尺寸
python scripts/yolo_infer.py --imgsz 1280

# 检查模型性能
python scripts/yolo_val.py --weights best.pt
```

**问题**: 推理速度慢
**解决方案**:
```bash
# 启用半精度推理
python scripts/yolo_infer.py --half True

# 使用较小的图像尺寸
python scripts/yolo_infer.py --imgsz 320

# 批量处理
python scripts/yolo_infer.py --batch 4

# 使用TensorRT优化
python scripts/yolo_infer.py --engine True
```

#### 3. 环境相关问题

**问题**: 导入模块失败
```
ModuleNotFoundError: No module named 'utils'
```
**解决方案**:
```bash
# 确保在yoloserver目录下运行
cd yoloserver

# 检查Python路径
python -c "import sys; print(sys.path)"

# 重新安装依赖
pip install -r requirements.txt
```

**问题**: GPU不可用
```
CUDA is not available
```
**解决方案**:
```bash
# 检查CUDA安装
nvidia-smi

# 检查PyTorch CUDA支持
python -c "import torch; print(torch.cuda.is_available())"

# 重新安装PyTorch（根据CUDA版本）
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

#### 4. 数据相关问题

**问题**: 数据格式转换失败
**解决方案**:
```bash
# 检查原始数据格式
python -c "
import json
with open('data/raw/annotations.json') as f:
    data = json.load(f)
    print(f'数据格式: {type(data)}, 键: {data.keys()}')
"

# 使用详细模式查看错误
python scripts/yolo_trans.py --format coco --input data/raw/ --verbose True
```

**问题**: 标注文件格式错误
**解决方案**:
```bash
# 验证YOLO格式标注
python -c "
from utils.data_utils import validate_yolo_labels
validate_yolo_labels('data/train/labels/')
"

# 检查类别数量一致性
python scripts/yolo_validate.py --data configs/data.yaml --check_classes True
```

### 日志分析

#### 查看训练日志
```bash
# 查看最新训练日志
tail -f logs/train_*.log

# 搜索错误信息
grep -i error logs/train_*.log

# 查看性能指标
grep -i "mAP\|precision\|recall" logs/train_*.log
```

#### 查看系统资源使用
```bash
# 监控GPU使用情况
watch -n 1 nvidia-smi

# 监控内存使用
python -c "
from utils.system_utils import monitor_performance
monitor_performance(duration=60)
"
```

### 性能调试

#### 训练性能分析
```bash
# 启用详细日志
python scripts/yolo_train.py --verbose True

# 性能分析模式
python scripts/yolo_train.py --profile True

# 检查数据加载速度
python scripts/yolo_train.py --benchmark True
```

#### 推理性能分析
```bash
# 测试推理速度
python scripts/yolo_infer.py --benchmark True

# 分析瓶颈
python scripts/yolo_infer.py --profile True
```

## 技术支持

### 获取帮助
1. **查看日志**: 首先检查 `logs/` 目录下的相关日志文件
2. **运行诊断**: 使用 `python scripts/yolo_validate.py` 进行系统诊断
3. **检查配置**: 验证 `configs/` 目录下的配置文件
4. **查看文档**: 参考本README和相关配置文件注释

### 报告问题
提交问题时请包含：
- 完整的错误信息和堆栈跟踪
- 使用的命令和参数
- 系统环境信息（Python版本、GPU型号等）
- 相关的日志文件内容

### 版本信息
- **YOLO版本**: 12.x
- **Ultralytics版本**: 8.0+
- **Python版本**: 3.8+
- **PyTorch版本**: 1.9+

---

**最后更新**: 2025-07-03
**维护状态**: 积极维护
**技术支持**: 完整的文档和示例代码
