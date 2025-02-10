*

# RASPA2 + MPICH + FastAPI Docker Project

**This project provides a Docker-based solution with pre-installed **MPICH 4.3.0** and **RASPA2**, while exposing a **FastAPI** interface for managing molecular simulations. The system supports:**

1. **Uploading user-defined input files** (`force_field_mixing_rules.def`, `pseudo_atoms.def`, `mof.cif`, `adsorbate.def`, `simulation.input`, etc.).
2. **Executing RASPA2 simulations asynchronously** using `mpiexec` to launch parallel computations.
3. **Providing real-time progress tracking** through an API endpoint that allows users to check the simulation status.
4. **Downloading simulation results** as a compressed `.zip` file upon completion.

**This container is ideal for deploying a parallel computing environment for adsorption simulations while leveraging HTTP API-based execution.**

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Environment Requirements](#environment-requirements)
3. [Quick Start](#quick-start)
4. [API Usage](#api-usage)
5. [Result Explanation](#result-explanation)
6. [FAQs](#faqs)
7. [License](#license)

---

## Project Structure

**A typical project directory structure:**

```
 project/
 ├─ Dockerfile
 ├─ requirements.txt
 ├─ main.py
 └─ README.md  <-- This file
```

* **Dockerfile**: Defines how to build the container, including MPICH, RASPA2, and FastAPI installation.
* **requirements.txt**: Lists required Python dependencies (`fastapi`, `uvicorn`, etc.).
* **main.py**: Implements FastAPI service for handling simulations, tracking progress, and providing result downloads.
* **README.md**: Project documentation.

---

## Environment Requirements

* **Docker** (Version 19+ recommended)
* **Internet Access** (Required during build to download MPICH and RASPA2)
* **System Configuration**
  * No strict CPU requirements, but multi-core CPUs improve parallel performance.
  * Tested on **Ubuntu 20.04** (compatible with Docker Desktop on Windows/macOS).

---

## Quick Start

### 1. Clone the project

```sh
git clone <your-repo>.git
cd project
```

### 2. Build the Docker image

```sh
docker build -t raspa-fastapi:v1 .
```

### 3. Run the container

```sh
docker run -d \
     -p 8000:8000 \
     -v /path/on/host:/data \
     --name raspa_container \
     raspa-fastapi:v1
```

* `-p 8000:8000` → Exposes the FastAPI service on port 8000.
* `-v /path/on/host:/data` → Mounts a host directory for logs and results.
* `--name raspa_container` → Assigns a container name.

### 4. Test the API

* Visit **`http://127.0.0.1:8000/docs`** for interactive API documentation.
* Or use **`curl`** or **Python requests** to interact with the API.

---

## API Usage

### 1. `POST /run_simulation`

#### Example (Curl)

```sh
curl -X POST "http://127.0.0.1:8000/run_simulation" \
   -F "force_field_mixing_rules=@./force_field_mixing_rules.def" \
   -F "pseudo_atoms=@./pseudo_atoms.def" \
   -F "mof_cif=@./example_mof.cif" \
   -F "adsorbate_def=@./adsorbate.def" \
   -F "simulation_input=@./simulation.input" \
   -F "nproc=4"
```

#### Example (Python)

```python
import requests

url = "http://127.0.0.1:8000/run_simulation"
files = {
    "force_field_mixing_rules": open("./force_field_mixing_rules.def", "rb"),
    "pseudo_atoms": open("./pseudo_atoms.def", "rb"),
    "mof_cif": open("./example_mof.cif", "rb"),
    "adsorbate_def": open("./adsorbate.def", "rb"),
    "simulation_input": open("./simulation.input", "rb"),
}
data = {"nproc": 4}
response = requests.post(url, files=files, data=data)
print(response.json())
```

### 2. `GET /task_status/{task_id}`

#### Example (Curl)

```sh
curl -X GET "http://127.0.0.1:8000/task_status/task_20240210_153000"
```

#### Example (Python)

```python
import requests

task_id = "task_20240210_153000"
url = f"http://127.0.0.1:8000/task_status/{task_id}"
response = requests.get(url)
print(response.json())
```

### 3. `GET /download_results/{task_id}`

#### Example (Curl)

```sh
curl -X GET "http://127.0.0.1:8000/download_results/task_20240210_153000" --output results.zip
```

#### Example (Python)

```python
import requests

task_id = "task_20240210_153000"
url = f"http://127.0.0.1:8000/download_results/{task_id}"
response = requests.get(url)

if response.status_code == 200:
    with open("results.zip", "wb") as f:
        f.write(response.content)
    print("Download complete.")
else:
    print("Error:", response.json())
```

---

## License

This project is built using **RASPA2 and MPICH**, which follow their respective open-source licenses. Users must comply with all relevant licensing terms and conditions.
