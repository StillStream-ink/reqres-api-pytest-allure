FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 暴露 Mock 服务端口
EXPOSE 5000

# 启动 Mock 服务
CMD ["python", "start_mock.py"]
