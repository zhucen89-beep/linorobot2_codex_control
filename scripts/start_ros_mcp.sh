#!/usr/bin/env bash
set -euo pipefail

# ROS-MCP is started by Codex as a stdio MCP server. Load the same ROS
# environment as the Gazebo terminal before starting it.
source /opt/ros/${ROS_DISTRO:-humble}/setup.bash
workspace="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -f "${workspace}/install/setup.bash" ]]; then
  source "${workspace}/install/setup.bash"
fi

uvx_bin="$(command -v uvx || true)"
if [[ -z "${uvx_bin}" && -x "${HOME}/.local/bin/uvx" ]]; then
  uvx_bin="${HOME}/.local/bin/uvx"
fi
if [[ -z "${uvx_bin}" ]]; then
  echo "ROS-MCP cannot start: uvx was not found. Install uv, then restart Codex." >&2
  exit 127
fi

exec "${uvx_bin}" ros-mcp --transport=stdio
