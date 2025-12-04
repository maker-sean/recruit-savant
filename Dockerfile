FROM python:3.10

# Install system packages for pandas, numpy, and other scientific libs
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    make \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    python3-dev \
    python3-distutils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080
EXPOSE 8080

CMD ["python", "app.py"]
