"""
PDF生成工具模块
用于生成口罩检测AI分析报告的PDF文件
"""

import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import re


def process_markdown_formatting(text):
    """
    处理markdown格式标记，转换为ReportLab支持的HTML标签

    Args:
        text: 包含markdown格式的文本

    Returns:
        str: 转换后的HTML格式文本
    """
    if not text:
        return text

    # 处理粗体 **text** -> <b>text</b>
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)

    # 处理斜体 *text* -> <i>text</i>
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)

    # 处理行内代码 `code` -> <font name="Courier">code</font>
    text = re.sub(r'`(.*?)`', r'<font name="Courier">\1</font>', text)

    return text


def format_markdown_for_pdf(markdown_text, chinese_font, styles):
    """
    将markdown文本转换为PDF格式的元素列表

    Args:
        markdown_text: 原始markdown文本
        chinese_font: 中文字体名称
        styles: ReportLab样式表

    Returns:
        list: PDF元素列表
    """
    elements = []

    # 创建不同级别的样式
    h1_style = ParagraphStyle(
        'MarkdownH1',
        parent=styles['Heading1'],
        fontName=chinese_font,
        fontSize=16,
        spaceAfter=12,
        spaceBefore=16,
        textColor=colors.darkblue,
        alignment=TA_LEFT
    )

    h2_style = ParagraphStyle(
        'MarkdownH2',
        parent=styles['Heading2'],
        fontName=chinese_font,
        fontSize=14,
        spaceAfter=10,
        spaceBefore=14,
        textColor=colors.darkblue,
        alignment=TA_LEFT
    )

    h3_style = ParagraphStyle(
        'MarkdownH3',
        parent=styles['Heading3'],
        fontName=chinese_font,
        fontSize=12,
        spaceAfter=8,
        spaceBefore=12,
        textColor=colors.darkblue,
        alignment=TA_LEFT
    )

    body_style = ParagraphStyle(
        'MarkdownBody',
        parent=styles['Normal'],
        fontName=chinese_font,
        fontSize=10,
        spaceAfter=6,
        alignment=TA_JUSTIFY,
        leading=14
    )

    list_style = ParagraphStyle(
        'MarkdownList',
        parent=styles['Normal'],
        fontName=chinese_font,
        fontSize=10,
        spaceAfter=4,
        leftIndent=20,
        alignment=TA_LEFT,
        leading=14
    )

    # 按行处理markdown文本
    lines = markdown_text.split('\n')
    current_paragraph = []

    for line in lines:
        line = line.strip()

        if not line:
            # 空行，结束当前段落
            if current_paragraph:
                para_text = ' '.join(current_paragraph)
                # 处理粗体和斜体
                para_text = process_markdown_formatting(para_text)
                elements.append(Paragraph(para_text, body_style))
                current_paragraph = []
            elements.append(Spacer(1, 6))
            continue

        # 处理标题
        if line.startswith('### '):
            if current_paragraph:
                para_text = ' '.join(current_paragraph)
                para_text = process_markdown_formatting(para_text)
                elements.append(Paragraph(para_text, body_style))
                current_paragraph = []
            title_text = process_markdown_formatting(line[4:])
            elements.append(Paragraph(title_text, h3_style))
            continue
        elif line.startswith('## '):
            if current_paragraph:
                para_text = ' '.join(current_paragraph)
                para_text = process_markdown_formatting(para_text)
                elements.append(Paragraph(para_text, body_style))
                current_paragraph = []
            title_text = process_markdown_formatting(line[3:])
            elements.append(Paragraph(title_text, h2_style))
            continue
        elif line.startswith('# '):
            if current_paragraph:
                para_text = ' '.join(current_paragraph)
                para_text = process_markdown_formatting(para_text)
                elements.append(Paragraph(para_text, body_style))
                current_paragraph = []
            title_text = process_markdown_formatting(line[2:])
            elements.append(Paragraph(title_text, h1_style))
            continue

        # 处理列表项
        if line.startswith('- ') or line.startswith('* '):
            if current_paragraph:
                para_text = ' '.join(current_paragraph)
                para_text = process_markdown_formatting(para_text)
                elements.append(Paragraph(para_text, body_style))
                current_paragraph = []
            list_text = '• ' + line[2:]
            list_text = process_markdown_formatting(list_text)
            elements.append(Paragraph(list_text, list_style))
            continue

        # 处理数字列表
        if re.match(r'^\d+\. ', line):
            if current_paragraph:
                para_text = ' '.join(current_paragraph)
                para_text = process_markdown_formatting(para_text)
                elements.append(Paragraph(para_text, body_style))
                current_paragraph = []
            list_text = process_markdown_formatting(line)
            elements.append(Paragraph(list_text, list_style))
            continue

        # 普通文本行，添加到当前段落
        current_paragraph.append(line)

    # 处理最后的段落
    if current_paragraph:
        para_text = ' '.join(current_paragraph)
        para_text = process_markdown_formatting(para_text)
        elements.append(Paragraph(para_text, body_style))

    return elements


def register_chinese_font():
    """注册中文字体"""
    try:
        # 尝试注册系统中的中文字体
        font_paths = [
            'C:/Windows/Fonts/simhei.ttf',  # 黑体
            'C:/Windows/Fonts/simsun.ttc',  # 宋体
            'C:/Windows/Fonts/msyh.ttc',    # 微软雅黑
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                return 'ChineseFont'
        
        # 如果没有找到系统字体，使用默认字体
        return 'Helvetica'
    except Exception:
        return 'Helvetica'


def create_pdf_report(record_data, detection_summary, llm_analysis):
    """
    创建PDF分析报告
    
    Args:
        record_data: 检测记录数据
        detection_summary: 检测结果摘要
        llm_analysis: LLM分析结果
    
    Returns:
        bytes: PDF文件的二进制数据
    """
    buffer = io.BytesIO()
    
    # 创建PDF文档
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18
    )
    
    # 注册中文字体
    chinese_font = register_chinese_font()
    
    # 创建样式
    styles = getSampleStyleSheet()
    
    # 标题样式
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=chinese_font,
        fontSize=18,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue
    )
    
    # 章节标题样式
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontName=chinese_font,
        fontSize=14,
        spaceAfter=12,
        spaceBefore=20,
        textColor=colors.darkblue
    )
    
    # 正文样式
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontName=chinese_font,
        fontSize=10,
        spaceAfter=6,
        alignment=TA_JUSTIFY,
        leading=14
    )
    
    # 构建PDF内容
    story = []
    
    # 标题
    story.append(Paragraph("口罩检测AI分析报告", title_style))
    story.append(Spacer(1, 20))
    
    # 基本信息表格
    basic_info_data = [
        ['检测记录ID', str(record_data.get('id', 'N/A'))],
        ['检测时间', record_data.get('upload_time', 'N/A')],
        ['使用模型', record_data.get('model_name', 'N/A')],
        ['置信度阈值', str(record_data.get('confidence_threshold', 'N/A'))],
        ['报告生成时间', datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
    ]
    
    basic_info_table = Table(basic_info_data, colWidths=[2*inch, 3*inch])
    basic_info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), chinese_font),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(Paragraph("基本信息", heading_style))
    story.append(basic_info_table)
    story.append(Spacer(1, 20))
    
    # 检测结果统计
    story.append(Paragraph("检测结果统计", heading_style))
    
    detection_data = [
        ['检测项目', '数量', '占比'],
        ['总检测数量', str(record_data.get('total_detections', 0)), '100%'],
        ['正确佩戴口罩', str(record_data.get('with_mask_count', 0)), 
         f"{(record_data.get('with_mask_count', 0) / max(record_data.get('total_detections', 1), 1) * 100):.1f}%"],
        ['未佩戴口罩', str(record_data.get('without_mask_count', 0)), 
         f"{(record_data.get('without_mask_count', 0) / max(record_data.get('total_detections', 1), 1) * 100):.1f}%"],
        ['错误佩戴口罩', str(record_data.get('incorrect_mask_count', 0)), 
         f"{(record_data.get('incorrect_mask_count', 0) / max(record_data.get('total_detections', 1), 1) * 100):.1f}%"],
        ['整体合规率', f"{detection_summary.get('compliance_rate', 0):.1f}%", '']
    ]
    
    detection_table = Table(detection_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
    detection_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), chinese_font),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(detection_table)
    story.append(Spacer(1, 20))
    
    # AI智能分析
    story.append(Paragraph("AI智能分析", heading_style))

    # 处理LLM分析内容，保留原始markdown格式并转换为PDF格式
    formatted_analysis = format_markdown_for_pdf(llm_analysis, chinese_font, styles)

    # 添加格式化后的内容到PDF
    for element in formatted_analysis:
        story.append(element)
    
    story.append(Spacer(1, 20))
    
    # 页脚信息
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontName=chinese_font,
        fontSize=8,
        alignment=TA_CENTER,
        textColor=colors.grey
    )
    
    story.append(Paragraph("本报告由口罩检测AI系统自动生成", footer_style))
    
    # 构建PDF
    doc.build(story)
    
    # 获取PDF数据
    pdf_data = buffer.getvalue()
    buffer.close()
    
    return pdf_data
