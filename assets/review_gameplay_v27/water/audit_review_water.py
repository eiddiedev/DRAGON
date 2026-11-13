"""Read-only audit of an actual review ZIP against the saved water node snapshot.

Does not create/delete triggers, rewrite water fields or operate an editor.
"""
import argparse
import collections
import hashlib
import json
import zlib
from pathlib import Path
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
DEFAULT_ZIP = Path("/Users/bytedance/Downloads/world_dev_unity_143175468-dsst-PROD.zip")


def audit(archive: Path):
    saved = json.loads((HERE / "saved-nodes.json").read_text())
    with ZipFile(archive) as package:
        scene_bytes = package.read("SerializePcgData.json")
        scene = json.loads(scene_bytes)
        nodes = {n["id"]: n for n in scene["nodeTransformDatas"]}
        refs = {r["id"]: r for r in scene["resourceRefs"]}
        children = collections.defaultdict(list)
        for node in nodes.values():
            children[node["basic"].get("parentId", 0)].append(node)
        water_nodes = []
        for source in saved:
            node = nodes.get(source["id"])
            result = {"id": source["id"], "name": source["basic"]["nodeName"], "in_archive": node is not None}
            if node:
                result["same_as_saved"] = {k: node.get(k) == source.get(k) for k in ("basic", "landscape", "physics")}
                landscape = node["landscape"]
                envelope = landscape.get("waterEditorData")
                if envelope:
                    result["river_parameters"] = {k: envelope.get(k) for k in (
                        "version", "kind", "waterNodeId", "terrainNodeId", "editorMeshSnapshotVersion",
                        "editorMeshSnapshotRefId", "editorMeshSnapshotChecksum", "depth", "riverWidth", "isReverse")}
                    result["control_points"] = len(envelope.get("controlPoints") or [])
                    result["terrain_reference_exists"] = envelope["terrainNodeId"] in nodes
                    reference = refs.get(envelope["editorMeshSnapshotRefId"])
                    result["snapshot_reference"] = reference
                    if reference and reference["pathOrUrl"] in package.namelist():
                        snapshot = package.read(reference["pathOrUrl"])
                        crc = zlib.crc32(snapshot)
                        result["snapshot_integrity"] = {
                            "bytes": len(snapshot), "sha256": hashlib.sha256(snapshot).hexdigest(),
                            "crc32": crc, "matches_envelope": crc == envelope["editorMeshSnapshotChecksum"],
                            "matches_zip_crc": crc == package.getinfo(reference["pathOrUrl"]).CRC,
                        }
                    result["water_body_authoring"] = landscape.get("waterBodyAuthoringData")
                    result["legacy_mesh_params"] = json.loads(landscape["riverDisplayData"]["meshParams"])
            water_nodes.append(result)
        roots = []
        for n in nodes.values():
            if n["basic"]["nodeName"] != "__DouyinWaterArea2Triggers":
                continue
            group = children[n["id"]]
            roots.append({
                "id": n["id"], "parent_id": n["basic"]["parentId"], "children": len(group),
                "children_with_physics_data": sum(bool(c.get("physics", {}).get("physicsColliderData")) for c in group),
                "children_with_trigger_data": sum(bool(c.get("physics", {}).get("triggerData")) for c in group),
                "children_with_other_components": sum(bool(set(c) - {"id", "basic", "physics"}) for c in group),
            })
        return {
            "review_zip": str(archive), "zip_bytes": archive.stat().st_size,
            "zip_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
            "scene_entry_timestamp": package.getinfo("SerializePcgData.json").date_time,
            "scene_sha256": hashlib.sha256(scene_bytes).hexdigest(),
            "is_open_streaming_load": scene["isOpenStreamingLoad"],
            "water_nodes": water_nodes, "serialized_trigger_groups": roots,
            "riverExportRuntime_literal_in_json": b"riverExportRuntime" in scene_bytes,
            "limitations": [
                "This dsst ZIP is the earlier supplied review package, not evidence of the user's latest failing v26 package.",
                "Serialized trigger node shells do not prove native water trigger/proxy registration in the consumer runtime.",
                "No current consumer runtime log or latest review ZIP is available in these inputs.",
            ],
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", nargs="?", type=Path, default=DEFAULT_ZIP)
    args = parser.parse_args()
    result = audit(args.archive)
    (HERE / "review-zip-audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"water_nodes": [(n["name"], n.get("same_as_saved")) for n in result["water_nodes"]],
                      "groups": result["serialized_trigger_groups"], "limitations": result["limitations"]}, ensure_ascii=False, indent=2))
