from pathlib import Path
import subprocess
import sys

if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm',str(root/'PokerVisionAI.spec')],cwd=root,check=True)
