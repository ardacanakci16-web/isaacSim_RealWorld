import sys, pathlib
for pkg in ["numpy", "matplotlib", "PIL"]:
    __import__(pkg)
print("[OK] Python paketleri ve USD sahne dosyalari hazir.")
for u in ["esentepe_harita.usd", "Kampüs.usd", "UçakHarita.usd", "models/sabit_kanat_iha.usd"]:
    assert (pathlib.Path(__file__).resolve().parent.parent / u).exists(), f"Missing {u}"
print("[OK] Tum USD ve 3B IHA modelleri dogrulandi.")
