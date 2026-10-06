#!/usr/bin/env bash
# Regenerates the MuJoCo model from my_robot.urdf.xacro into src/my_robot_simulation/mujoco/,
# next to the scene.xml that includes it. Run after any URDF or mujoco_inputs.xml change.
set -eo pipefail  # No -u: colcon setup scripts read unset variables.

source install/setup.bash
pkg="$(cd "$(dirname "$0")/.." && pwd)"
dest="${pkg}/mujoco"
work="$(mktemp -d)"
trap 'rm -rf "${work}"' EXIT

xacro "${pkg}/../my_robot_description/urdf/my_robot.urdf.xacro" > "${work}/my_robot.urdf"
# The converter resolves relative paths against the cwd, so run it from the work dir.
# Add --add_free_joint for a mobile robot: it turns the URDF root into a free body.
(cd "${work}" && ros2 run mujoco_ros2_control make_mjcf_from_robot_description.py \
  --urdf my_robot.urdf \
  --mujoco_inputs "${dest}/mujoco_inputs.xml" \
  --scene "${dest}/scene.xml" \
  --save_only --output out)
# Fixes the converter can't express through mujoco_inputs.xml (mesh unit rescaling, restoring
# dropped inertials, extra contact geoms) go in a script run here on "${work}/out".

# Keep only the model and the asset files it references; the converter leaves
# intermediates (unsplit OBJs, MTL folders) that roughly double the size.
out="${work}/out"
rm -rf "${dest}/assets"
if [[ -d "${out}/assets" ]]; then
  { grep -o 'file="[^"]*"' "${out}/mujoco_description_formatted.xml" || true; } | cut -d'"' -f2 | sort -u > "${work}/used"
  (cd "${out}/assets" && find . -type f | sed 's#^\./##' | sort | comm -23 - "${work}/used" | xargs -r rm)
  find "${out}/assets" -type d -empty -delete
  [[ -d "${out}/assets" ]] && mv "${out}/assets" "${dest}/"
fi
mv "${out}/mujoco_description_formatted.xml" "${dest}/"
echo "MJCF written to ${dest}"
