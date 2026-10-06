# my_robot_description

URDF description of **my_robot**. The template ships a placeholder: a two-joint arm built from
primitives, with its base fixed to the world. Replace it with your robot and update this README
as you go.

## Contents

| Path | What it is |
|---|---|
| `urdf/my_robot.urdf.xacro` | Top-level description, with an optional `<ros2_control>` block. The single source of truth for RViz and simulation. |
| `launch/display.launch.py` | Shows the robot in RViz with joint sliders. No physics. |
| `rviz/my_robot.rviz` | RViz config: grid, robot model, fixed frame `base_link`. |

Add a `meshes/` directory for your own or modified meshes, and add `meshes` to the
`install(DIRECTORY ...)` line in `CMakeLists.txt`. Vendor descriptions come from
`external_packages/` (see its README).

## Running

```bash
pixi run bash -c "source install/setup.bash && ros2 launch my_robot_description display.launch.py"
```

| Launch argument | Default | Effect |
|---|---|---|
| `gui` | `true` | `joint_state_publisher_gui` sliders; otherwise all joints sit at zero. |

## xacro arguments

| Argument | Default | Notes |
|---|---|---|
| `ros2_control` | `none` | `mujoco` adds a `<ros2_control>` block using `mujoco_ros2_control/MujocoSystemInterface`. Keep the default `none` for RViz and MJCF generation. |
| `mujoco_model` | `""` | MJCF scene path passed to the MuJoCo hardware plugin. |
| `headless` | `false` | Runs MuJoCo without its viewer. |

With `ros2_control:=mujoco`, both joints have a `position` command interface and `position` and
`velocity` state interfaces. Each commanded joint needs a MuJoCo actuator with the same name in
`my_robot_simulation/mujoco/mujoco_inputs.xml`.

## Robot structure

TF tree: `base_link → link1 → link2`.

| Joint | Type | Axis | Range | Velocity limit |
|---|---|---|---|---|
| `joint1` | revolute | z | ±3.14159 rad | 2.0 rad/s |
| `joint2` | revolute | y | ±1.5708 rad | 2.0 rad/s |

## Changes from upstream

None: the placeholder is written from scratch. When you copy or include vendor files, list here
each file's source (repo, branch, commit) and every change made to it, with the reason.

## Assumptions and caveats

- **Masses and inertias are estimates.** Every inertia tensor is a solid box or cylinder over the
  link geometry. Replace with CAD or measured values if dynamics matter.
- **The root link has no `<inertial>`.** KDL rejects one on the root link, and MuJoCo welds a root
  without a free joint to the world. A mobile base carries its mass on a fixed child link.
- **Effort limits** (10 N·m) are placeholders.
