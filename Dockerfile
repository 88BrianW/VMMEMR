# Start with a base Ubuntu image
FROM ubuntu:20.04

# Set environment variables to avoid prompts during apt-get install
ENV DEBIAN_FRONTEND=noninteractive

# Install required dependencies for building glibc, and also missing tools (gawk, bison, python3)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    sudo \
    wget \
    make \
    gcc \
    g++ \
    ca-certificates \
    gawk \
    bison \
    python3 \
    && rm -rf /var/lib/apt/lists/*

# Download and install the latest version of GLIBC (2.36 at the time of writing)
RUN curl -L https://ftp.gnu.org/gnu/libc/glibc-2.36.tar.gz -o glibc-2.36.tar.gz && \
    tar -xvzf glibc-2.36.tar.gz && \
    cd glibc-2.36 && \
    mkdir build && cd build && \
    ../configure --prefix=/usr && \
    make -j"$(nproc)" && \
    sudo make install && \
    cd ../.. && rm -rf glibc-2.36*

# Clean up unnecessary build dependencies and cached files
RUN rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# Set the working directory in the container (optional)
WORKDIR /root

# Set the entry point or command (optional, this can be a placeholder)
CMD ["bash"]
