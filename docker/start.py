#!/usr/bin/env python3
"""
Social-Hunt Universal Startup Script
Automatically detects OS and starts Docker containers
"""

import os
import platform
import subprocess
import sys
import time


def print_banner():
    """Print startup banner"""
    print("=" * 50)
    print("  Social-Hunt Docker Startup")
    print("=" * 50)
    print()


def detect_os():
    """Detect the current operating system"""
    system = platform.system()
    print(f"Detected OS: {system}")
    return system


def check_docker_running():
    """Check if Docker daemon is running"""
    print("Checking if Docker is running...")
    try:
        result = subprocess.run(
            ["docker", "info"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
        )
        if result.returncode == 0:
            print("✓ Docker is running")
            return True
        else:
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def wait_for_docker(max_wait=60):
    """Wait for Docker to start (useful on system boot)"""
    print(f"Waiting for Docker to start (max {max_wait}s)...")
    start_time = time.time()

    while time.time() - start_time < max_wait:
        if check_docker_running():
            return True
        print(".", end="", flush=True)
        time.sleep(2)

    print()
    return False


def start_docker_desktop(os_type):
    """Attempt to start Docker Desktop on Windows/macOS"""
    print("Attempting to start Docker Desktop...")

    try:
        if os_type == "Windows":
            # Try to start Docker Desktop on Windows
            subprocess.Popen(
                ["C:\\Program Files\\Docker\\Docker\\Docker Desktop.exe"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            print("Docker Desktop launch initiated...")
            return wait_for_docker(90)

        elif os_type == "Darwin":  # macOS
            subprocess.Popen(
                ["open", "-a", "Docker"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            print("Docker Desktop launch initiated...")
            return wait_for_docker(90)

        elif os_type == "Linux":
            # Try to start Docker service on Linux
            print("Attempting to start Docker service...")
            result = subprocess.run(
                ["sudo", "systemctl", "start", "docker"], capture_output=True
            )
            if result.returncode == 0:
                time.sleep(5)
                return check_docker_running()
            else:
                print(
                    "Could not start Docker service. You may need to start it manually."
                )
                return False
    except Exception as e:
        print(f"Could not auto-start Docker: {e}")
        return False


def start_containers():
    """Start Social-Hunt containers using docker compose"""
    print()
    print("Starting Social-Hunt containers...")
    print()

    try:
        # Change to script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)

        # Run docker compose up
        result = subprocess.run(["docker", "compose", "up", "-d"], capture_output=False)

        if result.returncode == 0:
            print()
            print("=" * 50)
            print("✓ Social-Hunt started successfully!")
            print("=" * 50)
            print()
            print("Access the application at:")
            print("  → http://localhost:8000")
            print("  → http://127.0.0.1:8000")
            print()
            print("Useful commands:")
            print("  View logs:    docker compose logs -f social-hunt")
            print("  Stop:         docker compose down")
            print("  Restart:      docker compose restart")
            print("  Status:       docker compose ps")
            print()
            return True
        else:
            print()
            print("✗ Failed to start containers")
            print("Please check the error messages above")
            return False

    except FileNotFoundError:
        print()
        print("✗ Error: 'docker' command not found")
        print("Please ensure Docker is installed and in your PATH")
        return False
    except Exception as e:
        print()
        print(f"✗ Error starting containers: {e}")
        return False


def main():
    """Main execution function"""
    print_banner()

    # Detect OS
    os_type = detect_os()
    print()

    # Check if Docker is running
    docker_running = check_docker_running()

    if not docker_running:
        print()
        print("✗ Docker is not running!")
        print()

        # Ask user if they want to try starting Docker
        response = (
            input("Would you like to attempt to start Docker? (y/n): ").strip().lower()
        )

        if response in ["y", "yes"]:
            if not start_docker_desktop(os_type):
                print()
                print("Failed to start Docker automatically.")
                print()
                print("Please start Docker manually:")
                if os_type == "Windows" or os_type == "Darwin":
                    print("  - Open Docker Desktop")
                else:
                    print("  - Run: sudo systemctl start docker")
                print()
                return 1
        else:
            print()
            print("Please start Docker and run this script again.")
            return 1

    print()

    # Start containers
    if start_containers():
        return 0
    else:
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print()
        print()
        print("Startup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print()
        print(f"Unexpected error: {e}")
        sys.exit(1)
