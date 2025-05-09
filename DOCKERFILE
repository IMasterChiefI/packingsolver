FROM ubuntu:22.04

# Install system dependencies
RUN apt-get update && apt-get install -y \
  python3 python3-pip cmake g++ git make curl

# Install Python packages
RUN pip3 install fastapi uvicorn

# Set working directory
WORKDIR /app

# Copy all project files
COPY . .

# Build the C++ solver (e.g. boxstacks)
RUN cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && \
    cmake --build build --config Release --parallel && \
    cmake --install build --config Release --prefix install

# Start FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
