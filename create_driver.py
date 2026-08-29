import json
import shutil
import os
import subprocess
import time
import urllib.request
from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager

EDGE_PATH  = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
DEBUG_PORT = 9222

STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
window.chrome = { runtime: {} };
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) => (
    parameters.name === 'notifications'
        ? Promise.resolve({ state: Notification.permission })
        : originalQuery(parameters)
);
"""

REAL_PROFILE = r"C:\Users\<User_account>\AppData\Local\Microsoft\Edge\User Data\Default"
SYNC_ITEMS = ["Cookies", "Login Data", "Local Storage", "Session Storage"]

def sync_profile_data(profile_path, profile_dir='Default'):
    print("[sync] Syncing cookies/session data from real Edge profile...")
    dest_dir = os.path.join(profile_path, profile_dir)
    os.makedirs(dest_dir, exist_ok=True)
    for item in SYNC_ITEMS:
        src = os.path.join(REAL_PROFILE, item)
        dst = os.path.join(dest_dir, item)
        try:
            if os.path.isdir(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            elif os.path.isfile(src):
                shutil.copy2(src, dst)
            print(f"[sync] Synced: {item}")
        except Exception as e:
            print(f"[sync][ERROR] Could not sync {item}: {e}")

def load_browser_config():
    with open('config.json', 'r') as f:
        config = json.load(f)
    return config.get('browser', {})

def create_driver(use_profile=False):
    profile_path = r'C:\SeleniumEdgeProfile'
    profile_dir  = 'Default'
    options = EdgeOptions()
    if use_profile:
        browser = load_browser_config()
        profile_path = browser.get('edge_profile_path', profile_path)
        profile_dir  = browser.get('edge_profile_directory', profile_dir)
        sync_profile_data(profile_path, profile_dir)
        options.add_argument('--user-data-dir=' + profile_path)
        options.add_argument('--profile-directory=' + profile_dir)
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--log-level=3')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36 Edg/149.0.0.0')
    driver = webdriver.Edge(
        service=EdgeService(EdgeChromiumDriverManager().install()),
        options=options
    )
    # Mask navigator.webdriver property
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
    })
    return driver
