import os
import subprocess
import sys
import webbrowser
import time

def check_requirements():
    """Checks if core dependencies are already installed to avoid slow pip calls."""
    core_packages = ["numpy", "scipy", "matplotlib", "requests"]
    missing = []
    for pkg in core_packages:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    return missing

def run_project():
    """
    Orchestrates the setup and execution of the Cascade Risk Engine.
    1. Installs dependencies from requirements.txt
    2. Launches the backend server (server.py)
    3. Opens the interactive dashboard in the default browser
    """
    
    # Ensure we are in the project root directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)

    print("==================================================")
    print(" CASCADE RISK ENGINE - Single Launch Script")
    print("==================================================")

    # 1. Dependency Check/Installation
    print("\n[1/3] Checking dependencies...")
    missing = check_requirements()
    
    if missing:
        print(f"Missing packages: {', '.join(missing)}. Installing...")
        try:
            # Use the current python executable to install requirements
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        except subprocess.CalledProcessError as e:
            print(f"Warning: Dependency installation failed with error: {e}")
            print("Attempting to proceed with existing environment...")
        except Exception as e:
            print(f"An unexpected error occurred during setup: {e}")
    else:
        print("All dependencies satisfied. Skipping pip install.")

    # 2. Launch Server
    print("\n[2/3] Launching backend server (server.py)...")
    # We use Popen to run the server in the background so we can open the browser
    try:
        server_process = subprocess.Popen(
            [sys.executable, "server.py"],
            stdout=None, # Share stdout/stderr with the current process
            stderr=None
        )
    except Exception as e:
        print(f"Failed to start server: {e}")
        sys.exit(1)

    # 3. Open Browser
    # Give the server a couple of seconds to initialize its port
    time.sleep(2)
    url = "http://localhost:8081"
    print(f"\n[3/3] Opening dashboard at {url}")
    webbrowser.open(url)

    print("\n[SUCCESS] System is live. Press Ctrl+C to shut down.")
    
    # 4. Monitor Process
    try:
        # Keep the script running as long as the server is alive
        server_process.wait()
    except KeyboardInterrupt:
        print("\n\nShutting down Cascade Risk Engine...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()
        print("Server stopped.")

if __name__ == "__main__":
    run_project()
