from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import argparse
import json
import platform
import time
from poker.monte_carlo import simulate

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--simulations',type=int,default=10000)
    args = parser.parse_args()
    results = []
    for opponents in (1,3,8):
        start = time.perf_counter()
        result = simulate(('Ah','Kh'),('Qh','Jh','2c'),opponents,args.simulations,seed=42)
        elapsed = time.perf_counter()-start
        results.append({'opponents':opponents,'seconds':elapsed,'simulations_per_second':args.simulations/elapsed,**result.to_dict()})
    print(json.dumps({'python':platform.python_version(),'platform':platform.platform(),'results':results},indent=2))

if __name__ == '__main__':
    main()
