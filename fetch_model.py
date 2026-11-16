#!/usr/bin/env python3
"""Fetch the official model and its referenced meshes at a single revision."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import time
from urllib.request import Request, urlopen
from urllib.parse import quote
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
API = "https://api.github.com/repos/unitreerobotics/unitree_ros"
RAW = "https://raw.githubusercontent.com/unitreerobotics/unitree_ros"
MODEL = "robots/g1_d_description"
REVISION = "157ff950351e5f535e03c5d85a16b7d594b3dbcc"


def get(url):
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers={"User-Agent": "gazebo-g1d-setup"}), timeout=35) as response:
                return response.read()
        except OSError:
            if attempt == 2:
                raise
            time.sleep(attempt + 1)


def main():
    revision = REVISION
    url = f"{RAW}/{revision}"
    urdf = get(f"{url}/{MODEL}/g1_d.urdf")
    meshes = {mesh.attrib["filename"].removeprefix("package://g1_d_description/")
              for mesh in ET.fromstring(urdf).findall(".//mesh")}
    entries = json.loads(get(f"{API}/contents/{MODEL}/meshes?ref={revision}"))
    mesh_names = {entry["name"].casefold(): entry["name"] for entry in entries}

    def save(relative, data=None):
        path = ROOT / "unitree_ros" / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if data is None:
            data = get(f"{url}/{relative}")
        path.write_bytes(data)

    def save_mesh(mesh):
        filename = mesh_names.get(Path(mesh).name.casefold())
        if filename is None:
            if "camera" in Path(mesh).name.casefold():
                print(f"Missing upstream camera mesh (preview will use a box): {mesh}", flush=True)
                return
            raise FileNotFoundError(f"Mesh referenced by the URDF is absent upstream: {mesh}")
        if (ROOT / "unitree_ros" / MODEL / mesh).is_file():
            return
        data = get(f"{url}/{MODEL}/meshes/{quote(filename)}")
        save(f"{MODEL}/{mesh}", data)

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(save_mesh, sorted(meshes)))
    save("LICENSE")
    save(f"{MODEL}/g1_d.urdf", urdf)
    (ROOT / "unitree_ros/REVISION").write_text(revision + "\n", encoding="utf-8")
    print(f"Unitree {revision}, {len(meshes)} meshes", flush=True)


if __name__ == "__main__":
    main()
