#! /bin/sh
# Run evaluation on all model output.

for output in model_outputs/*.test.jsonl; do
  python3 eval.py \
    --model_output $output \
    --gold_data "data/cpcd_v1.dialogs.test.jsonl" \
    --output "scores/$(basename $output .jsonl).csv";
done

for output in model_outputs/*.dev.jsonl; do
  python3 eval.py \
    --model_output "$output" \
    --gold_data "data/cpcd_v1.dialogs.dev.jsonl" \
    --output "scores/$(basename $output .jsonl).csv";
done
