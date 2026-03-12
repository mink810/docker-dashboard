from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import docker
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = docker.from_env()

@app.get("/containers")
def get_containers():
    containers = client.containers.list(all=True)   # 모든 컨테이너 목록 조회 젠킨스 테스트 
    return [
        {
            "id": c.short_id,
            "name": c.name,
            "status": c.status,
            "image": c.image.tags[0] if c.image.tags else "none",
            "ports": c.ports,
            "mounts": [
                {
                    "type": m["Type"],
                    "source": m.get("Source", ""),
                    "destination": m["Destination"],
                    "mode": m.get("Mode", ""),
                }
                for m in c.attrs.get("Mounts", [])
            ],
        }
        for c in containers
    ]


@app.post("/containers/{container_id}/start")
def start_container(container_id: str):
    try:
        container = client.containers.get(container_id)
        container.start()
        return {"ok": True}
    except Exception as e:
        return {"error": str(e)}


@app.post("/containers/{container_id}/stop")
def stop_container(container_id: str):
    try:
        container = client.containers.get(container_id)
        container.stop()
        return {"ok": True}
    except Exception as e:
        return {"error": str(e)}


@app.get("/images")
def get_images():
    images = client.images.list()
    return [
        {
            "id": i.short_id,
            "tags": i.tags,
            "size": round(i.attrs["Size"] / 1024 / 1024, 1),
        }
        for i in images
    ]

@app.get("/files")
def get_files(path: str = "/service"):
    try:
        items = os.listdir(path)
        result = []
        for item in items:
            full_path = os.path.join(path, item)
            result.append({
                "name": item,
                "path": full_path,
                "is_dir": os.path.isdir(full_path),
            })
        return {"current": path, "items": sorted(result, key=lambda x: (not x["is_dir"], x["name"]))}
    except Exception as e:
        return {"error": str(e)}


def _resolve_path(path: str) -> str:
    """Resolve to absolute path, ensure under /service."""
    base = os.path.abspath("/service")
    resolved = os.path.abspath(path)
    if not resolved.startswith(base):
        raise ValueError("path must be under /service")
    return resolved


@app.get("/file-content")
def get_file_content(path: str):
    """Return file content for preview. Text files only, max 512KB."""
    try:
        full_path = _resolve_path(path)
        if os.path.isdir(full_path):
            return {"error": "폴더는 미리보기를 지원하지 않습니다."}
        size = os.path.getsize(full_path)
        if size > 512 * 1024:
            return {"error": "파일이 너무 큽니다 (512KB 초과)."}
        with open(full_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return {"path": path, "content": content}
    except ValueError as e:
        return {"error": str(e)}
    except UnicodeDecodeError:
        return {"error": "미리보기를 지원하지 않는 파일입니다. (텍스트 파일만 가능)"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/volumes")
def get_volumes():
    volumes = client.volumes.list()
    result = []
    for v in volumes:
        result.append({
            "name": v.name,
            "driver": v.attrs["Driver"],
            "mountpoint": v.attrs["Mountpoint"],
        })
    return result

@app.get("/containers/{container_id}/volumes")
def get_container_volumes(container_id: str):
    try:
        container = client.containers.get(container_id)
        mounts = container.attrs["Mounts"]
        return [
            {
                "type": m["Type"],
                "source": m.get("Source", ""),
                "destination": m["Destination"],
                "mode": m.get("Mode", ""),
            }
            for m in mounts
        ]
    except Exception as e:
        return {"error": str(e)}        

@app.get("/containers/{container_id}/logs")
def get_logs(container_id: str, lines: int = 100):
    try:
        container = client.containers.get(container_id)
        logs = container.logs(tail=lines, timestamps=True).decode("utf-8")
        return {"logs": logs}
    except Exception as e:
        return {"error": str(e)}        