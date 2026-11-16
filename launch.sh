#!/usr/bin/env bash
set -eo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
source /opt/ros/jazzy/setup.bash
python3 build_scene.py
exec gz sim -r "$@" "$PWD/worlds/office.sdf"
