import logging
import random
import socket


def randomize_text(text):
    def discard():
        return random.choices([True, False], weights=[1, 5])[0]

    def repeat(char):
        should_repeat = random.choices([True, False], weights=[1, 5])[0]

        if should_repeat:
            repeat_amount = int(random.paretovariate(1))
            return char * repeat_amount
        else:
            return char

    text = text.decode()
    transformed_text = [repeat(c) for c in text if not discard()]

    if len(transformed_text) == 0:
        transformed_text = text[0]

    return "".join(transformed_text).encode()


def run(port):
    server_socket = socket.socket()
    server_socket.bind(("", port))
    server_socket.listen()

    while True:
        conn, address = server_socket.accept()
        logging.info(f"Connection from: {address}")

        while True:
            data = conn.recv(1024).decode()
            logging.info(f"Received: {data}")

            if not data:
                logging.info("Client disconnected...")
                break

            conn.send(data.upper().encode())

        conn.close()


if __name__ == "__main__":
    run(8083)
