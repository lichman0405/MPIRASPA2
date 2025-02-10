import os
import shutil
import datetime
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse, JSONResponse
from typing import Optional
import subprocess
import threading
import zipfile

app = FastAPI()

# Base directory where all simulation tasks will be stored
BASE_WORK_DIR = "/data"

# Dictionary to store task statuses
task_status = {}

def run_simulation_task(task_id: str, work_dir_path: str, nproc: int):
    """
    Runs a RASPA2 simulation task in the specified working directory.

    Parameters:
        task_id (str): Unique identifier for the simulation task.
        work_dir_path (str): Path to the directory where simulation files are stored.
        nproc (int): Number of processes to use for the simulation.

    This function executes the RASPA2 `simulate` command using `mpiexec` in a separate thread.
    It updates the `task_status` dictionary to track the simulation progress.
    """
    log_file_path = os.path.join(work_dir_path, "simulation.log")
    output_dir = os.path.join(work_dir_path, "Output", "System_0")

    # Update task status to "running"
    task_status[task_id] = {"status": "running", "log": []}

    # Construct the simulation command
    command = [
        "mpiexec",
        "-n", str(nproc),
        "simulate",
        "-i", "simulation.input"
    ]

    # Execute the simulation and capture the output log
    with open(log_file_path, "w") as log_file:
        process = subprocess.Popen(command, cwd=work_dir_path, stdout=log_file, stderr=subprocess.STDOUT)
        process.wait()  # Wait for RASPA2 to finish execution

    # Check if the simulation completed successfully
    if os.path.exists(output_dir):
        task_status[task_id]["status"] = "completed"
    else:
        task_status[task_id]["status"] = "failed"

@app.post("/run_simulation")
async def run_simulation(
    force_field_mixing_rules: UploadFile = File(...),
    pseudo_atoms: UploadFile = File(...),
    mof_cif: UploadFile = File(...),
    adsorbate_def: UploadFile = File(...),
    simulation_input: UploadFile = File(...),
    nproc: Optional[int] = Form(2)
):
    """
    Uploads simulation files, starts an asynchronous RASPA2 simulation, and returns a task ID.

    Parameters:
        force_field_mixing_rules (UploadFile): Force field mixing rules definition file.
        pseudo_atoms (UploadFile): Pseudo atoms definition file.
        mof_cif (UploadFile): CIF file containing the MOF structure.
        adsorbate_def (UploadFile): Definition file for the adsorbate molecule (e.g., CO2.def).
        simulation_input (UploadFile): RASPA2 input file.
        nproc (int, optional): Number of processes to use for the simulation (default is 2).

    Returns:
        JSONResponse: Contains task ID and initial status message.
    """
    # Generate a unique task ID based on the current timestamp
    now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    task_id = f"task_{now_str}"
    work_dir_path = os.path.join(BASE_WORK_DIR, task_id)
    os.makedirs(work_dir_path, exist_ok=True)

    # Dictionary to map filenames to uploaded files
    uploaded_files = {
        "force_field_mixing_rules.def": force_field_mixing_rules,
        "pseudo_atoms.def": pseudo_atoms,
        "mof.cif": mof_cif,
        "adsorbate.def": adsorbate_def,
        "simulation.input": simulation_input
    }

    # Save uploaded files to the working directory
    for fname, up_file in uploaded_files.items():
        dst_path = os.path.join(work_dir_path, fname)
        with open(dst_path, "wb") as f:
            shutil.copyfileobj(up_file.file, f)
        up_file.file.close()

    # Start the simulation in a separate thread
    thread = threading.Thread(target=run_simulation_task, args=(task_id, work_dir_path, nproc))
    thread.start()

    # Initialize task status
    task_status[task_id] = {"status": "queued"}

    return JSONResponse(
        status_code=202,
        content={
            "status": "queued",
            "message": "Simulation started.",
            "task_id": task_id
        }
    )

@app.get("/task_status/{task_id}")
async def get_status(task_id: str):
    """
    Retrieves the status of a specific simulation task.

    Parameters:
        task_id (str): The unique identifier for the task.

    Returns:
        JSONResponse: Contains task status and recent log output (if available).
    """
    if task_id not in task_status:
        return JSONResponse(status_code=404, content={"status": "error", "message": "Task not found."})

    # Retrieve the latest log output (last 10 lines)
    log_file_path = os.path.join(BASE_WORK_DIR, task_id, "simulation.log")
    if os.path.exists(log_file_path):
        with open(log_file_path, "r") as f:
            log_content = f.readlines()[-10:]

        task_status[task_id]["log"] = log_content

    return JSONResponse(status_code=200, content=task_status[task_id])

@app.get("/download_results/{task_id}")
async def download_results(task_id: str):
    """
    Downloads the simulation results as a ZIP file.

    Parameters:
        task_id (str): The unique identifier for the task.

    Returns:
        FileResponse: The ZIP file containing simulation results if available.
        JSONResponse: Error message if results are not found.
    """
    work_dir_path = os.path.join(BASE_WORK_DIR, task_id)
    output_dir = os.path.join(work_dir_path, "Output", "System_0")

    if not os.path.exists(output_dir):
        return JSONResponse(status_code=404, content={"status": "error", "message": "No results found."})

    # Create a ZIP archive of the simulation results
    zip_filename = f"results_{task_id}.zip"
    zip_filepath = os.path.join(work_dir_path, zip_filename)

    try:
        with zipfile.ZipFile(zip_filepath, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(output_dir):
                for file in files:
                    abs_file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(abs_file_path, start=output_dir)
                    zipf.write(abs_file_path, arcname=rel_path)
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": "Failed to create zip file.", "detail": str(e)})

    return FileResponse(path=zip_filepath, media_type="application/zip", filename=zip_filename)

