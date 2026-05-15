import os
import sys
import time
import json
import subprocess
import traceback

CYBRA_HOME = os.path.expanduser("~/.cybra")
STATE_FILE = f"{CYBRA_HOME}/state.json"
REPO_DIR = f"{CYBRA_HOME}/repo"

OWNER = "Lubnysash1980"

def ensure():
    os.makedirs(CYBRA_HOME, exist_ok=True)
    if not os.path.exists(STATE_FILE):
        save_state({
            "status": "active",
            "mode": "autostable",
            "owner": OWNER,
            "crashes": 0,
            "last_update": None
        })

def load_state():
    ensure()
    with open(STATE_FILE) as f:
        return json.load(f)

def save_state(data):
    os.makedirs(CYBRA_HOME, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(data, f, indent=2)

class AutoStable:
    def health(self):
        st = load_state()
        print("[CYBRA HEALTH]", st)

    def load(self):
        st = load_state()
        st["status"] = "loaded"
        save_state(st)
        print("[CYBRA] loaded")

    def reload(self):
        print("[CYBRA] reload runtime")
        os.execv(sys.executable, [sys.executable] + sys.argv)

    def update(self):
        print("[CYBRA] update from git")
        subprocess.run(["git", "-C", REPO_DIR, "pull"], check=False)
        st = load_state()
        st["last_update"] = time.time()
        save_state(st)

    def upgrade(self):
        print("[CYBRA] upgrade system")
        self.update()
        self.reload()

    def run(self):
        print("====================================")
        print(" CYBRA AUTOSTABLE ORCHESTRATOR")
        print("====================================")
        print("[OWNER]", OWNER)
        print("[MODE] autostable")
        print("[STATUS] active")

        while True:
            try:
                print("[CYBRA] stable heartbeat")
                time.sleep(5)
            except Exception:
                st = load_state()
                st["crashes"] += 1
                save_state(st)
                traceback.print_exc()
                time.sleep(3)

def main():
    ensure()
    c = AutoStable()

    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"

    if cmd == "health":
        c.health()
    elif cmd == "load":
        c.load()
    elif cmd == "reload":
        c.reload()
    elif cmd == "update":
        c.update()
    elif cmd == "upgrade":
        c.upgrade()
    else:
        c.run()

if __name__ == "__main__":
    main()
