"""Mandatory native DWPose smoothing for the H3 pose-control branch."""
from __future__ import annotations

from typing import Any


SMOOTHER_TYPE = "TSPoseKeypointSmoother"
SMOOTHER_WIDGET_NAMES = (
    "filter_extra_people", "smooth_alpha", "gap_frames", "min_run_frames",
    "conf_thresh_body", "conf_thresh_hands", "render_resolution", "smooth_hands",
    "smooth_face",
)
SMOOTHER_WIDGET_VALUES = (True, 0.7, 12, 3, 0.35, 0.6, 768, False, True)


class PoseSmootherError(RuntimeError):
    pass


def _nodes(workflow: dict[str, Any]) -> dict[int, dict[str, Any]]:
    raw_nodes = workflow.get("nodes")
    if not isinstance(raw_nodes, list):
        raise PoseSmootherError("Saved workflow has no nodes list")
    nodes = {node.get("id"): node for node in raw_nodes if isinstance(node, dict) and isinstance(node.get("id"), int)}
    if len(nodes) != len(raw_nodes):
        raise PoseSmootherError("Every workflow node must have a unique integer id")
    return nodes


def _links(workflow: dict[str, Any]) -> dict[int, list[Any]]:
    raw_links = workflow.get("links")
    if not isinstance(raw_links, list):
        raise PoseSmootherError("Saved workflow has no links list")
    links: dict[int, list[Any]] = {}
    for link in raw_links:
        if not isinstance(link, list) or len(link) < 6 or not isinstance(link[0], int):
            raise PoseSmootherError(f"Malformed workflow link: {link!r}")
        if link[0] in links:
            raise PoseSmootherError(f"Duplicate workflow link id {link[0]}")
        links[link[0]] = link
    return links


def _input(node: dict[str, Any], name: str) -> dict[str, Any]:
    for item in node.get("inputs", []):
        if item.get("name") == name:
            return item
    raise PoseSmootherError(f"Node {node.get('id')} has no {name!r} input")


def _source(links: dict[int, list[Any]], node: dict[str, Any], input_name: str) -> tuple[int, int]:
    item = _input(node, input_name)
    link_id = item.get("link")
    if not isinstance(link_id, int) or link_id not in links:
        raise PoseSmootherError(f"Node {node.get('id')} input {input_name!r} has no valid link")
    link = links[link_id]
    return link[1], link[2]


def _set_output_links(node: dict[str, Any], slot: int, link_ids: list[int]) -> None:
    outputs = node.get("outputs")
    if not isinstance(outputs, list) or slot >= len(outputs):
        raise PoseSmootherError(f"Node {node.get('id')} has no output slot {slot}")
    outputs[slot]["links"] = link_ids or None


def _remove_link(workflow: dict[str, Any], link_id: int, nodes: dict[int, dict[str, Any]]) -> None:
    link = next((item for item in workflow["links"] if item[0] == link_id), None)
    if link is None:
        return
    source = nodes.get(link[1])
    target = nodes.get(link[3])
    if source is not None:
        output_links = source["outputs"][link[2]].get("links") or []
        _set_output_links(source, link[2], [item for item in output_links if item != link_id])
    if target is not None:
        target_input = target["inputs"][link[4]]
        if target_input.get("link") == link_id:
            target_input["link"] = None
    workflow["links"] = [item for item in workflow["links"] if item[0] != link_id]


def _new_smoother(node_id: int, order: int, pos: list[float | int]) -> dict[str, Any]:
    return {
        "id": node_id,
        "type": SMOOTHER_TYPE,
        "pos": pos,
        "size": [360, 300],
        "flags": {},
        "order": order,
        "mode": 0,
        "title": "Native DWPose smoother — body + face",
        "inputs": [
            {"name": "pose_keypoints", "type": "POSE_KEYPOINT", "link": None},
            *[{"name": name, "type": value_type, "widget": {"name": name}, "link": None}
              for name, value_type in zip(SMOOTHER_WIDGET_NAMES,
                                          ("BOOLEAN", "FLOAT", "INT", "INT", "FLOAT", "FLOAT", "INT", "BOOLEAN", "BOOLEAN"))],
        ],
        "outputs": [
            {"name": "IMAGE", "type": "IMAGE", "links": None},
            {"name": "pose_keypoints", "type": "POSE_KEYPOINT", "links": None},
        ],
        "properties": {
            "Node name for S&R": SMOOTHER_TYPE,
            "aux_id": "teskor-hub/comfyui-teskors-utils",
            "ver": "c7ac65951426293d0e48839b6e7f70e7882a176f",
        },
        "widgets_values": list(SMOOTHER_WIDGET_VALUES),
        "widgets_values_named": dict(zip(SMOOTHER_WIDGET_NAMES, SMOOTHER_WIDGET_VALUES)),
    }


def assert_pose_smoother(workflow: dict[str, Any]) -> int:
    """Require the active pose route to be 170 keypoints → smoother → 171 → 173."""
    nodes = _nodes(workflow)
    links = _links(workflow)
    for node_id, expected_type in ((170, "DWPreprocessor"), (171, "ImageScale"), (173, "H3FunControlApply")):
        if nodes.get(node_id, {}).get("type") != expected_type:
            raise PoseSmootherError(f"Required pose node {node_id} is not {expected_type}")
    smoother_nodes = [node for node in nodes.values() if node.get("type") == SMOOTHER_TYPE]
    if len(smoother_nodes) != 1:
        raise PoseSmootherError(f"Expected exactly one {SMOOTHER_TYPE}, found {len(smoother_nodes)}")
    smoother = smoother_nodes[0]
    if smoother.get("mode") != 0:
        raise PoseSmootherError("TSPoseKeypointSmoother is disabled or bypassed")
    if tuple(smoother.get("widgets_values") or []) != SMOOTHER_WIDGET_VALUES:
        raise PoseSmootherError("TSPoseKeypointSmoother widgets do not match the required smoothing settings")
    named = smoother.get("widgets_values_named")
    if not isinstance(named, dict) or any(named.get(name) != value for name, value in zip(SMOOTHER_WIDGET_NAMES, SMOOTHER_WIDGET_VALUES)):
        raise PoseSmootherError("TSPoseKeypointSmoother named widget settings are incomplete or incorrect")
    if _source(links, smoother, "pose_keypoints") != (170, 1):
        raise PoseSmootherError("TSPoseKeypointSmoother must consume node 170 POSE_KEYPOINT output 1")
    if _source(links, nodes[171], "image") != (smoother["id"], 0):
        raise PoseSmootherError("ImageScale 171 must consume TSPoseKeypointSmoother IMAGE output")
    if _source(links, nodes[173], "control_video") != (171, 0):
        raise PoseSmootherError("Smoothed pose ImageScale 171 is not the active ancestor of H3 pose control 173")
    if any(link[1:5] == [170, 0, 171, 0] for link in links.values()):
        raise PoseSmootherError("Raw DWPose IMAGE bypass from 170 to 171 remains")
    return smoother["id"]


def wire_pose_smoother(workflow: dict[str, Any]) -> int:
    """Idempotently insert and verify the required native DWPose smoother."""
    nodes = _nodes(workflow)
    links = _links(workflow)
    if nodes.get(170, {}).get("type") != "DWPreprocessor" or nodes.get(171, {}).get("type") != "ImageScale":
        raise PoseSmootherError("Pose smoother wiring requires native DWPose node 170 and ImageScale node 171")
    existing = [node for node in nodes.values() if node.get("type") == SMOOTHER_TYPE]
    if len(existing) > 1:
        raise PoseSmootherError(f"Cannot select among {len(existing)} {SMOOTHER_TYPE} nodes")
    if existing:
        smoother = existing[0]
        assert_pose_smoother(workflow)
        return smoother["id"]

    raw_pose_links = [link_id for link_id, link in links.items() if link[1:5] == [170, 0, 171, 0]]
    if len(raw_pose_links) != 1:
        raise PoseSmootherError(f"Expected exactly one raw 170 IMAGE → 171 link, found {len(raw_pose_links)}")
    _remove_link(workflow, raw_pose_links[0], nodes)
    node_id = max(nodes) + 1
    link_id = max([*links, 0]) + 1
    order = max((node.get("order", -1) for node in nodes.values() if isinstance(node.get("order"), int)), default=-1) + 1
    node_170_pos = nodes[170].get("pos") or [0, 0]
    smoother = _new_smoother(node_id, order, [node_170_pos[0] + 400, node_170_pos[1]])
    workflow["nodes"].append(smoother)
    nodes[node_id] = smoother
    workflow["links"].extend([
        [link_id, 170, 1, node_id, 0, "POSE_KEYPOINT"],
        [link_id + 1, node_id, 0, 171, 0, "IMAGE"],
    ])
    _set_output_links(nodes[170], 1, [link_id])
    _set_output_links(smoother, 0, [link_id + 1])
    _input(smoother, "pose_keypoints")["link"] = link_id
    _input(nodes[171], "image")["link"] = link_id + 1
    workflow["last_node_id"] = max(int(workflow.get("last_node_id", 0)), node_id)
    workflow["last_link_id"] = max(int(workflow.get("last_link_id", 0)), link_id + 1)
    return assert_pose_smoother(workflow)
