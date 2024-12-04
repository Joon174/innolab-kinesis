from kinesis_handler import KinesisVideoConsumer, KinesisVideoProducer


# Run main loop
if __name__ == "__main__":
    
    # Create streamer to send data to the cloud
    """
    producer = KinesisVideoProducer("innolab-bag-scanning")

    producer.start_pipeline_stream()
    """

    # Or alternatively create a consumer to process the data coming in
    consumer = KinesisVideoConsumer("innolab-bag-scanning")

    consumer.service_loop()
    print("session terminated")

    exit()
