# external_packages

Upstream (vendor) repositories this project depends on, added as **git submodules**. Typically a
robot manufacturer's ROS repo that contains the `*_description` package (URDF + meshes) for an arm,
base or gripper you are assembling.

The directory exists so vendor code stays separate from code you own in `src/`, pinned to a
known commit and never edited in place.

## Rules

- **Read-only.** Do not edit files in here. To change a vendor file, copy it into your
  `src/<robot>_description/` package, modify the copy, and record what changed and why (with the
  upstream branch and commit) in that package's README. Missing data that can be *added* rather
  than changed, such as mass on a link without an `<inertial>`, goes on a fixed child link in your
  own xacro instead.
- **Build only what you need.** Vendor repos often target older ROS distros, and only their
  description packages are usually needed here. Add each one to `--base-paths` of the `build` task
  in `pixi.toml`; colcon does not scan this directory otherwise.
- **Pin a branch and keep it shallow.** Vendor repos can be large.
- **Keep their licenses.** Vendor code keeps its own license, not the project's MIT.

## Adding a vendor repo

```bash
git submodule add -b <branch> --depth 1 <url> external_packages/<repo>
git config -f .gitmodules submodule.external_packages/<repo>.shallow true
```

Then:

1. Add the description package to `pixi.toml`:
   `build = "colcon build --symlink-install --base-paths src external_packages/<repo>/<robot>_description"`.
2. Add `<exec_depend><robot>_description</exec_depend>` to your description package's `package.xml`.
3. `xacro:include` its URDF from your top-level xacro, e.g.
   `<xacro:include filename="$(find <robot>_description)/urdf/<robot>.urdf"/>`.

Clone a project that uses submodules with `git clone --recurse-submodules <url>`, or run
`git submodule update --init` in an existing clone.

## Example

emma (experimental_mobile_manipulator) uses two:

```ini
[submodule "external_packages/myagv_ros2"]
	path = external_packages/myagv_ros2
	url = https://github.com/elephantrobotics/myagv_ros2.git
	branch = galactic-JN
	shallow = true
[submodule "external_packages/mycobot_ros2"]
	path = external_packages/mycobot_ros2
	url = https://github.com/elephantrobotics/mycobot_ros2.git
	branch = humble
	shallow = true
```

Both repos target older distros, so only `myagv_description` and `mycobot_description` are built.
The base URDF is included unchanged. The arm URDF was copied into `emma_description` and modified
(inertials added, velocity limits fixed) because the original couldn't be simulated as shipped.
