FROM python:3.13-slim
WORKDIR /app

# 环境变量设置
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8088 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_BINARY=:all:  

# 安装系统依赖 - 确保构建环境完整
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    git \
    curl \
    vim \
    && rm -rf /var/lib/apt/lists/*

# 复制项目依赖文件
COPY pyproject.toml uv.lock ./

# 安装uv并同步依赖 - 使用--no-binary确保源码编译
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple uv \
    && uv sync --upgrade --no-cache -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制剩余项目文件
COPY . .

# 确保脚本文件有执行权限
RUN chmod +x /app/tools/github-issue

# 环境变量
ENV PYTHONPATH=/app

# 暴露端口
EXPOSE ${PORT}

# 添加健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# 设置非root用户运行
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# 启动命令
CMD ["uv", "run", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8088"]

COPY pyproject.toml ./
RUN pip install --no-cache-dir uv \
    && uv sync --upgrade --no-cache

ENV PYTHONPATH=/app
