#!/usr/bin/env python3
"""Validate speaker numbering and dialogue tags in a MiniMax H3 prompt."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


DIALOGUE_RE = re.compile(r"<d>(.*?)</d>", re.DOTALL)
SPEAKER_RE = re.compile(r"\((S\d+(?:\s*,\s*S\d+)*)\)")
LANGUAGE_RE = re.compile(r"^\[[^\]\r\n]+\]\s+.+[.!?]$", re.DOTALL)


def section(text: str, start: str, end: str | None = None) -> str:
    start_pos = text.find(start)
    if start_pos < 0:
        return ""
    start_pos += len(start)
    if end is None:
        return text[start_pos:]
    end_pos = text.find(end, start_pos)
    return text[start_pos:] if end_pos < 0 else text[start_pos:end_pos]


def lint_dialogue(text: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    events: list[str] = []
    body = section(text, "detailed_description:", "overall_soundscape:") or text
    retention = section(text, "retention_analysis:", "detailed_description:")

    if SPEAKER_RE.findall(retention):
        errors.append("speaker IDs must not appear in retention_analysis")

    seen: set[int] = set()
    next_new_id = 1
    previous_dialogue_end = 0

    for event_index, match in enumerate(DIALOGUE_RE.finditer(body), start=1):
        spoken = " ".join(match.group(1).split())
        if not LANGUAGE_RE.fullmatch(spoken):
            errors.append(
                f"dialogue event {event_index} must contain [Language], exact text, "
                "and final punctuation"
            )

        context = body[previous_dialogue_end : match.start()]
        speaker_matches = list(SPEAKER_RE.finditer(context))
        if not speaker_matches:
            errors.append(f"dialogue event {event_index} has no speaker ID before <d>")
            previous_dialogue_end = match.end()
            continue

        raw_ids = speaker_matches[-1].group(1)
        ids = [int(value[1:]) for value in re.findall(r"S\d+", raw_ids)]
        events.append(f"event {event_index}: ({raw_ids}) {spoken}")

        for speaker_id in ids:
            if speaker_id in seen:
                continue
            if speaker_id != next_new_id:
                errors.append(
                    f"dialogue event {event_index} introduces S{speaker_id}, "
                    f"but the next new speaker must be S{next_new_id}"
                )
            seen.add(speaker_id)
            while next_new_id in seen:
                next_new_id += 1

        previous_dialogue_end = match.end()

    if events and not re.match(r"event 1: \(S1(?:,|\))", events[0]):
        errors.append("the first actual vocal event must be assigned to S1")

    return errors, events


def run_self_test() -> int:
    valid = """detailed_description:
[Shot 1] The off-screen man (S1) says, <d>[English] Hey.</d>
The woman (S2) replies, <d>[English] Hello.</d>
overall_soundscape:
Room tone.
"""
    invalid = """detailed_description:
[Shot 1] The off-screen man (S2) says, <d>[English] Hey.</d>
The woman (S1) replies, <d>[English] Hello.</d>
overall_soundscape:
Room tone.
"""
    valid_errors, _ = lint_dialogue(valid)
    invalid_errors, _ = lint_dialogue(invalid)
    if valid_errors or not any("first actual vocal event" in item for item in invalid_errors):
        print("SELF-TEST FAILED", file=sys.stderr)
        return 1
    print("SELF-TEST OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check MiniMax H3 speaker order and <d> dialogue formatting."
    )
    parser.add_argument("prompt", nargs="?", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return run_self_test()
    if args.prompt is None:
        parser.error("prompt path is required unless --self-test is used")

    text = args.prompt.read_text(encoding="utf-8-sig")
    errors, events = lint_dialogue(text)
    for event in events:
        print(event)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("DIALOGUE CHECK OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
