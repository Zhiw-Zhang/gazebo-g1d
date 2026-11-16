#!/usr/bin/env python3
"""Build the Gazebo preview world from the unmodified Unitree URDF."""
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "unitree_ros/robots/g1_d_description"
URDF = SOURCE / "g1_d.urdf"


def add(parent, tag, value=None, **attrs):
    item = ET.SubElement(parent, tag, attrs)
    item.text = value
    return item


def vector(values):
    return " ".join(str(value) for value in values)


def shape(parent, kind, dimensions):
    geometry = add(parent, "geometry")
    if kind == "box":
        add(add(geometry, "box"), "size", vector(dimensions))
    else:
        cylinder = add(geometry, "cylinder")
        add(cylinder, "radius", str(dimensions[0]))
        add(cylinder, "length", str(dimensions[1]))


def prop(world, name, parts, color):
    model = add(world, "model", name=name)
    add(model, "static", "true")
    link = add(model, "link", name="body")
    for index, (kind, position, dimensions) in enumerate(parts):
        for role in ("visual", "collision"):
            part = add(link, role, name=f"{role}_{index}")
            add(part, "pose", vector((*position, 0, 0, 0)))
            shape(part, kind, dimensions)
            if role == "visual":
                material = add(part, "material")
                add(material, "ambient", color)
                add(material, "diffuse", color)
    return model


def table(world, name, x, y, width, depth, color):
    parts = [("box", (x, y, 0.73), (width, depth, 0.06))]
    for dx in (-1, 1):
        for dy in (-1, 1):
            parts.append(("box", (x + dx * (width / 2 - 0.1),
                                  y + dy * (depth / 2 - 0.1), 0.35),
                          (0.08, 0.08, 0.70)))
    prop(world, name, parts, color)


def build_robot(world):
    # Give the converter filesystem paths, then emit standard file URIs.
    robot = ET.parse(URDF)
    for geometry in robot.findall(".//geometry"):
        mesh = geometry.find("mesh")
        if mesh is None:
            continue
        relative = re.sub(r"^package://g1_d_description/", "", mesh.attrib["filename"])
        mesh_path = SOURCE / relative
        if not mesh_path.is_file() and "camera" in mesh_path.name.casefold():
            geometry.remove(mesh)
            add(geometry, "box", size="0.035 0.055 0.025")
            continue
        mesh.set("filename", str(mesh_path.resolve(strict=True)))
    build = ROOT / "build"
    build.mkdir(exist_ok=True)
    converted = build / "g1_d_resolved.urdf"
    robot.write(converted, encoding="utf-8", xml_declaration=True)
    sdf = subprocess.check_output(["gz", "sdf", "-p", str(converted)], text=True)
    model = ET.fromstring(sdf).find("model")
    if model is None:
        raise RuntimeError("URDF conversion did not produce a model")
    model.set("name", "g1_d")
    for uri in model.findall(".//mesh/uri"):
        if uri.text and uri.text.startswith(str(SOURCE)):
            uri.text = Path(uri.text).as_uri()
    # Hold the original articulated geometry in its neutral display pose.
    # Motion requires wheel and joint controllers plus base support.
    static = model.find("static")
    if static is None:
        static = add(model, "static")
    static.text = "true"
    pose = model.find("pose")
    if pose is None:
        pose = add(model, "pose")
    pose.text = "-1.8 0 0.13 0 0 0"
    world.append(model)


def main():
    sdf = ET.Element("sdf", version="1.9")
    world = add(sdf, "world", name="g1d_office")
    light = add(world, "light", name="ceiling_light", type="directional")
    add(light, "direction", "-0.3 0.2 -1")
    add(light, "diffuse", "0.9 0.9 0.9 1")
    add(light, "cast_shadows", "true")
    scene = add(world, "scene")
    add(scene, "ambient", "0.52 0.52 0.52 1")
    add(scene, "background", "0.74 0.81 0.86 1")
    prop(world, "floor", [("box", (0, 0, -0.05), (9, 7, 0.1))],
         "0.66 0.68 0.70 1")
    prop(world, "walls", [
        ("box", (0, 3.5, 0.75), (9, 0.12, 1.5)),
        ("box", (4.5, 0, 0.75), (0.12, 7, 1.5)),
        ("box", (-4.5, 0, 0.75), (0.12, 7, 1.5)),
    ], "0.83 0.86 0.89 1")
    table(world, "work_desk", -2.1, 2.0, 1.55, 0.8, "0.58 0.36 0.20 1")
    table(world, "meeting_table", 2.15, 1.65, 2.1, 1.15, "0.35 0.28 0.23 1")
    table(world, "dropoff_shelf", 2.8, -2.1, 1.3, 0.65, "0.30 0.49 0.58 1")
    prop(world, "red_cup", [("cylinder", (-2.25, 1.95, 0.815), (0.045, 0.11))],
         "0.78 0.10 0.08 1")
    prop(world, "small_box", [("box", (-1.85, 2.02, 0.815), (0.20, 0.16, 0.11))],
         "0.85 0.61 0.23 1")
    prop(world, "dropoff_marker", [("box", (2.8, -2.1, 0.763), (0.38, 0.30, 0.006))],
         "0.15 0.66 0.40 1")
    build_robot(world)
    target = ROOT / "worlds/office.sdf"
    target.parent.mkdir(exist_ok=True)
    ET.indent(sdf)
    ET.ElementTree(sdf).write(target, encoding="utf-8", xml_declaration=True)
    print(target, flush=True)


if __name__ == "__main__":
    main()
