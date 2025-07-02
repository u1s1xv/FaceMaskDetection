"""
PDF生成服务
用于生成包含检测结果和LLM分析的PDF报告
"""
import os
import io
from datetime import datetime
from django.conf import settings
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import logging
import re

logger = logging.getLogger(__name__)


class PDFReportService:
    """PDF报告生成服务"""
    
    def __init__(self):
        self.setup_fonts()
        self.styles = self.create_styles()
    
    def setup_fonts(self):
        """设置中文字体"""
        try:
            # 尝试注册中文字体
            font_paths = [
                # Windows系统字体路径
                'C:/Windows/Fonts/simhei.ttf',
                'C:/Windows/Fonts/simsun.ttc',
                'C:/Windows/Fonts/msyh.ttc',
                # Linux系统字体路径
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                '/System/Library/Fonts/PingFang.ttc',  # macOS
            ]
            
            font_registered = False
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont('SimHei', font_path))
                        font_registered = True
                        logger.info(f"成功注册字体: {font_path}")
                        break
                    except Exception as e:
                        logger.warning(f"注册字体失败 {font_path}: {str(e)}")
                        continue
            
            if not font_registered:
                logger.warning("未找到中文字体，将使用默认字体")
                
        except Exception as e:
            logger.error(f"字体设置失败: {str(e)}")
    
    def create_styles(self):
        """创建样式"""
        styles = getSampleStyleSheet()
        
        # 尝试使用中文字体，如果失败则使用默认字体
        try:
            font_name = 'SimHei'
            # 测试字体是否可用
            pdfmetrics.getFont(font_name)
        except:
            font_name = 'Helvetica'
            logger.warning("使用默认字体 Helvetica")
        
        # 标题样式
        styles.add(ParagraphStyle(
            name='ChineseTitle',
            parent=styles['Title'],
            fontName=font_name,
            fontSize=18,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        # 副标题样式
        styles.add(ParagraphStyle(
            name='ChineseHeading',
            parent=styles['Heading1'],
            fontName=font_name,
            fontSize=14,
            spaceAfter=12,
            spaceBefore=12,
            textColor=colors.darkblue
        ))
        
        # 正文样式
        styles.add(ParagraphStyle(
            name='ChineseNormal',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=10,
            spaceAfter=6,
            alignment=TA_JUSTIFY
        ))
        
        # 表格标题样式
        styles.add(ParagraphStyle(
            name='TableHeader',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=10,
            alignment=TA_CENTER,
            textColor=colors.white
        ))

        # 列表项样式
        styles.add(ParagraphStyle(
            name='ChineseListItem',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=10,
            spaceAfter=4,
            leftIndent=20,
            bulletIndent=10
        ))

        # 二级列表项样式
        styles.add(ParagraphStyle(
            name='ChineseListItem2',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=10,
            spaceAfter=4,
            leftIndent=40,
            bulletIndent=30
        ))

        # 子标题样式
        styles.add(ParagraphStyle(
            name='ChineseSubHeading',
            parent=styles['Heading2'],
            fontName=font_name,
            fontSize=12,
            spaceAfter=8,
            spaceBefore=8,
            textColor=colors.darkblue
        ))

        # 四级标题样式
        styles.add(ParagraphStyle(
            name='ChineseSubHeading2',
            parent=styles['Heading3'],
            fontName=font_name,
            fontSize=11,
            spaceAfter=6,
            spaceBefore=6,
            textColor=colors.darkblue
        ))

        # 强调文本样式
        styles.add(ParagraphStyle(
            name='ChineseBold',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=10,
            spaceAfter=6
        ))

        # 保存字体名称供后续使用
        self.font_name = font_name
        
        return styles
    
    def generate_llm_analysis_pdf(self, record, llm_content, model_used=None):
        """生成LLM分析PDF报告"""
        try:
            # 创建PDF缓冲区
            buffer = io.BytesIO()
            
            # 创建PDF文档
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            # 构建PDF内容
            story = []
            
            # 添加标题
            title = Paragraph("口罩检测AI分析报告", self.styles['ChineseTitle'])
            story.append(title)
            story.append(Spacer(1, 20))
            
            # 添加报告信息
            report_info = self._create_report_info(record, model_used)
            story.extend(report_info)
            story.append(Spacer(1, 20))
            
            # 添加图片对比
            if record.original_image and record.result_image:
                image_section = self._create_image_comparison(record)
                story.extend(image_section)
                story.append(Spacer(1, 20))
            
            # 添加检测结果表格
            detection_table = self._create_detection_table(record)
            story.extend(detection_table)
            story.append(Spacer(1, 20))
            
            # 添加LLM分析结果
            llm_section = self._create_llm_analysis_section(llm_content)
            story.extend(llm_section)
            
            # 生成PDF
            doc.build(story)
            
            # 获取PDF数据
            pdf_data = buffer.getvalue()
            buffer.close()
            
            return pdf_data
            
        except Exception as e:
            logger.error(f"PDF生成失败: {str(e)}")
            raise RuntimeError(f"PDF生成失败: {str(e)}")
    
    def _create_report_info(self, record, model_used):
        """创建报告信息部分"""
        info_data = [
            ['报告编号', f'MASK-{record.id:06d}'],
            ['生成时间', datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')],
            ['检测时间', record.upload_time.strftime('%Y年%m月%d日 %H:%M:%S')],
            ['使用模型', record.model_name],
            ['AI分析模型', model_used or '未指定'],
            ['置信度阈值', f'{record.confidence_threshold:.2f}'],
            ['处理时间', f'{record.processing_time:.2f}秒' if record.processing_time else '未知']
        ]
        
        info_table = Table(info_data, colWidths=[4*cm, 8*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.darkblue),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), self.font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        return [
            Paragraph("报告信息", self.styles['ChineseHeading']),
            info_table
        ]
    
    def _create_image_comparison(self, record):
        """创建图片对比部分"""
        try:
            elements = []
            elements.append(Paragraph("图像对比", self.styles['ChineseHeading']))
            
            # 创建图片表格
            image_data = []
            image_row = []
            
            # 原始图片
            if record.original_image and os.path.exists(record.original_image.path):
                try:
                    original_img = Image(record.original_image.path, width=7*cm, height=5*cm)
                    image_row.append(original_img)
                except Exception as e:
                    logger.warning(f"无法加载原始图片: {str(e)}")
                    image_row.append(Paragraph("原始图片\n(加载失败)", self.styles['ChineseNormal']))
            else:
                image_row.append(Paragraph("原始图片\n(不可用)", self.styles['ChineseNormal']))
            
            # 检测结果图片
            if record.result_image and os.path.exists(record.result_image.path):
                try:
                    result_img = Image(record.result_image.path, width=7*cm, height=5*cm)
                    image_row.append(result_img)
                except Exception as e:
                    logger.warning(f"无法加载结果图片: {str(e)}")
                    image_row.append(Paragraph("检测结果图片\n(加载失败)", self.styles['ChineseNormal']))
            else:
                image_row.append(Paragraph("检测结果图片\n(不可用)", self.styles['ChineseNormal']))
            
            image_data.append(image_row)
            image_data.append(['原始图片', '检测结果图片'])
            
            image_table = Table(image_data, colWidths=[8*cm, 8*cm])
            image_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 1), (-1, 1), self.font_name),
                ('FONTSIZE', (0, 1), (-1, 1), 10),
                ('BACKGROUND', (0, 1), (-1, 1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            elements.append(image_table)
            return elements
            
        except Exception as e:
            logger.error(f"创建图片对比失败: {str(e)}")
            return [Paragraph("图像对比", self.styles['ChineseHeading']),
                   Paragraph("图片加载失败", self.styles['ChineseNormal'])]
    
    def _create_detection_table(self, record):
        """创建检测结果表格"""
        elements = []
        elements.append(Paragraph("检测结果统计", self.styles['ChineseHeading']))
        
        # 检测结果数据
        detection_data = [
            ['检测项目', '数量', '占比'],
            ['总检测人数', str(record.total_detections), '100%'],
            ['正确佩戴口罩', str(record.with_mask_count), 
             f'{(record.with_mask_count/record.total_detections*100):.1f}%' if record.total_detections > 0 else '0%'],
            ['未佩戴口罩', str(record.without_mask_count),
             f'{(record.without_mask_count/record.total_detections*100):.1f}%' if record.total_detections > 0 else '0%'],
            ['错误佩戴口罩', str(record.incorrect_mask_count),
             f'{(record.incorrect_mask_count/record.total_detections*100):.1f}%' if record.total_detections > 0 else '0%'],
        ]
        
        # 计算合规率
        compliance_rate = (record.with_mask_count / record.total_detections * 100) if record.total_detections > 0 else 0
        detection_data.append(['整体合规率', f'{compliance_rate:.1f}%', 
                              '优秀' if compliance_rate >= 90 else '良好' if compliance_rate >= 70 else '需改进'])
        
        detection_table = Table(detection_data, colWidths=[5*cm, 3*cm, 4*cm])
        detection_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), self.font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ]))
        
        elements.append(detection_table)
        return elements
    
    def _create_llm_analysis_section(self, llm_content):
        """创建LLM分析部分"""
        elements = []
        elements.append(Paragraph("AI智能分析", self.styles['ChineseHeading']))

        # 解析Markdown内容
        parsed_elements = self._parse_markdown_content(llm_content)
        elements.extend(parsed_elements)

        return elements

    def _parse_markdown_content(self, content):
        """解析Markdown内容为PDF元素"""
        elements = []

        # 按行分割内容
        lines = content.split('\n')
        current_paragraph = []
        in_list = False

        for line in lines:
            original_line = line
            line = line.strip()

            # 空行处理
            if not line:
                if current_paragraph:
                    # 结束当前段落
                    para_text = ' '.join(current_paragraph)
                    if para_text:
                        elements.append(Paragraph(self._format_inline_markdown(para_text),
                                                self.styles['ChineseNormal']))
                        elements.append(Spacer(1, 6))
                    current_paragraph = []
                in_list = False
                continue

            # 分隔线处理 (--- 或 ***)
            if line.startswith('---') or line.startswith('***'):
                if current_paragraph:
                    para_text = ' '.join(current_paragraph)
                    if para_text:
                        elements.append(Paragraph(self._format_inline_markdown(para_text),
                                                self.styles['ChineseNormal']))
                        elements.append(Spacer(1, 6))
                    current_paragraph = []

                # 添加分隔线
                elements.append(Spacer(1, 10))
                elements.append(Paragraph("─" * 46, self.styles['ChineseNormal']))
                elements.append(Spacer(1, 10))
                in_list = False
                continue

            # 标题处理 (##, ###, ####)
            if line.startswith('####'):
                if current_paragraph:
                    para_text = ' '.join(current_paragraph)
                    if para_text:
                        elements.append(Paragraph(self._format_inline_markdown(para_text),
                                                self.styles['ChineseNormal']))
                        elements.append(Spacer(1, 6))
                    current_paragraph = []

                title = line[4:].strip()
                # 处理标题中的markdown格式，如 **3. 风险评估**
                formatted_title = self._format_inline_markdown(title)
                elements.append(Paragraph(formatted_title, self.styles['ChineseSubHeading2']))
                in_list = False
                continue

            elif line.startswith('###'):
                if current_paragraph:
                    para_text = ' '.join(current_paragraph)
                    if para_text:
                        elements.append(Paragraph(self._format_inline_markdown(para_text),
                                                self.styles['ChineseNormal']))
                        elements.append(Spacer(1, 6))
                    current_paragraph = []

                title = line[3:].strip()
                # 处理标题中的markdown格式
                formatted_title = self._format_inline_markdown(title)
                elements.append(Paragraph(formatted_title, self.styles['ChineseSubHeading']))
                in_list = False
                continue

            elif line.startswith('##'):
                if current_paragraph:
                    para_text = ' '.join(current_paragraph)
                    if para_text:
                        elements.append(Paragraph(self._format_inline_markdown(para_text),
                                                self.styles['ChineseNormal']))
                        elements.append(Spacer(1, 6))
                    current_paragraph = []

                title = line[2:].strip()
                # 处理标题中的markdown格式
                formatted_title = self._format_inline_markdown(title)
                elements.append(Paragraph(formatted_title, self.styles['ChineseHeading']))
                in_list = False
                continue

            # 列表项处理 (- 或 数字. 或带缩进的列表)
            if (line.startswith('- ') or re.match(r'^\d+\.\s', line) or
                (original_line.startswith('  - ') or original_line.startswith('    - ') or
                 re.match(r'^\s+\d+\.\s', original_line))):

                if current_paragraph:
                    para_text = ' '.join(current_paragraph)
                    if para_text:
                        elements.append(Paragraph(self._format_inline_markdown(para_text),
                                                self.styles['ChineseNormal']))
                        elements.append(Spacer(1, 6))
                    current_paragraph = []

                # 计算缩进级别
                indent_level = 0
                if original_line.startswith('    '):
                    indent_level = 2
                elif original_line.startswith('  '):
                    indent_level = 1

                # 处理列表项
                if '- ' in line:
                    list_text = line.split('- ', 1)[1].strip()
                    if indent_level == 0:
                        bullet_text = f"• {self._format_inline_markdown(list_text)}"
                        style = self.styles['ChineseListItem']
                    else:
                        bullet_text = f"◦ {self._format_inline_markdown(list_text)}"
                        style = self.styles['ChineseListItem2']
                else:
                    # 数字列表
                    match = re.match(r'^(\d+)\.\s(.+)', line)
                    if match:
                        number = match.group(1)
                        list_text = match.group(2)
                        if indent_level == 0:
                            bullet_text = f"{number}. {self._format_inline_markdown(list_text)}"
                            style = self.styles['ChineseListItem']
                        else:
                            bullet_text = f"{number}. {self._format_inline_markdown(list_text)}"
                            style = self.styles['ChineseListItem2']
                    else:
                        bullet_text = f"• {self._format_inline_markdown(line)}"
                        style = self.styles['ChineseListItem']

                elements.append(Paragraph(bullet_text, style))
                in_list = True
                continue

            # 普通文本行
            current_paragraph.append(line)

        # 处理最后的段落
        if current_paragraph:
            para_text = ' '.join(current_paragraph)
            if para_text:
                elements.append(Paragraph(self._format_inline_markdown(para_text),
                                        self.styles['ChineseNormal']))
                elements.append(Spacer(1, 6))

        return elements

    def _format_inline_markdown(self, text):
        """格式化行内Markdown元素"""
        if not text:
            return text

        # 先转义特殊字符，但保留我们要处理的markdown符号
        text = text.replace('&', '&amp;')

        # 处理粗体 **text** 或 __text__
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'__(.*?)__', r'<b>\1</b>', text)

        # 处理斜体 *text* 或 _text_ (但不要与粗体冲突)
        text = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<i>\1</i>', text)
        text = re.sub(r'(?<!_)_([^_]+?)_(?!_)', r'<i>\1</i>', text)

        # 处理代码 `code`
        text = re.sub(r'`([^`]+?)`', r'<font name="Courier" size="9">\1</font>', text)

        # 处理其他特殊字符
        text = text.replace('<', '&lt;').replace('>', '&gt;')

        # 恢复我们的HTML标签
        text = text.replace('&lt;b&gt;', '<b>').replace('&lt;/b&gt;', '</b>')
        text = text.replace('&lt;i&gt;', '<i>').replace('&lt;/i&gt;', '</i>')
        text = text.replace('&lt;font name="Courier" size="9"&gt;', '<font name="Courier" size="9">').replace('&lt;/font&gt;', '</font>')

        return text
