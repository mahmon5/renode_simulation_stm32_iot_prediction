import socket, math, random, csv
import json, time
import paho.mqtt.client as mqtt

mq = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mq.connect("localhost", 1883)
mq.loop_start()

HOST, PORT = "localhost", 4567
N, FS = 500, 50


def make_sensor(n, seed=42):
    rnd = random.Random(seed)
    rows = []
    for i in range(n):
        t = i / FS
        theta = math.radians(30*math.sin(2*math.pi*0.2*t)
                             + 10*math.sin(2*math.pi*0.7*t))
        ax = 1000*math.sin(theta) + rnd.gauss(0, 15)
        ay = rnd.gauss(0, 15)
        az = 1000*math.cos(theta) + rnd.gauss(0, 15)
        rows.append((round(ax), round(ay), round(az)))   # entiers en mg
    return rows


def c_div(a, b):                 # division entière du C : arrondi vers 0 (b > 0)
    q = abs(a) // b
    return q if a >= 0 else -q

class MA:                        # moyenne glissante sur 5 valeurs
    def __init__(self):
        self.buf = []
    def update(self, x):
        self.buf.append(x)
        if len(self.buf) > 5:
            self.buf.pop(0)
        return c_div(sum(self.buf), len(self.buf))

def pitch_cdeg(ax, az):          # centi-degrés, troncature vers 0 comme le C
    return int(math.atan2(ax, az) * 5729.578)


def read_reply(f):
    while True:
        line = f.readline()
        if line == "":
            raise ConnectionError("connexion fermée")
        line = line.strip()
        if line and not line.startswith("#") and line != "READY":
            return line
        if line.startswith("#"):
            print("firmware :", line)

s = socket.create_connection((HOST, PORT))
s.settimeout(10)
f = s.makefile("r", encoding="ascii", errors="ignore", newline="\n")

while f.readline().strip() != "READY":    # attendre READY avant tout envoi
    pass
print("READY reçu")

mx, my, mz = MA(), MA(), MA()
bad, max_pitch_err = 0, 0
out_rows = []

for i, (ax, ay, az) in enumerate(make_sensor(N)):
    s.sendall(f"{ax},{ay},{az}\n".encode())
    r = [int(v) for v in read_reply(f).split(",")]
    if len(r) != 9:
        print(i, "ligne mal formée :", r); bad += 1; continue

    fax, fay, faz = mx.update(ax), my.update(ay), mz.update(az)
    exp_raw  = pitch_cdeg(ax, az)
    exp_filt = pitch_cdeg(fax, faz)

    ok = (r[1:4] == [ax, ay, az] and r[4:7] == [fax, fay, faz]
          and abs(r[7] - exp_raw) <= 1 and abs(r[8] - exp_filt) <= 1)
    max_pitch_err = max(max_pitch_err, abs(r[7]-exp_raw), abs(r[8]-exp_filt))
    if not ok:
        bad += 1
        if bad <= 10:
            print(f"écart à i={i} : reçu {r[1:]} / attendu "
                  f"{[ax,ay,az,fax,fay,faz,exp_raw,exp_filt]}")
    mq.publish("soc/node1/telemetry", json.dumps({
               "t_ms": i*20, "ax": r[1], "ay": r[2], "az": r[3],
               "pitch_raw": r[7], "pitch_filt": r[8]}))
    if i % 50 == 0:
        print("publié", i)
    time.sleep(0.02)     
    out_rows.append([i*20] + r[1:])

s.close()
time.sleep(0.5)
mq.loop_stop()
mq.disconnect()
print(f"{N} échantillons, {bad} écarts, erreur max d'angle = {max_pitch_err} centi-deg")

with open("sim_data.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["t_ms","ax","ay","az","fax","fay","faz","pitch_raw","pitch_filt"])
    w.writerows(out_rows)
print("sim_data.csv écrit")