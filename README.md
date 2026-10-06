# mujoco_ros2_control project template

A starting layout for simulating a robot in [MuJoCo](https://mujoco.org) through
[mujoco_ros2_control](https://github.com/ros-controls/mujoco_ros2_control), extracted from
[experimental_mobile_manipulator](https://github.com/bgill92/experimental_mobile_manipulator)
(emma). MuJoCo runs inside the ros2_control controller manager as a hardware plugin, so the
controllers, topics and actions are the same ones a real robot would use.

The template is a working project, not a set of blanks. It ships a placeholder robot, `my_robot`
(a two-joint arm made of primitives), so `build → gen-mjcf → sim` runs end to end before you
change anything. You then rename it and swap in your robot one piece at a time, re-running the sim
after each step.

## Prerequisites

| Need | Why / notes |
|---|---|
| Linux x86-64 | `pixi.toml` only lists `linux-64`. Add platforms there (and check RoboStack builds them) to try others. |
| [pixi](https://pixi.sh) | Provides ROS 2 Lyrical, colcon, compilers, MuJoCo and every Python tool. **No system ROS install**; don't source `/opt/ros`. `curl -fsSL https://pixi.sh/install.sh \| sh` |
| git (with submodules) | Vendor description packages come in as submodules under `external_packages/`. |
| OpenGL-capable display | Only for the MuJoCo viewer and RViz. `headless:=true rviz:=false` runs without one (CI, SSH). |
| A robot description | URDF/xacro of your robot, or an upstream vendor description package. See [What the URDF needs](#what-the-urdf-needs) — vendor URDFs usually fail at least one of these. |
| Basic ROS 2 and ros2_control | Launch files, `robot_description`, hardware interfaces vs. controllers. The [ros2_control docs](https://control.ros.org) cover it. |

## Quick start

```bash
pixi run gen-mjcf                          # build, then URDF -> MJCF (already committed; rerun after URDF changes)
pixi run sim                               # MuJoCo viewer + RViz
pixi run sim headless:=true rviz:=false    # no windows
pixi run bash -c "source install/setup.bash && ros2 launch my_robot_description display.launch.py"  # RViz + joint sliders, no physics
```

Move the arm (in `pixi shell`, after `source install/setup.bash`):

```bash
ros2 action send_goal /arm_controller/follow_joint_trajectory control_msgs/action/FollowJointTrajectory \
  "{trajectory: {joint_names: [joint1, joint2], points: [{positions: [1.0, 0.5], time_from_start: {sec: 2}}]}}"
```

Physics only, no ROS: `pixi run python -m mujoco.viewer --mjcf=src/my_robot_simulation/mujoco/scene.xml`.

## Layout

```
.
├── pixi.toml                     # environment + tasks: build, gen-mjcf, sim
├── pixi.lock                     # pinned environment; commit it
├── AGENTS.md / CLAUDE.md         # rules for coding agents (pixi only, don't edit submodules, generated files)
├── external_packages/            # vendor repos as git submodules, never edited (see its README)
└── src/
    ├── my_robot_description/     # WHAT the robot is — no simulator knowledge except the ros2_control block
    │   ├── README.md                  # structure, xacro args, changes from upstream, assumptions
    │   ├── urdf/my_robot.urdf.xacro   # single source of truth for RViz, sim (and later real hardware)
    │   ├── meshes/                    # (add) your own or modified meshes
    │   ├── launch/display.launch.py   # RViz + joint_state_publisher_gui
    │   └── rviz/my_robot.rviz
    └── my_robot_simulation/      # HOW it is simulated
        ├── README.md                  # launch args, controllers, regeneration, model details, caveats
        ├── config/controllers.yaml    # controller_manager + controllers
        ├── launch/sim.launch.py       # robot_state_publisher, ros2_control_node (MuJoCo), spawner, RViz
        ├── mujoco/
        │   ├── scene.xml                         # hand-written: floor, lights, visuals; <include>s the robot
        │   ├── mujoco_inputs.xml                 # hand-written: actuators, damping, equalities, geom defaults
        │   ├── mujoco_description_formatted.xml  # GENERATED robot MJCF — never hand-edit
        │   └── assets/                           # GENERATED OBJ meshes (appears once the URDF has meshes)
        └── scripts/gen_mjcf.sh        # URDF -> MJCF pipeline
```

### Design rules

These are the decisions that kept emma maintainable; the template is built around them.

1. **The URDF is the only robot description.** The MJCF is generated from it, never forked. Anything
   MuJoCo needs that URDF can't say goes in one of three places, so regenerating never loses work:
   - `mujoco_inputs.xml` — actuators, joint damping/armature, equality constraints, geom defaults;
   - `scene.xml` — world, lights, floor, visual settings (included at load time, no regen needed);
   - a post-processing script called from `gen_mjcf.sh` — fixes the converter can't express (see below).
2. **Description and simulation are separate packages.** `*_description` knows nothing about MuJoCo
   except an opt-in `<ros2_control>` block behind the `ros2_control:=mujoco` xacro arg. The default
   (`none`) keeps RViz and the MJCF generator free of hardware tags. A real-hardware package later
   adds another value (e.g. `ros2_control:=real`) with its own plugin.
3. **Generated MJCF is committed** so `pixi run sim` works straight after a clone. `gen_mjcf.sh`
   copies back only the model and the assets it references; converter intermediates are discarded.
4. **Vendor code is read-only.** Upstream repos are submodules in `external_packages/`; only their
   `*_description` packages are added to the `build` task's `--base-paths` (the rest often targets
   older distros). To change a vendor file, copy it into your description package and edit the
   copy, recording what changed and why in that package's README. If the vendor URDF lacks mass,
   hang it on a fixed child link (emma's `base_inertia`) rather than editing the submodule.
5. **All tooling runs through pixi.** Add dependencies with `pixi add ros-lyrical-<name>` (or
   `[pypi-dependencies]` for pip-only tools), never apt/pip. Keep `<exec_depend>`s in each
   `package.xml` in sync.
6. **Every node uses sim time** (`use_sim_time: True`), so pausing MuJoCo pauses the controllers.
7. **One spawner activates all controllers in order.** Separate spawners race.

## Making it yours

1. **Rename.** Replace `my_robot` everywhere, including file and directory names:
   ```bash
   NAME=emma
   grep -rl my_robot --exclude-dir={.git,.pixi,build,install,log} . | xargs sed -i "s/my_robot/${NAME}/g"
   find src -depth -name '*my_robot*' -execdir bash -c 'mv "$1" "${1//my_robot/'"${NAME}"'}"' _ {} \;
   rm -rf build install log && pixi install
   ```
   Then fix `authors` in `pixi.toml`, the `<maintainer>` in both `package.xml`s, and `LICENSE`.
2. **Bring in the robot.** Either write links/joints in `urdf/<name>.urdf.xacro`, or add vendor
   repos (`git submodule add -b <branch> <url> external_packages/<repo>`), add their description
   package to the `build` task, and `xacro:include` their URDF. Check
   [What the URDF needs](#what-the-urdf-needs). View it with `display.launch.py` before simulating.
   Add `meshes` to the `install(DIRECTORY ...)` line in the description `CMakeLists.txt` once you have one.
3. **Expose joints to ros2_control.** List each commanded joint in the `<ros2_control>` block
   (the `position_joint` macro). Mimic/passive joints get state interfaces only.
4. **Add MuJoCo actuators** in `mujoco_inputs.xml`, **named exactly like their joints** — the plugin
   matches by name. Set `ctrlrange` to the joint limits. Add joint damping/armature there too.
5. **Mobile base?** Add `--add_free_joint` to the converter call in `gen_mjcf.sh`. The root link
   becomes a free body; its ground-truth pose is published on `/simulator/floating_base_state`. You
   will need contact geometry (wheels or a stand-in box) and probably a post-processing script.
6. **Configure controllers** in `config/controllers.yaml` and list them in the spawner in
   `sim.launch.py`; add each controller package to `pixi.toml` and the sim `package.xml`. A controller
   must not share a name with a joint (emma's `gripper_action_controller` vs. joint `gripper_controller`).
7. `pixi run gen-mjcf && pixi run sim`. Fix, repeat.
8. **Document** assumptions and caveats (estimated masses, untested limits, stand-ins) in each
   package's README; the shipped ones show the sections to keep. Future-you will need them when sim
   and reality disagree.

## What the URDF needs

The converter and MuJoCo are stricter than RViz. Each of these bit emma:

- **Every moving link has an `<inertial>`** with non-zero mass. MuJoCo rejects massless moving
  bodies. Box/cylinder estimates are fine to start; replace with CAD values if dynamics matter.
- **No `<inertial>` on the root link.** KDL (robot_state_publisher) warns and ignores it. Put base
  mass on a fixed child link instead.
- **Non-zero velocity limits** on actuated joints. Many vendor URDFs ship `velocity="0"`, which
  the joint limiter and trajectory controller then enforce.
- **Meshes in consistent, declared units.** RViz honours the COLLADA `<unit>` tag; the converter
  (trimesh) does not. Mixed-unit meshes (emma had metres, millimetres and inches) need a `scale`
  set in post-processing.
- **Collision geometry that matches the visuals.** Vendor URDFs sometimes rotate one but not the other.
- **`<mimic>` joints are dropped** by the converter. Recreate them as an `<equality><joint>` in
  `mujoco_inputs.xml` (see the comment there).

## Converter gotchas and post-processing

`gen_mjcf.sh` runs xacro → `make_mjcf_from_robot_description.py` → (optional) post-processing →
copy back. When the converter output needs fixing, write a small Python script that edits
`<work>/out/mujoco_description_formatted.xml` in place (idempotent, `xml.etree`) and call it where
the comment in `gen_mjcf.sh` says. emma's
[`postprocess_mjcf.py`](https://github.com/bgill92/experimental_mobile_manipulator/blob/main/src/emma_simulation/scripts/postprocess_mjcf.py)
does three things worth copying when you hit them:

- **Restores dropped inertials.** With body fusion on, the converter drops the `<inertial>` of
  bodies whose mass comes only from fused static links. The compiled reference URDF in the output
  dir still has the right values; copy them back with `mujoco.MjModel.from_xml_path`.
- **Rescales meshes** by filename prefix (the units problem above).
- **Adds contact geometry** (a box stand-in for wheels so a free base rests on the floor).

Other things to know:
- The global geom default in `mujoco_inputs.xml` turns collisions **off** (`contype=0
  conaffinity=0`) so overlapping meshes don't jam joints. Opt specific geoms back in when you need
  contacts (grasping, wheels).
- The converter resolves relative paths against the cwd, which is why `gen_mjcf.sh` runs it in a
  temp dir.
- `--symlink-install` only links files that exist at build time, so build after generating. The
  `sim` task already depends on `build`; launching `ros2 launch` directly after `gen-mjcf` without
  a build fails with `Error opening file 'mujoco_description_formatted.xml'`.

## Expected warnings

- `Could not enable FIFO RT scheduling policy` — harmless in simulation.
- `Unable to find the actuator '<joint>'` — expected for passive/mimic joints with no actuator.
- `ResourceManager has already loaded a urdf ... Ignoring attempt to reload` — harmless;
  robot_state_publisher republished the description.

## Tuning

Position actuators (`kp`, `dampratio`) are picked to hold pose and track goals, not to match real
motors. With `kp=50` the placeholder's `joint2` settles ~0.004 rad below target under gravity.
Raise `kp` in `mujoco_inputs.xml` and regenerate if that matters. Joint `damping` outside the
actuator keeps a saturated position actuator from limit-cycling.

## License

MIT, see [LICENSE](LICENSE). Keep `<license>MIT</license>` in each `package.xml` (create packages
with `ros2 pkg create --license MIT`). Vendor submodules and third-party meshes keep their own licenses.
