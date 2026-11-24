import json, os
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt

W, H = 5, 5                      # fenêtre de 5 angles, horizon de 5 échantillons


def make_windows(x, y):
    X, Y = [], []
    for i in range(W - 1, len(x) - H):
        X.append(x[i - W + 1 : i + 1])   # 5 angles se terminant en i
        Y.append(y[i + H])               # cible : angle en i+5
    return np.array(X), np.array(Y)


def metrics(y_true, y_pred):
    err = y_true - y_pred
    return np.mean(np.abs(err)), np.sqrt(np.mean(err ** 2))


def show(title, results):
    print(f"\n{title}")
    print(f"{'entrée':<8}{'méthode':<12}{'MAE (cdeg)':>12}{'RMSE (cdeg)':>13}{'MAE (deg)':>11}")
    for name, (nv, rg, _) in results.items():
        print(f"{name:<8}{'naïve':<12}{nv[0]:>12.1f}{nv[1]:>13.1f}{nv[0]/100:>11.2f}")
        print(f"{name:<8}{'régression':<12}{rg[0]:>12.1f}{rg[1]:>13.1f}{rg[0]/100:>11.2f}")



df = pd.read_csv("sim_data.csv")
raw  = df["pitch_raw"].to_numpy(dtype=float)
filt = df["pitch_filt"].to_numpy(dtype=float)

X_raw,  y = make_windows(raw,  filt)
X_filt, _ = make_windows(filt, filt)

split = int(0.7 * len(y))                # coupe chronologique 70/30

models = {}
results = {}
y_test = y[split:]

for name, X in [("brut", X_raw), ("filtré", X_filt)]:
    model = LinearRegression().fit(X[:split], y[:split])   # entraînement seulement
    models[name] = model
    pred = model.predict(X[split:])
    naive = X[split:, -1]                                  # dernier angle connu
    results[name] = (metrics(y_test, naive), metrics(y_test, pred), pred)
    print(f"\nEntrée {name} :")
    print("  poids :", np.round(model.coef_, 3), " biais :", round(model.intercept_, 1))

    if name == "filtré":                                   # modèle déployé par app_predict.py
        with open("model.json", "w") as fh:
            json.dump({"coef": model.coef_.tolist(),
                       "intercept": float(model.intercept_)}, fh)
        print("  model.json écrit")

print(f"\n{len(y)} exemples, {split} pour l'entraînement, {len(y) - split} pour le test")
show("Test interne (30 % finaux du même signal)", results)


t = df["t_ms"].to_numpy()[W - 1 + H + split : W - 1 + H + split + len(y_test)] / 1000
plt.figure(figsize=(9, 4))
plt.plot(t, y_test / 100, label="cible (angle filtré à +100 ms)")
plt.plot(t, X_filt[split:, -1] / 100, "--", label="naïve (filtré)")
plt.plot(t, results["filtré"][2] / 100, label="régression (entrée filtrée)")
plt.xlabel("temps (s)"); plt.ylabel("angle (deg)"); plt.legend(); plt.tight_layout()
plt.savefig("resultats_s7.png", dpi=150)
print("\nresultats_s7.png écrit")


if os.path.exists("sim_test.csv"):
    dt = pd.read_csv("sim_test.csv")
    raw_t  = dt["pitch_raw"].to_numpy(dtype=float)
    filt_t = dt["pitch_filt"].to_numpy(dtype=float)
    Xr_t, y_t = make_windows(raw_t,  filt_t)
    Xf_t, _   = make_windows(filt_t, filt_t)

    ext = {}
    for name, X_t in [("brut", Xr_t), ("filtré", Xf_t)]:
        pred_t = models[name].predict(X_t)                 # aucun réentraînement
        ext[name] = (metrics(y_t, X_t[:, -1]), metrics(y_t, pred_t), pred_t)
    print(f"\n{len(y_t)} exemples dans sim_test.csv (signal jamais vu à l'entraînement)")
    show("Test externe (autre signal : fréquences, amplitudes et bruit différents)", ext)

    t2 = dt["t_ms"].to_numpy()[W - 1 + H : W - 1 + H + len(y_t)] / 1000
    plt.figure(figsize=(9, 4))
    plt.plot(t2, y_t / 100, label="cible (angle filtré à +100 ms)")
    plt.plot(t2, Xf_t[:, -1] / 100, "--", label="naïve (filtré)")
    plt.plot(t2, ext["filtré"][2] / 100, label="régression (entrée filtrée)")
    plt.xlabel("temps (s)"); plt.ylabel("angle (deg)"); plt.legend(); plt.tight_layout()
    plt.savefig("resultats_test_externe.png", dpi=150)
    print("\nresultats_test_externe.png écrit")
else:
    print("\nsim_test.csv absent : lance `python3 sensor_sim.py test` pour le test externe")
