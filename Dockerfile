FROM debian:buster-slim

# Install packages as root
RUN apt update && apt install -y --no-install-recommends \
    python3-pip python3-setuptools mplayer && \
    apt -y autoremove && apt clean

# Create non-priviledge user
RUN useradd --create-home --groups audio muazzin
USER muazzin
WORKDIR /home/muazzin
ENV TZ="Asia/Kuala_Lumpur"
ENV KOD="PHG03"

# Install python module
COPY requirements.txt /home/muazzin/requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy source to image and run
COPY . /home/muazzin
CMD [ "python3", "./muazzin.py"]
