"""
YOLO推理服务模块
"""
import os
import sys
import subprocess
import json
import time
import logging
from pathlib import Path
from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image
import cv2
import numpy as np
import re

logger = logging.getLogger(__name__)




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
