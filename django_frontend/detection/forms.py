"""
表单定义
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.conf import settings
import os
import re
from .models import DetectionRecord, ModelConfig, BatchDetectionSession


class ImageUploadForm(forms.ModelForm):
    """图片上传表单"""

    class Meta:
        model = DetectionRecord
        fields = [
            'original_image',
            'model_name',
            'confidence_threshold',
            'iou_threshold',
            'image_size'
        ]
        widgets = {
            'original_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'model_name': forms.Select(attrs={
                'class': 'form-select'
            }),
            'confidence_threshold': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0.1',
                'max': '1.0',
                'step': '0.05'
            }),
            'iou_threshold': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0.1',
                'max': '1.0',
                'step': '0.05'
            }),
            'image_size': forms.Select(attrs={
                'class': 'form-select'
            }, choices=[
                (320, '320x320 (快速)'),
                (640, '640x640 (标准)'),
                (1280, '1280x1280 (高精度)'),
            ])
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 动态获取实际存在的模型文件
        model_choices = self._get_available_models()
        self.fields['model_name'].widget.choices = model_choices
        
        # 设置字段标签
        self.fields['original_image'].label = '选择图片'
        self.fields['model_name'].label = '检测模型'
        self.fields['confidence_threshold'].label = '置信度阈值'
        self.fields['iou_threshold'].label = 'IOU阈值'
        self.fields['image_size'].label = '图像尺寸'
        
        # 设置帮助文本
        self.fields['confidence_threshold'].help_text = '检测置信度阈值，越高越严格'
        self.fields['iou_threshold'].help_text = '重叠度阈值，用于去除重复检测'
        self.fields['image_size'].help_text = '输入图像尺寸，越大精度越高但速度越慢'

    def _get_available_models(self):
        """获取实际存在的模型文件"""
        from django.conf import settings
        from pathlib import Path

        model_choices = []
        models_dir = settings.YOLO_MODELS_DIR

        if models_dir.exists():
            # 扫描checkpoints目录下的.pt文件
            for model_file in models_dir.glob('*.pt'):
                model_name = model_file.name

                # 尝试从数据库获取模型描述
                try:
                    from .models import ModelConfig
                    model_config = ModelConfig.objects.filter(
                        name=model_name,
                        is_active=True
                    ).first()

                    if model_config:
                        description = model_config.description
                    else:
                        # 根据文件名生成描述
                        description = self._generate_model_description(model_name)

                    model_choices.append((model_name, f"{model_name} - {description}"))

                except Exception:
                    # 如果数据库查询失败，使用默认描述
                    description = self._generate_model_description(model_name)
                    model_choices.append((model_name, f"{model_name} - {description}"))

        # 如果没有找到任何模型文件，提供默认选项
        if not model_choices:
            model_choices = [
                ('yolo11n-seg.pt', 'YOLO11n-seg.pt - 默认模型（请确保文件存在）'),
            ]

        # 按文件名排序
        model_choices.sort(key=lambda x: x[0])
        return model_choices

    def _generate_model_description(self, model_name):
        """根据模型文件名生成描述"""
        name_lower = model_name.lower()

        if 'yolo11n' in name_lower:
            return 'YOLO11 Nano - 快速检测'
        elif 'yolo11s' in name_lower:
            return 'YOLO11 Small - 平衡性能'
        elif 'yolo11m' in name_lower:
            return 'YOLO11 Medium - 高精度'
        elif 'yolo11l' in name_lower:
            return 'YOLO11 Large - 超高精度'
        elif 'yolo11x' in name_lower:
            return 'YOLO11 XLarge - 最高精度'
        elif 'seg' in name_lower:
            return '分割模型'
        elif 'det' in name_lower:
            return '检测模型'
        else:
            return '自定义模型'
    
    def clean_original_image(self):
        """验证上传的图片"""
        image = self.cleaned_data.get('original_image')
        
        if not image:
            raise ValidationError('请选择要上传的图片')
        
        # 检查文件大小
        if image.size > settings.MAX_IMAGE_SIZE:
            raise ValidationError(
                f'图片文件过大，最大支持 {settings.MAX_IMAGE_SIZE // (1024*1024)}MB'
            )
        
        # 检查文件扩展名
        ext = os.path.splitext(image.name)[1].lower()
        if ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
            raise ValidationError(
                f'不支持的图片格式，支持的格式: {", ".join(settings.ALLOWED_IMAGE_EXTENSIONS)}'
            )
        
        return image
    
    def clean_confidence_threshold(self):
        """验证置信度阈值"""
        confidence = self.cleaned_data.get('confidence_threshold')
        if confidence is not None and (confidence < 0.1 or confidence > 1.0):
            raise ValidationError('置信度阈值必须在0.1到1.0之间')
        return confidence
    
    def clean_iou_threshold(self):
        """验证IOU阈值"""
        iou = self.cleaned_data.get('iou_threshold')
        if iou is not None and (iou < 0.1 or iou > 1.0):
            raise ValidationError('IOU阈值必须在0.1到1.0之间')
        return iou

    def clean_model_name(self):
        """验证模型文件是否存在"""
        model_name = self.cleaned_data.get('model_name')
        if model_name:
            # 检查模型文件是否实际存在
            from django.conf import settings
            model_path = settings.YOLO_MODELS_DIR / model_name
            if not model_path.exists():
                raise ValidationError(f'模型文件不存在: {model_name}')
        return model_name


class DetectionParametersForm(forms.Form):
    """检测参数调整表单"""
    
    model_name = forms.ChoiceField(
        label='检测模型',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    confidence_threshold = forms.FloatField(
        label='置信度阈值',
        initial=0.25,
        min_value=0.1,
        max_value=1.0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.05'
        })
    )
    iou_threshold = forms.FloatField(
        label='IOU阈值',
        initial=0.45,
        min_value=0.1,
        max_value=1.0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.05'
        })
    )
    image_size = forms.ChoiceField(
        label='图像尺寸',
        choices=[
            (320, '320x320 (快速)'),
            (640, '640x640 (标准)'),
            (1280, '1280x1280 (高精度)'),
        ],
        initial=640,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 动态获取实际存在的模型文件
        model_choices = self._get_available_models()
        self.fields['model_name'].choices = model_choices

    def _get_available_models(self):
        """获取实际存在的模型文件"""
        from django.conf import settings
        from pathlib import Path

        model_choices = []
        models_dir = settings.YOLO_MODELS_DIR

        if models_dir.exists():
            # 扫描checkpoints目录下的.pt文件
            for model_file in models_dir.glob('*.pt'):
                model_name = model_file.name
                model_choices.append((model_name, model_name))

        # 如果没有找到任何模型文件，提供默认选项
        if not model_choices:
            model_choices = [
                ('yolo11n-seg.pt', 'yolo11n-seg.pt（请确保文件存在）'),
            ]

        # 按文件名排序
        model_choices.sort(key=lambda x: x[0])
        return model_choices


class CustomUserCreationForm(UserCreationForm):
    """自定义用户注册表单"""

    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': '邮箱（可选）'
        }),
        help_text='可选，用于后续功能扩展'
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '用户名'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 自定义字段标签和帮助文本
        self.fields['username'].label = '用户名'
        self.fields['username'].help_text = '只允许数字和英文字母组合，3-150个字符'

        self.fields['password1'].label = '密码'
        self.fields['password1'].help_text = '至少6位，支持英文字母、数字、特殊符号'
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': '密码'
        })

        self.fields['password2'].label = '确认密码'
        self.fields['password2'].help_text = '请再次输入密码进行确认'
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': '确认密码'
        })

    def clean_username(self):
        """验证用户名格式"""
        username = self.cleaned_data.get('username')

        if not username:
            raise ValidationError('用户名不能为空')

        # 检查长度
        if len(username) < 3:
            raise ValidationError('用户名至少需要3个字符')

        if len(username) > 150:
            raise ValidationError('用户名不能超过150个字符')

        # 检查字符组成：只允许数字和英文字母
        if not re.match(r'^[a-zA-Z0-9]+$', username):
            raise ValidationError('用户名只能包含英文字母和数字')

        # 检查是否已存在
        if User.objects.filter(username=username).exists():
            raise ValidationError('该用户名已被使用')

        return username

    def clean_password1(self):
        """验证密码格式"""
        password1 = self.cleaned_data.get('password1')

        if not password1:
            raise ValidationError('密码不能为空')

        # 检查长度
        if len(password1) < 6:
            raise ValidationError('密码至少需要6个字符')

        # 检查字符组成：允许英文字母、数字、特殊符号
        if not re.match(r'^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]+$', password1):
            raise ValidationError('密码只能包含英文字母、数字和常见特殊符号')

        return password1

    def clean_email(self):
        """验证邮箱格式"""
        email = self.cleaned_data.get('email')

        if email:
            # 检查邮箱是否已被使用
            if User.objects.filter(email=email).exists():
                raise ValidationError('该邮箱已被使用')

        return email


class CustomLoginForm(forms.Form):
    """自定义登录表单"""

    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '用户名',
            'autofocus': True
        }),
        label='用户名'
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '密码'
        }),
        label='密码'
    )

    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='记住我'
    )

    def clean_username(self):
        """清理用户名输入"""
        username = self.cleaned_data.get('username', '').strip()

        if not username:
            raise ValidationError('请输入用户名')

        # 基本格式验证
        if not re.match(r'^[a-zA-Z0-9]+$', username):
            raise ValidationError('用户名格式不正确')

        return username

    def clean_password(self):
        """清理密码输入"""
        password = self.cleaned_data.get('password', '')

        if not password:
            raise ValidationError('请输入密码')

        return password


class BatchDetectionForm(forms.Form):
    """批量检测表单"""

    # 会话名称
    session_name = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '批量检测会话名称（可选）'
        }),
        label='会话名称',
        help_text='为这次批量检测起一个名称，便于后续查找'
    )

    # 检测参数（与单张检测保持一致）
    model_name = forms.ChoiceField(
        label='检测模型',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    confidence_threshold = forms.FloatField(
        label='置信度阈值',
        initial=0.25,
        min_value=0.1,
        max_value=1.0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0.1',
            'max': '1.0',
            'step': '0.05'
        }),
        help_text='检测结果的可信程度，值越高越严格'
    )

    iou_threshold = forms.FloatField(
        label='IOU阈值',
        initial=0.45,
        min_value=0.1,
        max_value=1.0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0.1',
            'max': '1.0',
            'step': '0.05'
        }),
        help_text='重叠检测框的过滤阈值'
    )

    image_size = forms.ChoiceField(
        label='图像尺寸',
        choices=[
            (320, '320x320 (快速)'),
            (640, '640x640 (标准)'),
            (1280, '1280x1280 (高精度)'),
        ],
        initial=640,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 动态加载可用模型 - 使用与单张检测相同的逻辑
        model_choices = self._get_available_models()
        self.fields['model_name'].choices = model_choices

    def _get_available_models(self):
        """获取实际存在的模型文件 - 与单张检测保持一致"""
        from django.conf import settings
        from pathlib import Path

        model_choices = []
        models_dir = settings.YOLO_MODELS_DIR  # 指向 yoloserver/models/checkpoints

        if models_dir.exists():
            # 扫描checkpoints目录下的.pt文件
            for model_file in models_dir.glob('*.pt'):
                model_name = model_file.name

                # 尝试从数据库获取模型描述
                try:
                    model_config = ModelConfig.objects.filter(
                        name=model_name,
                        is_active=True
                    ).first()

                    if model_config:
                        description = model_config.description
                    else:
                        # 根据文件名生成描述
                        description = self._generate_model_description(model_name)

                    model_choices.append((model_name, f"{model_name} - {description}"))

                except Exception:
                    # 如果数据库查询失败，使用默认描述
                    description = self._generate_model_description(model_name)
                    model_choices.append((model_name, f"{model_name} - {description}"))

        # 如果没有找到任何模型文件，提供默认选项
        if not model_choices:
            model_choices = [
                ('yolo11n-seg.pt', 'YOLO11n-seg.pt - 默认模型（请确保文件存在）'),
            ]

        # 按文件名排序
        model_choices.sort(key=lambda x: x[0])
        return model_choices

    def _generate_model_description(self, model_name):
        """根据模型文件名生成描述 - 与单张检测保持一致"""
        name_lower = model_name.lower()

        if 'yolo11n' in name_lower:
            return 'YOLO11 Nano - 快速检测'
        elif 'yolo11s' in name_lower:
            return 'YOLO11 Small - 平衡性能'
        elif 'yolo11m' in name_lower:
            return 'YOLO11 Medium - 高精度'
        elif 'yolo11l' in name_lower:
            return 'YOLO11 Large - 超高精度'
        elif 'yolo11x' in name_lower:
            return 'YOLO11 XLarge - 最高精度'
        elif 'seg' in name_lower:
            return '分割模型'
        elif 'det' in name_lower:
            return '检测模型'
        else:
            return '自定义模型'

    def clean_session_name(self):
        """验证会话名称"""
        session_name = self.cleaned_data.get('session_name', '').strip()

        # 如果没有提供名称，生成默认名称
        if not session_name:
            from django.utils import timezone
            session_name = f'批量检测_{timezone.now().strftime("%Y%m%d_%H%M%S")}'

        return session_name

    def clean_confidence_threshold(self):
        """验证置信度阈值"""
        confidence = self.cleaned_data.get('confidence_threshold')
        if confidence is not None and (confidence < 0.1 or confidence > 1.0):
            raise ValidationError('置信度阈值必须在0.1到1.0之间')
        return confidence

    def clean_iou_threshold(self):
        """验证IOU阈值"""
        iou = self.cleaned_data.get('iou_threshold')
        if iou is not None and (iou < 0.1 or iou > 1.0):
            raise ValidationError('IOU阈值必须在0.1到1.0之间')
        return iou
