# import socket
# import time
#      # 50 ms entre deux octets
# s = socket.create_connection(("localhost", 4567))
# s.settimeout(10)

# buf = b""
# while b"READY" not in buf:
#     buf += s.recv(10000)
# print("READY reçu :", buf)

# for b in b"500,0,866\n":
#     s.sendall(bytes([b]))
#     time.sleep(0.05) 
# print("ligne envoyée")

# buf = b""
# t0 = time.time()                     # heure de départ
# while time.time() - t0 < 5:          # tant que moins de 5 s se sont écoulées
#     try:
#         buf += s.recv(200)           # ajoute ce qui arrive
#     except socket.timeout:
#         pass                         # rien reçu pendant 1 s, on continue
# print("reçu :", buf)

# s.close()


import socket

s = socket.create_connection(("localhost",4567))
f = s.makefile("rw",newline="\n")

def read_line():
    while True:
        line = f.readline().strip()
        if line and not line.startswith("#") and line != "READY":
            return line
while True:
    ligne = f.readline().strip()
    if ligne == "READY":
        break
f.write("0,0,1000\n")
f.flush()
print("recu:",read_line())