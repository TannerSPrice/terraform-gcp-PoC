#  Python script that automates the CI/CD pipeline within GCP.

import os
import subprocess
import sys
import logging
from pathlib import Path
from google.cloud import storage
from google.auth import default

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Configuration Variables
VENV_DIR = "venv"
REQUIREMENTS_FILE = "requirements.txt"
TEST_COMMAND = ["pytest"]
DOCKER_IMAGE_NAME = "gcr.io/your-project-id/your-app-name"
DOCKER_TAG = "latest"
GKE_CLUSTER = "your-gke-cluster"
GKE_ZONE = "your-gke-zone"
GKE_NAMESPACE = "default"
KUBE_DEPLOYMENT_NAME = "your-deployment"

def run_command(command, cwd=None):
    """
    Runs a shell command and returns the output.
    Raises subprocess.CalledProcessError if the command fails.
    """
    logging.info(f"Running command: {' '.join(command)}")
    result = subprocess.run(command, cwd=cwd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    logging.debug(result.stdout)
    return result.stdout

def setup_virtualenv():
    """
    Sets up a Python virtual environment and installs dependencies.
    """
    if not Path(VENV_DIR).exists():
        logging.info("Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", VENV_DIR], check=True)
    else:
        logging.info("Virtual environment already exists.")

    logging.info("Activating virtual environment and installing dependencies...")
    pip_executable = os.path.join(VENV_DIR, "bin", "pip") if os.name != 'nt' else os.path.join(VENV_DIR, "Scripts", "pip.exe")
    run_command([pip_executable, "install", "--upgrade", "pip"])
    run_command([pip_executable, "install", "-r", REQUIREMENTS_FILE])

def run_tests():
    """
    Runs the test suite using pytest.
    """
    logging.info("Running tests...")
    venv_python = os.path.join(VENV_DIR, "bin", "python") if os.name != 'nt' else os.path.join(VENV_DIR, "Scripts", "python.exe")
    run_command([venv_python, "-m", "pytest"])

def build_docker_image():
    """
    Builds a Docker image for the application.
    """
    logging.info("Building Docker image...")
    run_command(["docker", "build", "-t", f"{DOCKER_IMAGE_NAME}:{DOCKER_TAG}", "."])

def push_docker_image():
    """
    Pushes the Docker image to Google Container Registry (GCR).
    """
    logging.info("Pushing Docker image to GCR...")
    # Authenticate Docker with GCR
    run_command(["gcloud", "auth", "configure-docker", "--quiet"])
    run_command(["docker", "push", f"{DOCKER_IMAGE_NAME}:{DOCKER_TAG}"])

def deploy_to_gke():
    """
    Deploys the Docker image to a GKE cluster.
    """
    logging.info("Deploying to GKE...")
    # Get credentials for the GKE cluster
    run_command([
        "gcloud", "container", "clusters", "get-credentials",
        GKE_CLUSTER, "--zone", GKE_ZONE, "--project", "your-project-id"
    ])
    # Update the image in the Kubernetes deployment
    run_command([
        "kubectl", "set", "image",
        f"deployment/{KUBE_DEPLOYMENT_NAME}",
        f"{KUBE_DEPLOYMENT_NAME}={DOCKER_IMAGE_NAME}:{DOCKER_TAG}",
        "-n", GKE_NAMESPACE
    ])
    # Optionally, wait for the deployment to complete
    run_command([
        "kubectl", "rollout", "status",
        f"deployment/{KUBE_DEPLOYMENT_NAME}",
        "-n", GKE_NAMESPACE
    ])

def main():
    try:
        setup_virtualenv()
        run_tests()
        build_docker_image()
        push_docker_image()
        deploy_to_gke()
        logging.info("CI/CD pipeline executed successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"An error occurred: {e.stderr}")
        sys.exit(1)

if __name__ == "__main__":
    main()
