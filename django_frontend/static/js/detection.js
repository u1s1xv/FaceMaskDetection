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

// 导出函数供其他脚本使用
window.DetectionJS = {
    showAlert,
    callDetectionAPI,
    checkDetectionStatus,
    getDetectionResult,
    formatFileSize,
    validateFile
};
