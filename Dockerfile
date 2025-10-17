FROM ubuntu:22.04

# Prevent interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:99

# Install dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-tk \
    xvfb \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip3 install pycrypto requests colorama

# Create stitch directory
WORKDIR /opt/stitch

# Copy enhanced Stitch files
COPY . /opt/stitch/

# Set up virtual display startup
RUN echo '#!/bin/bash\nXvfb :99 -screen 0 1024x768x24 &\nexec "$@"' > /entrypoint.sh && \
    chmod +x /entrypoint.sh

# Expose Stitch ports
EXPOSE 4433 4455

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python3", "main.py"]