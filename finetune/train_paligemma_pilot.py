#!/usr/bin/env python3
"""
Fine-tune PaliGemma 2 for pilot state classification (4 classes: ALERT / FATIGUED / DROWSY / CRITICAL).
Dataset: NTHU Drowsy Driver Detection + UTA Real-Life Drowsiness (relabel to 4 classes).
Method: LoRA with Unsloth, 4-bit quantization.
Run: ~45 min on RTX 3090+. Output: models/paligemma-pilot-lora/
"""
from __future__ import annotations

import os
import json
from pathlib import Path

# Unsloth + PaliGemma — install: pip install unsloth paligemma
# try:
#     from unsloth import FastLanguageModel
#     from unsloth import is_bfloat16_supported
# except ImportError:
#     print("Install: pip install unsloth")
#     raise

DATASET_DIR = Path(__file__).parent / "datasets" / "pilot_states"
OUTPUT_DIR = Path(__file__).parent.parent / "models" / "paligemma-pilot-lora"
CLASSES = ["ALERT", "FATIGUED", "DROWSY", "CRITICAL"]


def relabel_nthu_to_four_class(label: str) -> str:
    """Map NTHU/UTA labels to our 4 classes."""
    m = {
        "alert": "ALERT",
        "normal": "ALERT",
        "fatigued": "FATIGUED",
        "drowsy": "DROWSY",
        "sleepy": "DROWSY",
        "critical": "CRITICAL",
        "microsleep": "CRITICAL",
    }
    return m.get(label.lower(), "ALERT")


def main() -> None:
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    # Placeholder: actual training would load NTHU/UTA, relabel, then:
    # model, tokenizer = FastLanguageModel.from_pretrained("google/paligemma-2-...", load_in_4bit=True, ...)
    # model = FastLanguageModel.get_peft_model(model, r=16, target_modules=[...])
    # trainer = SFTTrainer(model=model, train_dataset=dataset, ...)
    # trainer.train(); model.save_pretrained(OUTPUT_DIR)
    meta = {
        "classes": CLASSES,
        "dataset": "NTHU + UTA relabeled",
        "method": "LoRA 4-bit Unsloth",
    }
    (OUTPUT_DIR / "config.json").write_text(json.dumps(meta, indent=2))
    print("PaliGemma pilot LoRA stub written to", OUTPUT_DIR)
    print("To run full fine-tune: install unsloth, download NTHU/UTA, then implement train loop.")


if __name__ == "__main__":
    main()
