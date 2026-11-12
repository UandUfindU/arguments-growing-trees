"""Optional System 1 training entry point. Default action validates, never trains."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .system1 import model_text


def validate_records(records):
    if not records:
        raise ValueError("No training records")
    count = 0
    for item in records:
        if item["supervision"] != "observed_execution_only":
            raise ValueError("Unrecognized label source")
        if not set(item["labels"]).issubset(item["target_ids"]):
            raise ValueError("Labels outside affected path")
        for target in item["target_ids"]:
            if item["tree"]["nodes"][target]["result"] != {"masked": True}:
                raise ValueError("Affected path must be masked jointly")
        if "events" in item["tree"]:
            raise ValueError("Execution logs cannot enter model input")
        count += len(item["labels"])
    if count == 0:
        raise ValueError("No observed labels")
    return {"examples": len(records), "observed_targets": count,
            "training_executed": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--execute-training", action="store_true")
    parser.add_argument("--base-model", help="Local HF model directory, no automatic download")
    parser.add_argument("--output", type=Path, default=Path("checkpoints/system1"))
    parser.add_argument("--epochs", type=int, default=1)
    args = parser.parse_args()
    records = [json.loads(line) for line in args.dataset.read_text(encoding="utf8").splitlines() if line.strip()]
    report = validate_records(records)
    print(json.dumps(report))
    if not args.execute_training:
        return
    if not args.base_model or not Path(args.base_model).is_dir():
        parser.error("Explicit local --base-model directory required")
    if args.epochs < 1:
        parser.error("epochs must be positive")
    import torch
    from transformers import AutoModel, AutoTokenizer
    torch.manual_seed(42)
    tokenizer = AutoTokenizer.from_pretrained(args.base_model, local_files_only=True)
    encoder = AutoModel.from_pretrained(args.base_model, local_files_only=True)
    head = torch.nn.Linear(encoder.config.hidden_size, 1)
    optimizer = torch.optim.AdamW(list(encoder.parameters())+list(head.parameters()), lr=2e-5)
    encoder.train()
    head.train()
    # Each observed path contributes one mean loss. All targets share an encoder
    # and full-tree context. Unsupported internal/root nodes have no label.
    for _ in range(args.epochs):
        for item in records:
            losses = []
            optimizer.zero_grad()
            for node_id, target in item["labels"].items():
                text = model_text(item) + "\nPredict log_e for node: " + node_id
                tokens = tokenizer(text, return_tensors="pt", truncation=False)
                limit = min(getattr(encoder.config, "max_position_embeddings", 32768), 32768)
                if tokens["input_ids"].shape[1] > limit:
                    raise ValueError("Full tree exceeds context; silent truncation is forbidden")
                hidden = encoder(**tokens).last_hidden_state
                mask = tokens["attention_mask"].unsqueeze(-1)
                pooled = (hidden*mask).sum(1)/mask.sum(1)
                prediction = head(pooled).squeeze()
                losses.append((prediction - float(target))**2)
            if losses:
                torch.stack(losses).mean().backward()
                optimizer.step()
    args.output.mkdir(parents=True, exist_ok=True)
    encoder.save_pretrained(args.output / "encoder")
    tokenizer.save_pretrained(args.output / "encoder")
    torch.save(head.state_dict(), args.output / "head.pt")
    print(json.dumps({"training_executed": True, "output": str(args.output)}))


if __name__ == "__main__":
    main()
