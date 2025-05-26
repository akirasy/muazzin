FROM alpine:3

RUN apk add --no-cache \
  gst-plugins-good gst-plugins-bad \
  python3 py3-pip tzdata

ENV TZ="Asia/Kuala_Lumpur"
WORKDIR /home/muazzin
COPY . /home/muazzin
RUN python -m pip install --no-cache-dir --break-system-packages -r requirements.txt

CMD ["python", "/home/muazzin/muazzin.py"]

