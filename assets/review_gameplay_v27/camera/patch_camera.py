"""Candidate-only bridge patch; call patch(source) from the integration script."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def patch(source: str) -> str:
    marker = "-- review-v27: prevent extreme upward orbit"
    if marker in source:
        raise ValueError("camera guard already present")
    required = ["function LateUpdate()", "function GetExplorationState()", "UI.dizzy={}", "DR.phase1={"]
    if any(x not in source for x in required):
        raise ValueError("unexpected bridge, camera scope anchors missing")
    return source + "\n" + (ROOT / "camera-guard.lua").read_text()


def remove_cloud_controller(source: str) -> str:
    start = source.index("---- 白天的云：绕地图缓慢飘动")
    end = source.index("---- 开船：", start)
    old = source[start:end]
    if 'GameObject.Find("cl_" .. i)' not in old:
        raise ValueError("unexpected cloud controller")
    replacement = "---- v27：云片场景节点已移除；保留天空盒、昼夜和漩涡。\nlocal function updateClouds()end\n\n"
    return source[:start] + replacement + source[end:]
