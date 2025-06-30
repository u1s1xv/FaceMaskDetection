@echo off
echo 正在激活FMD虚拟环境...
call conda activate FMD

echo 切换到项目根目录...
cd /d "%~dp0\.."

echo 初始化项目目录结构...
python yoloserver\initialize_project.py

echo 切换到爬虫脚本目录...
cd crawl_script

echo 检查并安装依赖包...
pip install -r crawler_requirements.txt

echo 开始运行口罩图片爬虫...
python mask_image_crawler.py

echo 爬虫运行完成！
pause
