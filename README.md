# My AI Project

This repository demonstrates an end-to-end CI/CD pipeline for an AI model using GitHub Actions.

## Overview

- **Train and Test Workflow:**  
  When any `.ipynb` file (specifically `notebooks/model.ipynb`) is pushed or updated, the training/testing workflow runs. It executes the notebook via Papermill and prints the output to the GitHub Actions log.

- **Deploy Workflow:**  
  After merging into the `main` branch, the deploy workflow:
  - Authenticates with a Flask server (exposed via ngrok if desired),
  - Retrieves a symmetric key,
  - Encrypts the trained model (e.g. `models/model.h5`),
  - Directly uploads the encrypted file to the server, where it is saved to disk.

- **Flask Server:**  
  Located in the `server/` folder, it:
  - Provides a **/get-key** endpoint for symmetric key generation,
  - Provides a **/upload-model** endpoint for file uploads,
  - Includes a **/decrypt** endpoint for demonstration.

## Setup

1. **Local CI/CD Testing:**
   - Install dependencies:
     ```bash
     pip install -r requirements.txt
     ```
2. **Flask Server Setup:**
   - Navigate to the `server/` directory.
   - Install server dependencies:
     ```bash
     pip install -r server/requirements.txt
     ```
   - Ensure you have a MySQL instance running (or adjust the MySQL configuration in `server/app.py`).
   - Run the server:
     ```bash
     python app.py
     ```
   - Optionally, expose the server using ngrok:
     ```bash
     ngrok http 5000
     ```

3. **GitHub Secrets for Deploy Workflow:**
   - Set the following secrets in your GitHub repository:
     - `SERVER_USERNAME`
     - `SERVER_PASSWORD`
     - `SERVER_URL` (e.g., your ngrok URL pointing to the Flask server)

## Testing the Pipeline

1. Modify or push `notebooks/model.ipynb` to trigger the train/test workflow.
2. Merge changes to the `main` branch to trigger the deploy workflow which encrypts and uploads the model.

Enjoy testing your full end-to-end pipeline!
