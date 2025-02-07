import os
import shutil
import datetime
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse, JSONResponse
from typing import Optional
import subprocess
import zipfile

app = FastAPI()

BASE_WORK_DIR = "/data"  # 容器内工作目录，挂载到宿主机

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
    上传 5 个文件，执行 RASPA2 模拟，然后返回 ./Output/System_0 下的所有文件（打包为zip）
    """

    # 1. 创建工作目录
    now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    work_dir_name = f"work_{now_str}"
    work_dir_path = os.path.join(BASE_WORK_DIR, work_dir_name)
    os.makedirs(work_dir_path, exist_ok=True)

    # 2. 保存上传文件
    uploaded_files = {
        "force_field_mixing_rules.def": force_field_mixing_rules,
        "pseudo_atoms.def": pseudo_atoms,
        "mof.cif": mof_cif,
        "adsorbate.def": adsorbate_def,
        "simulation.input": simulation_input
    }

    for fname, up_file in uploaded_files.items():
        dst_path = os.path.join(work_dir_path, fname)
        with open(dst_path, "wb") as f:
            shutil.copyfileobj(up_file.file, f)

    # 3. 日志文件名
    log_file_name = f"log_{now_str}.txt"
    log_file_path = os.path.join(work_dir_path, log_file_name)

    # 4. 构造 mpiexec 命令
    command = [
        "mpiexec",
        "-n", str(nproc),
        "simulate",
        "-i", "simulation.input"
    ]

    # 5. 执行 RASPA2 模拟并记录日志
    try:
        result = subprocess.run(
            command,
            cwd=work_dir_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=True
        )
        # 写入日志
        with open(log_file_path, "w") as f:
            f.write(result.stdout)

    except subprocess.CalledProcessError as e:
        # 失败则把错误信息写入日志
        with open(log_file_path, "w") as f:
            f.write(e.output if e.output else str(e))
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": "Simulation failed. Check log file.",
                "log_file": log_file_path
            }
        )

    # 6. 如果执行成功，则需要打包 "Output/System_0" 下的所有文件
    system_0_path = os.path.join(work_dir_path, "Output", "System_0")
    if not os.path.exists(system_0_path):
        # 如果意外地没有生成System_0目录，就返回提示
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "message": f"No System_0 folder found in {system_0_path}. Check the simulation results or inputs."
            }
        )

    # 创建zip包 (如: result_20230207_123456.zip)，存储在 work_dir_path 下
    zip_filename = f"results_{now_str}.zip"
    zip_filepath = os.path.join(work_dir_path, zip_filename)

    # 打包 System_0 目录
    with zipfile.ZipFile(zip_filepath, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(system_0_path):
            for file in files:
                abs_file_path = os.path.join(root, file)
                # 在zip中使用相对路径
                rel_path = os.path.relpath(abs_file_path, start=system_0_path)
                zipf.write(abs_file_path, arcname=rel_path)

    # 7. 返回 zip 文件给请求端
    #    使用FileResponse直接返回，会自动处理Content-Type等头部
    return FileResponse(
        path=zip_filepath,
        media_type="application/zip",
        filename=zip_filename
    )
