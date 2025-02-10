import os
import shutil
import datetime
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse, JSONResponse
from typing import Optional
import subprocess
import zipfile

app = FastAPI()

BASE_WORK_DIR = "/data"  # Working directory inside the container, mounted to the host

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
    Upload 5 files, execute RASPA2 simulation, and return all files in ./Output/System_0 (packaged as a zip)
    """

    # Validate number of processes
    if nproc <= 0:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": "Invalid number of processes. Must be greater than 0."
            }
        )

    # 1. Create working directory
    now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    work_dir_name = f"work_{now_str}"
    work_dir_path = os.path.join(BASE_WORK_DIR, work_dir_name)
    os.makedirs(work_dir_path, exist_ok=True)

    # 2. Save uploaded files
    uploaded_files = {
        "force_field_mixing_rules.def": force_field_mixing_rules,
        "pseudo_atoms.def": pseudo_atoms,
        "mof.cif": mof_cif,
        "adsorbate.def": adsorbate_def,
        "simulation.input": simulation_input
    }

    for fname, up_file in uploaded_files.items():
        try:
            dst_path = os.path.join(work_dir_path, fname)
            with open(dst_path, "wb") as f:
                shutil.copyfileobj(up_file.file, f)
            up_file.file.close()  # Ensure the uploaded file is properly closed
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": f"Failed to save uploaded file {fname}.",
                    "detail": str(e)
                }
            )

    # 3. Log file name
    log_file_name = f"log_{now_str}.txt"
    log_file_path = os.path.join(work_dir_path, log_file_name)

    # 4. Construct mpiexec command
    command = [
        "mpiexec",
        "-n", str(nproc),
        "simulate",
        "-i", "simulation.input"
    ]

    # 5. Execute RASPA2 simulation and log output
    try:
        result = subprocess.run(
            command,
            cwd=work_dir_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=True
        )
        # Write log
        with open(log_file_path, "w") as f:
            f.write(result.stdout)

    except subprocess.CalledProcessError as e:
        # On failure, write error message to log
        with open(log_file_path, "w") as f:
            f.write(e.stdout if e.stdout else str(e))
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": "Simulation failed. Check log file.",
                "log_file": log_file_path
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "An unexpected error occurred during simulation.",
                "detail": str(e)
            }
        )

    # 6. If successful, package all files in "Output/System_0"
    system_0_path = os.path.join(work_dir_path, "Output", "System_0")
    if not os.path.exists(system_0_path):
        # If System_0 directory is not found unexpectedly, return an error
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "message": f"No System_0 folder found in {system_0_path}. Check the simulation results or inputs. Or, to be specific, check the log file.",
            }
        )

    # Create a zip file (e.g., result_20230207_123456.zip) in the work_dir_path
    zip_filename = f"results_{now_str}.zip"
    zip_filepath = os.path.join(work_dir_path, zip_filename)

    # Package System_0 directory
    try:
        with zipfile.ZipFile(zip_filepath, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(system_0_path):
                for file in files:
                    abs_file_path = os.path.join(root, file)
                    # Use relative paths in the zip file
                    rel_path = os.path.relpath(abs_file_path, start=system_0_path)
                    zipf.write(abs_file_path, arcname=rel_path)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Failed to create zip file.",
                "detail": str(e)
            }
        )

    # 7. Return the zip file to the client
    #    Using FileResponse directly will automatically handle Content-Type headers, etc.
    return FileResponse(
        path=zip_filepath,
        media_type="application/zip",
        filename=zip_filename,
        status_code=200
    )