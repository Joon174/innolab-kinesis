from kinesis_handler import KinesisVideoConsumer
import time


# Run main loop
if __name__ == "__main__":

    # Due to the consumer having a bug issue where the stream gets hogged if no fragments are in the stream,
    # Currently the solution will be to reinstantiate multiple times until the payload is active.
    while True:
        # Init the consumer constantly until we find the payload has something in it
        while True:
            consumer = KinesisVideoConsumer("innolab-bag-scanning")
            print("Starting up Video Consumer...")
            consumer.start()
            time.sleep(10)
            if consumer.fragment_received:
                print("Fragment detected in payload")
                break
            else:
                print("No fragments received")
                consumer.stop()  # 10 seconds is currently how fast for the fragments to return.

        # Let the consumer run until the stream is terminated and restart the search process again.
        while True:
            if consumer.producer_terminated:
                print("Producer stream has been terminated")
                break
            else:
                print("Running consumer")
                time.sleep(5)
    exit()


