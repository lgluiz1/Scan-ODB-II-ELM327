"""Packaging script to build standalone Windows OBDScanner.exe.
"""
import subprocess
import sys
import os
import shutil


def build():
    print("==================================================")
    print(" Compilando OBD Scanner para Windows com PyInstaller")
    print("==================================================")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(base_dir, "dist")
    build_dir = os.path.join(base_dir, "build")

    # Terminate running instances on Windows before overwriting
    if os.name == "nt":
        subprocess.run(["taskkill", "/F", "/IM", "OBDScanner.exe"], capture_output=True)

    pyinstaller_cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name=OBDScanner",
        "--noconfirm",
        "--clean",
        "--windowed",              # No terminal popup window
        "--onefile",               # Single standalone .exe
        "--noupx",                 # Disable UPX to prevent high CPU load and DLL corruption
        "--collect-all=pyserial",
        "--exclude-module=PySide6.QtWebEngineCore",
        "--exclude-module=PySide6.QtWebEngineWidgets",
        "--exclude-module=PySide6.Qt3DCore",
        "--exclude-module=PySide6.QtQuick",
        "--exclude-module=PySide6.QtQml",
        "--exclude-module=PySide6.QtMultimedia",
        "--exclude-module=PySide6.QtDesigner",
        "--exclude-module=matplotlib",
        "--exclude-module=scipy",
        "--exclude-module=numpy",
        "--exclude-module=tkinter",
        "--exclude-module=unittest",
        os.path.join(base_dir, "main.py")
    ]

    print(f"Executando comando otimizado: {' '.join(pyinstaller_cmd)}")
    
    # Run with BELOW_NORMAL priority on Windows to guarantee system never freezes
    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.BELOW_NORMAL_PRIORITY_CLASS

    result = subprocess.run(pyinstaller_cmd, cwd=base_dir, creationflags=creationflags)

    if result.returncode == 0:
        exe_path = os.path.join(dist_dir, "OBDScanner.exe")
        print("\n==================================================")
        print(" SUCESSO! Executável gerado:")
        print(f" {exe_path}")
        print(" O executável é 100% autônomo (não necessita de Python instalado).")
        print("==================================================")
        return True
    else:
        print("\n[ERRO] Falha ao compilar com PyInstaller.")
        return False


if __name__ == "__main__":
    success = build()
    sys.exit(0 if success else 1)
