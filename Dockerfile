# 使用 Playwright 官方 Python 镜像（已预装浏览器）
FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy

WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 设置环境变量
ENV HEADLESS=true

# 运行脚本
CMD ["python", "tennis_checker.py"]

