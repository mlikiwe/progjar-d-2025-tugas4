import os
import json
from glob import glob
from datetime import datetime
import base64

class HttpServer:
    def __init__(self):
        self.sessions = {}
        self.types = {}
        self.types['.pdf'] = 'application/pdf'
        self.types['.jpg'] = 'image/jpeg'
        self.types['.png'] = 'image/png'
        self.types['.txt'] = 'text/plain'
        self.types['.html'] = 'text/html'
        self.upload_dir = 'files/'
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)

    def response(self, kode=404, message='Not Found', messagebody=bytes(), headers={}):
        tanggal = datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
        resp = []
        resp.append(f"HTTP/1.1 {kode} {message}\r\n")
        resp.append(f"Date: {tanggal}\r\n")
        resp.append("Connection: close\r\n")
        resp.append("Server: myserver/1.0\r\n")
        resp.append(f"Content-Length: {len(messagebody)}\r\n")
        for kk in headers:
            resp.append(f"{kk}: {headers[kk]}\r\n")
        resp.append("\r\n")

        response_headers = ''.join(resp)
        
        if not isinstance(messagebody, bytes):
            messagebody = messagebody.encode()

        return response_headers.encode() + messagebody

    def proses(self, data: bytes): 
        header_end = data.find(b'\r\n\r\n')
        if header_end == -1:
            return self.response(400, 'Bad Request', b'Malformed request header')

        header_bytes = data[:header_end]
        body_bytes = data[header_end+4:]
        header_str = header_bytes.decode('utf-8')

        requests = header_str.split('\r\n')
        baris = requests[0]
        
        headers = {}
        for line in requests[1:]:
            if ": " in line:
                key, value = line.split(": ", 1)
                headers[key] = value

        j = baris.split(" ")
        try:
            method = j[0].upper().strip()
            object_address = j[1].strip()

            if method == 'GET':
                return self.http_get(object_address, headers)
            elif method == 'POST':
                content_type = headers.get('Content-Type', '')
                boundary = None
                if 'multipart/form-data' in content_type:
                    parts = content_type.split('; boundary=')
                    if len(parts) > 1:
                        boundary = parts[1]
                
                return self.http_post(object_address, headers, body_bytes, boundary)

            elif method == 'DELETE':
                return self.http_delete(object_address, headers)
            else:
                return self.response(405, 'Method Not Allowed', b'Method Not Allowed', {})
        except IndexError:
            return self.response(400, 'Bad Request', b'Bad Request', {})

    def http_get(self, object_address, headers):
        path = object_address.lstrip('/')
        
        if '..' in path:
            return self.response(403, 'Forbidden', b'Access is forbidden.', {})

        if path == '':
            path = self.upload_dir

        if os.path.isdir(path):
            try:
                if not object_address.endswith('/'):
                    object_address += '/'
                
                file_list = os.listdir(path)
                html_body = f"<html><body><h1>Directory Listing for {object_address}</h1><ul>"
                for item in file_list:
                    # Buat link yang benar
                    item_url = f"{object_address}{item}"
                    html_body += f'<li><a href="{item_url}">{item}</a></li>'
                html_body += "</ul></body></html>"
                return self.response(200, 'OK', html_body.encode(), {'Content-Type': 'text/html'})
            except OSError as e:
                return self.response(500, 'Internal Server Error', f'Could not list directory: {e}'.encode(), {})

        elif os.path.isfile(path):
            try:
                with open(path, 'rb') as fp:
                    isi = fp.read()
                
                fext = os.path.splitext(path)[1].lower()
                content_type = self.types.get(fext, 'application/octet-stream')
                
                headers_resp = {'Content-Type': content_type}
                return self.response(200, 'OK', isi, headers_resp)
            except Exception as e:
                return self.response(500, 'Internal Server Error', f'Could not read file: {e}'.encode(), {})
        else:
            body_message = f"<h1>404 Not Found</h1><p>The requested path '{path}' was not found on this server.</p>"
            return self.response(404, 'Not Found', body_message.encode(), {'Content-Type': 'text/html'})

    def http_post(self, object_address, headers, body: bytes, boundary: str): # body sekarang bytes
        if object_address != '/upload' or not boundary:
            return self.response(400, 'Bad Request', b'Invalid POST request. Use /upload endpoint with multipart/form-data.', {})
        
        try:
            boundary_bytes = f'--{boundary}'.encode('utf-8')
            
            parts = body.split(boundary_bytes)
            for part in parts:
                if b'Content-Disposition: form-data;' in part:
                    try:
                        header_part_bytes, content_part_bytes = part.split(b'\r\n\r\n', 1)
                    except ValueError:
                        continue 

                    header_part_str = header_part_bytes.decode('utf-8')
                    if 'filename="' in header_part_str:
                        filename_start = header_part_str.find('filename="') + 10
                        filename_end = header_part_str.find('"', filename_start)
                        filename = header_part_str[filename_start:filename_end]
                        
                        file_content_bytes = content_part_bytes.rsplit(b'\r\n', 1)[0]
                        
                        filepath = os.path.join(self.upload_dir, os.path.basename(filename))
                        
                        with open(filepath, 'wb') as f:
                            f.write(file_content_bytes)
                            
                        return self.response(201, 'Created', f'File {filename} uploaded successfully.'.encode(), {})
            
            return self.response(400, 'Bad Request', b'File data not found in POST request.', {})

        except Exception as e:
            return self.response(500, 'Internal Server Error', f'Error processing upload: {str(e)}'.encode(), {})

    def http_delete(self, object_address, headers):
        filepath = os.path.join(self.upload_dir, os.path.basename(object_address))

        if not os.path.abspath(filepath).startswith(os.path.abspath(self.upload_dir)):
            return self.response(403, 'Forbidden', b'Access is forbidden.', {})

        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                return self.response(200, 'OK', f'File {os.path.basename(filepath)} deleted.'.encode(), {})
            except OSError:
                return self.response(500, 'Internal Server Error', b'Error deleting file.', {})
        else:
            return self.response(404, 'Not Found', b'File not found.', {})