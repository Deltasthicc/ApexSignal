"""Generate ApexSignal's browser circuit atlas from TUMFTM centerline CSVs.

Usage:
    python scripts/build_circuit_atlas.py /path/to/racetrack-database

The generated TypeScript is intentionally committed so the website remains
self-contained and does not fetch geometry at runtime. Every outline is
uniformly scaled; aspect ratios are never stretched to fit a card.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "apps" / "web" / "src" / "data" / "circuits.ts"
MAX_POINTS = 88

# Copy stays descriptive and stable rather than claiming current-calendar
# status. Shape notes identify the visual landmarks used to recognize a map.
META = {
    "Melbourne": ("Albert Park", "Melbourne, Australia", "AUS", "Lakeside semi-street loop with fast direction changes."),
    "Spa": ("Spa-Francorchamps", "Stavelot, Belgium", "BEL", "Long Ardennes lap, steep Eau Rouge climb and sweeping back half."),
    "Monza": ("Autodromo Nazionale Monza", "Monza, Italy", "ITA", "Long straights, compact chicanes and the Parabolica arc."),
    "Silverstone": ("Silverstone Circuit", "Silverstone, United Kingdom", "GBR", "Angular high-speed outline shaped by Maggotts and Becketts."),
    "Suzuka": ("Suzuka Circuit", "Suzuka, Japan", "JPN", "The unmistakable figure-eight with Esses and Spoon curve."),
    "SaoPaulo": ("Interlagos", "Sao Paulo, Brazil", "BRA", "Compact anti-clockwise loop with a long uphill final sweep."),
    "Sakhir": ("Bahrain International Circuit", "Sakhir, Bahrain", "BHR", "Wide desert layout built around straights and heavy braking zones."),
    "Austin": ("Circuit of the Americas", "Austin, United States", "USA", "Uphill Turn 1, flowing Esses and a long back straight."),
    "Catalunya": ("Circuit de Barcelona-Catalunya", "Montmelo, Spain", "ESP", "Balanced reference lap with a long main straight and broad final sector."),
    "Spielberg": ("Red Bull Ring", "Spielberg, Austria", "AUT", "Short Alpine lap with three straights and a compact downhill return."),
    "Zandvoort": ("Circuit Zandvoort", "Zandvoort, Netherlands", "NED", "Tight coastal ribbon bookended by distinctive banked turns."),
    "Montreal": ("Circuit Gilles Villeneuve", "Montreal, Canada", "CAN", "Stop-start island circuit with long straights and quick chicanes."),
    "MexicoCity": ("Autodromo Hermanos Rodriguez", "Mexico City, Mexico", "MEX", "Long opening straight feeding a technical stadium section."),
    "Budapest": ("Hungaroring", "Mogyorod, Hungary", "HUN", "Continuous, tightly linked corners with very little recovery time."),
    "Shanghai": ("Shanghai International Circuit", "Shanghai, China", "CHN", "Recognisable opening snail and an extended back straight."),
    "YasMarina": ("Yas Marina Circuit", "Abu Dhabi, United Arab Emirates", "UAE", "Marina-side loop combining long straights with a compact final sector."),
    "Sepang": ("Sepang International Circuit", "Sepang, Malaysia", "MAS", "Broad, flowing layout framed by two parallel long straights."),
    "Hockenheim": ("Hockenheimring", "Hockenheim, Germany", "GER", "Long hairpin run linked to the compact stadium complex."),
    "Nuerburgring": ("Nuerburgring GP-Strecke", "Nurburg, Germany", "GER", "Modern Grand Prix loop with a tight arena opening sector."),
    "Sochi": ("Sochi Autodrom", "Sochi, Russia", "RUS", "Olympic Park street layout defined by its long constant-radius turn."),
    "BrandsHatch": ("Brands Hatch", "West Kingsdown, United Kingdom", "GBR", "Compact natural-amphitheatre circuit with a plunging opening bend."),
    "IMS": ("Indianapolis Road Course", "Indianapolis, United States", "USA", "Infield road course enclosed by the Speedway's rectangular oval."),
    "MoscowRaceway": ("Moscow Raceway", "Volokolamsk, Russia", "RUS", "Technical modern circuit with a dense, folded infield."),
    "Norisring": ("Norisring", "Nuremberg, Germany", "GER", "Very short street circuit formed by two hairpins and linked straights."),
    "Oschersleben": ("Motorsport Arena Oschersleben", "Oschersleben, Germany", "GER", "Compact technical lap with frequent low-speed direction changes."),
}


def read_points(path: Path) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        columns = line.split(",")
        points.append((float(columns[0]), float(columns[1])))
    if len(points) < 3:
        raise ValueError(f"{path.name}: not enough centerline points")
    return points


def sample(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    count = min(MAX_POINTS, len(points))
    result = [points[round(index * (len(points) - 1) / (count - 1))] for index in range(count)]
    if result[0] != result[-1]:
        result.append(result[0])
    return result


def normalize(points: list[tuple[float, float]]) -> list[list[float]]:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    width = max(xs) - min(xs)
    height = max(ys) - min(ys)
    scale = 0.9 / max(width, height)
    offset_x = (1 - width * scale) / 2
    offset_y = (1 - height * scale) / 2
    return [
        [round((x - min(xs)) * scale + offset_x, 4), round(1 - ((y - min(ys)) * scale + offset_y), 4)]
        for x, y in points
    ]


def length_km(points: list[tuple[float, float]]) -> float:
    closed = points if points[0] == points[-1] else points + [points[0]]
    return round(sum(math.dist(a, b) for a, b in zip(closed, closed[1:])) / 1000, 3)


def build(source: Path) -> list[dict[str, object]]:
    tracks_dir = source / "tracks"
    atlas = []
    for key, (name, location, code, description) in META.items():
        path = tracks_dir / f"{key}.csv"
        if not path.exists():
            raise FileNotFoundError(path)
        raw_points = read_points(path)
        atlas.append(
            {
                "key": key,
                "name": name,
                "location": location,
                "code": code,
                "description": description,
                "lengthKm": length_km(raw_points),
                "points": normalize(sample(raw_points)),
            }
        )
    return atlas


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="Path to a racetrack-database checkout")
    args = parser.parse_args()
    atlas = build(args.source.resolve())
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(atlas, ensure_ascii=True, separators=(",", ":"))
    OUTPUT.write_text(
        "// Generated by scripts/build_circuit_atlas.py; do not hand-edit.\n"
        "// Geometry: TUMFTM/racetrack-database (LGPL-3.0). See THIRD_PARTY_NOTICES.md.\n"
        "export type CircuitShape = {\n"
        "  key: string; name: string; location: string; code: string;\n"
        "  description: string; lengthKm: number; points: [number, number][];\n"
        "};\n\n"
        f"export const CIRCUITS: CircuitShape[] = {payload};\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"Wrote {len(atlas)} accurate circuit centerlines to {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
