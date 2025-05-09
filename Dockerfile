FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
  python3 python3-pip curl unzip g++ git make cmake \
  liblapack-dev liblapacke-dev libblas-dev \
  libbz2-dev

# Manually install CMake 3.28.3
RUN curl -L -o cmake.tar.gz https://github.com/Kitware/CMake/releases/download/v3.28.3/cmake-3.28.3-linux-x86_64.tar.gz && \
    tar -xzf cmake.tar.gz && \
    mv cmake-3.28.3-linux-x86_64 /opt/cmake && \
    ln -s /opt/cmake/bin/* /usr/local/bin/ && \
    rm cmake.tar.gz

COPY requirements.txt .
RUN pip3 install -r requirements.txt

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

# Lade die offiziellen Beispiel-Testdaten für boxstacks
RUN python3 scripts/download_data.py --data roadef2022_2024-04-25_bpp

