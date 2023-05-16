#! /usr/bin/env python3
# pylint: disable=W0311
"""Common retrieval evaluation metrics.

For more details regarding these metrics, see:
https://en.wikipedia.org/wiki/Evaluation_measures_(information_retrieval)#Offline_metrics
"""

from collections.abc import Collection, Sequence
from typing import Any


def get_hit(gold: Collection[str], preds: Sequence[str], k: int) -> int:
  """Returns 1 if any of the top-k predictions are in the gold set, else 0."""
  preds = preds[:k]
  return 1 if len(set(gold).intersection(preds)) > 0 else 0


def get_reciprocal_rank(gold: Collection[str], preds: Sequence[str], k: int) -> float:
  """Returns the reciprocal rank at k; 0 if no relevants items are found."""
  preds = preds[:k]
  for i, pred in enumerate(preds, start=1):
    if pred in gold:
      return 1 / i
  return 0


def get_precision(gold: Collection[str], preds: Sequence[str], k: int) -> float:
  """Returns the precision at k."""
  preds = preds[:k]
  num_hit = len(set(gold).intersection(preds))
  return num_hit / len(preds)


def get_recall(gold: Collection[str], preds: Sequence[str], k: int) -> float:
  """Returns the recall at k."""
  preds = preds[:k]
  num_hit = len(set(gold).intersection(preds))
  return num_hit / len(gold)


def get_average_precision(gold: Collection[str], preds: Sequence[str], k: int) -> float:
  """Returns the average precision at k."""
  preds = preds[:k]
  num_hit = 0
  total_precision = 0.
  for i, pred in enumerate(preds, start=1):
    if pred in gold:
      num_hit += 1
      total_precision += num_hit / i
  return total_precision / min(len(gold), len(preds))


def _has_duplicates(values: Collection[Any]):
  """Returns True if the list has duplicates, else False."""
  return len(values) > len(set(values))


_STANDARD_METRIC_MAP = {
        "hit": get_hit,
        "map": get_average_precision,
        "recall": get_recall,
        "precision": get_precision,
        "mrr": get_reciprocal_rank,
        }
STANDARD_METRICS = sorted(_STANDARD_METRIC_MAP.keys())


def compute_metrics(preds: Sequence[str],
                    gold: Collection[str],
                    k_values: Sequence[int],
                    metrics: Sequence[str]=STANDARD_METRICS
                    ) -> dict[str, float]:
  """Computes retrieval metrics for 'preds' and 'golds' for 'k_values'.

  Args:
    preds: The list of retrieved items for the example.
    gold: The list of gold (i.e. relevant) items for the example.
    k_values: The list of k values to compute metrics for (e.g. recall@k).
    metrics: The list of metrics to compute.g. recall@k).

  Returns:
    A dictionary of retrieval metrics.
  """
  if _has_duplicates(preds):
    raise ValueError("Predictions should be unique. Duplicates detected.")
  if _has_duplicates(gold):
    raise ValueError("Gold item list should be unique. Duplicates detected.")
  if any(metric not in _STANDARD_METRIC_MAP for metric in metrics):
    raise ValueError("Couldn't find implementation for some metrics.")
  if max(k_values) > len(preds):
    raise ValueError(
        f"k is larger than the number of retrieved preds, {max(k_values)} > {len(preds)}."
    )

  metric_vals = {}
  for metric in metrics:
      metric_fn = _STANDARD_METRIC_MAP[metric]
      for k in k_values:
        metric_vals[f"{metric}@{k}"] = metric_fn(gold=gold, preds=preds, k=k)
  return metric_vals
