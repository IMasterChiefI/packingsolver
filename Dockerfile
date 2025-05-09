FROM ubuntu:22.04

# System dependencies inkl. LAPACK + BLAS
RUN apt-get update && apt-get install -y \
  python3 python3-pip curl unzip g++ git make \
  liblapack-dev libblas-dev

# Manually install CMake 3.28.3
RUN curl -L -o cmake.tar.gz https://github.com/Kitware/CMake/releases/download/v3.28.3/cmake-3.28.3-linux-x86_64.tar.gz && \
    tar -xzf cmake.tar.gz && \
    mv cmake-3.28.3-linux-x86_64 /opt/cmake && \
    ln -s /opt/cmake/bin/* /usr/local/bin/ && \
    rm cmake.tar.gz

# Install Python packages
RUN pip3 install fastapi uvicorn

# Set working directory
WORKDIR /app

# Copy source code
COPY . .

# Build the C++ packingsolver with CMake
RUN cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && \
    cmake --build build --config Release --parallel && \
    cmake --install build --config Release --prefix install

# Expose default port
EXPOSE 8000

# Start the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
