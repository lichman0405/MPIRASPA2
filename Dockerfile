# Use Ubuntu 24.04 as the base image
FROM ubuntu:24.04

# Set non-interactive mode to avoid `apt-get` interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Update the system and install basic dependencies
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
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create a Python virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Compile MPICH 4.3.0
WORKDIR /tmp
RUN wget https://www.mpich.org/static/downloads/4.3.0/mpich-4.3.0.tar.gz && \
    tar -xvf mpich-4.3.0.tar.gz && \
    cd mpich-4.3.0 && \
    ./configure --prefix=/usr/local/mpich --disable-fortran && \
    make -j "$(nproc)" && \
    make install && \
    cd /tmp && rm -rf mpich-4.3.0 mpich-4.3.0.tar.gz

# Set environment variables
ENV PATH="/usr/local/mpich/bin:${PATH}"
ENV LD_LIBRARY_PATH="/usr/local/mpich/lib:${LD_LIBRARY_PATH:-}"

# Update .bashrc to include MPICH environment variables
RUN echo 'export PATH="/usr/local/mpich/bin:${PATH}"' >> ~/.bashrc && \
    echo 'export LD_LIBRARY_PATH="/usr/local/mpich/lib:${LD_LIBRARY_PATH:-}"' >> ~/.bashrc

# Clone RASPA2 and compile it
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

# Set RASPA environment variables
ENV RASPA_DIR="/usr/local/raspa"
ENV PATH="${RASPA_DIR}/bin:${PATH}"
ENV RAPSA_SHARE="${RASPA_DIR}/share"

# Update .bashrc to include RASPA2 environment variables
RUN echo 'export RASPA_DIR="/usr/local/raspa"' >> ~/.bashrc && \
    echo 'export PATH="${RASPA_DIR}/bin:${PATH}"' >> ~/.bashrc && \
    echo 'export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}"' >> ~/.bashrc && \
    echo 'export RAPSA_SHARE="${RASPA_DIR}/share"' >> ~/.bashrc

# Declare data mount directory
VOLUME /data

# Copy FastAPI code
WORKDIR /app
COPY app.py /app/app.py

# Expose port
EXPOSE 8000

# Start FastAPI service
CMD ["/opt/venv/bin/uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]