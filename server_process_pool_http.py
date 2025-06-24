from socket import *
import socket
import time
import sys
import logging
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from my_http import HttpServer

httpserver = HttpServer()

def ProcessTheClient(connection, address):
    try:
        data = connection.recv(4096)
        if not data:
            connection.close()
            return

        header_str = data.split(b'\r\n\r\n', 1)[0].decode('utf-8', errors='ignore')
        content_length_header = [h for h in header_str.split('\r\n') if h.lower().startswith('content-length:')]
        
        total_size = 0
        if content_length_header:
            total_size = int(content_length_header[0].split(': ')[1])
        
        body_start_index = data.find(b'\r\n\r\n')
        if body_start_index != -1:
            header_len = body_start_index + 4
            body_received_len = len(data) - header_len
            
            while body_received_len < total_size:
                chunk = connection.recv(4096)
                if not chunk:
                    break
                data += chunk
                body_received_len += len(chunk)
        
        hasil = httpserver.proses(data)
        
        connection.sendall(hasil)
    except (OSError, ValueError) as e:
        logging.error(f"Error processing client {address}: {e}")
    finally:
        connection.close()

def Server():
	the_clients = []
	my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

	my_socket.bind(('0.0.0.0', 8889))
	my_socket.listen(1)

	with ProcessPoolExecutor(20) as executor:
		while True:
				connection, client_address = my_socket.accept()
				p = executor.submit(ProcessTheClient, connection, client_address)
				the_clients.append(p)
				jumlah = ['x' for i in the_clients if i.running()==True]
				print(jumlah)

def main():
	Server()

if __name__=="__main__":
	main()