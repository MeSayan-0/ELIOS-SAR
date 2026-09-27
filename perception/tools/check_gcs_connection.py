#!/usr/bin/env python3
"""
ELIOS-SAR GCS Connectivity Diagnostic Tool
Quickly tests network reachability, firewall, and TCP ports (8765 & 8766) between Raspberry Pi and GCS.
"""

from pathlib import Path
import argparse
import os
import socket
import subprocess
import sys
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def test_tcp_port(host: str, port: int, timeout: float = 2.0) -> tuple[bool, str]:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        sock.close()
        return True, "OK"
    except socket.timeout:
        return False, "Connection Timed Out (Firewall or IP not reachable)"
    except ConnectionRefusedError:
        return False, "Connection Refused (GCS backend is not running on this port)"
    except Exception as e:
        return False, str(e)


def main():
    parser = argparse.ArgumentParser(description="Test connection to GCS computer")
    parser.add_argument(
        "--host",
        type=str,
        default=os.getenv("GCS_HOST", "127.0.0.1"),
        help="GCS Computer IP address",
    )
    parser.add_argument(
        "--video-port",
        type=int,
        default=int(os.getenv("VIDEO_PORT", 8765)),
        help="Video TCP stream port (default: 8765)",
    )
    parser.add_argument(
        "--ai-port",
        type=int,
        default=int(os.getenv("AI_PORT", 8766)),
        help="AI TCP stream port (default: 8766)",
    )
    args = parser.parse_args()

    local_ip = get_local_ip()

    print("=" * 65)
    print("ELIOS-SAR GCS CONNECTIVITY DIAGNOSTIC")
    print("=" * 65)
    print(f"[*] Raspberry Pi Local IP: {local_ip}")
    print(f"[*] Target GCS Host      : {args.host}")
    print(f"[*] Target Video Port    : {args.video_port} (TCP)")
    print(f"[*] Target AI Port       : {args.ai_port} (TCP)")
    print("-" * 65)

    # Subnet check
    pi_subnet = ".".join(local_ip.split(".")[:3])
    gcs_subnet = ".".join(args.host.split(".")[:3])
    if pi_subnet != gcs_subnet and args.host not in ("127.0.0.1", "localhost"):
        print(f"[!] WARNING: Subnet mismatch!")
        print(f"    Raspberry Pi is on subnet: {pi_subnet}.x")
        print(f"    Target GCS is on subnet  : {gcs_subnet}.x")
        print(f"    If both devices are on the same Wi-Fi, the GCS IP should start with: {pi_subnet}.xxx\n")

    # Ping check
    print(f"[*] Testing ICMP Ping to {args.host}...")
    try:
        ping_res = subprocess.run(
            ["ping", "-c", "2", "-W", "1", args.host],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if ping_res.returncode == 0:
            print("    [+] Ping successful!")
        else:
            print("    [-] Ping failed (host unreachable, or Windows Firewall ICMP echo disabled)")
    except Exception as e:
        print(f"    [-] Ping test error: {e}")

    # Video Port 8765
    print(f"[*] Testing Video Port {args.video_port} (TCP)...")
    v_ok, v_msg = test_tcp_port(args.host, args.video_port)
    if v_ok:
        print(f"    [+] Port {args.video_port} (Video) is OPEN and REACHABLE!")
    else:
        print(f"    [-] Port {args.video_port} (Video) FAILED: {v_msg}")

    # AI Port 8766
    print(f"[*] Testing AI Port {args.ai_port} (TCP)...")
    a_ok, a_msg = test_tcp_port(args.host, args.ai_port)
    if a_ok:
        print(f"    [+] Port {args.ai_port} (AI) is OPEN and REACHABLE!")
    else:
        print(f"    [-] Port {args.ai_port} (AI) FAILED: {a_msg}")

    print("=" * 65)
    if v_ok and a_ok:
        print("[SUCCESS] All GCS streaming ports are connected and ready!")
        print("You can run test_mp4_pipeline.py now.")
    else:
        print("[ACTION REQUIRED]")
        if not v_ok or not a_ok:
            print("1. Check GCS IP: Ensure you have the actual Wi-Fi IP of the GCS computer.")
            print("   - On Windows GCS machine: run 'ipconfig' in cmd/PowerShell (look for Wi-Fi IPv4).")
            print("2. Ensure GCS Backend is Running:")
            print("   - Start the backend on the other computer (listening on 8765 & 8766).")
            print("3. Check Firewall on the GCS computer:")
            print("   - On Windows (PowerShell as Admin):")
            print("     New-NetFirewallRule -DisplayName 'ELIOS GCS Ports' -Direction Inbound -LocalPort 8765,8766 -Protocol TCP -Action Allow")
    print("=" * 65)


if __name__ == "__main__":
    main()
