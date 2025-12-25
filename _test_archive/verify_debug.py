
import os
import json
import sqlite3
import re
# Mock logger to avoid import issues
class MockLogger:
    def info(self, msg): print(f"[INFO] {msg}")
    def warning(self, msg): print(f"[WARN] {msg}")
    def error(self, msg): print(f"[ERROR] {msg}")
    def debug(self, msg): pass

import sys
# Hack to allow importing repository without utils.logger dependency if needed, 
# but utils.logger only imports standard libs so it should be fine if path is set.
sys.path.append(os.getcwd())

# We need to manually mock logger in utils.logger if we can't import it,
# but let's try importing repository. If it fails on logger, we'll see.
try:
    from storage.repository import MovieRepository
except ImportError:
    # If import fails, we might need to mock the whole module or fix path
    print("Import failed, ensure running from project root.")
    raise

CONFIG_PATH = "data/repo_config.json"

def test_persistence():
    print("--- Testing Persistence (Simplified) ---")
    
    # 1. Clear existing config
    if os.path.exists(CONFIG_PATH):
        os.remove(CONFIG_PATH)
        print(f"Removed existing config: {CONFIG_PATH}")
    
    # 2. Initialize repo (should default)
    repo = MovieRepository()
    print(f"Initial Table: {repo.table_name}")
    
    # 3. Set table to something else
    NEW_TABLE = "test_rag_table_v2"
    print(f"Setting table to: {NEW_TABLE}")
    repo.set_table(NEW_TABLE)
    
    # 4. Check if file exists
    if os.path.exists(CONFIG_PATH):
        print("Config file created.")
        with open(CONFIG_PATH, 'r') as f:
            print(f"Config content: {f.read()}")
    else:
        print("ERROR: Config file NOT created!")
        return
        
    # 5. Simulate Restart
    print("Simulating server restart (new Repo instance)...")
    repo2 = MovieRepository()
    print(f"New Repo Table: {repo2.table_name}")
    
    if repo2.table_name == NEW_TABLE:
        print("SUCCESS: Persistence working!")
    else:
        print(f"FAILURE: Expected {NEW_TABLE}, got {repo2.table_name}")

if __name__ == "__main__":
    test_persistence()
