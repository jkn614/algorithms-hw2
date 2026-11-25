"""Measure separate-chaining search costs at several load factors."""

import csv
import math
import random
import string
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape

from src.hash_table import HashTable

CAPACITY = 4093
LOAD_FACTORS = (0.25, 0.5, 1, 2, 3, 4)
RANDOM_SEED = 20261125
TOKEN_ALPHABET = string.ascii_lowercase + string.digits


@dataclass(frozen=True)
class LoadResult:
    target_load_factor: float
    actual_load_factor: float
    item_count: int
    successful_measured: float
    successful_theoretical: float
    unsuccessful_measured: float
    unsuccessful_theoretical: float


def _random_url(rng: random.Random, kind: str, index: int) -> str:
    token = "".join(rng.choice(TOKEN_ALPHABET) for _ in range(24))
    return f"https://{token}.example/{kind}/{index}"


def _average_comparisons(
    table: HashTable, urls: list[str], should_be_found: bool
) -> float:
    total_comparisons = 0
    for url in urls:
        value, comparisons = table.find(url)
        if (value is not None) != should_be_found:
            raise RuntimeError(f"unexpected lookup result for {url!r}")
        total_comparisons += comparisons
    return total_comparisons / len(urls)


def measure_load_factor(
    target_load_factor: float, rng: random.Random
) -> LoadResult:
    item_count = int(CAPACITY * target_load_factor + 0.5)
    table = HashTable(capacity=CAPACITY, max_load=None)
    inserted_urls = [
        _random_url(rng, "stored", index) for index in range(item_count)
    ]
    for url in inserted_urls:
        table.put(url, True)

    missing_urls = [
        _random_url(rng, "missing", index) for index in range(item_count)
    ]
    actual_load_factor = table.load_factor()
    return LoadResult(
        target_load_factor=target_load_factor,
        actual_load_factor=actual_load_factor,
        item_count=item_count,
        successful_measured=_average_comparisons(table, inserted_urls, True),
        successful_theoretical=1 + actual_load_factor / 2,
        unsuccessful_measured=_average_comparisons(table, missing_urls, False),
        unsuccessful_theoretical=actual_load_factor,
    )


def write_csv(results: list[LoadResult], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(
            (
                "target_load_factor",
                "actual_load_factor",
                "items",
                "successful_measured",
                "successful_theoretical",
                "unsuccessful_measured",
                "unsuccessful_theoretical",
            )
        )
        for result in results:
            writer.writerow(
                (
                    f"{result.target_load_factor:g}",
                    f"{result.actual_load_factor:.6f}",
                    result.item_count,
                    f"{result.successful_measured:.6f}",
                    f"{result.successful_theoretical:.6f}",
                    f"{result.unsuccessful_measured:.6f}",
                    f"{result.unsuccessful_theoretical:.6f}",
                )
            )


def write_svg(results: list[LoadResult], path: Path) -> None:
    width, height = 1000, 620
    left, right, top, bottom = 100, 710, 60, 520
    plot_width, plot_height = right - left, bottom - top
    x_max = 4.2
    observed_max = max(
        result.successful_measured for result in results
    )
    observed_max = max(
        observed_max,
        *(result.unsuccessful_measured for result in results),
        *(result.successful_theoretical for result in results),
        *(result.unsuccessful_theoretical for result in results),
    )
    y_max = max(1, math.ceil(observed_max * 1.1))

    def x_position(load_factor: float) -> float:
        return left + load_factor / x_max * plot_width

    def y_position(value: float) -> float:
        return bottom - value / y_max * plot_height

    series = (
        ("Successful search (measured)", "successful_measured", "#2563eb", ""),
        (
            "Successful search (theory)",
            "successful_theoretical",
            "#93c5fd",
            "8 5",
        ),
        ("Failed search (measured)", "unsuccessful_measured", "#dc2626", ""),
        (
            "Failed search (theory)",
            "unsuccessful_theoretical",
            "#fca5a5",
            "8 5",
        ),
    )
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="500" y="30" text-anchor="middle" font-family="sans-serif" font-size="20">Separate-chaining search cost</text>',
    ]

    for tick in range(y_max + 1):
        y = y_position(tick)
        svg.extend(
            (
                f'<line x1="{left}" y1="{y:.2f}" x2="{right}" y2="{y:.2f}" stroke="#e5e7eb"/>',
                f'<text x="{left - 12}" y="{y + 5:.2f}" text-anchor="end" font-family="sans-serif" font-size="13">{tick}</text>',
            )
        )

    for tick in LOAD_FACTORS:
        x = x_position(tick)
        svg.extend(
            (
                f'<line x1="{x:.2f}" y1="{bottom}" x2="{x:.2f}" y2="{bottom + 6}" stroke="#111827"/>',
                f'<text x="{x:.2f}" y="{bottom + 25}" text-anchor="middle" font-family="sans-serif" font-size="13">{tick:g}</text>',
            )
        )

    svg.extend(
        (
            f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" stroke="#111827"/>',
            f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" stroke="#111827"/>',
            f'<text x="{(left + right) / 2:.2f}" y="{height - 28}" text-anchor="middle" font-family="sans-serif" font-size="16">Load factor (α)</text>',
            f'<text x="25" y="{(top + bottom) / 2:.2f}" text-anchor="middle" transform="rotate(-90 25 {(top + bottom) / 2:.2f})" font-family="sans-serif" font-size="16">Average node comparisons</text>',
        )
    )

    for label, field, color, dash in series:
        values = [
            (
                x_position(result.actual_load_factor),
                y_position(getattr(result, field)),
            )
            for result in results
        ]
        points = " ".join(f"{x:.2f},{y:.2f}" for x, y in values)
        dash_attribute = f' stroke-dasharray="{dash}"' if dash else ""
        svg.append(
            f'<polyline fill="none" stroke="{color}" stroke-width="2.5"{dash_attribute} points="{points}"/>'
        )
        for x, y in values:
            svg.append(
                f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="{color}"/>'
            )

    for index, (label, _, color, dash) in enumerate(series):
        y = top + 20 + index * 28
        dash_attribute = f' stroke-dasharray="{dash}"' if dash else ""
        svg.extend(
            (
                f'<line x1="745" y1="{y}" x2="780" y2="{y}" stroke="{color}" stroke-width="2.5"{dash_attribute}/>',
                f'<text x="790" y="{y + 5}" font-family="sans-serif" font-size="13">{escape(label)}</text>',
            )
        )

    svg.append("</svg>")
    path.write_text("\n".join(svg) + "\n", encoding="utf-8")


def print_results(results: list[LoadResult]) -> None:
    print(
        "target α | actual α | items | success measured | success theory "
        "| failed measured | failed theory"
    )
    print("-" * 100)
    for result in results:
        print(
            f"{result.target_load_factor:8.2f} | "
            f"{result.actual_load_factor:8.4f} | "
            f"{result.item_count:5d} | "
            f"{result.successful_measured:16.4f} | "
            f"{result.successful_theoretical:14.4f} | "
            f"{result.unsuccessful_measured:15.4f} | "
            f"{result.unsuccessful_theoretical:13.4f}"
        )


def main() -> None:
    rng = random.Random(RANDOM_SEED)
    results = [
        measure_load_factor(load_factor, rng) for load_factor in LOAD_FACTORS
    ]
    output_directory = Path(__file__).resolve().parent
    csv_path = output_directory / "results.csv"
    svg_path = output_directory / "results.svg"
    write_csv(results, csv_path)
    write_svg(results, svg_path)
    print_results(results)
    print(f"\nWrote {csv_path}")
    print(f"Wrote {svg_path}")


if __name__ == "__main__":
    main()
