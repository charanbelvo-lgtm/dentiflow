"""
DentiFlow Multi-Device Network & Tunnel Launcher
------------------------------------------------
This script runs DentiFlow on all network interfaces (0.0.0.0:5000)
and simultaneously launches a secure, instant Cloudflare Tunnel.

Features:
1. Detects your local Wi-Fi IP address (e.g., http://192.168.1.5:5000)
   so phones and tablets on the same Wi-Fi can open it immediately.
2. Launches an encrypted HTTPS Public URL (e.g., https://xxx.trycloudflare.com)
   so ANY device outside your Wi-Fi (e.g., cellular data, remote devices) can open it.
3. Automatically writes the URL to tunnel_url.txt for the in-app /mobile-connect page.
4. Clean shutdown on Ctrl+C.
"""

import os
import sys
import re
import time
import socket
import signal
import subprocess
import threading

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CLOUDFLARED_PATH = os.path.join(BASE_DIR, "cloudflared.exe")
TUNNEL_URL_FILE = os.path.join(BASE_DIR, "tunnel_url.txt")

def get_network_adapters():
    """Detect LAN IPv4 addresses on active network adapters (Wi-Fi / Ethernet)."""
    adapters = []
    try:
        output = subprocess.check_output('ipconfig', text=True, stderr=subprocess.DEVNULL)
        current_adapter = None
        for line in output.splitlines():
            if line and not line.startswith(' ') and ':' in line:
                current_adapter = line.strip().rstrip(':')
            elif current_adapter and 'IPv4 Address' in line:
                ip = line.split(':')[-1].strip()
                if ip and not ip.startswith('127.'):
                    adapters.append((current_adapter, ip))
    except Exception:
        pass

    if not adapters:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            sock_ip = s.getsockname()[0]
            s.close()
            if sock_ip and not sock_ip.startswith('127.'):
                adapters.append(('Local Network', sock_ip))
        except Exception:
            pass

    return adapters

def get_preferred_ip(adapters):
    for name, ip in adapters:
        if any(w in name.lower() for w in ['wi-fi', 'wifi', 'wireless', 'ethernet']):
            return ip
    if adapters:
        return adapters[-1][1]
    return '127.0.0.1'

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

def print_banner(local_url, wifi_url, public_url=None):
    border = "=" * 72
    print("\n" + border)
    print("   [DentiFlow] MULTI-DEVICE NETWORK & TUNNEL SERVER")
    print(border)
    print(" [1] THIS COMPUTER:")
    print(f"     >> {local_url}")
    print("")
    print(" [2] OTHER DEVICES ON THE SAME WI-FI (Phones / Tablets / PCs):")
    if wifi_url:
        print(f"     >> {wifi_url}")
        print("        (Make sure your phone or other device is on the same Wi-Fi)")
    else:
        print("     >> No Wi-Fi IP detected (check network connection)")
    print("")
    print(" [3] ANY DEVICE WORLDWIDE (Cellular 4G/5G / Remote / Outside Wi-Fi):")
    if public_url:
        print(f"     >> {public_url}")
        print("        (Free secure HTTPS tunnel - works from ANY device anywhere!)")
    else:
        print("     >> Generating secure Public URL, please wait 3-5 seconds...")
    print(border)
    print("Press Ctrl + C to stop the server.\n")

def run_cloudflared(port, on_url_ready):
    """Start cloudflared tunnel and extract trycloudflare.com URL."""
    if not os.path.isfile(CLOUDFLARED_PATH):
        print(f"[!] Warning: cloudflared.exe not found at {CLOUDFLARED_PATH}")
        return None

    cmd = [CLOUDFLARED_PATH, "tunnel", "--url", f"http://127.0.0.1:{port}"]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
    )

    url_found = False

    def monitor_stream(stream):
        nonlocal url_found
        for line in stream:
            m = re.search(r'https://[a-zA-Z0-9\-]+\.trycloudflare\.com', line)
            if m:
                public_url = m.group(0)
                try:
                    with open(TUNNEL_URL_FILE, 'w') as f:
                        f.write(public_url)
                except Exception:
                    pass
                os.environ['PUBLIC_TUNNEL_URL'] = public_url
                if not url_found:
                    url_found = True
                    on_url_ready(public_url)

    t_err = threading.Thread(target=monitor_stream, args=(proc.stderr,), daemon=True)
    t_out = threading.Thread(target=monitor_stream, args=(proc.stdout,), daemon=True)
    t_err.start()
    t_out.start()

    return proc

def main():
    port = int(os.environ.get('PORT', 5000))
    adapters = get_network_adapters()
    pref_ip = get_preferred_ip(adapters)
    local_url = f"http://localhost:{port}"
    wifi_url = f"http://{pref_ip}:{port}" if pref_ip else None

    # Clear old tunnel file
    if os.path.exists(TUNNEL_URL_FILE):
        try:
            os.remove(TUNNEL_URL_FILE)
        except Exception:
            pass

    print("\nStarting DentiFlow multi-device server...")
    print_banner(local_url, wifi_url, public_url=None)

    tunnel_proc = None

    def on_tunnel_url(public_url):
        print_banner(local_url, wifi_url, public_url=public_url)

    if os.path.isfile(CLOUDFLARED_PATH):
        tunnel_proc = run_cloudflared(port, on_tunnel_url)

    # Start Flask app
    try:
        from app import create_app
        app = create_app()
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("\nStopping DentiFlow...")
    finally:
        if tunnel_proc:
            tunnel_proc.terminate()
            try:
                tunnel_proc.wait(timeout=3)
            except Exception:
                tunnel_proc.kill()
        if os.path.exists(TUNNEL_URL_FILE):
            try:
                os.remove(TUNNEL_URL_FILE)
            except Exception:
                pass
        print("Server stopped cleanly. Goodbye!")

if __name__ == '__main__':
    main()
