# Gazebo G1-D 办公室仿真

## 首次运行

需要 Ubuntu 24.04（或 WSL2 上的 Ubuntu 24.04）、ROS 2 Jazzy、
Gazebo Harmonic 和 Python 3。使用 ROS 仓库安装 Gazebo 时，
可安装 `ros-jazzy-ros-gz`。首次下载模型需要连接 GitHub。

克隆本项目后，在仓库目录运行：

```bash
python3 fetch_model.py
./launch.sh
```

无窗口启动：`./launch.sh -s`。启动脚本从 Unitree 上游原始
`unitree_ros/robots/g1_d_description/g1_d.urdf` 转换模型并重新生成
`worlds/office.sdf`。场景结构在 `build_scene.py` 中定义。
官方 URDF 原样保留；上游缺失的相机网格在 Gazebo 预览中用小型盒体代替。
`fetch_model.py` 下载锁定版本的模型和上游许可证。第三方文件和生成的
SDF 不提交到项目仓库。修改场景请编辑 `build_scene.py`。

办公室含办公桌、会议桌、置物区和中间通道，桌上放有红色水杯与小盒子。
本版为静态场景预览，机器人保留官方模型外观和关节定义。底盘、双臂控制，
RGB-D、雷达和物体抓取需要后续接入。

查看当前模型版本：

```bash
cat unitree_ros/REVISION
```
