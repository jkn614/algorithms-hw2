"""Compare separate chaining and linear probing search costs."""

import csv
import math
import random
import string
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape

from src.hash_table import HashTable
from src.linear_probing import LinearProbingTable

CAPACITY = 4093
LOAD_FACTORS = tuple(index / 10 for index in range(1, 10))
RANDOM_SEED = 20261127
TOKEN_ALPHABET = string.ascii_lowercase + string.digits


@dataclass(frozen=True)
class CompareResult:
    target_load_factor: float
    actual_load_factor: float
    item_count: int
    chaining_success_measured: float
    chaining_success_theoretical: float
    linear_success_measured: float
    linear_success_theoretical: float
    chaining_failed_measured: float
    chaining_failed_theoretical: float
    linear_failed_measured: float
    linear_failed_theoretical: float


def _random_url(rng: random.Random, kind: str, index: int) -> str:
    token = "".join(rng.choice(TOKEN_ALPHABET) for _ in range(24))
    return f"https://{token}.example/{kind}/{index}"


def _average_find_count(
    table: HashTable | LinearProbingTable,
    urls: list[str],
    should_be_found: bool,
) -> float:
    total_count = 0
    for url in urls:
        value, find_count = table.find(url)
        if (value is not None) != should_be_found:
            raise RuntimeError(f"unexpected lookup result for {url!r}")
        total_count += find_count
    return total_count / len(urls)


def measure_load_factor(
    target_load_factor: float,
    stored_urls: list[str],
    missing_urls: list[str],
) -> CompareResult:
    item_count = int(CAPACITY * target_load_factor + 0.5)
    selected_urls = stored_urls[:item_count]
    selected_missing_urls = missing_urls[:item_count]

    chaining_table = HashTable(capacity=CAPACITY, max_load=None)
    linear_table = LinearProbingTable(capacity=CAPACITY, max_load=None)
    for index, url in enumerate(selected_urls):
        chaining_table.put(url, index)
        linear_table.put(url, index)

    if len(chaining_table) != item_count or len(linear_table) != item_count:
        raise RuntimeError("a hash table did not retain all inserted URLs")

    actual_load_factor = item_count / CAPACITY
    return CompareResult(
        target_load_factor=target_load_factor,
        actual_load_factor=actual_load_factor,
        item_count=item_count,
        chaining_success_measured=_average_find_count(
            chaining_table, selected_urls, True
        ),
        chaining_success_theoretical=1 + target_load_factor / 2,
        linear_success_measured=_average_find_count(
            linear_table, selected_urls, True
        ),
        linear_success_theoretical=(
            1 + 1 / (1 - target_load_factor)
        )
        / 2,
        chaining_failed_measured=_average_find_count(
            chaining_table, selected_missing_urls, False
        ),
        chaining_failed_theoretical=target_load_factor,
        linear_failed_measured=_average_find_count(
            linear_table, selected_missing_urls, False
        ),
        linear_failed_theoretical=(
            1 + 1 / (1 - target_load_factor) ** 2
        )
        / 2,
    )


def write_csv(results: list[CompareResult], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(
            (
                "target_load_factor",
                "actual_load_factor",
                "items",
                "chaining_success_measured",
                "chaining_success_theoretical",
                "linear_success_measured",
                "linear_success_theoretical",
                "chaining_failed_measured",
                "chaining_failed_theoretical",
                "linear_failed_measured",
                "linear_failed_theoretical",
            )
        )
        for result in results:
            writer.writerow(
                (
                    f"{result.target_load_factor:.1f}",
                    f"{result.actual_load_factor:.6f}",
                    result.item_count,
                    f"{result.chaining_success_measured:.6f}",
                    f"{result.chaining_success_theoretical:.6f}",
                    f"{result.linear_success_measured:.6f}",
                    f"{result.linear_success_theoretical:.6f}",
                    f"{result.chaining_failed_measured:.6f}",
                    f"{result.chaining_failed_theoretical:.6f}",
                    f"{result.linear_failed_measured:.6f}",
                    f"{result.linear_failed_theoretical:.6f}",
                )
            )


def write_svg(
    results: list[CompareResult],
    path: Path,
    search_kind: str,
    title: str,
) -> None:
    width, height = 1000, 620
    left, right, top, bottom = 100, 710, 60, 520
    plot_width, plot_height = right - left, bottom - top
    fields = (
        ("Chaining (measured)", f"chaining_{search_kind}_measured", "#2563eb", ""),
        (
            "Chaining (theory)",
            f"chaining_{search_kind}_theoretical",
            "#93c5fd",
            "8 5",
        ),
        (
            "Linear probing (measured)",
            f"linear_{search_kind}_measured",
            "#dc2626",
            "",
        ),
        (
            "Linear probing (theory)",
            f"linear_{search_kind}_theoretical",
            "#fca5a5",
            "8 5",
        ),
    )
    observed_max = max(
        getattr(result, field)
        for result in results
        for _, field, _, _ in fields
    )
    y_max = max(1, math.ceil(observed_max * 1.1))

    def x_position(load_factor: float) -> float:
        return left + load_factor * plot_width

    def y_position(value: float) -> float:
        return bottom - value / y_max * plot_height

    svg = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
            f'height="{height}" viewBox="0 0 {width} {height}">'
        ),
        '<rect width="100%" height="100%" fill="white"/>',
        (
            f'<text x="{width / 2:.0f}" y="30" text-anchor="middle" '
            f'font-family="sans-serif" font-size="20">{escape(title)}</text>'
        ),
    ]

    for tick in range(6):
        value = y_max * tick / 5
        y = y_position(value)
        svg.extend(
            (
                (
                    f'<line x1="{left}" y1="{y:.2f}" x2="{right}" '
                    f'y2="{y:.2f}" stroke="#e5e7eb"/>'
                ),
                (
                    f'<text x="{left - 12}" y="{y + 5:.2f}" '
                    f'text-anchor="end" font-family="sans-serif" '
                    f'font-size="13">{value:.1f}</text>'
                ),
            )
        )

    for tick in range(11):
        load_factor = tick / 10
        x = x_position(load_factor)
        svg.extend(
            (
                (
                    f'<line x1="{x:.2f}" y1="{bottom}" '
                    f'x2="{x:.2f}" y2="{bottom + 6}" stroke="#111827"/>'
                ),
                (
                    f'<text x="{x:.2f}" y="{bottom + 25}" '
                    f'text-anchor="middle" font-family="sans-serif" '
                    f'font-size="13">{load_factor:.1f}</text>'
                ),
            )
        )

    svg.extend(
        (
            f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" stroke="#111827"/>',
            f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" stroke="#111827"/>',
            (
                f'<text x="{(left + right) / 2:.2f}" y="{height - 28}" '
                'text-anchor="middle" font-family="sans-serif" '
                'font-size="16">Load factor (α)</text>'
            ),
            (
                f'<text x="25" y="{(top + bottom) / 2:.2f}" '
                f'text-anchor="middle" transform="rotate(-90 25 '
                f'{(top + bottom) / 2:.2f})" font-family="sans-serif" '
                'font-size="16">Average find inspections</text>'
            ),
        )
    )

    for label, field, color, dash in fields:
        points = " ".join(
            (
                f"{x_position(result.target_load_factor):.2f},"
                f"{y_position(getattr(result, field)):.2f}"
            )
            for result in results
        )
        dash_attribute = f' stroke-dasharray="{dash}"' if dash else ""
        svg.append(
            (
                f'<polyline fill="none" stroke="{color}" stroke-width="2.5"'
                f'{dash_attribute} points="{points}"/>'
            )
        )
        if "measured" in field:
            for result in results:
                x = x_position(result.target_load_factor)
                y = y_position(getattr(result, field))
                svg.append(
                    f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="{color}"/>'
                )

    for index, (label, _, color, dash) in enumerate(fields):
        y = top + 20 + index * 28
        dash_attribute = f' stroke-dasharray="{dash}"' if dash else ""
        svg.extend(
            (
                (
                    f'<line x1="745" y1="{y}" x2="780" y2="{y}" '
                    f'stroke="{color}" stroke-width="2.5"{dash_attribute}/>'
                ),
                (
                    f'<text x="790" y="{y + 5}" font-family="sans-serif" '
                    f'font-size="13">{escape(label)}</text>'
                ),
            )
        )

    svg.append("</svg>")
    path.write_text("\n".join(svg) + "\n", encoding="utf-8")


def print_results(results: list[CompareResult]) -> None:
    print(
        "target α | actual α | items | chaining success measured/theory "
        "| linear success measured/theory | chaining failed measured/theory "
        "| linear failed measured/theory"
    )
    print("-" * 150)
    for result in results:
        print(
            f"{result.target_load_factor:8.1f} | "
            f"{result.actual_load_factor:8.4f} | "
            f"{result.item_count:5d} | "
            f"{result.chaining_success_measured:7.4f}/"
            f"{result.chaining_success_theoretical:7.4f} | "
            f"{result.linear_success_measured:7.4f}/"
            f"{result.linear_success_theoretical:7.4f} | "
            f"{result.chaining_failed_measured:7.4f}/"
            f"{result.chaining_failed_theoretical:7.4f} | "
            f"{result.linear_failed_measured:7.4f}/"
            f"{result.linear_failed_theoretical:7.4f}"
        )
    print(
        "체이닝은 빈 칸을 0번으로 세고, "
        "선형 탐지는 마지막에 만난 빈 칸까지 셉니다."
    )


def main() -> None:
    rng = random.Random(RANDOM_SEED)
    max_item_count = int(CAPACITY * LOAD_FACTORS[-1] + 0.5)
    stored_urls = [
        _random_url(rng, "stored", index) for index in range(max_item_count)
    ]
    missing_urls = [
        _random_url(rng, "missing", index) for index in range(max_item_count)
    ]
    results = [
        measure_load_factor(load_factor, stored_urls, missing_urls)
        for load_factor in LOAD_FACTORS
    ]

    output_directory = Path(__file__).resolve().parent
    csv_path = output_directory / "compare_results.csv"
    success_svg_path = output_directory / "compare_success.svg"
    failure_svg_path = output_directory / "compare_failure.svg"
    write_csv(results, csv_path)
    write_svg(results, success_svg_path, "success", "Successful search cost")
    write_svg(results, failure_svg_path, "failed", "Failed search cost")
    print_results(results)
    print(f"\nWrote {csv_path}")
    print(f"Wrote {success_svg_path}")
    print(f"Wrote {failure_svg_path}")


if __name__ == "__main__":
    main()
