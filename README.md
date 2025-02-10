# RASPA2 + MPICH + FastAPI Docker Project

**This project is based on a Docker container with precompiled installations of **MPICH 4.3.0** and **RASPA2**, while also exposing a **FastAPI** interface to achieve the following functions:**

1. **Receive user-uploaded input files** (`force_field_mixing_rules.def`, `pseudo_atoms.def`, `mof.cif`, `adsorbate.def`, `simulation.input`, etc.).
2. **Execute RASPA2 simulations within the container** using the `mpiexec` command to call the `simulate` program.
3. **Automatically log execution details** and return the results in a packaged format, particularly the **`./Output/System_0`** directory.

**This image is suitable for applications that require a rapid setup of a parallel computing environment (MPI + RASPA2) while providing a simple HTTP API for distributed execution.**

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

**A typical project directory structure (adjustable as needed):**

```
 project/
 ├─ Dockerfile
 ├─ requirements.txt
 ├─ main.py
 └─ README.md  <-- This file
```

* **Dockerfile**: The Docker build script, including steps to compile and install MPICH and RASPA2, as well as install Python and FastAPI.
* **requirements.txt**: The Python dependency list, including `fastapi`, `uvicorn`, etc.
* **main.py**: The FastAPI backend service, handling file uploads, executing simulations, packaging results, and returning them to the client.
* **README.md**: The project documentation (this file).

---

## Environment Requirements

* **Docker**
  * Ensure Docker is installed (version 19+ required).
* **Network Access**
  * The image build process requires downloading MPICH 4.3.0 and cloning the RASPA2 repository.
* **Server/Host Configuration**
  * No strict CPU core requirements, but for parallel simulations (e.g., `-n 4`), sufficient cores should be allocated.
  * Tested on **Ubuntu 20.04**; other OS (Windows, macOS) can run via Docker Desktop or similar technologies.

---

## Quick Start

1. **Clone the project or prepare the necessary files**

   ```
    git clone <your-project-repo>.git
    cd project
   ```
2. **Build the Docker image** in the project root directory (where the Dockerfile is located):

   ```
    docker build -t raspa-fastapi:v1 .
   ```

   * `-t raspa-fastapi:v1` specifies the image name and tag, which can be adjusted as needed.
3. **Run the container**

   ```
    docker run -d \
         -p 8000:8000 \
         -v /path/on/host:/data \
         --name raspa_container \
         raspa-fastapi:v1
   ```

   * `-p 8000:8000`: Maps the container's port 8000 to the host's port 8000.
   * `-v /path/on/host:/data`: Maps a host directory to the container's `/data`, for storing logs, working directories, and result files.
   * `--name raspa_container`: Custom container name, change as needed.
4. **Test the service**

   * Once the container is running, visit **`http://127.0.0.1:8000/docs`** to access the auto-generated FastAPI documentation.
   * Alternatively, test using the **`curl`** command.

---

## API Usage

### 1. Endpoint: `POST /run_simulation`

* **Function**: Upload required files, start the RASPA2 parallel simulation, and return the results as a zip file.
* **Request Parameters****(multipart/form-data format):**
  * `force_field_mixing_rules` (File)
  * `pseudo_atoms` (File)
  * `mof_cif` (File)
  * `adsorbate_def` (File)
  * `simulation_input` (File)
  * `nproc` (Form, optional, default: 2)
* **Response**:
  * **Success**: Returns a **`.zip` file** containing all results from `Output/System_0`.
  * **Failure**: Returns a JSON error message and log location.

#### Example Usage (via `curl`)

```
curl -X POST "http://127.0.0.1:8000/run_simulation" \
   -F "force_field_mixing_rules=@./force_field_mixing_rules.def" \
   -F "pseudo_atoms=@./pseudo_atoms.def" \
   -F "mof_cif=@./example_mof.cif" \
   -F "adsorbate_def=@./adsorbate.def" \
   -F "simulation_input=@./simulation.input" \
   -F "nproc=4" \
   --output results.zip
```

#### Example Usage (via Python)

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

if response.status_code == 200:
    with open("results.zip", "wb") as f:
        f.write(response.content)
    print("Simulation completed, results saved as results.zip")
else:
    print("Error:", response.json())
```

---

## Result Explanation

* **RASPA2 creates four subdirectories in the working directory during execution:**

  1. **Movies**
  2. **Output**
  3. **Restart**
  4. **VTK**

---

## FAQs

1. **Will the API timeout if the simulation takes too long?**
   * **FastAPI/uvicorn has default timeout limits. For long-running simulations, consider using asynchronous processing or a task queue to prevent HTTP timeouts.**
2. **What if the result files are too large?**
   * **If the result files are very large (hundreds of MB to GBs), consider:**
     * **(a) Returning large files synchronously (bandwidth-intensive).**
     * **(b) Using asynchronous processing and providing a task ID for later download.**
3. **How can I view logs and result files?**
   * **Mount the **`<span><strong>/data</strong></span>`** directory to a host directory for direct access to logs, working directories, and results.**
4. **Can multiple simulations run concurrently?**
   * **For concurrent requests, consider CPU core availability, memory, and MPI parallel execution conflicts. Scale using Kubernetes or implement a job queue.**

---

## License

* **Both RASPA2 and MPICH comply with their respective open-source licenses. This image only compiles and packages them, with no commercial guarantees.**
* **Users must ensure compliance with relevant open-source licenses, project terms, and institutional policies.**
