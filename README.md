# linorobot2

Linorobot2 是基于 ROS 2 的移动机器人项目，支持两轮差速、四轮和麦克纳姆轮底盘，提供实物机器人启动、传感器接入、建图、自动导航及 Gazebo 仿真功能。

本仓库主要包含启动脚本、参数配置和机器人模型。建图使用 SLAM Toolbox，导航使用 Nav2，里程计与 IMU 数据融合使用 robot_localization；单片机固件和硬件搭建说明位于 [linorobot2_hardware](https://github.com/linorobot/linorobot2_hardware)。

## 目录说明

- **[linorobot2/](./linorobot2)**：项目基础包，包含 ROS 包声明和构建文件。
- **[linorobot2_base/](./linorobot2_base)**：底盘定位配置，`config/ekf.yaml` 用于融合里程计与 IMU 数据，输出 `/odom`。
- **[linorobot2_bringup/](./linorobot2_bringup)**：实物机器人启动入口，接入 micro-ROS、传感器、机器人模型和定位滤波器，并提供手柄遥控与自定义机器人启动文件。
- **[linorobot2_description/](./linorobot2_description)**：URDF/Xacro 机器人模型，描述车体、车轮、传感器位置及仿真控制插件。
- **[linorobot2_gazebo/](./linorobot2_gazebo)**：Gazebo 仿真启动文件和场景；包含速度指令超时停止、二维地图转仿真场景等辅助脚本。
- **[linorobot2_navigation/](./linorobot2_navigation)**：SLAM 与 Nav2 启动文件、实物和仿真导航参数、地图及 RViz 配置。
- **[docker/](./docker)**：容器构建与运行配置，可运行实物启动、仿真、建图、导航和 RViz。
- **[docs/](./docs)**：架构图和演示动图。

根目录辅助文件：

- **[ROBOT_INSTALLATION.md](./ROBOT_INSTALLATION.md)**：实物机器人手动安装、传感器配置和开机自启动说明。
- **[install_linorobot2.bash](./install_linorobot2.bash)**：安装依赖和驱动，创建工作空间并设置环境变量。
- **[update_microros.bash](./update_microros.bash)**：更新并重新构建 micro-ROS Agent。
- **[LICENSE](./LICENSE)**：Apache 2.0 许可证。

## 安装与配置

当前分支为 `humble`，请使用与本机 ROS 2 发行版匹配的分支。以下命令在已有 ROS 2 工作空间中执行：

```bash
source /opt/ros/humble/setup.bash
cd <ros2_ws>
git clone -b humble https://github.com/linorobot/linorobot2 src/linorobot2
rosdep update
rosdep install --from-path src --ignore-src -y --skip-keys microxrcedds_agent --skip-keys micro_ros_agent
colcon build
source install/setup.bash
```

实物机器人还需安装 micro-ROS Agent 和对应的传感器驱动，具体参阅 [安装说明](./ROBOT_INSTALLATION.md)。

主要环境变量：

- `LINOROBOT2_BASE`：底盘类型，常用值为 `2wd`、`4wd`、`mecanum`。
- `LINOROBOT2_LASER_SENSOR`：激光扫描传感器型号，用于选择对应驱动。
- `LINOROBOT2_DEPTH_SENSOR`：深度传感器型号，用于选择对应驱动。

例如，选择两轮底盘：

```bash
export LINOROBOT2_BASE=2wd
```

机器人尺寸和传感器安装位置在 `linorobot2_description/urdf/*_properties.urdf.xacro` 中配置。导航参数位于 `linorobot2_navigation/config/`。修改后重新构建并加载工作空间。

## 核心运行流程

先启动实物机器人或 Gazebo，再建图并保存地图，最后加载地图进行自动导航。各组件在独立终端运行，每个终端都需加载 ROS 2 和工作空间环境；模型相关启动还需设置 `LINOROBOT2_BASE`。

### 1. 启动机器人

实物机器人：

```bash
ros2 launch linorobot2_bringup bringup.launch.py
```

默认单片机串口为 `/dev/ttyACM0`，可通过 `base_serial_port:=/dev/ttyACM1` 修改。等待 micro-ROS Agent 连接成功后，再运行建图或导航。

Gazebo 仿真：

```bash
ros2 launch linorobot2_gazebo gazebo.launch.py
```

### 2. 建图与保存地图

```bash
ros2 launch linorobot2_navigation slam.launch.py
```

仿真时添加 `sim:=true rviz:=true`。在另一个终端启动键盘遥控，控制机器人覆盖工作区域：

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

保存地图，使用实际路径替换占位符：

```bash
ros2 run nav2_map_server map_saver_cli -f <地图保存路径>/<地图名> --ros-args -p save_map_timeout:=10000.
```

### 3. 自动导航

结束 SLAM 后，保持机器人或仿真运行，加载已保存的地图：

```bash
ros2 launch linorobot2_navigation navigation.launch.py map:=<地图保存路径>/<地图名>.yaml
```

仿真时添加 `sim:=true rviz:=true`；有图形界面的实物运行环境可添加 `rviz:=true`。在 RViz 中设置初始位姿，再发送导航目标。无图形界面的机器人可通过主机上的 [linorobot2_viz](https://github.com/linorobot/linorobot2_viz) 远程查看。

## Codex / ROS-MCP Gazebo 仿真

可以用下面的入口同时启动现有 `playground.world` Gazebo 场景、机器人模型、Nav2、RViz 和 rosbridge WebSocket（默认端口 `9090`）：

```bash
sudo apt install ros-$ROS_DISTRO-rosbridge-server
export LINOROBOT2_BASE=4wd
ros2 launch linorobot2_gazebo simulation_stack.launch.py
```

如果需要显式指定场景：

```bash
ros2 launch linorobot2_gazebo simulation_stack.launch.py \
  world:=/home/zjj/code/linorobot2/install/linorobot2_gazebo/share/linorobot2_gazebo/worlds/playground.world
```

检查接口：

```bash
ss -lnt | grep 9090
ros2 topic list
ros2 action list | grep navigate_to_pose
```

ROS-MCP 使用 `ws://localhost:9090` 连接。机器人规格文件位于
`linorobot2_gazebo/robot_specifications/linorobot2-sim.yaml`，其中记录当前仿真使用的 Topic、Nav2 Action、诊断顺序和人工确认规则。它不会假设某个真实机器人型号；实际底盘由 Gazebo 启动时加载的 linorobot2 URDF 决定。该文件只是给 Codex 的上下文，不是安全控制器；速度限制、碰撞检测和急停仍由 Gazebo、Nav2 和底盘控制器负责。

### 启动 ROS-MCP

Codex 的 MCP 配置必须能找到 `uvx`，并在启动 ROS-MCP 前加载 ROS 2 环境。请在能访问网络的本机终端安装 `uv`（当前 Codex 沙箱无法解析外网域名，不能代为下载）：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.local/bin/env
```

安装后检查：

```bash
uv --version
uvx --version
uvx ros-mcp --transport=stdio
```

本仓库提供了环境包装脚本：

```bash
chmod +x scripts/start_ros_mcp.sh
./scripts/start_ros_mcp.sh
```

在 Codex MCP 配置中，将 `ros_mcp` 的 command 改为该脚本的绝对路径：

```toml
[mcp_servers.ros_mcp]
enabled = true
command = "/home/zjj/code/linorobot2/scripts/start_ros_mcp.sh"
args = []
cwd = "/home/zjj/code/linorobot2"
```

启动 Gazebo 后重启 Codex/MCP 会话，再让 Codex 执行只读检查。若 `uvx` 不存在，Codex 不会得到任何 ROS 工具；仅启动 rosbridge 不能替代 ROS-MCP。

仿真入口默认启动 `codex_perception_gateway`。它订阅 Gazebo 的原始 RGB/深度图，并发布适合 MCP 读取的压缩预览：`/codex/perception/rgb/compressed`、`/codex/perception/depth/compressed`，以及中心区域深度和数据可用性摘要 `/codex/perception/status`。这样 Codex 可以直接查看仿真相机画面，再结合深度、TF 和 costmap 推理目标位置；目标识别由 Codex 完成，不需要预先部署 YOLO。深度预览是伪彩色图，精确距离仍应结合原始深度数据或点云读取。

建议交互顺序：先检查 `/clock`、TF、`/scan`、`/odom`、`/codex/perception/status` 和 Nav2 节点；读取 RGB 预览识别目标；读取深度/点云和 TF 估计目标位置；结合 costmap 选择距目标约 1 米的安全位姿；展示 `/navigate_to_pose` 目标并等待人工确认后再发送 Action。
