# Build docker with
# docker build -t kinesis-video-producer-sdk-cpp-amazon-linux .
#
FROM ubuntu:20.04

ENV DEBIAN_FRONTEND noninteractive

RUN apt update && \
    apt install -y \
	autoconf \
	automake  \
	build-essential \
	bison \
	bzip2 \
	cmake \
	curl \
	diffutils \
	flex \
	gcc \
	g++ \
	git \
	libgmp-dev \
	libgstreamer1.0-dev \
	libgstreamer-plugins-base1.0-dev \
	libgstreamer-plugins-bad1.0-dev \
	gstreamer1.0-plugins-base \
	gstreamer1.0-plugins-good \
	gstreamer1.0-plugins-bad \
	gstreamer1.0-plugins-ugly \
	gstreamer1.0-libav \
	gstreamer1.0-tools \
	gstreamer1.0-x \
	gstreamer1.0-alsa \
	gstreamer1.0-gl \
	gstreamer1.0-gtk3 \
	gstreamer1.0-qt5 \
	gstreamer1.0-pulseaudio \
	libcurl4-openssl-dev \
	libffi-dev \
	libmpc-dev \
	libtool \
	make \
	m4 \
	libmpfr-dev \
	pkg-config \
	python3-pip \
	vim \
	wget \
	xz-utils && \
    apt clean all

ENV KVS_SDK_VERSION v3.2.0

WORKDIR /opt/
RUN git clone --depth 1 --branch $KVS_SDK_VERSION https://github.com/awslabs/amazon-kinesis-video-streams-producer-sdk-cpp.git
WORKDIR /opt/amazon-kinesis-video-streams-producer-sdk-cpp/build/
RUN cmake .. -DBUILD_GSTREAMER_PLUGIN=ON -DCMAKE_VERBOSE_MAKEFILE:BOOL=ON && \
    make 

ENV LD_LIBRARY_PATH=/opt/amazon-kinesis-video-streams-producer-sdk-cpp/open-source/local/lib
ENV GST_PLUGIN_PATH=/opt/amazon-kinesis-video-streams-producer-sdk-cpp/build/:$GST_PLUGIN_PATH


# Download and plugin the consumer
ENV AWS_DEFAULT_REGION="ap-southeast-2"

WORKDIR /opt/
RUN git clone --depth 1 --branch main https://github.com/Joon174/innolab-kinesis.git
WORKDIR /opt/innolab-kinesis/

COPY settings.py .
RUN python3 -m pip install -r requirements.txt

ENTRYPOINT ["python3", "/opt/innolab-kinesis/run_consumer.py"]
