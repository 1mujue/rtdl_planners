#!/usr/bin/env python3
import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Optional


# safe guard
# NOTE: there might be some INVALID value in records, therefore, we need to handle it 
# to increase robustness.
def safe_float(x: Any) -> Optional[float]:
    if x is None or x == "":
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None

def safe_int(x: Any) -> Optional[int]:
    if x is None or x == "":
        return None
    try:
        return int(x)
    except (TypeError, ValueError):
        try:
            return int(float(x))
        except (TypeError, ValueError):
            return None

def safe_bool(x: Any) -> Optional[bool]:
    if x is None or x == "":
        return None

    if isinstance(x, bool):
        return x

    if isinstance(x, (int, float)):
        return bool(x)

    if isinstance(x, str):
        s = x.strip().lower()
        if s in {"true", "1", "yes", "y"}:
            return True
        if s in {"false", "0", "no", "n"}:
            return False

    return None


def safe_unit_float(x: Any) -> Optional[float]:
    """
    Convert manual score to a float in [0, 1].
    """
    value = safe_float(x)
    if value is None:
        return None

    if 0.0 <= value <= 1.0:
        return value

    return None


# statistic helpers
def mean(values: list[float]) -> Optional[float]:
    if not values:
        return None
    return sum(values) / len(values)


def variance(values: list[float]) -> Optional[float]:
    # note the formula of variance.
    if len(values) <= 1:
        return None

    m = mean(values)
    assert m is not None

    return sum((x - m) ** 2 for x in values) / (len(values) - 1)


def std(values: list[float]) -> Optional[float]:
    v = variance(values)
    if v is None:
        return None
    return math.sqrt(v)


def percent(x: Optional[float]) -> Optional[float]:
    if x is None:
        return None
    return x * 100.0


def fmt_float(x: Any, ndigits: int = 4) -> Any:
    if x is None:
        return ""
    if isinstance(x, float):
        return round(x, ndigits)
    return x


# benchmark-specific helpers
def starts_with_compiler_failed(record: dict[str, Any]) -> bool:
    """
    if syntax/semantic error occurs, error_message starts with "Compiler failed".
    Also check rtdl_error for compatibility with older records.
    """
    for key in ["error_message", "rtdl_error"]:
        value = record.get(key)
        if isinstance(value, str) and value.strip().startswith("Compiler failed"):
            return True
    return False


def infer_rtdl_valid(record: dict[str, Any]) -> bool:
    """
    Prefer explicit rtdl_valid.
    If missing, infer from compiler error / status.
    """
    explicit = safe_bool(record.get("rtdl_valid"))
    if explicit is not None:
        return explicit

    if starts_with_compiler_failed(record):
        return False

    if record.get("status") == "rtdl_invalid":
        return False

    # Fallback: if RTDL exists and no compiler error is recorded, treat it as valid.
    return bool(record.get("rtdl"))


def compute_logic_score(record: dict[str, Any]) -> Optional[float]:
    """
        score = 0.7 * manual_logic_correct
              + 0.3 * manual_logic_completeness

    Both fields are real numbers in [0, 1].
    Return None if either field is missing or invalid.
    """
    logic_correct = safe_unit_float(record.get("manual_logic_correct"))
    logic_completeness = safe_unit_float(record.get("manual_logic_completeness"))

    if logic_correct is None or logic_completeness is None:
        return None

    return 0.7 * logic_correct + 0.3 * logic_completeness


# file loading
def load_records_from_record_json(root: Path) -> list[dict[str, Any]]:
    records = []

    for path in sorted(root.rglob("record.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            record["_source_file"] = str(path)
            records.append(record)
        except Exception as e:
            print(f"[WARN] Failed to load {path}: {e}")

    return records


def load_records(root: Path) -> list[dict[str, Any]]:
    """
    Prefer round_xxx/record.json.
    If not found, fallback to summary.jsonl.
    """
    records = load_records_from_record_json(root)
    if records:
        return records
    return None


# grouping and summary

def group_records(
    records: list[dict[str, Any]],
    keys: tuple[str, ...],
) -> dict[tuple[Any, ...], list[dict[str, Any]]]:
    groups = defaultdict(list)

    for record in records:
        group_key = tuple(record.get(k) for k in keys)
        groups[group_key].append(record)

    return dict(groups)


def summarize_group(
    records: list[dict[str, Any]],
    group_info: dict[str, Any],
) -> dict[str, Any]:
    total = len(records)

    if total == 0:
        return {
            **group_info,
            "total": 0,
        }

    # ===== syntax / semantic correctness =====
    valid_flags = [infer_rtdl_valid(r) for r in records]
    valid_count = sum(1 for x in valid_flags if x)

    compiler_failed_count = sum(
        1 for r in records
        if starts_with_compiler_failed(r)
    )

    syntax_semantic_rate = valid_count / total

    # ===== logic score =====
    logic_correct_values = [
        safe_unit_float(r.get("manual_logic_correct"))
        for r in records
    ]

    logic_completeness_values = [
        safe_unit_float(r.get("manual_logic_completeness"))
        for r in records
    ]

    logic_scores = [
        compute_logic_score(r)
        for r in records
    ]

    logic_reviewed_count = sum(
        1 for score in logic_scores
        if score is not None
    )

    logic_correct_reviewed_values = [
        x for x in logic_correct_values
        if x is not None
    ]

    logic_completeness_reviewed_values = [
        x for x in logic_completeness_values
        if x is not None
    ]

    logic_score_reviewed_values = [
        x for x in logic_scores
        if x is not None
    ]

    logic_correct_sum = sum(logic_correct_reviewed_values)
    logic_completeness_sum = sum(logic_completeness_reviewed_values)
    logic_score_sum = sum(logic_score_reviewed_values)

    # all口径：未标注样本按0计入。
    logic_correct_mean_all = logic_correct_sum / total
    logic_completeness_mean_all = logic_completeness_sum / total
    logic_score_mean_all = logic_score_sum / total

    # reviewed口径：只统计已人工标注完整的样本。
    logic_correct_mean_reviewed = mean(logic_correct_reviewed_values)
    logic_completeness_mean_reviewed = mean(logic_completeness_reviewed_values)
    logic_score_mean_reviewed = mean(logic_score_reviewed_values)

    logic_score_var_reviewed = variance(logic_score_reviewed_values)
    logic_score_std_reviewed = std(logic_score_reviewed_values)

    # ===== execution success =====
    execution_values = [
        safe_bool(r.get("execution_success"))
        for r in records
    ]

    executed_count = sum(
        1 for r in records
        if safe_float(r.get("execution_time_sec")) is not None
    )

    execution_success_count = sum(
        1 for x in execution_values
        if x is True
    )

    execution_success_rate_all = execution_success_count / total

    execution_success_rate_executed = (
        execution_success_count / executed_count
        if executed_count > 0 else None
    )

    # ===== LLM planning time =====
    llm_times = [
        x for x in (
            safe_float(r.get("llm_time_sec"))
            for r in records
        )
        if x is not None
    ]

    # ===== RTDL execution time =====
    execution_times = [
        x for x in (
            safe_float(r.get("execution_time_sec"))
            for r in records
        )
        if x is not None
    ]

    # ===== collision count =====
    collision_values = [
        safe_int(r.get("manual_collision_observed"))
        for r in records
    ]

    collision_reviewed = [
        float(x) for x in collision_values
        if x is not None
    ]

    collision_reviewed_count = len(collision_reviewed)
    collision_total = sum(collision_reviewed)

    # all口径：未标注碰撞次数按0计入。
    collision_all = [
        float(x) if x is not None else 0.0
        for x in collision_values
    ]

    collision_mean_all = mean(collision_all)
    collision_var_all = variance(collision_all)
    collision_std_all = std(collision_all)

    collision_mean_reviewed = mean(collision_reviewed)
    collision_var_reviewed = variance(collision_reviewed)
    collision_std_reviewed = std(collision_reviewed)

    # ===== status counts =====
    plan_failed_count = sum(
        1 for r in records
        if r.get("status") == "plan_failed"
    )

    rtdl_invalid_count = sum(
        1 for r in records
        if r.get("status") == "rtdl_invalid"
    )

    error_count = sum(
        1 for r in records
        if r.get("status") == "error"
    )

    executed_status_count = sum(
        1 for r in records
        if r.get("status") == "executed"
    )

    return {
        **group_info,

        "total": total,

        # syntax / semantic correctness
        "valid_count": valid_count,
        "compiler_failed_count": compiler_failed_count,
        "syntax_semantic_correct_rate": syntax_semantic_rate,

        # logic score
        "logic_reviewed_count": logic_reviewed_count,

        "logic_correct_sum": logic_correct_sum,
        "logic_completeness_sum": logic_completeness_sum,
        "logic_score_sum": logic_score_sum,

        "logic_correct_mean_all": logic_correct_mean_all,

        "logic_completeness_mean_all": logic_completeness_mean_all,

        "logic_score_mean_all": logic_score_mean_all,
        "logic_correct_mean_reviewed": logic_correct_mean_reviewed,
        "logic_completeness_mean_reviewed": logic_completeness_mean_reviewed,

        "logic_score_mean_reviewed": logic_score_mean_reviewed,
        "logic_score_var_reviewed": logic_score_var_reviewed,
        "logic_score_std_reviewed": logic_score_std_reviewed,

        # execution success
        "executed_count": executed_count,
        "executed_status_count": executed_status_count,
        "execution_success_count": execution_success_count,

        "execution_success_rate_all": execution_success_rate_all,
        "execution_success_rate_executed": execution_success_rate_executed,

        # LLM planning time
        "llm_time_count": len(llm_times),
        "llm_time_mean_sec": mean(llm_times),
        "llm_time_var_sec2": variance(llm_times),
        "llm_time_std_sec": std(llm_times),

        # RTDL execution time
        "execution_time_count": len(execution_times),
        "execution_time_mean_sec": mean(execution_times),
        "execution_time_var_sec2": variance(execution_times),
        "execution_time_std_sec": std(execution_times),

        # collision count
        "collision_reviewed_count": collision_reviewed_count,
        "collision_total": collision_total,

        "collision_mean_all": collision_mean_all,
        "collision_var_all": collision_var_all,
        "collision_std_all": collision_std_all,

        "collision_mean_reviewed": collision_mean_reviewed,
        "collision_var_reviewed": collision_var_reviewed,
        "collision_std_reviewed": collision_std_reviewed,

        # status
        "plan_failed_count": plan_failed_count,
        "rtdl_invalid_count": rtdl_invalid_count,
        "error_count": error_count,
    }


# =========================
# output helpers
# =========================

def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        path.write_text("", encoding="utf-8")
        return

    fieldnames = list(rows[0].keys())

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            writer.writerow({
                key: fmt_float(row.get(key))
                for key in fieldnames
            })


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def flatten_record(record: dict[str, Any]) -> dict[str, Any]:
    logic_correct = safe_unit_float(record.get("manual_logic_correct"))
    logic_completeness = safe_unit_float(record.get("manual_logic_completeness"))
    logic_score = compute_logic_score(record)

    return {
        "model": record.get("model"),
        "level": record.get("level"),
        "round": record.get("round"),
        "task": record.get("task"),
        "status": record.get("status"),

        "llm_time_sec": safe_float(record.get("llm_time_sec")),

        "rtdl_valid": infer_rtdl_valid(record),
        "compiler_failed": starts_with_compiler_failed(record),

        "execution_time_sec": safe_float(record.get("execution_time_sec")),
        "execution_success": safe_bool(record.get("execution_success")),

        "manual_logic_correct": logic_correct,
        "manual_logic_completeness": logic_completeness,
        "manual_logic_score": logic_score,

        "manual_collision_observed": safe_int(record.get("manual_collision_observed")),
        "manual_notes": record.get("manual_notes", ""),

        "error_type": record.get("error_type"),
        "error_message": record.get("error_message"),
        "rtdl_error": record.get("rtdl_error"),

        "source_file": record.get("_source_file"),
    }


def print_table(rows: list[dict[str, Any]], title: str) -> None:
    print("\n" + "=" * 100)
    print(title)
    print("=" * 100)

    if not rows:
        print("(empty)")
        return

    compact_cols = [
        "model",
        "level",
        "total",
        "syntax_semantic_correct_percent",
        "logic_score_percent_all",
        "execution_success_percent_all",
        "llm_time_mean_sec",
        "llm_time_std_sec",
        "execution_time_mean_sec",
        "execution_time_std_sec",
        "collision_mean_all",
        "collision_std_all",
        "collision_total",
    ]

    existing_cols = [c for c in compact_cols if c in rows[0]]

    print("\t".join(existing_cols))
    for row in rows:
        print("\t".join(
            str(fmt_float(row.get(c)))
            for c in existing_cols
        ))


# =========================
# main
# =========================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze RTDL benchmark records."
    )

    parser.add_argument(
        "--input",
        type=str,
        default="benchmark_results",
        help="Benchmark results root directory."
    )

    parser.add_argument(
        "--output",
        type=str,
        default="benchmark_analysis",
        help="Output directory for analysis CSV/JSON files."
    )

    args = parser.parse_args()

    input_root = Path(args.input)
    output_root = Path(args.output)

    records = load_records(input_root)

    if not records:
        raise RuntimeError(f"No benchmark records found under {input_root}")

    print(f"[analyze] loaded {len(records)} records from {input_root}")

    # Per-round flattened records
    flat_records = [flatten_record(r) for r in records]

    write_csv(output_root / "records_flat.csv", flat_records)
    write_json(output_root / "records_flat.json", flat_records)

    # Summary by model + level
    by_model_level = []
    for (model, level), group in sorted(
        group_records(records, ("model", "level")).items(),
        key=lambda item: (str(item[0][0]), str(item[0][1])),
    ):
        by_model_level.append(
            summarize_group(
                group,
                {
                    "model": model,
                    "level": level,
                }
            )
        )

    # Summary by model
    by_model = []
    for (model,), group in sorted(
        group_records(records, ("model",)).items(),
        key=lambda item: str(item[0][0]),
    ):
        by_model.append(
            summarize_group(
                group,
                {
                    "model": model,
                }
            )
        )

    # Summary by level
    by_level = []
    for (level,), group in sorted(
        group_records(records, ("level",)).items(),
        key=lambda item: str(item[0][0]),
    ):
        by_level.append(
            summarize_group(
                group,
                {
                    "level": level,
                }
            )
        )

    # Overall
    overall = summarize_group(records, {"scope": "overall"})

    write_csv(output_root / "summary_by_model_level.csv", by_model_level)
    write_json(output_root / "summary_by_model_level.json", by_model_level)

    write_csv(output_root / "summary_by_model.csv", by_model)
    write_json(output_root / "summary_by_model.json", by_model)

    write_csv(output_root / "summary_by_level.csv", by_level)
    write_json(output_root / "summary_by_level.json", by_level)

    write_json(output_root / "summary_overall.json", overall)

    print_table(by_model_level, "Summary by model + level")
    print_table(by_model, "Summary by model")
    print_table(by_level, "Summary by level")

    print(f"\n[analyze] analysis saved to: {output_root}")


if __name__ == "__main__":
    main()