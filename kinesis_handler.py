'''
Example based on the Python AWS example on https://github.com/aws-samples/amazon-kinesis-video-streams-consumer-library-for-python.git
'''

# AWS native & relevant local libraries
import boto3
from settings import KINESIS_REGION_NAME, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY_ID
from amazon_kinesis_video_consumer_library.kinesis_video_streams_parser import KvsConsumerLibrary
from amazon_kinesis_video_consumer_library.kinesis_video_fragment_processor import KvsFragmentProcessor

# For processing video frame datatype
import numpy

# Python native libraries
import time, json, uuid, gi, os
from io import BytesIO
gi.require_version('Gst', '1.0')
from gi.repository import Gst


class KinesisVideoConsumer:
    '''
    Initialise the KVS Client. Thi will include the Fragment processor for 
    uploading the frames onto the Kinesis Video Stream.
    1) Start a Fragment processor for the video stream
    2) Connect to client
    '''
    def __init__(self, stream_name):
        self.kvs_fragment_processor = KvsFragmentProcessor()
        self.stream_name = stream_name
        self.session = boto3.Session(region_name=KINESIS_REGION_NAME)
        self.kvs_client = self.session.client("kinesisvideo")
        self.last_good_fragment_tags = None

    # Main loop for consuming fragments
    def service_loop(self):

        # Obtain media endpoint for GetMedia Call
        media_endpoint = self._get_data_endpoint(self.stream_name, 'GET_MEDIA')
        print("Endpoint of kinesis stream is {}".format(media_endpoint))
        kvs_media_client = self.session.client('kinesis-video-media', endpoint_url=media_endpoint)


        # Make an API call to start connection
        media_response_callback = kvs_media_client.get_media(
                StreamName=self.stream_name,
                StartSelector={
                    'StartSelectorType': 'NOW',
                }
            )

        stream_consumer = KvsConsumerLibrary(self.stream_name,
                            media_response_callback,
                            self.fragment_callback,
                            self.stream_read_complete,
                            self.stream_read_error
                        )
        
        # Start the instance and run the consumer
        stream_consumer.start()
        while True:
            print("Running Consumer")
            time.sleep(5)

    # Callback function for when frames are recvd in the data stream
    def fragment_callback(self, stream_name, fragment_bytes, fragment_dom, fragment_recv_duration):
        try:

            print('\n\n##########################\nFragment Received on Stream: {}\n##########################'.format(stream_name))
            
            # Print the fragment receive and processing duration as measured by the KvsConsumerLibrary
            print('####### Fragment Receive and Processing Duration: {} secs'.format(fragment_recv_duration))
            time_now = time.time()

            self.last_good_fragment_tags = self.kvs_fragment_processor.get_fragment_tags(fragment_dom)
            
            kvs_ms_behind_live = float(self.last_good_fragment_tags['AWS_KINESISVIDEO_MILLIS_BEHIND_NOW'])
            producer_timestamp = float(self.last_good_fragment_tags['AWS_KINESISVIDEO_PRODUCER_TIMESTAMP'])
            server_timestamp = float(self.last_good_fragment_tags['AWS_KINESISVIDEO_SERVER_TIMESTAMP'])

            pretty_frag_dom = self.kvs_fragment_processor.get_fragement_dom_pretty_string(fragment_dom)

            # Uncomment to save the fragments as frames to local dir
            # self.save_fragment_as_jpg(fragment_bytes)

        except:
            print("callback failed")

    # Save fragments as JPGs in local dir
    def save_fragment_as_jpg(self, fragment_bytes):
        # Construct the frame based on the fragment received:
        one_in_frames_ratio = 5
        print('#######  Reading 1 in {} Frames from fragment as ndarray:'.format(one_in_frames_ratio))
        ndarray_frames = self.kvs_fragment_processor.get_frames_as_ndarray(fragment_bytes, one_in_frames_ratio)
        print('Processing frames: ')
        for i in range(len(ndarray_frames)):
            ndarray_frame = ndarray_frames[i]
            print('Frame-{} Shape: {}'.format(i, ndarray_frame.shape))

        # Save them as JPEG frames locally:
        print('###### Saving frames to local dir:')
        one_in_frames_ratio = 5
        save_dir = 'images_from_kinesis'
        jpg_file_base_name = self.last_good_fragment_tags['AWS_KINESISVIDEO_FRAGMENT_NUMBER']
        jpg_file_base_path = os.path.join(save_dir, jpg_file_base_name)

        jpeg_paths = self.kvs_fragment_processor.save_frames_as_jpeg(fragment_bytes, one_in_frames_ratio, jpg_file_base_path)
        for i in range(len(jpeg_paths)):
            jpeg_path = jpeg_paths[i]
            print('Saved JPEG-{} Path: {}'.format(i, jpeg_path))

    # Callback trigger when the stream exits or there are no fragments left
    # available.
    def stream_read_complete(self, stream_name):
        print(f'Read Media on stream: {stream_name} Completed successfully - Last Fragment Tags: {self.last_good_fragment_tags}')

    # Callback trigger for any exceptions thrown when reading the fragments
    # during the stream
    def stream_read_error(self, stream_name, error):
        print(f'####### ERROR: Exception on read stream: {stream_name}\n####### Fragment Tags:\n{self.last_good_fragment_tags}\nError Message:{error}')

    def _get_data_endpoint(self, stream_name, api_name):
        response = self.kvs_client.get_data_endpoint(
            StreamName=stream_name,
            APIName=api_name
        )
        return response['DataEndpoint']


class KinesisVideoProducer:
    """
    Creates a producer using the local SDK to push data to remote. Pipeline command based on https://github.com/awslabs/amazon-kinesis-video-streams-producer-sdk-cpp/blob/master/docs/linux.md
    """
#   VIDEO_CAPTURE_PIPELINE = 'v4l2src do-timestamp=TRUE device=/dev/video0 ! videoconvert ! video/x-raw,format=I420,width=640,height=480,framerate=30/1 ! x264enc ! h264parse ! video/x-h264,stream-format=avc,alignment=au,width=640,height=480,framerate=30/1,profile=baseline ! kvssink stream-name="innolab-bag-scanning"'

    def __init__(self, stream_name):
        Gst.init(None)  
        
        # Create Kinesis Video Client:
        self.kinesis_video_client = boto3.client('kinesisvideo', region_name=KINESIS_REGION_NAME)
        self.stream_name = stream_name

        # Get the Kinesis Video Stream endpoint
        stream_endpoint_response = self.kinesis_video_client.get_data_endpoint(
            StreamName=self.stream_name,
            APIName='PUT_MEDIA'
        )
        self.endpoint_url = stream_endpoint_response['DataEndpoint']
        print(self.endpoint_url)
        
        # Set up the Kinesis Video Media Client
        self.media_client = boto3.client('kinesis-video-media', endpoint_url=self.endpoint_url, region_name=KINESIS_REGION_NAME)

        self.gst_pipeline = Gst.parse_launch(KinesisVideoProducer.VIDEO_CAPTURE_PIPELINE)
        self.appsink = self.gst_pipeline.get_by_name('appsink0')

    def send_to_kinesis(self, datastream):
        try:
            response = self.media_client.put_media(
                StreamName=self.stream_name,
                Payload=datastream,
                PartitionKey='partition-key',
            )
            print(f"Successfully send data to Kinesis: {response}")

        except Exception as e:
            print(f"Error sending data to Kinesis: {e}")

    def on_new_sample(self, sink):
        sample = sink.emit('pull-sample')
        if sample:
            kvs_buffer = sample.get_buffer()
            data = kvs_buffer.extract_dup(0, kvs_buffer.get_size())
            self.send_to_kinesis(data)

        return Gst.FlowReturn.OK


    def start_pipeline_stream(self):
        self.appsink.connect('new-sample', self.on_new_sample)
        self.gst_pipeline.set_state(Gst.State.PLAYING)
        print("Pipeline started")

        try:
            while True:
                print("Running")
                time.sleep(0.5)

        except KeyboardInterrupt:
            print("Keyboard interrupt signal received, STOPPING...")
            self.gst_pipeline.set_state(Gst.State.NULL)


