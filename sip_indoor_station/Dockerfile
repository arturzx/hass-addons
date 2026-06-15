ARG BUILD_FROM
FROM ${BUILD_FROM}

SHELL ["/bin/ash", "-o", "pipefail", "-c"]

RUN apk add --no-cache \
    bash \
    jq \
    py3-pip \
    py3-gobject3 \
    gstreamer \
    gst-plugins-base \
    gst-plugins-good \
    gst-plugins-bad \
    gst-plugins-ugly \
    gst-libav \
    libnice

WORKDIR /app
COPY sip-indoor-station/ /app/sip-indoor-station/

RUN pip3 install --break-system-packages "aiohttp>=3.12" \
    && pip3 install --break-system-packages --no-deps /app/sip-indoor-station

COPY run.sh /run.sh
RUN chmod a+x /run.sh

CMD ["/run.sh"]
