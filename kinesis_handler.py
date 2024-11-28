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
import time, json, uuid


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
            time.sleep(5)

    # Callback function for when frames are recvd in the data stream
    def fragment_callback(self, fragment_bytes, fragment_dom, fragment_recv_duration):
        try:
            time_now = time.time()

            self.last_good_fragment_tags = self.kvs_fragment_processor.get_fragment_tags(fragment_dom)
            
            kvs_ms_behind_live = float(self.last_good_fragment_tags['AWS_KINESISVIDEO_MILLIS_BEHIND_NOW'])
            producer_timestamp = float(self.last_good_fragment_tags['AWS_KINESISVIDEO_PRODUCER_TIMESTAMP'])
            server_timestamp = float(self.last_good_fragment_tags['AWS_KINESISVIDEO_SERVER_TIMESTAMP'])

            pretty_frag_dom = self.kvs_fragment_processor.get_fragement_dom_pretty_string(fragment_dom)
        except:
            print("callback failed")

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


