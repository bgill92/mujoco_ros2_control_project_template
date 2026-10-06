# my_robot_simulation

MuJoCo simulation of my_robot through
[mujoco_ros2_control](https://github.com/ros-controls/mujoco_ros2_control). MuJoCo runs inside
the controller manager as a ros2_control hardware plugin, so the controllers are the same ones a
real robot would use.

## Contents

| Path | What it is |
|---|---|
| `launch/sim.launch.py` | Starts MuJoCo + controller manager, `robot_state_publisher`, controller spawner, and RViz. |
| `config/controllers.yaml` | Controller manager and controller parameters. |
| `mujoco/scene.xml` | Top-level MJCF: floor, lights, visual settings; includes the robot model. |
| `mujoco/mujoco_inputs.xml` | Converter input: actuators, joint damping, geom defaults. |
| `mujoco/mujoco_description_formatted.xml` | **Generated** robot MJCF. Do not hand-edit; regenerate. |
| `mujoco/assets/` | **Generated** OBJ meshes. Appears once the URDF has meshes. |
| `scripts/gen_mjcf.sh` | Regenerates the two generated items above from the URDF. |

## Running

```bash
pixi run sim                               # MuJoCo viewer + RViz
pixi run sim headless:=true rviz:=false    # no windows
```

| Launch argument | Default | Effect |
|---|---|---|
| `headless` | `false` | Run MuJoCo without its viewer. |
| `rviz` | `true` | Start RViz with `my_robot_description`'s config. |
| `mujoco_model` | `share/my_robot_simulation/mujoco/scene.xml` | MJCF scene to load. |

`pixi run sim` builds the workspace first, so freshly generated MJCF files get installed.

### Controllers

| Controller | Type | Interface |
|---|---|---|
| `joint_state_broadcaster` | `joint_state_broadcaster/JointStateBroadcaster` | Publishes `/joint_states`. |
| `arm_controller` | `joint_trajectory_controller/JointTrajectoryController` | Action `/arm_controller/follow_joint_trajectory`; position commands on `joint1` and `joint2`; partial goals allowed. |

### Example goal

Run in `pixi shell` after `source install/setup.bash`:

```bash
ros2 action send_goal /arm_controller/follow_joint_trajectory \
  control_msgs/action/FollowJointTrajectory \
  "{trajectory: {joint_names: [joint1, joint2], points: [{positions: [1.0, 0.5], time_from_start: {sec: 2}}]}}"
```

`/clock` carries sim time. Every node runs with `use_sim_time`, so pausing MuJoCo pauses the
controllers.

### Physics only (no ROS)

```bash
pixi run python -m mujoco.viewer --mjcf=src/my_robot_simulation/mujoco/scene.xml
```

## Regenerating the MuJoCo model

```bash
pixi run gen-mjcf
```

Rerun after changing anything in `my_robot_description/urdf/` or `mujoco/mujoco_inputs.xml`.
`scene.xml` is included at load time, so editing it needs no regeneration. The steps:

1. **xacro**: expands `my_robot.urdf.xacro` with defaults (`ros2_control:=none`).
2. **Converter**: mujoco_ros2_control's `make_mjcf_from_robot_description.py` runs in a temp
   directory. It converts meshes to OBJ and merges `mujoco_inputs.xml`. Add `--add_free_joint`
   for a mobile robot.
3. **Post-processing** (none yet): if the converter output needs fixes `mujoco_inputs.xml` can't
   express, call a script where the comment in `gen_mjcf.sh` says. See the top-level README.
4. **Copy back**: only `mujoco_description_formatted.xml` and the asset files it references go
   into `mujoco/`. The rest are converter intermediates and are discarded.

## Model details

- **Actuators**: MuJoCo `position` actuators named after their joints (mujoco_ros2_control
  matches them by name), kp 50, `dampratio` 1, plus joint damping 1 and armature 0.01.
- **Contacts**: every robot geom has `contype=0 conaffinity=0`, so the robot collides with
  nothing, itself included. Opt geoms back in when you need contacts.
- **Fixed base**: there is no free joint, so MuJoCo welds `base_link` to the world.

## Assumptions and caveats

- **Dynamics are approximate**: masses and inertias are estimates, and the actuator gains were
  picked to hold pose and track goals, not to match real motors. With kp 50, `joint2` settles
  about 0.004 rad below its target under gravity.
- **Generated files** are kept in the source tree, so the sim runs straight after a clone.
- **Real-time warning**: `Could not enable FIFO RT scheduling policy` at startup is harmless in
  simulation.
