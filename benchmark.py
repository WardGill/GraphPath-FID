"""Validate, regenerate, or score the released GraphPath-FID benchmark."""
import argparse
import hashlib
import json
from pathlib import Path

from evaluation.scoring import parse_json_object
from evaluation.protocol import TASKS, RETENTION_TASKS, build_trial, score_trial
from generation.generator import build_dataset
from generation.validate import validate_dataset

DATA = Path(__file__).resolve().parent / "data" / "task_families_v4.json"


def content_hash(dataset):
    payload = {key: value for key, value in dataset.items() if key != "content_sha256"}
    return hashlib.sha256(json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    actions.add_parser("validate")
    regenerate = actions.add_parser("regenerate")
    regenerate.add_argument("eedi_zip", type=Path)
    regenerate.add_argument("--output", type=Path)
    score = actions.add_parser("score")
    score.add_argument("family")
    score.add_argument("task", choices=TASKS + RETENTION_TASKS)
    score.add_argument("response", type=Path)
    args = parser.parse_args()
    dataset = json.loads(DATA.read_text(encoding="utf8"))
    if content_hash(dataset) != dataset["content_sha256"]:
        parser.error("Released dataset checksum mismatch")

    if args.action == "validate":
        result = validate_dataset(dataset)
        print(json.dumps(result, indent=2))
        return int(result["status"] != "PASS")
    if args.action == "regenerate":
        rebuilt = build_dataset(args.eedi_zip, seed=dataset["seed"])
        for family in rebuilt["families"]:
            for key in ("official_name", "first_sorted_example_question_ids"):
                family["source"].pop(key)
        rebuilt["content_sha256"] = content_hash(rebuilt)
        if rebuilt != dataset:
            parser.error("Regeneration differs from the released snapshot")
        if args.output:
            args.output.write_text(json.dumps(rebuilt, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
        print(f"Regeneration matched {len(rebuilt['families'])} task families.")
        return 0

    family = next((f for f in dataset["families"] if f["family_id"] == args.family), None)
    if family is None:
        parser.error(f"Unknown family: {args.family}")
    trial = build_trial(family, args.task, "defect", "pre")
    response = parse_json_object(args.response.read_text(encoding="utf8"))
    print(json.dumps(score_trial(response, trial), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
