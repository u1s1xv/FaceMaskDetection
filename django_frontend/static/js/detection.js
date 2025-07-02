/**
 * 口罩检测系统前端JavaScript
 */

// 全局变量
let uploadForm, fileInput, uploadArea, imagePreview, previewContainer;
let singlePreview, multiplePreview, previewImg;
let submitBtn, progressContainer, progressBar, progressText;
let selectedFiles = [];

// 初始化
$(document).ready(function() {
    initializeElements();
    setupEventListeners();
    setupDragAndDrop();
});

// 初始化DOM元素
function initializeElements() {
    uploadForm = $('#uploadForm');
    // 使用Django默认生成的ID
    fileInput = $('#id_original_image');
    uploadArea = $('#uploadArea');
    imagePreview = $('#imagePreview');
    singlePreview = $('#singlePreview');
    multiplePreview = $('#multiplePreview');
    previewContainer = $('#previewContainer');
    previewImg = $('#previewImg');
    submitBtn = $('#submitBtn');
    progressContainer = $('.progress-container');
    progressBar = $('.progress-bar');
    progressText = $('#progressText');

    // 验证关键元素是否存在
    if (!fileInput || fileInput.length === 0) {
        console.error('文件输入框未找到！');
        console.log('尝试查找的ID: #id_original_image');
        console.log('页面中的所有input元素:', $('input'));
    }

    if (!uploadArea || uploadArea.length === 0) {
        console.error('上传区域未找到！');
    }
}

// 设置事件监听器
function setupEventListeners() {
    // 注意：点击事件现在在模板中处理，避免重复绑定
    
    // 文件选择变化
    fileInput.on('change', function() {
        const files = Array.from(this.files);
        if (files.length > 0) {
            if (files.length === 1) {
                // 单张图片处理
                handleSingleFileSelect(files[0]);
            } else {
                // 多张图片处理
                handleMultipleFileSelect(files);
            }
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

        const files = Array.from(e.originalEvent.dataTransfer.files);
        if (files.length > 0) {
            // 验证所有文件
            const validFiles = files.filter(file => validateFile(file));
            if (validFiles.length > 0) {
                // 创建新的FileList对象
                const dt = new DataTransfer();
                validFiles.forEach(file => dt.items.add(file));
                fileInput[0].files = dt.files;

                // 智能处理单张或多张图片
                if (validFiles.length === 1) {
                    handleSingleFileSelect(validFiles[0]);
                } else {
                    handleMultipleFileSelect(validFiles);
                }
            }
        }
    });
}

// 处理单文件选择
function handleSingleFileSelect(file) {
    if (!validateFile(file)) {
        return;
    }

    selectedFiles = [file]; // 保存为数组以保持一致性
    previewSingleImage(file);
    updateUploadAreaForSingle(file);
}

// 处理文件选择（保持向后兼容）
function handleFileSelect(file) {
    handleSingleFileSelect(file);
}

// 处理多文件选择
function handleMultipleFileSelect(files) {
    selectedFiles = [];
    const validFiles = [];

    // 验证所有文件
    for (let file of files) {
        if (validateFile(file)) {
            validFiles.push(file);
        }
    }

    if (validFiles.length === 0) {
        return;
    }

    // 限制最多10张图片
    if (validFiles.length > 10) {
        showAlert('最多只能同时上传10张图片', 'warning');
        selectedFiles = validFiles.slice(0, 10);
    } else {
        selectedFiles = validFiles;
    }

    previewMultipleImages(selectedFiles);
    updateUploadAreaForMultiple(selectedFiles);
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

// 单图片预览
function previewSingleImage(file) {
    const reader = new FileReader();
    reader.onload = function(e) {
        previewImg.attr('src', e.target.result);
        singlePreview.show();
        multiplePreview.hide();
        imagePreview.fadeIn();
    };
    reader.readAsDataURL(file);
}

// 图片预览（保持向后兼容）
function previewImage(file) {
    previewSingleImage(file);
}

// 多图片预览
function previewMultipleImages(files) {
    previewContainer.empty();
    singlePreview.hide();
    multiplePreview.show();

    files.forEach((file, index) => {
        const reader = new FileReader();
        reader.onload = function(e) {
            const previewHtml = `
                <div class="col-md-3 col-sm-4 col-6 mb-3">
                    <div class="position-relative">
                        <img src="${e.target.result}" class="img-fluid rounded preview-thumbnail"
                             alt="预览图片 ${index + 1}" style="height: 150px; object-fit: cover; width: 100%;">
                        <button type="button" class="btn btn-danger btn-sm position-absolute top-0 end-0 m-1 remove-image"
                                data-index="${index}" style="padding: 2px 6px; font-size: 12px;">
                            <i class="fas fa-times"></i>
                        </button>
                        <div class="text-center mt-1">
                            <small class="text-muted">${file.name}</small><br>
                            <small class="text-muted">${formatFileSize(file.size)}</small>
                        </div>
                    </div>
                </div>
            `;
            previewContainer.append(previewHtml);
        };
        reader.readAsDataURL(file);
    });

    // 更新文件计数
    $('#fileCount').text(files.length);
    imagePreview.fadeIn();

    // 绑定删除按钮事件
    $(document).off('click', '.remove-image').on('click', '.remove-image', function() {
        const index = parseInt($(this).data('index'));
        removeImageFromSelection(index);
    });
}

// 更新单文件上传区域显示
function updateUploadAreaForSingle(file) {
    const fileName = file.name;
    const fileSize = formatFileSize(file.size);

    uploadArea.html(`
        <i class="fas fa-check-circle fa-2x text-success mb-2"></i>
        <h6 class="text-success">已选择 1 张图片</h6>
        <p class="mb-1"><strong>${fileName}</strong></p>
        <p class="text-muted small">${fileSize}</p>
        <p class="text-muted small">点击重新选择文件或拖拽多张图片</p>
    `);
}

// 更新上传区域显示（保持向后兼容）
function updateUploadArea(file) {
    updateUploadAreaForSingle(file);
}

// 更新多文件上传区域显示
function updateUploadAreaForMultiple(files) {
    const fileCount = files.length;
    const totalSize = files.reduce((sum, file) => sum + file.size, 0);

    uploadArea.html(`
        <i class="fas fa-check-circle fa-2x text-success mb-2"></i>
        <h6 class="text-success">已选择 ${fileCount} 张图片</h6>
        <p class="text-muted small">总大小: ${formatFileSize(totalSize)}</p>
        <p class="text-muted small">点击重新选择文件</p>
    `);
}

// 从选择中移除图片
function removeImageFromSelection(index) {
    selectedFiles.splice(index, 1);

    if (selectedFiles.length === 0) {
        // 重置上传区域
        resetUploadArea();
        imagePreview.fadeOut();
    } else if (selectedFiles.length === 1) {
        // 切换到单图片模式
        const dt = new DataTransfer();
        selectedFiles.forEach(file => dt.items.add(file));
        fileInput[0].files = dt.files;

        handleSingleFileSelect(selectedFiles[0]);
    } else {
        // 继续多图片模式
        const dt = new DataTransfer();
        selectedFiles.forEach(file => dt.items.add(file));
        fileInput[0].files = dt.files;

        previewMultipleImages(selectedFiles);
        updateUploadAreaForMultiple(selectedFiles);
    }
}

// 重置上传区域
function resetUploadArea() {
    selectedFiles = [];
    singlePreview.hide();
    multiplePreview.hide();
    uploadArea.html(`
        <i class="fas fa-cloud-upload-alt fa-3x text-muted mb-3"></i>
        <h5>拖拽图片到此处或点击选择文件</h5>
        <p class="text-muted">支持 JPG, PNG, JPEG, BMP 格式，最大 10MB，支持单张或多张图片上传</p>
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
