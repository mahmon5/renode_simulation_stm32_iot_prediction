import json

import matplotlib
matplotlib.use("Agg")            # pas de fenêtre : la figure est enregistrée dans un fichier
import matplotlib.pyplot as plt
import numpy as np
import paho.mqtt.client as mqtt

BROKER, PORT = "localhost", 1883
T_IN, T_OUT = "soc/node1/telemetry", "soc/node1/prediction"
W, H = 5, 5                      # fenêtre de 5 angles
N_EXPECTED = 500                 # nombre d'échantillons envoyés par sensor_sim


with open("model.json") as fh:
    m = json.load(fh)
coef = np.array(m["coef"])       
intercept = m["intercept"]       
print("modèle chargé :", np.round(coef, 3), round(intercept, 1))


ts, raw, filt = [], [], []       
preds = {}                       
errors = []                      


def on_connect(client, userdata, flags, reason_code, properties):
    print("connecté au broker, code :", reason_code)
    client.subscribe(T_IN)


def on_message(client, userdata, msg):
    d = json.loads(msg.payload)
    ts.append(d["t_ms"])
    raw.append(d["pitch_raw"])
    filt.append(d["pitch_filt"])
    i = len(filt) - 1

   
    if (i - H) in preds:
        errors.append(abs(preds[i - H] - filt[i]))

    if len(filt) >= W:           
        pred = float(np.dot(coef, filt[-W:]) + intercept)
        preds[i] = pred
        client.publish(T_OUT, json.dumps({"t_ms": d["t_ms"],
                                          "pitch_pred_100ms": round(pred)}))
        if d["t_ms"] % 500 == 0:
            mae = np.mean(errors) if errors else float("nan")
            print(f"t={d['t_ms']} ms  angle={d['pitch_filt']}  prédit(+100 ms)={round(pred)}"
                  f"  écart courant={mae:.1f} cdeg")

    if len(filt) >= N_EXPECTED:  
        client.disconnect()


def make_plot():
    idx = [i for i in preds if i + H < len(filt)]
    if not idx:
        print("pas assez d'échantillons reçus pour tracer la courbe")
        return
    t = np.array([ts[i + H] for i in idx]) / 1000          # instant visé, en secondes
    target = np.array([filt[i + H] for i in idx]) / 100    # angle filtré réellement mesuré
    pred = np.array([preds[i] for i in idx]) / 100         # angle prédit 100 ms plus tôt
    raw_t = np.array([raw[i + H] for i in idx]) / 100      # angle brut mesuré
    naive = np.array([filt[i] for i in idx]) / 100         # référence naïve : dernier angle connu

    mae_pred = np.mean(np.abs(target - pred))
    mae_naive = np.mean(np.abs(target - naive))
    print(f"\nflux complet : {len(idx)} prédictions comparées à l'angle réel")
    print(f"MAE prédiction : {mae_pred:.2f} deg, MAE référence naïve : {mae_naive:.2f} deg")

    plt.figure(figsize=(10, 4.5))
    plt.plot(t, raw_t, color="0.75", linewidth=0.8, label="angle brut mesuré")
    plt.plot(t, target, label="angle filtré mesuré (cible)")
    plt.plot(t, pred, "--", label="angle prédit (calculé 100 ms plus tôt)")
    plt.xlabel("temps (s)")
    plt.ylabel("angle (deg)")
    plt.title(f"Prédiction à +100 ms contre angle mesuré : MAE {mae_pred:.2f} deg "
              f"(référence naïve {mae_naive:.2f} deg)")
    lo, hi = min(raw_t.min(), pred.min()), max(raw_t.max(), pred.max())
    plt.ylim(lo - 0.05 * (hi - lo), hi + 0.25 * (hi - lo))   # place pour la légende en haut
    plt.legend(loc="upper center", ncol=3, frameon=False)
    plt.tight_layout()
    plt.savefig("resultats_app.png", dpi=150)
    print("resultats_app.png écrit")


if __name__ == "__main__":
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT)
    try:
        client.loop_forever()
    except KeyboardInterrupt:    
        client.disconnect()
    make_plot()
