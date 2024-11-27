# Start with a base Ubuntu image
FROM ubuntu:20.04

# Set environment variables to avoid prompts during apt-get install
ENV DEBIAN_FRONTEND=noninteractive

# Install required dependencies for building glibc and CA certificates
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    sudo \
    wget \
    make \
    gcc \
    g++ \
    ca-certificates \
    python3 \
    python3-pip \
    git \
    gawk \
    bison \
    && rm -rf /var/lib/apt/lists/*

# Install glibc 2.38
RUN curl -L https://ftp.gnu.org/gnu/libc/glibc-2.38.tar.gz -o glibc-2.38.tar.gz && \
    tar -xvzf glibc-2.38.tar.gz && \
    cd glibc-2.38 && \
    mkdir build && cd build && \
    ../configure --prefix=/usr && \
    make -j"$(nproc)" && \
    make install && \
    cd ../.. && rm -rf glibc-2.38*

# Clean up unnecessary build dependencies and cached files
RUN rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# Set the working directory in the container
WORKDIR /app

# Copy your project files into the container
COPY . /app

# Install Python dependencies from requirements.txt
RUN pip3 install -r requirements.txt

# Run Prisma generate and db push (ensure Prisma is configured in your project)
RUN prisma generate && prisma db push

# Expose the port your app will run on (adjust the port if needed)
EXPOSE 80

# Set the entry point to start your app
CMD ["python3", "server.py"]
