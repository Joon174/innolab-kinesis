from kinesis_handler import KinesisVideoConsumer


# Run main loop
if __name__ == "__main__":

    # Create streamer to send data to the cloud
    
    # Or alternatively create a consumer to process the data coming in
    consumer = KinesisVideoConsumer("innolab-bag-scanning")

    consumer.service_loop()
    print("session terminated")

    exit()
