#!/usr/bin/env python3
"""
Setup script to help users get ModelSwitch up and running quickly.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")


def print_success(text):
    """Print a success message."""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_error(text):
    """Print an error message."""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_info(text):
    """Print an info message."""
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


def print_warning(text):
    """Print a warning message."""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def check_python_version():
    """Check if Python version is 3.11 or higher."""
    print_info("Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print_error(f"Python 3.11+ required. Current version: {version.major}.{version.minor}")
        return False
    print_success(f"Python {version.major}.{version.minor}.{version.micro} detected")
    return True


def check_command_exists(command):
    """Check if a command exists in PATH."""
    try:
        subprocess.run(
            [command, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False
        )
        return True
    except FileNotFoundError:
        return False


def create_virtual_environment():
    """Create a Python virtual environment."""
    print_info("Creating virtual environment...")
    
    venv_path = Path("venv")
    if venv_path.exists():
        print_warning("Virtual environment already exists")
        return True
    
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print_success("Virtual environment created")
        return True
    except subprocess.CalledProcessError:
        print_error("Failed to create virtual environment")
        return False


def get_pip_command():
    """Get the appropriate pip command based on OS."""
    if platform.system() == "Windows":
        return os.path.join("venv", "Scripts", "pip.exe")
    return os.path.join("venv", "bin", "pip")


def install_dependencies():
    """Install Python dependencies."""
    print_info("Installing dependencies...")
    
    pip_cmd = get_pip_command()
    
    try:
        # Upgrade pip
        subprocess.run([pip_cmd, "install", "--upgrade", "pip"], check=True)
        
        # Install main dependencies
        subprocess.run([pip_cmd, "install", "-r", "requirements.txt"], check=True)
        print_success("Main dependencies installed")
        
        # Ask if user wants dev dependencies
        response = input(f"\n{Colors.OKCYAN}Install development dependencies? (y/n): {Colors.ENDC}")
        if response.lower() in ['y', 'yes']:
            subprocess.run([pip_cmd, "install", "-r", "requirements-dev.txt"], check=True)
            print_success("Development dependencies installed")
        
        return True
    except subprocess.CalledProcessError:
        print_error("Failed to install dependencies")
        return False


def setup_environment_file():
    """Create .env file from template."""
    print_info("Setting up environment file...")
    
    env_path = Path(".env")
    if env_path.exists():
        print_warning(".env file already exists")
        response = input(f"{Colors.OKCYAN}Overwrite? (y/n): {Colors.ENDC}")
        if response.lower() not in ['y', 'yes']:
            return True
    
    try:
        # Copy env.example to .env
        with open("env.example", "r") as src:
            content = src.read()
        
        with open(".env", "w") as dst:
            dst.write(content)
        
        print_success(".env file created")
        return True
    except Exception as e:
        print_error(f"Failed to create .env file: {e}")
        return False


def create_models_directory():
    """Create models directory structure."""
    print_info("Creating models directory...")
    
    models_dir = Path("models")
    if models_dir.exists():
        print_warning("Models directory already exists")
        return True
    
    try:
        models_dir.mkdir()
        (models_dir / "v1").mkdir()
        (models_dir / "v2").mkdir()
        print_success("Models directory created")
        return True
    except Exception as e:
        print_error(f"Failed to create models directory: {e}")
        return False


def train_example_models():
    """Train example models."""
    print_info("Training example models...")
    
    response = input(f"{Colors.OKCYAN}Train example models now? (y/n): {Colors.ENDC}")
    if response.lower() not in ['y', 'yes']:
        print_info("Skipping model training")
        return True
    
    python_cmd = sys.executable if not Path("venv").exists() else (
        os.path.join("venv", "Scripts", "python.exe") if platform.system() == "Windows"
        else os.path.join("venv", "bin", "python")
    )
    
    try:
        subprocess.run([python_cmd, "examples/train_example_models.py"], check=True)
        print_success("Example models trained")
        return True
    except subprocess.CalledProcessError:
        print_error("Failed to train example models")
        return False


def setup_pre_commit():
    """Setup pre-commit hooks."""
    print_info("Setting up pre-commit hooks...")
    
    response = input(f"{Colors.OKCYAN}Install pre-commit hooks? (y/n): {Colors.ENDC}")
    if response.lower() not in ['y', 'yes']:
        print_info("Skipping pre-commit setup")
        return True
    
    pip_cmd = get_pip_command()
    
    try:
        subprocess.run([pip_cmd, "install", "pre-commit"], check=True)
        subprocess.run(["pre-commit", "install"], check=True)
        print_success("Pre-commit hooks installed")
        return True
    except subprocess.CalledProcessError:
        print_error("Failed to install pre-commit hooks")
        return False


def check_docker():
    """Check if Docker is available."""
    print_info("Checking for Docker...")
    
    if check_command_exists("docker"):
        print_success("Docker is installed")
        
        response = input(f"{Colors.OKCYAN}Would you like to use Docker? (y/n): {Colors.ENDC}")
        if response.lower() in ['y', 'yes']:
            return True
    else:
        print_warning("Docker not found (optional)")
    
    return False


def print_next_steps(use_docker=False):
    """Print next steps for the user."""
    print_header("Setup Complete!")
    
    if use_docker:
        print(f"{Colors.OKGREEN}To start with Docker:{Colors.ENDC}")
        print("  docker-compose up --build\n")
    else:
        print(f"{Colors.OKGREEN}To start the application:{Colors.ENDC}")
        if platform.system() == "Windows":
            print("  venv\\Scripts\\activate")
        else:
            print("  source venv/bin/activate")
        print("  uvicorn app.main:app --reload\n")
    
    print(f"{Colors.OKBLUE}Access points:{Colors.ENDC}")
    print("  API:        http://localhost:8000")
    print("  Docs:       http://localhost:8000/docs")
    print("  Health:     http://localhost:8000/healthz")
    
    if use_docker:
        print("  Prometheus: http://localhost:9090")
        print("  Grafana:    http://localhost:3000 (admin/admin)")
    
    print(f"\n{Colors.OKBLUE}To run tests:{Colors.ENDC}")
    print("  pytest")
    
    print(f"\n{Colors.OKBLUE}Documentation:{Colors.ENDC}")
    print("  README.md        - Project overview")
    print("  ARCHITECTURE.md  - System architecture")
    print("  DEPLOYMENT.md    - Deployment guides")
    print("  CONTRIBUTING.md  - Contribution guidelines")
    
    print(f"\n{Colors.BOLD}Happy coding! 🚀{Colors.ENDC}\n")


def main():
    """Main setup function."""
    print_header("ModelSwitch Setup")
    print("This script will help you set up ModelSwitch for development.\n")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check for Docker
    use_docker = check_docker()
    
    if not use_docker:
        # Create virtual environment
        if not create_virtual_environment():
            sys.exit(1)
        
        # Install dependencies
        if not install_dependencies():
            sys.exit(1)
        
        # Setup pre-commit
        setup_pre_commit()
    
    # Setup environment file
    if not setup_environment_file():
        sys.exit(1)
    
    # Create models directory
    if not create_models_directory():
        sys.exit(1)
    
    if not use_docker:
        # Train example models
        if not train_example_models():
            print_warning("You can train models later with: python examples/train_example_models.py")
    
    # Print next steps
    print_next_steps(use_docker)


if __name__ == "__main__":
    main()
