#! /usr/bin/env python3
"""Data schemas and loading utilities."""

import collections
import json
from typing import cast, NewType, TypedDict

DialogId = NewType("DialogId", str)
TrackId = NewType("TrackId", str)
ClusterId = NewType("ClusterId", str)

class Track(TypedDict):
    track_ids: TrackId
    track_titles: str
    track_artists: list[str]
    track_release_titles: str
    track_canonical_ids: TrackId
    track_cluster_ids: ClusterId


class Turn(TypedDict):
    user_query: str
    system_response: str
    search_queries: list[str]
    search_results: list[list[TrackId]]
    liked_results: list[TrackId]
    disliked_results: list[TrackId]


class Dialog(TypedDict):
    id: DialogId
    turns: list[Turn]
    tracks: dict[TrackId, Track]
    goal_playlist: list[TrackId]


class Neighbor(TypedDict, total=False):
    docid: TrackId
    distance: float


class Result(TypedDict, total=False):
    docid: str
    neighbor: list[Neighbor]


def load_jsonl(fname: str) -> list[dict]:
    """Loads a file in JSONL format.

    Args:
        fname: Filename to load.
    Returns:
        List with the object loaded for each line in `fname`.
    """
    with open(fname, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def load_cpcd_dialogs(fname: str) -> dict[DialogId, Dialog]:
    results = cast(list[Dialog], load_jsonl(fname))
    return {x["id"]: x for x in results}

def load_cpcd_tracks(fname: str) -> dict[TrackId, Track]:
    results = cast(list[Track], load_jsonl(fname))
    return {x["track_ids"]: x for x in results}

def load_results(fname: str) -> dict[DialogId, list[list[TrackId]]]:
    results = cast(list[Result], load_jsonl(fname))

    per_turn_results = collections.defaultdict[DialogId, dict[int, list[TrackId]]](dict)
    for result in results:
        dialog_id, turn_idx = result["docid"].split(":", 1)
        per_turn_results[DialogId(dialog_id)][int(turn_idx)] = [
                n["docid"] for n in result["neighbor"]]

    return {
            dialog_id: [per_turn_result.get(i, []) for i in range(max(per_turn_result)+1)]
            for dialog_id, per_turn_result in per_turn_results.items()
            }
