"""
 HTTP Server Shell
 Author: Ofri Guz
 Date: December 30, 2023,
 Purpose: Ex. 4
"""
# Modules
import socket
import os
import logging

# Constants
DEFAULT_URL = "/index.html"
ROOT_WEB = "C:\\work\\cyber\\webroot"

INVALID_REQUEST_ERROR = 400
FILE_NOT_FOUND_ERROR = 404
FORBIDDEN_ERROR = 403
INTERNAL_SERVER_ERROR = 500

HTTP_OK = 'HTTP/1.1 200 OK\r\n'
HTTP_FOUND = 'HTTP/1.1 302 Found\r\n'
HTTP_BAD_REQUEST = 'HTTP/1.1 ' + str(INVALID_REQUEST_ERROR) + ' Bad Request\r\n'  # **********
HTTP_FORBIDDEN = 'HTTP/1.1 ' + str(FORBIDDEN_ERROR) + ' Forbidden\r\n'  # **************
HTTP_NOT_FOUND = 'HTTP/1.1 ' + str(FILE_NOT_FOUND_ERROR) + ' Not Found\r\n'  # **************
HTTP_INTERNAL_SERVER_ERR = 'HTTP/1.1 ' + str(INTERNAL_SERVER_ERROR) + ' Internal Server Error\r\n'

REDIRECTION_DICTIONARY = {
    '/forbidden': (FORBIDDEN_ERROR, "Forbidden"),
    '/moved': (HTTP_FOUND, '/index.html'),
    '/error': (INTERNAL_SERVER_ERROR, "Internal Server Error"),
}

QUEUE_SIZE = 10
IP = '0.0.0.0'
PORT = 80
SOCKET_TIMEOUT = 2
BUFFER_SIZE = 1024


def protocol_receive(my_socket):
    """
    Protocol to receive message from client to server
    :param my_socket: The socket for communication
    :return: message sent from client
    """
    try:
        return my_socket.recv(BUFFER_SIZE).decode()
    except socket.error as e:
        logging.error(f"Socket error: {e}")
        return ''
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return ''


def get_file_data(file_name):
    """
    Get data from file
    :param file_name: the name of the file
    :return: the file data in a string
    """
    try:
        with open(file_name, 'rb') as file:
            return file.read()
    except FileNotFoundError:
        logging.error(f"Error: File '{file_name}' not found.")
    except OSError as e:
        logging.error(f"An unexpected error occurred: {e}")


def get_content_type(file_type):
    """
    Get the Content-Type header based on the file type
    :param file_type: The file type
    :return: The content type
    """
    content_types = {
        'html': 'text/html;charset=utf-8',
        'jpg': 'image/jpeg',
        'css': 'text/css',
        'js': 'text/javascript; charset=UTF-8',
        'txt': 'text/plain',
        'ico': 'image/x-icon',
        'gif': 'image/jpeg',
        'png': 'image/png',
    }
    return content_types.get(file_type, 'application/octet-stream')


def handle_error(client_socket, status_code, status_text):
    """
    Send an error response to the client
    :param client_socket: The client socket
    :param status_code: The status code
    :param status_text: The status text
    :return:
    """
    if status_code == FILE_NOT_FOUND_ERROR:
        # Custom Not Found Page with Image
        error_page_path = "C:\\work\\cyber\\webroot\\404.jpeg"
        image_path = "C:\\work\\cyber\\webroot\\404.jpeg"
        if os.path.exists(error_page_path):
            with open(error_page_path, 'rb') as error_page_file:
                error_page_data = error_page_file.read()
            content_type = 'text/html;charset=utf-8'
        else:
            error_page_data = b"<html><body><h1>404 Not Found</h1></body></html>"
            content_type = 'text/html;charset=utf-8'
        if os.path.exists(image_path):
            with open(image_path, 'rb') as image_file:
                image_data = image_file.read()
            image_content_type = 'image/jpeg'
            content_type += f"\r\nContent-Type: {image_content_type}"
            # Add image data to the error page
            error_page_data = error_page_data.replace(b"<!-- INSERT_IMAGE_HERE -->", image_data)
        error_header = f"{HTTP_NOT_FOUND}Content-Type: {content_type}\r\nContent-Length: {len(error_page_data)}\r\n\r\n"
        error_response = error_header.encode() + error_page_data
        client_socket.send(error_response)
    else:
        error_message = f"{status_code} {status_text}"
        error_header = f"{HTTP_INTERNAL_SERVER_ERR}Content-Type: text/plain\r\nContent-Length: {len(error_message)}\r\n\r\n"
        error_response = error_header.encode() + error_message.encode()
        client_socket.send(error_response)


def handle_redirection(client_socket, new_location):
    """
    Send a redirection response to the client
    :param client_socket: The client socket
    :param new_location: The new location
    :return: None
    """
    redirection_header = f"{HTTP_FOUND}Location: {new_location}\r\n\r\n"
    redirection_response = redirection_header.encode()
    client_socket.send(redirection_response)


def validate_http_request(request):
    """
    Check if request is a valid HTTP request and returns TRUE / FALSE and
    the requested URL
    :param request: the request which was received from the client
    :return: a tuple of (True/False - depending on if the request is valid,
    the requested resource )
    """
    try:
        request_line = request.split('\r\n')
        method, resource, http_version = request_line[0].split(' ')
        if method != 'GET' or http_version != "HTTP/1.1":
            return False, ''
        return True, resource
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return False, ''


def handle_client_request(resource, client_socket):
    """
    Check the required resource, generate proper HTTP response and send
    to client
    :param resource: the required resource
    :param client_socket: a socket for the communication with the client
    :return: None
    """
    """ """
    if resource == '/' or resource == ' ':
        uri = DEFAULT_URL
    else:
        uri = resource

    filename = ROOT_WEB + uri

    if uri in REDIRECTION_DICTIONARY:
        status_code, response_data = REDIRECTION_DICTIONARY[uri]
        if status_code == HTTP_FOUND:
            handle_redirection(client_socket, response_data)
        else:
            handle_error(client_socket, status_code, response_data)
        return

    if not os.path.exists(filename):
        handle_error(client_socket, FILE_NOT_FOUND_ERROR, "Not Found")
        return

    file_type = uri.split('.')[-1]
    http_header = f"{HTTP_OK}Content-Type: {get_content_type(file_type)}\r\n"

    # Read the data from the file
    data = get_file_data(filename)
    http_header += f"Content-Length: {len(data)}\r\n\r\n"

    # http_header should be encoded before sent
    # data encoding depends on its content. text should be encoded, while files shouldn't
    http_response = http_header.encode() + data
    client_socket.send(http_response)


def handle_client(client_socket):
    """
    Handles client requests: verifies client's requests are legal HTTP, calls
    function to handle the requests
    :param client_socket: the socket for the communication with the client
    :return: None
    """
    logging.info("Client connected")
    try:
        while True:
            logging.debug("in handle client loop")
            client_request = protocol_receive(client_socket)
            if client_request != '':
                valid_http, resource = validate_http_request(client_request)
                if valid_http:
                    logging.info('Got a valid HTTP request')
                    handle_client_request(resource, client_socket)
                else:
                    logging.error('Error: Not a valid HTTP request')
                    handle_error(client_socket, INVALID_REQUEST_ERROR, "Bad Request")
                    break
            else:
                logging.error('Error: Not a valid HTTP request')
                handle_error(client_socket, INVALID_REQUEST_ERROR, "Bad Request")
                break
    except socket.error as err:
        logging.error(f'Received socket exception: {err}')
    finally:
        # client_socket.close()
        logging.info('Closing connection')


def main():
    logging.basicConfig(filename="server.log", level=logging.DEBUG)
    # Open a socket and loop forever while waiting for clients
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((IP, PORT))
        server_socket.listen(QUEUE_SIZE)
        print("Listening for connections on port %d" % PORT)
        while True:
            client_socket, client_address = server_socket.accept()
            try:
                logging.info('New connection received')
                client_socket.settimeout(SOCKET_TIMEOUT)
                handle_client(client_socket)
            except socket.error as err:
                logging.error('received socket exception - ' + str(err))
            finally:
                client_socket.close()
    except socket.error as err:
        logging.error('received socket exception - ' + str(err))
    finally:
        server_socket.close()


if __name__ == "__main__":
    # Call the main handler function
    main()
