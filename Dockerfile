FROM python:3.11-slim-bookworm

WORKDIR /app

# System dependencies
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    build-essential curl git wget pv jq \
    ffmpeg aria2 cmake mediainfo \
    && rm -rf /var/lib/apt/lists/*

# Build Bento4 (provides mp4decrypt)
RUN git clone https://github.com/axiomatic-systems/Bento4.git /tmp/Bento4 && \
    cd /tmp/Bento4 && \
    mkdir cmakebuild && cd cmakebuild && \
    cmake -DCMAKE_BUILD_TYPE=Release .. && \
    make -j$(nproc) && make install && \
    rm -rf /tmp/Bento4

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
