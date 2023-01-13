import socket
from fastapi import FastAPI
from lxml import etree
import uvicorn

app = FastAPI()

host = 'localhost'
port = 4000

# Create a socket connection on startup
@app.on_event("startup")
def startup():
    global s
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))

# Close the socket connection on shutdown
@app.on_event("shutdown")
def shutdown():
    s.close()

# GET /conditioner
@app.get("/conditioner")
def get_conditioner_info():
    s.sendall(b'/get cond info\n')
    data = s.recv(1024)
    print(data)
    root = etree.fromstring(data)
    return {elem.tag: elem.text for elem in root.iter()}

# POST /conditioner/speed
@app.post("/conditioner/speed/{speed}")
def set_conditioner_speed(speed: int):
    s.sendall(f'/set speed {speed}\n'.encode())
    data = s.recv(1024)
    root = etree.fromstring(data)
    return {elem.tag: elem.text for elem in root.iter()}

# POST /conditioner/t_in
@app.post("/conditioner/t_in/{t_in}")
def set_conditioner_t_in(t_in: int):
    s.sendall(f'/set t_in {t_in}\n'.encode())
    data = s.recv(1024)
    root = etree.fromstring(data)
    return {elem.tag: elem.text for elem in root.iter()}

# Run the application
if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
