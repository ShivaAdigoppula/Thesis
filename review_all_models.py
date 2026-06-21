import argparse
import csv
import json
import os
import re
import time
from datetime import datetime

import requests


MODELS = [
    "llama3:latest",
    "mistral:latest",
    "qwen2.5-coder:1.5b",
    "tinyllama:latest",
]


def safe_name(value):
    value = value.replace("/", "_").replace(":", "_")
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", value)


def read_code_file(file_path):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
        return file.read()


def build_prompt(file_path, code):
    return f"""
You are a senior software engineer performing a code review.

Review this code file.

File name: {file_path}

Check for:
1. Bugs
2. Security issues
3. Performance problems
4. Code quality and maintainability
5. Error handling
6. Suggestions for improvement

Give output in this format:
- Summary
- Issues found
- Severity: Low / Medium / High
- Suggested fixes
- Rating out of 5

Code:
{code}
"""


def call_ollama(model, prompt):
    url = "http://localhost:11434/api/generate"

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 700,
            "num_ctx": 10000
        }
    }

    start_time = time.perf_counter()

    try:
        response = requests.post(url, json=payload, timeout=1800)
        wall_time_seconds = time.perf_counter() - start_time

        if response.status_code != 200:
            return {
                "success": False,
                "data": None,
                "error": response.text,
                "wall_time_seconds": wall_time_seconds
            }

        return {
            "success": True,
            "data": response.json(),
            "error": None,
            "wall_time_seconds": wall_time_seconds
        }

    except Exception as e:
        wall_time_seconds = time.perf_counter() - start_time

        return {
            "success": False,
            "data": None,
            "error": str(e),
            "wall_time_seconds": wall_time_seconds
        }


def calculate_cost(ec2_hourly_price, wall_time_seconds, total_tokens):
    cost_per_run = ec2_hourly_price * (wall_time_seconds / 3600)

    if total_tokens > 0:
        cost_per_1k_tokens = (cost_per_run / total_tokens) * 1000
    else:
        cost_per_1k_tokens = 0

    return cost_per_run, cost_per_1k_tokens


def safe_tokens_per_second(tokens, duration_seconds):
    if duration_seconds > 0:
        return tokens / duration_seconds
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Run code review using multiple Ollama models and save metrics."
    )

    parser.add_argument(
        "--code-file",
        required=True,
        help="Path of the code file to review. Example: sample_codes/sample_01.py"
    )

    parser.add_argument(
        "--ec2-hourly-price",
        type=float,
        required=True,
        help="Hourly price of EC2 instance. Example: 0.187"
    )

    parser.add_argument(
        "--environment",
        default="ec2-c6a-2xlarge",
        help="Environment name for experiment tracking."
    )

    args = parser.parse_args()

    if not os.path.exists(args.code_file):
        raise FileNotFoundError(f"Code file not found: {args.code_file}")

    os.makedirs("results", exist_ok=True)
    os.makedirs("reviews", exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    code = read_code_file(args.code_file)
    prompt = build_prompt(args.code_file, code)

    summary_file = f"results/summary_{timestamp}.csv"

    fieldnames = [
        "timestamp",
        "environment",
        "model",
        "code_file",
        "status",

        "wall_time_seconds",
        "ollama_total_duration_seconds",
        "load_duration_seconds",
        "prompt_eval_duration_seconds",
        "eval_duration_seconds",
        "backend_overhead_seconds",

        "prompt_tokens",
        "response_tokens",
        "total_tokens",

        "prompt_tokens_per_second",
        "response_tokens_per_second",
        "total_tokens_per_second",

        "cost_per_run",
        "cost_per_1k_tokens",

        "review_file",
        "metrics_file",
        "error"
    ]

    with open(summary_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for model in MODELS:
            print("=" * 80)
            print(f"Running code review using model: {model}")
            print("=" * 80)

            result = call_ollama(model, prompt)

            model_folder = safe_name(model)

            review_dir = f"reviews/{model_folder}"
            metrics_dir = f"results/{model_folder}"

            os.makedirs(review_dir, exist_ok=True)
            os.makedirs(metrics_dir, exist_ok=True)

            review_file = f"{review_dir}/review_{timestamp}.md"
            metrics_file = f"{metrics_dir}/metrics_{timestamp}.json"

            wall_time_seconds = result["wall_time_seconds"]

            if result["success"]:
                data = result["data"]

                review_text = data.get("response", "")

                prompt_tokens = data.get("prompt_eval_count", 0)
                response_tokens = data.get("eval_count", 0)
                total_tokens = prompt_tokens + response_tokens

                ollama_total_duration_seconds = data.get("total_duration", 0) / 1_000_000_000
                load_duration_seconds = data.get("load_duration", 0) / 1_000_000_000
                prompt_eval_duration_seconds = data.get("prompt_eval_duration", 0) / 1_000_000_000
                eval_duration_seconds = data.get("eval_duration", 0) / 1_000_000_000

                backend_overhead_seconds = wall_time_seconds - ollama_total_duration_seconds

                if backend_overhead_seconds < 0:
                    backend_overhead_seconds = 0

                prompt_tokens_per_second = safe_tokens_per_second(
                    prompt_tokens,
                    prompt_eval_duration_seconds
                )

                response_tokens_per_second = safe_tokens_per_second(
                    response_tokens,
                    eval_duration_seconds
                )

                total_tokens_per_second = safe_tokens_per_second(
                    total_tokens,
                    ollama_total_duration_seconds
                )

                cost_per_run, cost_per_1k_tokens = calculate_cost(
                    args.ec2_hourly_price,
                    wall_time_seconds,
                    total_tokens
                )

                status = "success"
                error = ""

            else:
                review_text = f"ERROR:\n{result['error']}"

                prompt_tokens = 0
                response_tokens = 0
                total_tokens = 0

                ollama_total_duration_seconds = 0
                load_duration_seconds = 0
                prompt_eval_duration_seconds = 0
                eval_duration_seconds = 0
                backend_overhead_seconds = wall_time_seconds

                prompt_tokens_per_second = 0
                response_tokens_per_second = 0
                total_tokens_per_second = 0

                cost_per_run, cost_per_1k_tokens = calculate_cost(
                    args.ec2_hourly_price,
                    wall_time_seconds,
                    total_tokens
                )

                status = "failed"
                error = result["error"]

            with open(review_file, "w", encoding="utf-8") as file:
                file.write("# Code Review Result\n\n")
                file.write(f"Model: {model}\n\n")
                file.write(f"Code file: {args.code_file}\n\n")
                file.write(f"Environment: {args.environment}\n\n")
                file.write(f"Timestamp: {timestamp}\n\n")
                file.write("---\n\n")
                file.write(review_text)

            metrics = {
                "timestamp": timestamp,
                "environment": args.environment,
                "model": model,
                "code_file": args.code_file,
                "status": status,

                "wall_time_seconds": wall_time_seconds,
                "ollama_total_duration_seconds": ollama_total_duration_seconds,
                "load_duration_seconds": load_duration_seconds,
                "prompt_eval_duration_seconds": prompt_eval_duration_seconds,
                "eval_duration_seconds": eval_duration_seconds,
                "backend_overhead_seconds": backend_overhead_seconds,

                "prompt_tokens": prompt_tokens,
                "response_tokens": response_tokens,
                "total_tokens": total_tokens,

                "prompt_tokens_per_second": prompt_tokens_per_second,
                "response_tokens_per_second": response_tokens_per_second,
                "total_tokens_per_second": total_tokens_per_second,

                "ec2_hourly_price": args.ec2_hourly_price,
                "cost_per_run": cost_per_run,
                "cost_per_1k_tokens": cost_per_1k_tokens,

                "review_file": review_file,
                "metrics_file": metrics_file,
                "error": error
            }

            with open(metrics_file, "w", encoding="utf-8") as file:
                json.dump(metrics, file, indent=2)

            writer.writerow({
                "timestamp": timestamp,
                "environment": args.environment,
                "model": model,
                "code_file": args.code_file,
                "status": status,

                "wall_time_seconds": wall_time_seconds,
                "ollama_total_duration_seconds": ollama_total_duration_seconds,
                "load_duration_seconds": load_duration_seconds,
                "prompt_eval_duration_seconds": prompt_eval_duration_seconds,
                "eval_duration_seconds": eval_duration_seconds,
                "backend_overhead_seconds": backend_overhead_seconds,

                "prompt_tokens": prompt_tokens,
                "response_tokens": response_tokens,
                "total_tokens": total_tokens,

                "prompt_tokens_per_second": prompt_tokens_per_second,
                "response_tokens_per_second": response_tokens_per_second,
                "total_tokens_per_second": total_tokens_per_second,

                "cost_per_run": cost_per_run,
                "cost_per_1k_tokens": cost_per_1k_tokens,

                "review_file": review_file,
                "metrics_file": metrics_file,
                "error": error
            })

            print(f"Status: {status}")
            print(f"Wall time: {wall_time_seconds:.2f} seconds")
            print(f"Load time: {load_duration_seconds:.2f} seconds")
            print(f"Prompt eval time: {prompt_eval_duration_seconds:.2f} seconds")
            print(f"Generation time: {eval_duration_seconds:.2f} seconds")
            print(f"Response tokens/sec: {response_tokens_per_second:.2f}")
            print(f"Review saved: {review_file}")
            print(f"Metrics saved: {metrics_file}")

    print("=" * 80)
    print(f"Summary saved: {summary_file}")
    print("=" * 80)


if __name__ == "__main__":
    main()
