import json
from collections import deque

import numpy as np
import paho.mqtt.client as mqtt

BROKER, PORT = "localhost", 1883
T_IN, T_OUT = "soc/node1/telemetry", "soc/node1/prediction"
W, H = 5, 5                      # fenêtre de 5 angles, horizon de 5 échantillons


with open("model.json") as fh:
    m = json.load(fh)
coef = np.array(m["coef"])       # 5 poids
intercept = m["intercept"]       # biais
print("modèle chargé :", np.round(coef, 3), round(intercept, 1))


window = deque(maxlen=W)         # derniers angles filtrés reçus
pending = deque()                # prédictions en attente de leur valeur réelle
errors = []


def on_connect(client, userdata, flags, reason_code, properties):
    print("connecté au broker, code :", reason_code)
    client.subscribe(T_IN)


def on_message(client, userdata, msg):
    d = json.loads(msg.payload)
    angle = d["pitch_filt"]

    # la prédiction faite il y a H échantillons se compare à l'angle réel d'aujourd'hui
    if len(pending) == H:
        errors.append(abs(pending.popleft() - angle))

    window.append(angle)
    if len(window) == W:
        pred = float(np.dot(coef, list(window)) + intercept)
        pending.append(pred)
        client.publish(T_OUT, json.dumps({"t_ms": d["t_ms"],
                                          "pitch_pred_100ms": round(pred)}))
        if d["t_ms"] % 500 == 0:
            mae = np.mean(errors) if errors else float("nan")
            print(f"t={d['t_ms']} ms  angle={angle}  prédit(+100 ms)={round(pred)}"
                  f"  écart courant={mae:.1f} cdeg")


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT)
client.loop_forever()
