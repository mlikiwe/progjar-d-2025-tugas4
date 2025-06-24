import requests
import os

BASE_URL = "http://127.0.0.1:8889"
UPLOAD_DIR = "files/"

def list_files():
    """Mengirim GET request untuk melihat daftar file."""
    print("\n[CLIENT] -> Melakukan GET untuk melihat daftar file...")
    try:
        response = requests.get(f"{BASE_URL}/{UPLOAD_DIR}")
        print("[SERVER] -> Status Code:", response.status_code)
        print("[SERVER] -> Response Body:")
        print(response.text)
    except requests.exceptions.ConnectionError as e:
        print(f"Koneksi gagal: {e}")

def upload_file(filename):
    """Mengirim POST request untuk mengunggah file."""
    filepath = os.path.join(filename)
    if not os.path.exists(filepath):
        print(f"File {filename} tidak ditemukan.")
        with open(filepath, 'w') as f:
            f.write("Ini adalah file tes untuk diunggah.")
        print(f"File dummy '{filename}' dibuat.")

    print(f"\n[CLIENT] -> Melakukan POST untuk mengunggah file: {filename}...")
    try:
        with open(filepath, 'rb') as f:
            files = {'file': (filename, f)}
            response = requests.post(f"{BASE_URL}/upload", files=files)
            print("[SERVER] -> Status Code:", response.status_code)
            print("[SERVER] -> Response Body:", response.text)
    except requests.exceptions.ConnectionError as e:
        print(f"Koneksi gagal: {e}")

def delete_file(filename):
    """Mengirim DELETE request untuk menghapus file."""
    print(f"\n[CLIENT] -> Melakukan DELETE untuk menghapus file: {filename}...")
    try:
        response = requests.delete(f"{BASE_URL}/{UPLOAD_DIR}{filename}")
        print("[SERVER] -> Status Code:", response.status_code)
        print("[SERVER] -> Response Body:", response.text)
    except requests.exceptions.ConnectionError as e:
        print(f"Koneksi gagal: {e}")

if __name__ == "__main__":
    list_files()
    
    upload_file("testfile.txt")
    upload_file("pokijan.jpg")
    upload_file("donalbebek.jpg")
    upload_file("research_center.jpg")
    
    list_files()
    
    delete_file("testfile.txt")
    
    list_files()