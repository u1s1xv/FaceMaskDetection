"""
YOLO推理服务模块
"""
import os
import sys
import subprocess
import json
import time
import logging
import hashlib
import threading
from pathlib import Path
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.cache import cache
from PIL import Image
import cv2
import numpy as np
import re

logger = logging.getLogger(__name__)

# 全局推理服务实例
_optimized_inference_service = None
_service_lock = threading.Lock()




class YOLOInferenceService:
    """YOLO推理服务类"""
    
    def __init__(self):
        self.yolo_root = settings.YOLO_SERVER_ROOT
        self.models_dir = settings.YOLO_MODELS_DIR
        self.scripts_dir = settings.YOLO_SCRIPTS_DIR
        self.infer_script = self.scripts_dir / 'yolo_infer.py'
        
        # 确保路径存在
        if not self.yolo_root.exists():
            raise FileNotFoundError(f"YOLO服务器根目录不存在: {self.yolo_root}")
        if not self.infer_script.exists():
            raise FileNotFoundError(f"YOLO推理脚本不存在: {self.infer_script}")
    
    def get_available_models(self):
        """获取可用的模型列表"""
        models = []
        if self.models_dir.exists():
            for model_file in self.models_dir.glob('*.pt'):
                try:
                    file_size = model_file.stat().st_size / (1024 * 1024)  # MB

                    # 尝试从数据库获取模型信息
                    model_info = {
                        'name': model_file.name,
                        'path': str(model_file),
                        'size': round(file_size, 2),
                        'description': self._get_model_description(model_file.name),
                        'last_modified': model_file.stat().st_mtime
                    }

                    # 尝试从数据库获取额外信息
                    try:
                        from .models import ModelConfig
                        db_model = ModelConfig.objects.filter(
                            name=model_file.name,
                            is_active=True
                        ).first()

                        if db_model:
                            model_info.update({
                                'description': db_model.description,
                                'accuracy': db_model.accuracy,
                                'inference_speed': db_model.inference_speed,
                            })
                    except Exception:
                        pass  # 如果数据库查询失败，使用默认信息

                    models.append(model_info)

                except Exception as e:
                    logger.warning(f"获取模型信息失败 {model_file.name}: {str(e)}")
                    continue

        # 按文件名排序
        models.sort(key=lambda x: x['name'])
        return models

    def _get_model_description(self, model_name):
        """根据模型文件名生成描述"""
        name_lower = model_name.lower()

        if 'yolo11n' in name_lower:
            return 'YOLO11 Nano - 快速检测，适合实时应用'
        elif 'yolo11s' in name_lower:
            return 'YOLO11 Small - 平衡性能，推荐使用'
        elif 'yolo11m' in name_lower:
            return 'YOLO11 Medium - 高精度检测'
        elif 'yolo11l' in name_lower:
            return 'YOLO11 Large - 超高精度，较慢'
        elif 'yolo11x' in name_lower:
            return 'YOLO11 XLarge - 最高精度，最慢'
        elif 'seg' in name_lower:
            return '分割模型 - 支持实例分割'
        elif 'det' in name_lower:
            return '检测模型 - 目标检测'
        else:
            return '自定义训练模型'
    
    def run_inference(self, image_path, model_name='yolo11n-seg.pt', 
                     confidence=0.25, iou=0.45, imgsz=640):
        """
        运行YOLO推理
        
        Args:
            image_path: 输入图像路径
            model_name: 模型名称
            confidence: 置信度阈值
            iou: IOU阈值
            imgsz: 图像尺寸
            
        Returns:
            dict: 包含检测结果的字典
        """
        try:
            start_time = time.time()
            
            # 构建模型路径
            model_path = self.models_dir / model_name
            if not model_path.exists():
                raise FileNotFoundError(f"模型文件不存在: {model_path}")
            
            # 创建临时输出目录
            output_dir = settings.MEDIA_ROOT / 'temp_inference'
            output_dir.mkdir(exist_ok=True, parents=True)
            
            # 构建推理命令
            cmd = [
                sys.executable,
                str(self.infer_script),
                '--weights', str(model_path),
                '--source', str(image_path),
                '--conf', str(confidence),
                '--iou', str(iou),
                '--imgsz', str(imgsz),
                '--save', 'True',
                '--save_txt', 'True',
                '--save_conf', 'True',
                '--project', str(output_dir),
                '--name', 'exp'
            ]
            
            logger.info(f"执行YOLO推理命令: {' '.join(cmd)}")
            
            # 执行推理
            result = subprocess.run(
                cmd,
                cwd=str(self.yolo_root),
                capture_output=True,
                text=True,
                encoding='utf-8',  # 显式指定UTF-8编码，避免Windows系统默认GBK编码导致的解码错误
                errors='replace',  # 使用replace错误处理策略，避免解码错误导致程序崩溃
                timeout=300  # 5分钟超时
            )
            
            processing_time = time.time() - start_time
            
            if result.returncode != 0:
                logger.error(f"YOLO推理失败: {result.stderr}")
                raise RuntimeError(f"YOLO推理失败: {result.stderr}")
            
            exp_dirs = [d for d in output_dir.iterdir() if d.is_dir() and re.match(r"exp\d*$", d.name)]
            if not exp_dirs:
                raise RuntimeError("未找到推理输出exp目录")
            
            latest_exp_dir = max(exp_dirs, key=lambda d: d.stat().st_mtime)

            # 解析结果
            inference_result = self._parse_inference_results(
                latest_exp_dir,
                processing_time
            )
            
            return inference_result
            
        except subprocess.TimeoutExpired:
            logger.error("YOLO推理超时")
            raise RuntimeError("推理超时，请稍后重试")
        except Exception as e:
            logger.error(f"YOLO推理异常: {str(e)}")
            raise RuntimeError(f"推理失败: {str(e)}")
    
    def _parse_inference_results(self, result_dir, processing_time):
        """解析推理结果"""
        try:
            result_data = {
                'processing_time': processing_time,
                'total_detections': 0,
                'with_mask_count': 0,
                'without_mask_count': 0,
                'incorrect_mask_count': 0,
                'detections': [],
                'result_image_path': None,
                'beautified_image_path': None
            }
            
            # 查找结果图像
            for img_file in result_dir.glob('*.jpg'):
                result_data['result_image_path'] = str(img_file)
                break
            
            # 查找美化图像
            beautified_dir = result_dir / 'beautified'
            if beautified_dir.exists():
                for img_file in beautified_dir.glob('*.png'):
                    result_data['beautified_image_path'] = str(img_file)
                    break
            
            # 解析标签文件
            labels_dir = result_dir / 'labels'
            if labels_dir.exists():
                for label_file in labels_dir.glob('*.txt'):
                    detections = self._parse_label_file(label_file)
                    result_data['detections'].extend(detections)
            
            # 统计各类别数量
            for detection in result_data['detections']:
                class_id = detection['class_id']
                if class_id == 0:  # mask_weared_incorrect
                    result_data['incorrect_mask_count'] += 1
                elif class_id == 1:  # with_mask
                    result_data['with_mask_count'] += 1
                elif class_id == 2:  # without_mask
                    result_data['without_mask_count'] += 1
            
            result_data['total_detections'] = len(result_data['detections'])
            
            return result_data
            
        except Exception as e:
            logger.error(f"解析推理结果失败: {str(e)}")
            raise RuntimeError(f"解析结果失败: {str(e)}")
    
    def _parse_label_file(self, label_file):
        """解析YOLO标签文件"""
        detections = []
        class_names = {
            0: 'mask_weared_incorrect',
            1: 'with_mask', 
            2: 'without_mask'
        }
        
        try:
            with open(label_file, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 6:  # class_id x_center y_center width height confidence
                        detection = {
                            'class_id': int(parts[0]),
                            'class_name': class_names.get(int(parts[0]), 'unknown'),
                            'x_center': float(parts[1]),
                            'y_center': float(parts[2]),
                            'width': float(parts[3]),
                            'height': float(parts[4]),
                            'confidence': float(parts[5]) if len(parts) > 5 else 0.0
                        }
                        detections.append(detection)
        except Exception as e:
            logger.warning(f"解析标签文件失败 {label_file}: {str(e)}")
        
        return detections
    
    def copy_result_image(self, source_path, target_field):
        """复制结果图像到Django媒体目录"""
        if not source_path or not Path(source_path).exists():
            return None
        
        try:
            with open(source_path, 'rb') as f:
                image_content = f.read()
            
            filename = Path(source_path).name
            return ContentFile(image_content, name=filename)
            
        except Exception as e:
            logger.error(f"复制结果图像失败: {str(e)}")
            return None


class OptimizedYOLOInferenceService:
    """优化的YOLO推理服务类 - 在内存中保持模型加载"""

    def __init__(self):
        self.yolo_root = settings.YOLO_SERVER_ROOT
        self.models_dir = settings.YOLO_MODELS_DIR
        self.scripts_dir = settings.YOLO_SCRIPTS_DIR

        # 模型缓存
        self._models = {}
        self._model_lock = threading.Lock()

        # 类别映射
        self.class_names = {
            0: 'mask_weared_incorrect',
            1: 'with_mask',
            2: 'without_mask'
        }

        logger.info("优化推理服务初始化完成")

    def preload_image(self, image_path):
        """预加载图像到内存，减少I/O操作"""
        try:
            # 使用OpenCV读取图像（更快）
            image = cv2.imread(str(image_path))
            if image is None:
                # 尝试使用PIL
                pil_image = Image.open(image_path)
                image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

            return image
        except Exception as e:
            logger.warning(f"预加载图像失败 {image_path}: {e}")
            return None

    def run_inference_with_preload(self, image_path, model_name='yolo11n-seg.pt',
                                  confidence=0.25, iou=0.45, imgsz=640):
        """
        预加载图像并执行推理（进一步优化性能）

        Args:
            image_path: 图像文件路径
            model_name: 模型名称
            confidence: 置信度阈值
            iou: IOU阈值
            imgsz: 图像尺寸

        Returns:
            dict: 包含检测结果的字典
        """
        # 预加载图像到内存
        image_data = self.preload_image(image_path)
        if image_data is not None:
            # 使用内存中的图像数据进行推理
            return self.run_inference(
                image_data=image_data,
                model_name=model_name,
                confidence=confidence,
                iou=iou,
                imgsz=imgsz
            )
        else:
            # 回退到文件路径推理
            return self.run_inference(
                image_path=image_path,
                model_name=model_name,
                confidence=confidence,
                iou=iou,
                imgsz=imgsz
            )

    def _get_image_hash(self, image_path):
        """计算图像文件的哈希值用于缓存"""
        try:
            with open(image_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            logger.warning(f"计算图像哈希失败: {e}")
            return None

    def _load_model(self, model_name):
        """加载并缓存YOLO模型"""
        with self._model_lock:
            if model_name not in self._models:
                try:
                    # 动态导入YOLO
                    from ultralytics import YOLO

                    model_path = self.models_dir / model_name
                    if not model_path.exists():
                        raise FileNotFoundError(f"模型文件不存在: {model_path}")

                    logger.info(f"加载YOLO模型: {model_name}")
                    model = YOLO(str(model_path))
                    self._models[model_name] = model
                    logger.info(f"模型 {model_name} 加载完成")

                except Exception as e:
                    logger.error(f"加载模型失败 {model_name}: {e}")
                    raise RuntimeError(f"模型加载失败: {e}")

            return self._models[model_name]

    def run_inference(self, image_path=None, image_data=None, model_name='yolo11n-seg.pt',
                     confidence=0.25, iou=0.45, imgsz=640):
        """
        执行优化的推理

        Args:
            image_path: 图像文件路径 (与image_data二选一)
            image_data: 图像数据 (numpy数组或PIL图像，与image_path二选一)
            model_name: 模型名称
            confidence: 置信度阈值
            iou: IOU阈值
            imgsz: 图像尺寸

        Returns:
            dict: 包含检测结果的字典
        """
        try:
            start_time = time.time()

            # 确定输入源
            if image_path:
                source = str(image_path)
                cache_key = self._get_cache_key(image_path, model_name, confidence, iou, imgsz)
            elif image_data is not None:
                source = image_data
                # 为内存数据生成缓存键
                cache_key = self._get_cache_key_for_data(image_data, model_name, confidence, iou, imgsz)
            else:
                raise ValueError("必须提供image_path或image_data参数")

            # 检查缓存
            cached_result = cache.get(cache_key) if cache_key else None
            if cached_result:
                logger.info(f"使用缓存结果: {cache_key}")
                return cached_result

            # 加载模型
            model = self._load_model(model_name)

            # 执行推理
            logger.info(f"开始推理: {source if isinstance(source, str) else '内存图像数据'}")
            results = model.predict(
                source=source,
                imgsz=imgsz,
                conf=confidence,
                iou=iou,
                save=False,  # 不保存到文件系统
                verbose=False
            )

            # 处理结果
            inference_result = self._process_results(
                results, source, start_time
            )

            # 缓存结果（缓存1小时）
            if cache_key:
                cache.set(cache_key, inference_result, 3600)

            processing_time = time.time() - start_time
            logger.info(f"推理完成，耗时: {processing_time:.2f}秒")

            return inference_result

        except Exception as e:
            logger.error(f"优化推理失败: {str(e)}")
            raise RuntimeError(f"推理失败: {str(e)}")

    def _get_cache_key(self, image_path, model_name, confidence, iou, imgsz):
        """生成缓存键"""
        image_hash = self._get_image_hash(image_path)
        if image_hash:
            key_data = f"{image_hash}_{model_name}_{confidence}_{iou}_{imgsz}"
            return f"yolo_inference_{hashlib.md5(key_data.encode()).hexdigest()}"
        return None

    def _get_cache_key_for_data(self, image_data, model_name, confidence, iou, imgsz):
        """为内存图像数据生成缓存键"""
        try:
            # 将图像数据转换为字节并计算哈希
            if isinstance(image_data, np.ndarray):
                data_bytes = image_data.tobytes()
            elif hasattr(image_data, 'tobytes'):
                data_bytes = image_data.tobytes()
            else:
                # 尝试转换为numpy数组
                data_array = np.array(image_data)
                data_bytes = data_array.tobytes()

            data_hash = hashlib.md5(data_bytes).hexdigest()
            key_data = f"{data_hash}_{model_name}_{confidence}_{iou}_{imgsz}"
            return f"yolo_inference_{hashlib.md5(key_data.encode()).hexdigest()}"
        except Exception as e:
            logger.warning(f"生成内存数据缓存键失败: {e}")
            return None

    def _process_results(self, results, image_path, start_time):
        """处理推理结果"""
        try:
            result_data = {
                'processing_time': time.time() - start_time,
                'total_detections': 0,
                'with_mask_count': 0,
                'without_mask_count': 0,
                'incorrect_mask_count': 0,
                'detections': [],
                'result_image_path': str(image_path),
                'beautified_image_path': None
            }

            if results and len(results) > 0:
                result = results[0]

                # 处理检测框
                if result.boxes is not None and len(result.boxes) > 0:
                    boxes = result.boxes
                    for i in range(len(boxes)):
                        # 获取检测信息
                        class_id = int(boxes.cls[i].item())
                        confidence = float(boxes.conf[i].item())

                        # 获取边界框坐标 (xyxy格式)
                        x1, y1, x2, y2 = boxes.xyxy[i].tolist()

                        # 转换为YOLO格式 (归一化的中心点坐标和宽高)
                        img_height, img_width = result.orig_shape
                        x_center = (x1 + x2) / 2 / img_width
                        y_center = (y1 + y2) / 2 / img_height
                        width = (x2 - x1) / img_width
                        height = (y2 - y1) / img_height

                        detection = {
                            'class_id': class_id,
                            'class_name': self.class_names.get(class_id, 'unknown'),
                            'x_center': x_center,
                            'y_center': y_center,
                            'width': width,
                            'height': height,
                            'confidence': confidence
                        }
                        result_data['detections'].append(detection)

                        # 统计各类别数量
                        if class_id == 0:  # mask_weared_incorrect
                            result_data['incorrect_mask_count'] += 1
                        elif class_id == 1:  # with_mask
                            result_data['with_mask_count'] += 1
                        elif class_id == 2:  # without_mask
                            result_data['without_mask_count'] += 1

                result_data['total_detections'] = len(result_data['detections'])

                # 生成美化图像
                beautified_image = self._create_beautified_image(result, result_data['detections'])
                if beautified_image is not None:
                    result_data['beautified_image_data'] = beautified_image

            return result_data

        except Exception as e:
            logger.error(f"处理推理结果失败: {str(e)}")
            raise RuntimeError(f"结果处理失败: {str(e)}")

    def _create_beautified_image(self, result, detections):
        """创建美化的检测结果图像"""
        try:
            # 获取原始图像
            img = result.orig_img.copy()

            # 颜色映射 (BGR格式)
            color_mapping = {
                0: (0, 255, 255),    # 错误佩戴 - 黄色
                1: (0, 255, 0),      # 正确佩戴 - 绿色
                2: (0, 0, 255)       # 未佩戴 - 红色
            }

            # 绘制检测框和标签
            for detection in detections:
                class_id = detection['class_id']
                confidence = detection['confidence']
                class_name = detection['class_name']

                # 转换坐标回像素坐标
                img_height, img_width = img.shape[:2]
                x_center = detection['x_center'] * img_width
                y_center = detection['y_center'] * img_height
                width = detection['width'] * img_width
                height = detection['height'] * img_height

                x1 = int(x_center - width / 2)
                y1 = int(y_center - height / 2)
                x2 = int(x_center + width / 2)
                y2 = int(y_center + height / 2)

                # 获取颜色
                color = color_mapping.get(class_id, (255, 255, 255))

                # 绘制边界框
                cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)

                # 绘制标签
                label = f"{class_name}: {confidence:.2f}"
                label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                cv2.rectangle(img, (x1, y1 - label_size[1] - 10),
                            (x1 + label_size[0], y1), color, -1)
                cv2.putText(img, label, (x1, y1 - 5),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            # 转换为PIL图像并返回字节数据
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(img_rgb)

            import io
            img_bytes = io.BytesIO()
            pil_img.save(img_bytes, format='PNG')
            img_bytes.seek(0)

            return img_bytes.getvalue()

        except Exception as e:
            logger.error(f"创建美化图像失败: {str(e)}")
            return None


def get_optimized_inference_service():
    """获取优化的推理服务单例"""
    global _optimized_inference_service

    if _optimized_inference_service is None:
        with _service_lock:
            if _optimized_inference_service is None:
                _optimized_inference_service = OptimizedYOLOInferenceService()

    return _optimized_inference_service


def clear_inference_cache():
    """清理推理缓存"""
    try:
        # 清理Django缓存中的推理结果
        cache_keys = cache.keys("yolo_inference_*")
        if cache_keys:
            cache.delete_many(cache_keys)
            logger.info(f"清理了 {len(cache_keys)} 个推理缓存")

        # 清理模型缓存（可选，通常不需要）
        global _optimized_inference_service
        if _optimized_inference_service:
            with _service_lock:
                _optimized_inference_service._models.clear()
                logger.info("清理了模型缓存")

        return True
    except Exception as e:
        logger.error(f"清理缓存失败: {e}")
        return False


def get_cache_stats():
    """获取缓存统计信息"""
    try:
        # 尝试获取缓存键（不同缓存后端可能不支持keys方法）
        cache_count = 0
        try:
            if hasattr(cache, 'keys'):
                cache_keys = cache.keys("yolo_inference_*")
                cache_count = len(cache_keys) if cache_keys else 0
            else:
                # 对于不支持keys方法的缓存后端，返回估计值
                cache_count = -1  # 表示无法获取准确数量
        except:
            cache_count = -1

        model_count = 0
        global _optimized_inference_service
        if _optimized_inference_service:
            model_count = len(_optimized_inference_service._models)

        return {
            'inference_cache_count': cache_count,
            'loaded_models_count': model_count,
            'cache_enabled': True,
            'cache_backend': str(type(cache).__name__)
        }
    except Exception as e:
        logger.error(f"获取缓存统计失败: {e}")
        return {
            'inference_cache_count': 0,
            'loaded_models_count': 0,
            'cache_enabled': False,
            'error': str(e)
        }
