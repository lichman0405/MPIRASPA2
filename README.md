# RASPA2 + MPICH + FastAPI Docker 项目

**本项目基于 Docker 容器，预先编译安装了 ****MPICH 4.3.0** 与 **RASPA2**，并使用 **FastAPI** 对外提供接口，实现以下功能：

1. **接收用户上传的必要输入文件（**`force_field_mixing_rules.def`, `pseudo_atoms.def`, `mof.cif`, `adsorbate.def`, `simulation.input` 等）。
2. **在容器内部通过 **`mpiexec` 命令调用 RASPA2 的 `simulate` 程序执行模拟计算。
3. **自动记录日志，并将输出目录下的结果（特别是 **`./Output/System_0` 文件）打包并返回给客户端。

**该镜像适用于需要快速搭建并行计算环境（MPI + RASPA2）的应用场景，同时提供简洁的 HTTP API，方便分布式调用。**

---

## 目录

1. [项目结构](#%E9%A1%B9%E7%9B%AE%E7%BB%93%E6%9E%84)
2. [环境依赖](#%E7%8E%AF%E5%A2%83%E4%BE%9D%E8%B5%96)
3. [快速开始](#%E5%BF%AB%E9%80%9F%E5%BC%80%E5%A7%8B)
4. [API 使用方法](#api-%E4%BD%BF%E7%94%A8%E6%96%B9%E6%B3%95)
5. [结果说明](#%E7%BB%93%E6%9E%9C%E8%AF%B4%E6%98%8E)
6. [常见问题](#%E5%B8%B8%E8%A7%81%E9%97%AE%E9%A2%98)
7. [许可证](#%E8%AE%B8%E5%8F%AF%E8%AF%81)

---

## 项目结构

**一个典型的项目目录结构示例（可根据实际情况调整）：**

```
 project/
 ├── Dockerfile
 ├── requirements.txt
 ├── main.py
 └── README.md  <-- 本文件
```

* **Dockerfile**：Docker 构建脚本，包含了编译安装 MPICH 与 RASPA2 的步骤，以及安装 Python + FastAPI。
* **requirements.txt**：Python 依赖清单，示例中包含 `fastapi` 和 `uvicorn` 等基础组件。
* **main.py**：FastAPI 后端服务逻辑，包括接收上传文件、执行模拟、打包结果并返回给客户端等。
* **README.md**：项目说明文档（本文件）。

---

## 环境依赖

* **Docker**
  * **确保已安装 Docker（版本不低于 19+）。**
* **网络环境**
  * **构建镜像时需要从官方站点下载 MPICH 4.3.0 以及克隆 RASPA2 的代码仓库。**
* **服务器/主机配置**
  * **对 CPU 核心数没有特别限制，但如果要跑并行模拟（如 **`-n 4`），建议预留足够的核心。
  * **本项目在 Ubuntu 20.04 环境下测试。其他操作系统（如 Windows、macOS）可通过 Docker Desktop 或类似技术运行。**

---

## 快速开始

1. **克隆项目或准备所需文件**

   ```
    git clone <your-project-repo>.git
    cd project
   ```
2. **构建 Docker 镜像** ** 在项目根目录（含有 Dockerfile）下执行：**

   ```
    docker build -t raspa-fastapi:v1 .
   ```

   * `-t raspa-fastapi:v1` 为自定义镜像名称和标签，实际可根据需要调整。
3. **运行容器**

   ```
    docker run -d \
        -p 8000:8000 \
        -v /path/on/host:/data \
        --name raspa_container \
        raspa-fastapi:v1
   ```

   * `-p 8000:8000`：将容器内部的 8000 端口映射到宿主机的 8000 端口。
   * `-v /path/on/host:/data`：将宿主机的某个目录映射到容器的 `/data`，用来保存并查看计算日志、工作目录及结果文件。
   * `--name raspa_container`：容器名称自定义，可自由更改。
4. **测试服务**

   * **容器启动后，访问 **`http://127.0.0.1:8000/docs` 可查看自动生成的 FastAPI 文档（在本机上）。
   * **也可以在命令行使用 **`curl` 进行测试。

---

## API 使用方法

### 1. 接口：`POST /run_simulation`

* **功能**：上传所需文件，启动 RASPA2 并行模拟，并返回结果的 zip 包。
* **请求参数**
  **（**

  ```
   multipart/form-data
  ```

  **）：**

  * `force_field_mixing_rules` (File)
  * `pseudo_atoms` (File)
  * `mof_cif` (File)
  * `adsorbate_def` (File)
  * `simulation_input` (File)
  * `nproc` (Form, 可选，默认值 2)
* **返回值**
  **：**

  * **成功时：返回一个 **`.zip` 文件，内含 `Output/System_0` 目录下的所有计算结果。
  * **失败时：返回 JSON，包含错误信息和日志位置。**

#### 使用示例（`curl` 命令）

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

* `--output results.zip` 将服务器返回的压缩包保存到本地文件 `results.zip`。
* **如果模拟失败，返回 JSON 格式的错误信息，可从中查看原因并在 **`/data/work_xxx/log_xxx.txt` 查看日志。

---

## 结果说明

* **RASPA2 在执行模拟时，会自动在工作目录下创建四个子目录：**
  1. **Movies**
  2. **Output**
  3. **Restart**
  4. **VTK**
* **本项目只打包并返回 ****`Output/System_0`** 文件夹中的结果文件。根据具体模拟类型，`System_0` 目录下可能含有：
  * `Framework_*.data`
  * `Block*_*_*.data`
  * `*.tab` 等。
* **日志文件：**
  * **名称格式：**`log_YYYYMMDD_HHMMSS.txt`，保存在对应的工作目录下（例如 `/data/work_20230207_123456`）。
  * **如果模拟失败，也可查看该日志文件获取更详细的错误信息。**

---

## 常见问题

1. **模拟时间较长，接口是否会超时？**
   * **FastAPI/uvicorn 默认有超时限制。如果计算较长，需要在生产环境中考虑异步调用或队列调度，避免 HTTP 超时。**
2. **结果文件很大，直接返回 zip 是否合适？**
   * **如果结果文件过于庞大（数百 MB 至数 GB），可以考虑：**
     * **(a) 同步返回大文件，对带宽有较大消耗；**
     * **(b) 采用异步处理，并提供任务 ID，用户后续再下载结果文件。**
3. **如何查看日志与结果文件？**
   * **通过挂载到 **`/data`，可在宿主机上的对应目录下查看相应工作目录、日志与结果。
4. **可以并发执行吗？**
   * **默认情况下若多请求并发到来，需要考虑容器 CPU 核数、内存以及 MPI 并行冲突等问题。可以在 K8s 等平台进行扩缩容，或使用队列机制顺序执行。**

---

## 许可证

* **本项目使用的 ****RASPA2** 及 **MPICH** 均遵循各自的开源许可协议，在此镜像中仅作编译与打包，不做任何商业担保。
* **使用者需确保符合相关开源协议、项目许可及所在实验室/单位的合规要求。**
