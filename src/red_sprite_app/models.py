from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path


REVIEW_STATES = {"confirmed", "suspected", "false_positive", "unreviewed"}


@dataclass
class Candidate:
    candidate_id: str
    video: str
    event_rank: int
    frame_index: int
    timestamp_seconds: float
    score: float
    red_pixels: int
    red_strength: float
    clip_start_seconds: float
    clip_end_seconds: float
    image_path: str
    clip_path: str
    image_relpath: str
    clip_relpath: str
    state: str = "unreviewed"


@dataclass
class CandidateReview:
    candidate_id: str
    state: str


def default_output_dir(source: Path) -> Path:
    source = source.expanduser()
    if source.is_dir():
        return source / "红色精灵筛选结果"
    return source.parent / f"{source.stem}_红色精灵筛选结果"


def _float(row: dict[str, str], key: str) -> float:
    return float(row.get(key, "0") or "0")


def _int(row: dict[str, str], key: str) -> int:
    return int(float(row.get(key, "0") or "0"))


def _relpath(path_text: str, root: Path) -> str:
    if not path_text:
        return ""
    path = Path(path_text)
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def candidate_id(video: str, event_rank: int, timestamp_seconds: float) -> str:
    return f"{Path(video).name}:{event_rank}:{timestamp_seconds:.3f}"


def load_review_state(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    reviews = payload.get("reviews", [])
    return {
        item["candidate_id"]: item["state"]
        for item in reviews
        if item.get("state") in REVIEW_STATES and item.get("candidate_id")
    }


def load_candidates_csv(csv_path: Path, review_state_path: Path | None = None) -> list[Candidate]:
    csv_path = csv_path.expanduser().resolve()
    root = csv_path.parent
    reviews = load_review_state(review_state_path or root / "review_state.json")
    if not csv_path.exists():
        return []

    candidates: list[Candidate] = []
    with csv_path.open("r", newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            event_rank = _int(row, "event_rank")
            timestamp = _float(row, "timestamp_seconds")
            cid = candidate_id(row.get("video", ""), event_rank, timestamp)
            candidates.append(
                Candidate(
                    candidate_id=cid,
                    video=row.get("video", ""),
                    event_rank=event_rank,
                    frame_index=_int(row, "frame_index"),
                    timestamp_seconds=timestamp,
                    score=_float(row, "score"),
                    red_pixels=_int(row, "red_pixels"),
                    red_strength=_float(row, "red_strength"),
                    clip_start_seconds=_float(row, "clip_start_seconds"),
                    clip_end_seconds=_float(row, "clip_end_seconds"),
                    image_path=row.get("image_path", ""),
                    clip_path=row.get("clip_path", ""),
                    image_relpath=_relpath(row.get("image_path", ""), root),
                    clip_relpath=_relpath(row.get("clip_path", ""), root),
                    state=reviews.get(cid, "unreviewed"),
                )
            )
    return candidates


def write_review_state(out_dir: Path, reviews: list[CandidateReview]) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "review_state.json"
    payload = {"reviews": [asdict(review) for review in reviews if review.state in REVIEW_STATES]}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def export_confirmed_csv(out_dir: Path, reviews: list[CandidateReview]) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "confirmed_candidates.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["candidate_id", "state"])
        writer.writeheader()
        for review in reviews:
            if review.state == "confirmed":
                writer.writerow({"candidate_id": review.candidate_id, "state": review.state})
    return path
