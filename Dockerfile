FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

# 1. 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gfortran \
    cmake \
    wget \
    curl \
    git \
    python3 \
    python3-pip \
    automake \
    autoconf \
    libtool \
    && rm -rf /var/lib/apt/lists/*

# 2. 安装 Python 库
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# 3. 编译 MPICH 4.3.0
WORKDIR /tmp
RUN wget https://www.mpich.org/static/downloads/4.3.0/mpich-4.3.0.tar.gz && \
    tar -xvf mpich-4.3.0.tar.gz && \
    cd mpich-4.3.0 && \
    ./configure --prefix=/usr/local/mpich && \
    make -j "$(nproc)" && \
    make install && \
    cd /tmp && rm -rf mpich-4.3.0 mpich-4.3.0.tar.gz

ENV PATH="/usr/local/mpich/bin:${PATH}"
ENV LD_LIBRARY_PATH="/usr/local/mpich/lib:${LD_LIBRARY_PATH}"

# 4. 编译 RASPA2（autoreconf + configure + make）
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

ENV RASPA_DIR="/usr/local/raspa"
ENV PATH="${RASPA_DIR}/bin:${PATH}"

# 声明挂载点
VOLUME /data

# 将 FastAPI 脚本复制进去
WORKDIR /app
COPY main.py /app/main.py

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
