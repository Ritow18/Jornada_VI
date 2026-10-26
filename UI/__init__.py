import subprocess
import sys

scripts = [
    "TPrincipal.py"
]

proc = []

for script in scripts:
    print(f"iniciando{script}...")
    p = subprocess.Popen([sys.executable,script])
    proc.append(p)

print("scripts iniciados, ctrl + c para finalizar todos")

try:
    for p in proc:
        p.wait()
except KeyboardInterrupt:
    print("encerrando")
    for p in proc:
        p.terminate()
