# .devcontainer/Dockerfile
FROM mcr.microsoft.com/devcontainers/python:3.9-bullseye

# Установка системных зависимостей
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    build-essential \
    curl \
    wget \
    git \
    vim \
    nano \
    htop \
    tmux \
    graphviz \
    graphviz-dev \
    libatlas-base-dev \
    libblas-dev \
    liblapack-dev \
    gfortran \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Создание необходимых директорий
RUN mkdir -p /workspace/data \
    /workspace/logs \
    /workspace/models \
    /workspace/.streamlit

# Установка рабочей директории
WORKDIR /workspace

# Копирование requirements.txt
COPY requirements.txt /tmp/requirements.txt

# Установка Python пакетов
RUN pip3 install --upgrade pip setuptools wheel \
    && pip3 install --no-cache-dir -r /tmp/requirements.txt \
    && pip3 install --no-cache-dir \
    jupyter \
    ipykernel \
    black \
    flake8 \
    isort \
    pytest \
    pytest-cov \
    && rm -rf /tmp/requirements.txt \
    && rm -rf /root/.cache/pip

# Установка прав
RUN chown -R vscode:vscode /workspace

# Копирование скриптов
COPY .devcontainer/post-create.sh /usr/local/bin/post-create.sh
RUN chmod +x /usr/local/bin/post-create.sh

# Switch back to vscode user
USER vscode

# Настройка git
RUN git config --global core.editor "vim" \
    && git config --global pull.rebase false

# Создание alias
RUN echo "alias ll='ls -la'" >> ~/.zshrc \
    && echo "alias la='ls -A'" >> ~/.zshrc \
    && echo "alias l='ls -CF'" >> ~/.zshrc \
    && echo "alias python=python3" >> ~/.zshrc \
    && echo "alias pip=pip3" >> ~/.zshrc \
    && echo "alias streamlit='streamlit run'" >> ~/.zshrc \
    && echo "alias run-app='streamlit run app.py'" >> ~/.zshrc

# Добавление Python пути
ENV PYTHONPATH="/workspace:${PYTHONPATH}"
ENV PATH="/workspace:${PATH}"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

LABEL maintainer="Yeruslan Technologies" \
      version="6.0.0" \
      description="AVCS DNA Industrial Monitor Development Container"
