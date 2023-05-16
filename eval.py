#! /usr/bin/env python3
# pylint: disable=W0311
r"""Evaluation script for CPCD.

This script provides canonical evaluation metrics for the CPCD benchmark.

It expects model output to be in the folloing JSONL format:
    {"docid": "<dialog_id>:<turn_index>", "neighbor": [{"docid": <track_id>}, ...]}
    ...

Example invocation:
    python3 eval.py \
        --model_output model_output/bm25.test.jsonl \
        --gold_data data/cpcd_v1.dialogs.test.jsonl \
        --output scores/bm25.test.csv
"""

import collections
from collections.abc import Sequence
import csv
import dataclasses
import logging

from absl import app  # type: ignore
from absl import flags  # type: ignore
import tqdm

import data
import metrics


_MAX_TURNS = 10
_DEFAULT_K_VALUES = (1, 5, 10, 20, 100)


@dataclasses.dataclass
class _AveragedValue:
  """Convenient wrapper to maintain a rolling average value."""

  value: float = 0.0
  count: float = 0.0

  def update(self, value: float) -> float:
    """Update the running average."""
    self.count += 1
    self.value += (value - self.value) / self.count
    return self.value

  def __str__(self):
    return f"{self.value:0.4f} / {self.count}"


class _PerTurnMetricSummary:
  """Maintains the summary for a metric over turns."""

  def __init__(self, max_turns: int = _MAX_TURNS):
    self.micro_average = _AveragedValue()
    self.macro_average = _AveragedValue()
    self.per_turn_average = [_AveragedValue() for _ in range(max_turns)]

  def update(self, values: list[float]):
    """Update per-turn running averages."""
    self.macro_average.update(sum(values)/len(values))
    for turn_idx, value in enumerate(values):
      if turn_idx < len(self.per_turn_average):
        self.per_turn_average[turn_idx].update(value)
      self.micro_average.update(value)

  def __str__(self):
    per_turn = [str(turn_avg) for turn_avg in self.per_turn_average]
    return (
        f"Micro: {self.micro_average}\n"
        + f"Macro: {self.macro_average}\n"
        + f"Turns: {'; '.join(per_turn)}\n"
    )


def convert_to_cluster_ids(
    track_ids: list[data.TrackId],
    tracks: dict[data.TrackId, data.Track]) -> list[data.ClusterId]:
  """Convert and deduplicate track ids into cluster ids."""
  cluster_ids = []

  seen_clusters = set()
  for track_id in track_ids:
    cluster_id = tracks[track_id]["track_cluster_ids"]
    if cluster_id in seen_clusters:
      continue
    seen_clusters.add(cluster_id)
    cluster_ids.append(cluster_id)

  return cluster_ids


def get_gold_results(
    dialogs: dict[data.DialogId, data.Dialog],
    ) -> dict[data.DialogId, list[data.TrackId]]:
  """Extracts gold tracks from a dialog dataset.

  Args:
    dialogs: A mapping from dialog id to dialog.

  Returns:
    A mapping from dialog id to the list of positively rated tracks in that
    dialog.
  """
  return {
      dialog_id: dialog["goal_playlist"]
      for dialog_id, dialog in dialogs.items()
  }


def get_seed_tracks(
    dialogs: dict[data.DialogId, data.Dialog],
    num_previous_tracks: int = 3,
    ) -> dict[data.DialogId, list[list[data.TrackId]]]:
  """Extracts seed_tracks from a dialog dataset.

  Args:
    dialogs: A mapping from dialog id to dialog.
    num_previous_tracks: The number of previous tracks from each turn to use as
      seed tracks for the following turns.

  Returns:
    A mapping from dialog id to a list of seed tracks to consider for each turn
    of the example.
  """

  seed_tracks: dict[data.DialogId, list[list[data.TrackId]]] = {}
  for dialog_id, dialog in dialogs.items():
    # First turn has no previous turns and therefore has no seed tracks.
    seed_tracks[dialog_id] = [[]]

    # Iterate over the tracks for each turn.
    # We exclude the last turn as the tracks from the last turn are not used as
    # seed tracks for any turn.
    for turn in dialog["turns"][:-1]:
      # Add first 'num_previous_tracks' as the seed tracks for the next turn.
      seed_tracks[dialog_id].append(turn["liked_results"][:num_previous_tracks])
  return seed_tracks


def _filter_tracks(tracks: list[data.ClusterId],
                   seed_tracks: set[data.ClusterId]) -> list[data.ClusterId]:
  """Returns list of original tracks that do not occur in 'seed_tracks'."""
  return [track for track in tracks if track not in seed_tracks]


def compute_metrics_per_turn(
    preds: list[list[data.ClusterId]],
    gold: list[data.ClusterId],
    seed_tracks: list[list[data.ClusterId]],
    k_values: Sequence[int],
) -> dict[str, list[float]]:
  """Computes retrieval metrics per-turn for a single example.

  Args:
    preds: The list of preds for each turn.
    gold: The list of gold tracks (e.g. tracks in the goal playlist).
    seed_tracks: The list of seed tracks for each turn.
    k_values: The k values to use to compute metrics.
    maxs_turns: The maximum number of turns to compute metrics for.

  Returns:
    A mapping from metric name to a list of metric values for each turn.
  """
  ret = collections.defaultdict[str, list[float]](list)

  prev_seed_tracks = set()
  for turn_preds, turn_seed_tracks in zip(preds, seed_tracks):
    prev_seed_tracks.update(turn_seed_tracks)
    filtered_preds = _filter_tracks(turn_preds, prev_seed_tracks)
    filtered_gold = _filter_tracks(gold, prev_seed_tracks)
    # If there are no gold tracks remaining, skip the turn.
    if not filtered_gold:
      continue
    turn_metrics = metrics.compute_metrics(
        preds=filtered_preds, gold=filtered_gold, k_values=k_values)
    # Keep track of metric values for each turn.
    for metric_name, metric_vals in turn_metrics.items():
      ret[metric_name].append(metric_vals)
  return ret


def score_dataset(
    preds: dict[data.DialogId, list[list[data.ClusterId]]],
    gold: dict[data.DialogId, list[data.ClusterId]],
    seed_tracks: dict[data.DialogId, list[list[data.ClusterId]]],
    k_values: Sequence[int] = _DEFAULT_K_VALUES,
    max_turns: int = _MAX_TURNS,
) -> dict[str, list[float]]:
  """Computes metrics average over all examples.

  Args:
    preds: A mapping from dialog id to a list of predicted tracks for each turn.
    gold: A mapping from dialog id to the list of its gold tracks (e.g. tracks
        liked by the user).
    seed_tracks: A mapping from dialog id to the list of seed tracks for each turn.
    k_values: The k values to use to compute metrics.
    max_turns: The maximum number of turns considered.

  Returns:
    A mapping from retrieval metrics to a list of macro, micro and per-turn
    averaged scores.
  """
  agg_metrics = collections.defaultdict[str, _PerTurnMetricSummary](
    lambda: _PerTurnMetricSummary(max_turns))

  for dialog_id, dialog_preds in tqdm.tqdm(preds.items(),
                                           total=len(preds), desc="Scoring examples"):
    dialog_metrics = compute_metrics_per_turn(
        dialog_preds,
        gold[dialog_id],
        seed_tracks[dialog_id],
        k_values)

    # Aggregate each metric across examples.
    for metric_name, metric_vals in dialog_metrics.items():
      agg_metrics[metric_name].update(metric_vals)

  # Reformating the averaged metrics into a list so we can save to CSV.
  reported_metrics = {}
  for metric_name, metric_summ in agg_metrics.items():
    reported_metrics[metric_name] = [
        metric_summ.macro_average.value,
        metric_summ.micro_average.value,
        *[turn_avg.value for turn_avg in metric_summ.per_turn_average],
    ]
    # NOTE: This is being intentionally multiply-written out of convenience.
    reported_metrics["counts"] = [
        metric_summ.macro_average.count,
        metric_summ.micro_average.count,
        *[turn_avg.count for turn_avg in metric_summ.per_turn_average],
    ]
  return reported_metrics


def write_output(
    agg_metrics: dict[str, list[float]], fname: str
) -> None:
  """Writes retrieval evaluation metrics to a CSV file."""
  # -2 because the first two columns are "macro" and "micro".
  max_turns = len(next(iter(agg_metrics.values()))) - 2

  with open(fname, "w", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["metric", "macro", "micro", *[f"Turn {i}" for i in range(max_turns)]])
    for metric_name, values in agg_metrics.items():
      writer.writerow([metric_name] + [f"{v:0.4f}" for v in values])


_INPUT_PRED = flags.DEFINE_string(
    name="model_output",
    default=None,
    help=(
        "Path to JSONL file containing model predictions.",
    ),
    required=True,
)
_INPUT_GOLD = flags.DEFINE_string(
    name="gold_data",
    default="data/cpcd_v1.dialogs.test.jsonl",
    help="Path to gold data.",
    )
_INPUT_TRACKS = flags.DEFINE_string(
    name="tracks",
    default="data/cpcd_v1.tracks.jsonl",
    help="Path to gold data.",
    )
_NUM_PREV_TRACKS = flags.DEFINE_integer(
    name="num_prev_tracks",
    default=3,
    help="Number of tracks previous tracks to include as seed tracks.")
_OUTPUT = flags.DEFINE_string(
    name="output",
    default="eval_results.csv",
    help="Where to save the eval results.",
)


def main(unused_argv):
  logging.info("Loading predictions from %s", _INPUT_PRED.value)
  model_results = data.load_results(_INPUT_PRED.value)
  logging.info("Loading gold labels from %s", _INPUT_GOLD.value)
  gold_dialogs = data.load_cpcd_dialogs(_INPUT_GOLD.value)
  logging.info("Loading tracks from %s", _INPUT_TRACKS.value)
  tracks = data.load_cpcd_tracks(_INPUT_TRACKS.value)

  gold_results = get_gold_results(gold_dialogs)
  seed_tracks = get_seed_tracks(gold_dialogs, _NUM_PREV_TRACKS.value)

  logging.info("Converting to cluster ids")
  model_results_ = {dialog_id:
                    [convert_to_cluster_ids(track_ids, tracks) for track_ids in results]
                    for dialog_id, results in model_results.items()}
  gold_results_ = {dialog_id: convert_to_cluster_ids(results, tracks)
                   for dialog_id, results in gold_results.items()}
  seed_tracks_ = {dialog_id:
                  [convert_to_cluster_ids(track_ids, tracks) for track_ids in results]
                  for dialog_id, results in seed_tracks.items()}

  logging.info("Computing metrics")
  agg_metrics = score_dataset(
      model_results_, gold_results_, seed_tracks_)


  logging.info("Writing results to %s", _OUTPUT.value)
  write_output(agg_metrics, _OUTPUT.value)


if __name__ == "__main__":
  app.run(main)
