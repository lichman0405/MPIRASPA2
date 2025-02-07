# 使用 Ubuntu 24.04 作为基础镜像
FROM ubuntu:24.04

# 设置非交互模式，避免 `apt-get` 交互式提示
ENV DEBIAN_FRONTEND=noninteractive

# 更新系统并安装基础依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gfortran \
    cmake \
    wget \
    curl \
    git \
    software-properties-common \
    python3 \
    python3-venv \
    python3-dev \
    python3-pip \
    automake \
    autoconf \
    libtool \
    && rm -rf /var/lib/apt/lists/*

# 创建 Python 虚拟环境
RUN python3.10 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 复制并安装 Python 依赖
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# 编译 MPICH 4.3.0
WORKDIR /tmp
RUN wget https://www.mpich.org/static/downloads/4.3.0/mpich-4.3.0.tar.gz && \
    tar -xvf mpich-4.3.0.tar.gz && \
    cd mpich-4.3.0 && \
    ./configure --prefix=/usr/local/mpich --disable-fortran && \
    make -j "$(nproc)" && \
    make install && \
    cd /tmp && rm -rf mpich-4.3.0 mpich-4.3.0.tar.gz

# 设置环境变量
ENV PATH="/usr/local/mpich/bin:${PATH}"
ENV LD_LIBRARY_PATH="/usr/local/mpich/lib:${LD_LIBRARY_PATH:-}"

# 克隆 RASPA2 并编译
RUN git clone https://github.com/iRASPA/RASPA2.git /opt/RASPA2
WORKDIR /opt/RASPA2

RUN rm -rf autom4te.cache \
    && mkdir -p m4 \
    && aclocal \
    && autoreconf -i \
    && automake --add-missing \
    && autoconf \
    && ./configure --prefix=/usr/local/raspa \
    && make -j "$(nproc)" \
    && make install

# 设置 RASPA 环境变量
ENV RASPA_DIR="/usr/local/raspa"
ENV PATH="${RASPA_DIR}/bin:${PATH}"

# 声明数据挂载目录
VOLUME /data

# 复制 FastAPI 代码
WORKDIR /app
COPY main.py /app/main.py

# 启动 FastAPI 服务
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
