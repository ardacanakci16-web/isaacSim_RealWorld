import subprocess, sys, shutil
from pathlib import Path
root = Path(__file__).resolve().parent.parent
subprocess.run([sys.executable, str(root / "src" / "render_preview.py")], cwd=root / "models", check=False)
print("[OK] plots/sonuc_1.png hazir.")
