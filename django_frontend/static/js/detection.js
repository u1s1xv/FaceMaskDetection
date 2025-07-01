/**
 * 口罩检测系统前端JavaScript
 */

// 全局变量
let uploadForm, fileInput, uploadArea, imagePreview, previewImg;
let submitBtn, progressContainer, progressBar, progressText;

// 初始化
$(document).ready(function() {
    initializeElements();
    setupEventListeners();
    setupDragAndDrop();
});

// 初始化DOM元素
function initializeElements() {
    uploadForm = $('#uploadForm');
    fileInput = $('#imageInput');
    uploadArea = $('#uploadArea');
    imagePreview = $('#imagePreview');
    previewImg = $('#previewImg');
    submitBtn = $('#submitBtn');
    progressContainer = $('.progress-container');
    progressBar = $('.progress-bar');
    progressText = $('#progressText');
}

// 设置事件监听器
function setupEventListeners() {
    // 点击上传区域
    uploadArea.on('click', function(e) {
        e.preventDefault();
        fileInput.click();
    });
    
    // 文件选择变化
    fileInput.on('change', function() {
        const file = this.files[0];
        if (file) {
            handleFileSelect(file);
        }
    });
    
    // 表单提交
    uploadForm.on('submit', function(e) {
        if (!validateForm()) {
            e.preventDefault();
            return false;
        }
        
        startProcessing();
    });
    
    // 参数变化时的实时验证
    $('input[type="number"]').on('input', function() {
        validateParameter($(this));
    });
}

// 设置拖拽上传
function setupDragAndDrop() {
    uploadArea.on('dragover', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).addClass('dragover');
    });
    
    uploadArea.on('dragleave', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).removeClass('dragover');
    });
    
    uploadArea.on('drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).removeClass('dragover');
        
        const files = e.originalEvent.dataTransfer.files;
        if (files.length > 0) {
            const file = files[0];
            if (validateFile(file)) {
                fileInput[0].files = files;
                handleFileSelect(file);
            }
        }
    });
}

// 处理文件选择
function handleFileSelect(file) {
    if (!validateFile(file)) {
        return;
    }
    
    previewImage(file);
    updateUploadArea(file);
}

// 验证文件
function validateFile(file) {
    // 检查文件类型
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/bmp'];
    if (!allowedTypes.includes(file.type)) {
        showAlert('请选择有效的图片文件 (JPG, PNG, BMP)', 'danger');
        return false;
    }
    
    // 检查文件大小 (10MB)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
        showAlert('文件大小不能超过 10MB', 'danger');
        return false;
    }
    
    return true;
}

// 图片预览
function previewImage(file) {
    const reader = new FileReader();
    reader.onload = function(e) {
        previewImg.attr('src', e.target.result);
        imagePreview.fadeIn();
    };
    reader.readAsDataURL(file);
}

// 更新上传区域显示
function updateUploadArea(file) {
    const fileName = file.name;
    const fileSize = formatFileSize(file.size);
    
    uploadArea.html(`
        <i class="fas fa-check-circle fa-2x text-success mb-2"></i>
        <h6 class="text-success">文件已选择</h6>
        <p class="mb-1"><strong>${fileName}</strong></p>
        <p class="text-muted small">${fileSize}</p>
        <p class="text-muted small">点击重新选择文件</p>
    `);
}

// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 验证表单
function validateForm() {
    // 检查是否选择了文件
    if (!fileInput[0].files.length) {
        showAlert('请先选择要检测的图片', 'warning');
        return false;
    }
    
    // 验证参数
    const confidence = parseFloat($('#id_confidence_threshold').val());
    const iou = parseFloat($('#id_iou_threshold').val());
    
    if (confidence < 0.1 || confidence > 1.0) {
        showAlert('置信度阈值必须在 0.1 到 1.0 之间', 'warning');
        return false;
    }
    
    if (iou < 0.1 || iou > 1.0) {
        showAlert('IOU阈值必须在 0.1 到 1.0 之间', 'warning');
        return false;
    }
    
    return true;
}

// 验证单个参数
function validateParameter($input) {
    const value = parseFloat($input.val());
    const min = parseFloat($input.attr('min'));
    const max = parseFloat($input.attr('max'));
    
    if (value < min || value > max) {
        $input.addClass('is-invalid');
        return false;
    } else {
        $input.removeClass('is-invalid');
        return true;
    }
}

// 开始处理
function startProcessing() {
    submitBtn.prop('disabled', true)
             .html('<i class="fas fa-spinner fa-spin"></i> 检测中...');
    
    progressContainer.fadeIn();
    
    // 模拟进度条
    simulateProgress();
}

// 模拟进度条
function simulateProgress() {
    let progress = 0;
    const stages = [
        { progress: 20, text: '正在上传图片...' },
        { progress: 40, text: '正在加载AI模型...' },
        { progress: 60, text: '正在进行检测分析...' },
        { progress: 80, text: '正在生成结果...' },
        { progress: 95, text: '即将完成...' }
    ];
    
    let currentStage = 0;
    
    const interval = setInterval(function() {
        if (currentStage < stages.length) {
            const stage = stages[currentStage];
            progress = stage.progress;
            
            progressBar.css('width', progress + '%');
            progressText.text(stage.text);
            
            currentStage++;
        } else {
            clearInterval(interval);
        }
    }, 1000);
    
    // 清理定时器（实际提交后会跳转页面）
    setTimeout(function() {
        clearInterval(interval);
    }, 30000);
}

// 显示警告消息
function showAlert(message, type = 'info') {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    // 移除现有的警告
    $('.alert').remove();
    
    // 添加新警告
    $('main.container').prepend(alertHtml);
    
    // 自动消失
    setTimeout(function() {
        $('.alert').fadeOut();
    }, 5000);
}

// API调用函数
function callDetectionAPI(formData) {
    return $.ajax({
        url: '/api/detect/',
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        timeout: 300000, // 5分钟超时
        xhr: function() {
            const xhr = new window.XMLHttpRequest();
            // 上传进度
            xhr.upload.addEventListener("progress", function(evt) {
                if (evt.lengthComputable) {
                    const percentComplete = (evt.loaded / evt.total) * 100;
                    progressBar.css('width', Math.min(percentComplete, 30) + '%');
                    if (percentComplete < 100) {
                        progressText.text('正在上传图片...');
                    }
                }
            }, false);
            return xhr;
        }
    });
}

// 检查检测状态
function checkDetectionStatus(recordId) {
    return $.get(`/status/${recordId}/`);
}

// 获取检测结果
function getDetectionResult(recordId) {
    return $.get(`/api/result/${recordId}/`);
}

// 工具函数：防抖
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 工具函数：节流
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    }
}

// 增强的用户体验功能
class UIEnhancer {
    constructor() {
        this.init();
    }

    init() {
        this.setupTooltips();
        this.setupLoadingOverlay();
        this.setupKeyboardShortcuts();
        this.setupAutoSave();
        this.setupNetworkStatus();
    }

    // 设置工具提示
    setupTooltips() {
        // 初始化Bootstrap工具提示
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });

        // 动态添加工具提示
        this.addDynamicTooltips();
    }

    addDynamicTooltips() {
        // 为参数输入框添加工具提示
        $('#id_confidence_threshold').attr({
            'data-bs-toggle': 'tooltip',
            'data-bs-placement': 'top',
            'title': '置信度阈值：控制检测的敏感度，值越高越严格'
        });

        $('#id_iou_threshold').attr({
            'data-bs-toggle': 'tooltip',
            'data-bs-placement': 'top',
            'title': 'IOU阈值：控制重叠检测框的合并，值越高合并越少'
        });

        $('#id_image_size').attr({
            'data-bs-toggle': 'tooltip',
            'data-bs-placement': 'top',
            'title': '图像尺寸：处理图像的大小，越大精度越高但速度越慢'
        });
    }

    // 设置加载覆盖层
    setupLoadingOverlay() {
        if (!$('.loading-overlay').length) {
            $('body').append(`
                <div class="loading-overlay" style="display: none;">
                    <div class="loading-content">
                        <div class="spinner-border" role="status">
                            <span class="visually-hidden">加载中...</span>
                        </div>
                        <h5 class="mt-3">处理中...</h5>
                        <p class="text-muted mb-0">请稍候，正在处理您的请求</p>
                    </div>
                </div>
            `);
        }
    }

    showLoadingOverlay(message = '处理中...') {
        $('.loading-overlay .loading-content h5').text(message);
        $('.loading-overlay').fadeIn();
    }

    hideLoadingOverlay() {
        $('.loading-overlay').fadeOut();
    }

    // 设置键盘快捷键
    setupKeyboardShortcuts() {
        $(document).on('keydown', (e) => {
            // Ctrl+U: 上传文件
            if (e.ctrlKey && e.key === 'u') {
                e.preventDefault();
                $('#imageInput').click();
            }

            // Ctrl+Enter: 提交表单
            if (e.ctrlKey && e.key === 'Enter') {
                e.preventDefault();
                if ($('#uploadForm').length) {
                    $('#uploadForm').submit();
                }
            }

            // Esc: 关闭模态框或取消操作
            if (e.key === 'Escape') {
                $('.modal').modal('hide');
                this.hideLoadingOverlay();
            }
        });
    }

    // 设置自动保存参数
    setupAutoSave() {
        const saveParams = debounce(() => {
            const params = {
                confidence: $('#id_confidence_threshold').val(),
                iou: $('#id_iou_threshold').val(),
                imageSize: $('#id_image_size').val(),
                model: $('#id_model_name').val()
            };
            localStorage.setItem('detectionParams', JSON.stringify(params));
        }, 1000);

        // 监听参数变化
        $('input, select').on('change input', saveParams);

        // 页面加载时恢复参数
        this.restoreParams();
    }

    restoreParams() {
        const saved = localStorage.getItem('detectionParams');
        if (saved) {
            try {
                const params = JSON.parse(saved);
                $('#id_confidence_threshold').val(params.confidence);
                $('#id_iou_threshold').val(params.iou);
                $('#id_image_size').val(params.imageSize);
                $('#id_model_name').val(params.model);
            } catch (e) {
                console.warn('无法恢复保存的参数:', e);
            }
        }
    }

    // 网络状态监控
    setupNetworkStatus() {
        window.addEventListener('online', () => {
            this.showNetworkStatus('网络连接已恢复', 'success');
        });

        window.addEventListener('offline', () => {
            this.showNetworkStatus('网络连接已断开', 'danger');
        });
    }

    showNetworkStatus(message, type) {
        const statusHtml = `
            <div class="alert alert-${type} alert-dismissible fade show position-fixed"
                 style="top: 20px; right: 20px; z-index: 9999;" role="alert">
                <i class="fas fa-wifi me-2"></i>${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        $('body').append(statusHtml);
        setTimeout(() => $('.alert').fadeOut(), 3000);
    }
}

// 图片处理工具类
class ImageProcessor {
    static compressImage(file, maxWidth = 1920, quality = 0.8) {
        return new Promise((resolve) => {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            const img = new Image();

            img.onload = () => {
                // 计算新尺寸
                let { width, height } = img;
                if (width > maxWidth) {
                    height = (height * maxWidth) / width;
                    width = maxWidth;
                }

                canvas.width = width;
                canvas.height = height;

                // 绘制压缩后的图片
                ctx.drawImage(img, 0, 0, width, height);

                canvas.toBlob(resolve, 'image/jpeg', quality);
            };

            img.src = URL.createObjectURL(file);
        });
    }

    static getImageInfo(file) {
        return new Promise((resolve) => {
            const img = new Image();
            img.onload = () => {
                resolve({
                    width: img.width,
                    height: img.height,
                    aspectRatio: img.width / img.height,
                    size: file.size,
                    type: file.type
                });
            };
            img.src = URL.createObjectURL(file);
        });
    }
}

// 性能监控类
class PerformanceMonitor {
    constructor() {
        this.startTime = null;
        this.metrics = {};
    }

    start(operation) {
        this.startTime = performance.now();
        this.metrics[operation] = { start: this.startTime };
    }

    end(operation) {
        if (this.metrics[operation]) {
            const endTime = performance.now();
            this.metrics[operation].end = endTime;
            this.metrics[operation].duration = endTime - this.metrics[operation].start;

            console.log(`${operation} 耗时: ${this.metrics[operation].duration.toFixed(2)}ms`);
        }
    }

    getMetrics() {
        return this.metrics;
    }
}

// 初始化增强功能
$(document).ready(function() {
    window.uiEnhancer = new UIEnhancer();
    window.performanceMonitor = new PerformanceMonitor();
});

// 导出函数供其他脚本使用
window.DetectionJS = {
    showAlert,
    callDetectionAPI,
    checkDetectionStatus,
    getDetectionResult,
    formatFileSize,
    validateFile,
    UIEnhancer,
    ImageProcessor,
    PerformanceMonitor
};
