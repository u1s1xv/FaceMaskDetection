#!/usr/bin/env python
"""
测试改进后的PDF生成功能（支持markdown格式）
"""

import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'face_mask_detection.settings')
django.setup()

from detection.pdf_utils import create_pdf_report
from datetime import datetime

def test_markdown_pdf_generation():
    """测试支持markdown的PDF生成功能"""
    print("开始测试支持markdown的PDF生成功能...")
    
    # 模拟检测记录数据
    record_data = {
        'id': 1,
        'upload_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'model_name': 'yolo11n-seg.pt',
        'confidence_threshold': 0.25,
        'total_detections': 5,
        'with_mask_count': 3,
        'without_mask_count': 1,
        'incorrect_mask_count': 1,
    }
    
    # 模拟检测摘要
    detection_summary = {
        'compliance_rate': 60.0
    }
    
    # 模拟包含markdown格式的LLM分析结果
    llm_analysis = """# 口罩检测分析报告

## 检测结果评估

根据本次口罩检测的结果，我们可以看到以下情况：

### 总体情况
- **总检测人数**：5人
- **正确佩戴口罩**：3人
- **未佩戴口罩**：1人  
- **错误佩戴口罩**：1人

### 合规率分析
整体合规率为**60%**，这个数值相对较低，需要引起重视。

## 风险评估

当前检测结果显示存在以下风险：

1. **中等风险**：40%的人员未能正确佩戴口罩
2. **健康隐患**：存在一定的传播风险
3. **管理问题**：需要加强监督和管理

## 改进建议

为了提高口罩佩戴的合规率，建议采取以下措施：

- 加强口罩佩戴的**培训和宣传**
- 设置更多的*提醒标识*
- 定期进行口罩佩戴检查
- 提供正确的口罩佩戴示范

### 具体实施步骤

1. 制定详细的培训计划
2. 安排专人负责监督
3. 建立奖惩机制
4. 定期评估效果

## 总结

本次检测发现了一些口罩佩戴不规范的情况，**建议立即采取相应的改进措施**，以提高整体的防护效果和安全水平。

*注：本报告基于AI智能分析生成，仅供参考。*"""
    
    try:
        # 生成PDF
        pdf_data = create_pdf_report(record_data, detection_summary, llm_analysis)
        
        # 保存到文件
        output_file = 'test_markdown_report.pdf'
        with open(output_file, 'wb') as f:
            f.write(pdf_data)
        
        print(f"✅ 支持markdown的PDF生成成功！")
        print(f"📄 文件保存为: {output_file}")
        print(f"📊 文件大小: {len(pdf_data)} bytes")
        
        # 检查文件是否存在
        if os.path.exists(output_file):
            print(f"✅ 文件验证成功，文件大小: {os.path.getsize(output_file)} bytes")
            print(f"📝 请打开 {output_file} 查看markdown格式是否正确转换")
        else:
            print("❌ 文件验证失败")
            
    except Exception as e:
        print(f"❌ PDF生成失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_markdown_pdf_generation()
