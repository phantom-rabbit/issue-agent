# Docker Makefile for issue-assistant

# 镜像名称和标签
IMAGE_NAME := issue-assistant
IMAGE_TAG := latest
FULL_IMAGE_NAME := $(IMAGE_NAME):$(IMAGE_TAG)

# 默认构建本机镜像
.DEFAULT_GOAL := build

# 构建本机架构镜像
build:
	cp tools/github-mcp-server-mac tools/github-issue
	@echo "Building image for native architecture..."
	docker build -t $(FULL_IMAGE_NAME) .
	@echo "Image built: $(FULL_IMAGE_NAME)"

# 构建Linux/AMD64架构镜像
build-linux:
	cp tools/github-mcp-server-linux tools/github-issue
	@echo "Building Linux/AMD64 image..."
	docker buildx create --use || true
	docker buildx build --platform linux/amd64 -t $(FULL_IMAGE_NAME) --load .
	@echo "Linux/AMD64 image built: $(FULL_IMAGE_NAME)"

.PHONY: build build-linux