import logging
import random
import socket
import argparse
import struct

DEFAULT_RECEIVE_SIZE = 4
HEADER_SIZE = 4


# fucntion to randomize text
def text_to_random(text):
    def discard():
        return random.choices([True, False], weights=[1, 5])[0]

    def repeat(char):
        should_repeat = random.choices([True, False], weights=[1, 5])[0]

        # repeat if should_repeat is true or don't
        if should_repeat:
            repeat_amount = int(random.paretovariate(1))
            return char * repeat_amount
        else:
            return char

    transformed_text = [repeat(c) for c in text if not discard()]

    # check if transformed_text has length of 0
    if len(transformed_text) == 0:
        transformed_text = text[0]

    return "".join(transformed_text)


# function to turn text to uppercase
def text_to_upper(text):
    return text.upper()


# function to turn text to lowercase
def text_to_lower(text):
    return text.lower()


# function to reverse the text
def text_to_reverse(text):
    return text[::-1]


# function to shuffle the text
def text_to_shuffle(text):
    return "".join(random.sample(text, len(text)))


# function to get action and message_length
def get_action_message_length(data):
    binary_header = format(int(struct.unpack("!I", data[0:4])[0]), "032b")
    action = get_action_in_english(int(binary_header[0:5], 2))
    message_length = int(binary_header[5:32], 2)
    return action, message_length


# fucntion to get action in words, return 0 if bad action is detected
def get_action_in_english(action_int):
    if action_int == 1:
        return "uppercase"
    if action_int == 2:
        return "lowercase"
    if action_int == 4:
        return "reverse"
    if action_int == 8:
        return "shuffle"
    if action_int == 16:
        return "random"
    return 0


# function to process a request, calls appropriate function based on action
def process_request(conn, action, message):
    processed_text = ""
    if action == "uppercase":
        processed_text = text_to_upper(message)
    if action == "lowercase":
        processed_text = text_to_lower(message)
    if action == "reverse":
        processed_text = text_to_reverse(message)
    if action == "shuffle":
        processed_text = text_to_shuffle(message)
    if action == "random":
        processed_text = text_to_random(message)
    if action == 0:
        processed_text = message
    message_length = struct.pack("!I", len(processed_text))
    conn.send(message_length + processed_text.encode())


# function to run non-stop until KeyboardInterrupt
def run(port):
    server_socket = socket.socket()
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("", port))
    server_socket.listen()
    logging.info(f"Listening on port {port}")

    receive_size = DEFAULT_RECEIVE_SIZE
    data_bytearray = bytearray([])
    has_message_length = False

    # loop forever until KeyboardInterrupt is detected (Exception thrown)
    while True:
        conn, address = server_socket.accept()
        logging.info(f"Connection from: {address}")

        # loop until current client disconnects
        while True:
            data = bytearray(conn.recv(receive_size))

            data_bytearray += data
            logging.info(f"Received: {data}")

            # if data is 0, meaning client disconnected, up one level and wait
            if not data:
                logging.info("Client disconnected...")
                receive_size = DEFAULT_RECEIVE_SIZE
                data_bytearray = bytearray([])
                break

            # loop untill more data needs to be received
            while True:
                # up one level to receive more data if complete header is not detected
                if len(data_bytearray) < 4:
                    logging.info("Need more bytes for complete header...")
                    break
                # if has_message_length is false, call function to get action and message_length
                if not has_message_length:
                    action, message_length = get_action_message_length(data_bytearray)
                    has_message_length = True
                    # if action is 0, meaning bad action detected
                    if action == 0:
                        process_request(
                            conn, 0, "Bad action detected! Request skipped!"
                        )
                        # loop to receive and remove data related to the bad action
                        while message_length > len(data_bytearray) - HEADER_SIZE:
                            data = bytearray(conn.recv(receive_size))
                            data_bytearray += data
                        data_bytearray = data_bytearray[4 + message_length :]
                        has_message_length = False
                        continue

                # if more message is coming, double the receive_size to save time
                if message_length > (len(data_bytearray) - HEADER_SIZE):
                    receive_size = receive_size * 2
                    logging.info("More message coming...")
                    break

                process_request(
                    conn, action, data_bytearray[4 : 4 + message_length].decode()
                )
                data_bytearray = data_bytearray[4 + message_length :]
                has_message_length = False


# function to parse arguments
def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v",
        "--verbose",
        required=False,
        action="store_true",
        help="Sets log level to verbose",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        required=False,
        default=8083,
        help="Default port is set to 8083",
    )
    return parser.parse_args()


# main function
if __name__ == "__main__":
    args = parse_arguments()
    # if verbose flag is high, turn on verbose
    if args.verbose:
        logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.DEBUG)
    # this try-except block is for catching Keyboard Interrupt
    try:
        run(args.port)
    except KeyboardInterrupt:
        logging.info("Keyboard Interrupt Detected!")
