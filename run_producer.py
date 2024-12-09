from kinesis_handler import KinesisVideoProducer


# Run main loop
if __name__ == "__main__":

    # Create streamer to send data to the cloud
    # Startup the producer for KVS innolab-bag-scanning
    producer = KinesisVideoProducer("innolab-bag-scanning")

    producer.start_pipeline_stream()

