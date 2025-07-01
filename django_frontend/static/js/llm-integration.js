/**
 * 大模型API集成JavaScript模块
 * 处理与大模型API的交互、UI更新和错误处理
 */

class LLMIntegration {
    constructor() {
        this.isLoading = false;
        this.apiEndpoint = '/api/llm/analyze/';
        this.historyEndpoint = '/api/llm/history/';
        this.init();
    }

    init() {
        this.bindEvents();
        this.setupCSRF();
    }

    /**
     * 绑定事件监听器
     */
    bindEvents() {
        // 提交按钮点击事件
        $(document).on('click', '.llm-submit-btn', (e) => {
            e.preventDefault();
            this.handleSubmit();
        });

        // 输入框回车事件
        $(document).on('keypress', '.llm-prompt-input', (e) => {
            if (e.which === 13 && e.ctrlKey) {
                e.preventDefault();
                this.handleSubmit();
            }
        });

        // 清除响应按钮
        $(document).on('click', '.llm-clear-btn', (e) => {
            e.preventDefault();
            this.clearResponse();
        });

        // 复制响应按钮
        $(document).on('click', '.llm-copy-btn', (e) => {
            e.preventDefault();
            this.copyResponse();
        });

        // 快捷提示词按钮
        $(document).on('click', '.quick-prompt', (e) => {
            e.preventDefault();
            const prompt = $(e.target).data('prompt');
            this.setPrompt(prompt);
        });
    }

    /**
     * 设置CSRF令牌
     */
    setupCSRF() {
        const csrfToken = $('[name=csrfmiddlewaretoken]').val() || 
                         $('meta[name=csrf-token]').attr('content');
        if (csrfToken) {
            $.ajaxSetup({
                beforeSend: function(xhr, settings) {
                    if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", csrfToken);
                    }
                }
            });
        }
    }

    /**
     * 处理表单提交
     */
    async handleSubmit() {
        if (this.isLoading) return;

        const prompt = $('.llm-prompt-input').val().trim();
        const recordId = this.getRecordId();

        if (!prompt) {
            this.showError('请输入您的问题或需求');
            return;
        }

        if (!recordId) {
            this.showError('无法获取检测记录ID');
            return;
        }

        try {
            this.setLoading(true);
            const response = await this.callLLMAPI(prompt, recordId);
            this.displayResponse(response);
            this.clearInput();
        } catch (error) {
            this.showError(error.message || '请求失败，请稍后重试');
        } finally {
            this.setLoading(false);
        }
    }

    /**
     * 调用大模型API
     */
    async callLLMAPI(prompt, recordId) {
        const response = await $.ajax({
            url: this.apiEndpoint,
            method: 'POST',
            data: {
                prompt: prompt,
                record_id: recordId
            },
            timeout: 30000 // 30秒超时
        });

        if (!response.success) {
            throw new Error(response.error || '服务器返回错误');
        }

        return response;
    }

    /**
     * 设置加载状态
     */
    setLoading(loading) {
        this.isLoading = loading;
        const $submitBtn = $('.llm-submit-btn');
        const $loadingArea = $('.llm-loading');
        const $responseArea = $('.llm-response-area');

        if (loading) {
            $submitBtn.prop('disabled', true).html(
                '<span class="spinner-border spinner-border-sm me-2"></span>分析中...'
            );
            $loadingArea.show();
            $responseArea.hide();
        } else {
            $submitBtn.prop('disabled', false).html(
                '<i class="fas fa-paper-plane me-2"></i>发送分析请求'
            );
            $loadingArea.hide();
            $responseArea.show();
        }
    }

    /**
     * 显示响应结果
     */
    displayResponse(response) {
        const $responseArea = $('.llm-response-area');
        const $responseContent = $('.llm-response-content');
        
        if (response.analysis) {
            $responseContent.text(response.analysis);
            $responseArea.removeClass('d-none').show();
            this.showSuccess('分析完成！');
        } else {
            this.showError('未收到有效的分析结果');
        }
    }

    /**
     * 显示错误信息
     */
    showError(message) {
        const errorHtml = `
            <div class="llm-error alert alert-danger alert-dismissible fade show" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        $('.llm-messages').html(errorHtml);
        setTimeout(() => $('.llm-error').fadeOut(), 5000);
    }

    /**
     * 显示成功信息
     */
    showSuccess(message) {
        const successHtml = `
            <div class="llm-success alert alert-success alert-dismissible fade show" role="alert">
                <i class="fas fa-check-circle me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        $('.llm-messages').html(successHtml);
        setTimeout(() => $('.llm-success').fadeOut(), 3000);
    }

    /**
     * 清除输入框
     */
    clearInput() {
        $('.llm-prompt-input').val('');
    }

    /**
     * 设置提示词到输入框
     */
    setPrompt(prompt) {
        $('.llm-prompt-input').val(prompt).focus();
    }

    /**
     * 清除响应内容
     */
    clearResponse() {
        $('.llm-response-content').text('');
        $('.llm-response-area').hide();
        $('.llm-messages').empty();
    }

    /**
     * 复制响应内容到剪贴板
     */
    async copyResponse() {
        const content = $('.llm-response-content').text();
        if (!content) {
            this.showError('没有可复制的内容');
            return;
        }

        try {
            await navigator.clipboard.writeText(content);
            this.showSuccess('内容已复制到剪贴板');
        } catch (error) {
            // 降级方案
            const textArea = document.createElement('textarea');
            textArea.value = content;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            this.showSuccess('内容已复制到剪贴板');
        }
    }

    /**
     * 获取当前检测记录ID
     */
    getRecordId() {
        // 从URL中提取记录ID
        const pathParts = window.location.pathname.split('/');
        const resultIndex = pathParts.indexOf('result');
        if (resultIndex !== -1 && pathParts[resultIndex + 1]) {
            return parseInt(pathParts[resultIndex + 1]);
        }
        
        // 从数据属性中获取
        const recordId = $('.llm-analysis-section').data('record-id');
        if (recordId) {
            return parseInt(recordId);
        }
        
        return null;
    }
}

// 页面加载完成后初始化
$(document).ready(function() {
    window.llmIntegration = new LLMIntegration();
});

// 导出模块（如果需要）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LLMIntegration;
}
