#!/usr/bin/env python


import os
import sys
import subprocess
import time
import signal
from pathlib import Path
from typing import Optional, List
import argparse
import threading
import json
from datetime import datetime
import shutil

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header():
    """Print startup header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("=" * 70)
    print("  private-converter Development Stack")
    print("=" * 70)
    print(f"{Colors.RESET}\n")

def log_service(service_name: str, message: str, status: str = "INFO"):
    """Log messages with service prefix and timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    if status == "INFO":
        color = Colors.CYAN
    elif status == "SUCCESS":
        color = Colors.GREEN
    elif status == "ERROR":
        color = Colors.RED
    elif status == "WARN":
        color = Colors.YELLOW
    else:
        color = Colors.RESET
    
    print(f"{color}[{timestamp}] {service_name:15} | {message}{Colors.RESET}")

def get_project_root() -> Path:
    """Get the private-converter project root"""
    return Path(__file__).parent

def get_venv_python() -> str:
    """Get the Python executable from the virtual environment"""
    project_root = get_project_root()
    venv_path = project_root / ".venv"
    
    if sys.platform == "win32":
        python_exe = venv_path / "Scripts" / "python.exe"
    else:
        python_exe = venv_path / "bin" / "python"
    
    if python_exe.exists():
        return str(python_exe)
    else:
        # Fallback to system Python
        log_service("STARTUP", f"venv not found at {venv_path}, using system python", "WARN")
        return sys.executable

def check_redis_running(host: str = "localhost", port: int = 6379) -> bool:
    """Check if Redis is already running"""
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False

def start_redis() -> Optional[subprocess.Popen]:
    """Start Redis using docker-compose"""
    project_root = get_project_root()
    compose_file = project_root / "docker-compose.yml"
    
    if not compose_file.exists():
        log_service("REDIS", f"docker-compose.yml not found", "ERROR")
        return None
    
    try:
        log_service("REDIS", "Starting Redis container...", "INFO")
        process = subprocess.Popen(
            ["docker-compose", "-f", str(compose_file), "up", "redis"],
            cwd=str(project_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        time.sleep(3)  # Give Redis time to start
        
        if check_redis_running():
            log_service("REDIS", "✓ Redis running on localhost:6379", "SUCCESS")
            return process
        else:
            log_service("REDIS", "Redis started but not responding, retrying...", "WARN")
            time.sleep(2)
            if check_redis_running():
                log_service("REDIS", "✓ Redis now responding", "SUCCESS")
                return process
            else:
                log_service("REDIS", "Redis not responding after startup", "ERROR")
                return process
    except FileNotFoundError:
        log_service("REDIS", "docker-compose not found. Ensure Docker Desktop is running.", "ERROR")
        return None
    except Exception as e:
        log_service("REDIS", f"Failed to start Redis: {e}", "ERROR")
        return None

def start_backend(python_exe: str, backend_dir: Path) -> Optional[subprocess.Popen]:
    """Start Django development server (no blocking timeouts)"""
    log_service("BACKEND", "Starting Django dev server...", "INFO")

    try:
        process = subprocess.Popen(
            [python_exe, "manage.py", "runserver", "0.0.0.0:8000"],
            cwd=str(backend_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env={**os.environ, "PYTHONUNBUFFERED": "1"}
        )

        # No waiting; let streaming thread handle logs
        log_service("BACKEND", f"✓ Django dev server started (PID: {process.pid})", "SUCCESS")
        return process

    except Exception as e:
        log_service("BACKEND", f"Failed to start backend: {e}", "ERROR")
        return None

def start_celery(python_exe: str, backend_dir: Path) -> Optional[subprocess.Popen]:
    """Start Celery worker (no timeout waits)"""
    log_service("CELERY", "Starting Celery worker...", "INFO")

    try:
        process = subprocess.Popen(
            [python_exe, "-m", "celery", "-A", "celery_config", "worker", "-l", "debug"],
            cwd=str(backend_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env={**os.environ, "PYTHONUNBUFFERED": "1"}
        )

        log_service("CELERY", f"✓ Celery worker started (PID: {process.pid})", "SUCCESS")
        return process

    except Exception as e:
        log_service("CELERY", f"Failed to start Celery: {e}", "ERROR")
        return None

def start_frontend(frontend_dir: Path) -> Optional[subprocess.Popen]:
    """Start React frontend dev server (no blocking waits)"""
    log_service("FRONTEND", "Starting React dev server...", "INFO")

    try:
        if sys.platform == "win32":
            npm_cmd = shutil.which("npm.cmd") or shutil.which("npm")
        else:
            npm_cmd = shutil.which("npm")

        if not npm_cmd:
            log_service("FRONTEND", "npm not found in PATH.", "ERROR")
            return None

        # Install dependencies if first run — no timeout
        node_modules = frontend_dir / "node_modules"
        if not node_modules.exists():
            log_service("FRONTEND", "Installing dependencies...", "INFO")
            install_proc = subprocess.run(
                [npm_cmd, "install"],
                cwd=str(frontend_dir),
                capture_output=True,
                text=True
            )
            if install_proc.returncode != 0:
                log_service("FRONTEND", install_proc.stderr or "npm install failed.", "ERROR")
                return None

        process = subprocess.Popen(
            [npm_cmd, "run", "dev"],
            cwd=str(frontend_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        log_service("FRONTEND", f"✓ React dev server started (PID: {process.pid})", "SUCCESS")
        return process

    except Exception as e:
        log_service("FRONTEND", f"Failed to start frontend: {e}", "ERROR")
        return None


def stream_process_output(process: subprocess.Popen, service_name: str, stop_event: threading.Event):
    """Stream process output to console in a separate thread"""
    try:
        while not stop_event.is_set() and process.poll() is None:
            line = process.stdout.readline()
            if line:
                # Filter out noisy warnings
                if "pkg_resources" not in line and "UserWarning" not in line:
                    log_service(service_name, line.strip(), "INFO")
    except Exception:
        pass

def print_summary(backend_port: int = 8000, frontend_port: int = 5173):
    """Print stack summary"""
    print(f"\n{Colors.BOLD}{Colors.GREEN}")
    print("=" * 70)
    print("  ✓ private-converter Stack is Ready!")
    print("=" * 70)
    print(f"{Colors.RESET}\n")
    
    print(f"{Colors.BOLD}URLs:{Colors.RESET}")
    print(f"  Backend API:      {Colors.CYAN}http://127.0.0.1:{backend_port}/{Colors.RESET}")
    print(f"  API Docs:         {Colors.CYAN}http://127.0.0.1:{backend_port}/api/schema/{Colors.RESET}")
    print(f"  Frontend:         {Colors.CYAN}http://localhost:{frontend_port}/{Colors.RESET}")
    
    print(f"{Colors.BOLD}Services:{Colors.RESET}")
    print(f"  {Colors.GREEN}✓{Colors.RESET} Django Backend (PID: TBD)")
    print(f"  {Colors.GREEN}✓{Colors.RESET} React Frontend (PID: TBD)")
    print(f"  {Colors.GREEN}✓{Colors.RESET} Celery Worker")
    print(f"  {Colors.GREEN}✓{Colors.RESET} Redis")
    
    print(f"\n{Colors.BOLD}Next Steps:{Colors.RESET}")
    print(f"  1. Open browser: {Colors.CYAN}http://localhost:{frontend_port}{Colors.RESET}")
    print(f"  2. Create superuser: {Colors.YELLOW}python manage.py createsuperuser{Colors.RESET} (in new terminal)")
    print(f"\n{Colors.BOLD}To Stop:{Colors.RESET}")
    print(f"  Press {Colors.YELLOW}Ctrl+C{Colors.RESET} to gracefully shutdown all services\n")

def cleanup_processes(processes: List[subprocess.Popen], stop_event: threading.Event):
    """Cleanup and terminate all processes"""
    log_service("SHUTDOWN", "Shutting down services gracefully...", "WARN")
    stop_event.set()
    
    for process in processes:
        if process and process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            except Exception:
                pass
    
    log_service("SHUTDOWN", "All services stopped", "SUCCESS")

def main():
    parser = argparse.ArgumentParser(description="private-converter Development Stack Launcher")
    parser.add_argument("--no-frontend", action="store_true", help="Skip React frontend")
    parser.add_argument("--no-celery", action="store_true", help="Skip Celery worker")
    parser.add_argument("--no-redis", action="store_true", help="Skip Redis (assumes external Redis)")
    args = parser.parse_args()
    
    print_header()
    
    project_root = get_project_root()
    backend_dir = project_root / "backend"
    frontend_dir = project_root / "frontend"
    python_exe = get_venv_python()
    
    # Validate directories
    if not backend_dir.exists():
        print(f"{Colors.RED}Error: backend directory not found at {backend_dir}{Colors.RESET}")
        sys.exit(1)
    if not args.no_frontend and not frontend_dir.exists():
        print(f"{Colors.RED}Error: frontend directory not found at {frontend_dir}{Colors.RESET}")
        sys.exit(1)
    
    processes: List[subprocess.Popen] = []
    stop_event = threading.Event()
    
    try:
        # Start Redis (optional)
        if not args.no_redis:
            if check_redis_running():
                log_service("REDIS", "✓ Redis already running on localhost:6379", "SUCCESS")
            else:
                redis_proc = start_redis()
                if redis_proc:
                    processes.append(redis_proc)
                else:
                    log_service("REDIS", "Skipping Redis (Docker not available). Make sure Redis is running externally.", "WARN")
        
        time.sleep(1)
        
        # Start Django Backend
        backend_proc = start_backend(python_exe, backend_dir)
        if backend_proc:
            processes.append(backend_proc)
        else:
            print(f"{Colors.RED}Failed to start backend. Exiting.{Colors.RESET}")
            cleanup_processes(processes, stop_event)
            sys.exit(1)
        
        time.sleep(2)
        
        # Start Frontend (optional)
        if not args.no_frontend:
            frontend_proc = start_frontend(frontend_dir)
            if frontend_proc:
                processes.append(frontend_proc)
            else:
                log_service("FRONTEND", "Failed to start frontend, continuing without it", "WARN")
        
        time.sleep(1)
        
        # Start Celery (optional)
        if not args.no_celery:
            celery_proc = start_celery(python_exe, backend_dir)
            if celery_proc:
                processes.append(celery_proc)
            else:
                log_service("CELERY", "Failed to start Celery, continuing without it", "WARN")
        
        time.sleep(1)
        
        # Print summary
        print_summary()
        
        # Keep services running and stream output
        output_threads = []
        service_names = ["REDIS", "BACKEND", "FRONTEND", "CELERY"]
        for i, process in enumerate(processes):
            service_name = service_names[i] if i < len(service_names) else f"SERVICE-{i}"
            thread = threading.Thread(
                target=stream_process_output,
                args=(process, service_name, stop_event),
                daemon=True
            )
            thread.start()
            output_threads.append(thread)
        
        # Wait for Ctrl+C
        while True:
            time.sleep(1)
            # Check if any process died
            for process in processes:
                if process.poll() is not None:
                    log_service("MONITOR", f"A service stopped unexpectedly (PID: {process.pid})", "ERROR")
    
    except KeyboardInterrupt:
        print(f"\n")
        cleanup_processes(processes, stop_event)
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.RESET}")
        cleanup_processes(processes, stop_event)
        sys.exit(1)

if __name__ == "__main__":
    main()
