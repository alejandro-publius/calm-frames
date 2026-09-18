#!/usr/bin/env python3
"""What the AWS stack would cost a month, from published list prices.

    .venv/bin/python scripts/cost_estimate.py     writes results/cost_estimate.json

This is an estimate. Nothing has been deployed, no bill exists, and the one
input that matters most, how long the ingest task runs per title, has never been
measured because the container has never processed a video. The arithmetic is
here so it can be argued with rather than believed.

Every unit price was read from the AWS pricing pages on the date in PRICES_READ
below, and each one carries the page it came from. Two are not in the table
because at this volume they round to nothing whatever the rate is: Lambda, at
twenty invocations a month against a million free ones, and CloudWatch Logs,
at a few megabytes of task output.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUTPUT = REPO / "results" / "cost_estimate.json"

PRICES_READ = "2026-09-17"
HOURS_PER_MONTH = 730

PRICES = {
    "fargate_arm_vcpu_hour": (0.032380, "https://aws.amazon.com/fargate/pricing/"),
    "fargate_arm_gb_hour": (0.003560, "https://aws.amazon.com/fargate/pricing/"),
    "s3_standard_gb_month": (0.023, "https://aws.amazon.com/s3/pricing/"),
    "s3_put_per_1000": (0.005, "https://aws.amazon.com/s3/pricing/"),
    "dynamodb_write_per_million": (0.625, "https://aws.amazon.com/dynamodb/pricing/on-demand/"),
    "dynamodb_gb_month": (0.25, "https://aws.amazon.com/dynamodb/pricing/on-demand/"),
    "ecr_gb_month": (0.10, "https://aws.amazon.com/ecr/pricing/"),
    "cloudfront_free_tb_out": (1.0, "https://aws.amazon.com/cloudfront/pricing/pay-as-you-go/"),
    "cloudfront_gb_out_after_free": (0.085, "https://aws.amazon.com/cloudfront/pricing/pay-as-you-go/"),
    "nat_gateway_hour": (0.045, "https://aws.amazon.com/vpc/pricing/"),
}

# The assumptions. These are the numbers to argue with.
ASSUMPTIONS = {
    "titles_per_month": 20,
    "minutes_per_title": 10,
    "task_minutes_per_title": 15,
    "task_vcpu": 2,
    "task_memory_gb": 4,
    "delivery_gb_per_title": 0.8,
    "source_gb_per_title": 1.0,
    "source_kept_days": 30,
    "objects_put_per_title": 120,
    "image_gb": 1.0,
    "cloudfront_gb_out_per_month": 20,
}


def estimate() -> dict:
    a = ASSUMPTIONS
    price = {name: value for name, (value, _) in PRICES.items()}

    task_hours = a["titles_per_month"] * a["task_minutes_per_title"] / 60
    fargate = task_hours * (
        a["task_vcpu"] * price["fargate_arm_vcpu_hour"]
        + a["task_memory_gb"] * price["fargate_arm_gb_hour"]
    )

    delivery_gb = a["titles_per_month"] * a["delivery_gb_per_title"]
    # Sources expire after 30 days, so a month's worth is what sits there.
    source_gb = a["titles_per_month"] * a["source_gb_per_title"]
    storage = (delivery_gb + source_gb) * price["s3_standard_gb_month"]

    puts = a["titles_per_month"] * a["objects_put_per_title"]
    requests = puts / 1000 * price["s3_put_per_1000"]

    dynamodb = (
        a["titles_per_month"] / 1_000_000 * price["dynamodb_write_per_million"]
        + 0.001 * price["dynamodb_gb_month"]
    )
    ecr = a["image_gb"] * price["ecr_gb_month"]

    # Under the always free tier of 1 TB out a month, so nothing to pay.
    cloudfront = 0.0
    cloudfront_free = a["cloudfront_gb_out_per_month"] <= price["cloudfront_free_tb_out"] * 1024

    lines = {
        "fargate_ingest": round(fargate, 2),
        "s3_storage": round(storage, 2),
        "s3_requests": round(requests, 2),
        "dynamodb": round(dynamodb, 2),
        "ecr_image": round(ecr, 2),
        "cloudfront": round(cloudfront, 2),
    }
    total = round(sum(lines.values()), 2)

    # The one input nobody has measured, moved in both directions.
    sensitivity = {}
    for factor in (0.5, 2, 4):
        hours = task_hours * factor
        moved = hours * (
            a["task_vcpu"] * price["fargate_arm_vcpu_hour"]
            + a["task_memory_gb"] * price["fargate_arm_gb_hour"]
        )
        sensitivity[f"task_time_x{factor:g}"] = round(total - lines["fargate_ingest"] + moved, 2)

    nat_if_default = round(2 * HOURS_PER_MONTH * price["nat_gateway_hour"], 2)

    return {
        "statement": (
            "An estimate from published list prices, not a bill. Nothing has been "
            "deployed. The largest uncertainty is how long the ingest task runs "
            "per title, which has never been measured, so the sensitivity block "
            "moves it by half, double and quadruple."
        ),
        "prices_read_on": PRICES_READ,
        "region": "us-east-1",
        "unit_prices": {name: {"usd": value, "source": url} for name, (value, url) in PRICES.items()},
        "assumptions": ASSUMPTIONS,
        "monthly_usd": lines,
        "published": {
            "monthly_total_usd": total,
            "fargate_usd": lines["fargate_ingest"],
            "storage_usd": lines["s3_storage"],
            "budget_alarm_usd": 20,
            "nat_gateways_would_add_usd": nat_if_default,
            "task_time_double_usd": sensitivity["task_time_x2"],
            "task_time_quadruple_usd": sensitivity["task_time_x4"],
        },
        "sensitivity_monthly_usd": sensitivity,
        "cloudfront_inside_free_tier": cloudfront_free,
        "not_counted": [
            "Lambda, which is twenty invocations a month against a million free ones",
            "CloudWatch Logs, a few megabytes of task output",
            "the CDK bootstrap bucket, a few megabytes of templates and assets",
            "tax",
        ],
    }


def main() -> int:
    report = estimate()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n")
    published = report["published"]
    print(f"estimate: {published['monthly_total_usd']} USD a month, against a {published['budget_alarm_usd']} USD alarm")
    for name, value in report["monthly_usd"].items():
        print(f"  {name:<16} {value:>6.2f}")
    print(f"if the task takes twice as long: {published['task_time_double_usd']}")
    print(f"a NAT gateway per zone would add: {published['nat_gateways_would_add_usd']}")
    print(f"written to {OUTPUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
