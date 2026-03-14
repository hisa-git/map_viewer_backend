import csv
import logging
import statistics
import sys
import time
from pathlib import Path

import fiona
import geopandas as gpd


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
LOG_PATH = BASE_DIR / "benchmark.log"
CSV_PATH = BASE_DIR / "benchmark_results.csv"

DATASETS = {
    "geojson":    DATA_DIR / "buildings.geojson",
    "flatgeobuf": DATA_DIR / "buildings.fgb",
    "geopackage": DATA_DIR / "buildings.gpkg",
}

BBOXES = {
    "kyiv_district": (3338308, 6404372, 3348308, 6414372),
    "kyiv_city":     (3300000, 6370000, 3360000, 6430000),
    "ukraine":       (2438917, 5525517, 4476759, 6867524),
}

RUNS_GEOJSON   = 3
WARMUP_GEOJSON = 1
RUNS_INDEXED   = 8
WARMUP_INDEXED = 2

GEOJSON_COMBOS = {("geojson", bb) for bb in ["kyiv_district", "kyiv_city", "ukraine"]}


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("benchmark")
    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s",
                            datefmt="%Y-%m-%d %H:%M:%S")

    fh = logging.FileHandler(LOG_PATH, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


log = setup_logging()


def _proc_stat_idle_total():
    with open("/proc/stat", encoding="ascii") as f:
        parts = list(map(int, f.readline().split()[1:]))
    return parts[3], sum(parts)


def cpu_delta_percent(before: tuple, after: tuple) -> float:
    idle  = after[0] - before[0]
    total = after[1] - before[1]
    if total == 0:
        return 0.0
    return 100.0 * (1.0 - idle / total)


def rss_kb() -> int:
    with open("/proc/self/status", encoding="ascii") as f:
        for line in f:
            if line.startswith("VmRSS:"):
                return int(line.split()[1])
    return 0


def io_read_bytes() -> int:
    with open("/proc/self/io", encoding="ascii") as f:
        for line in f:
            if line.startswith("read_bytes:"):
                return int(line.split()[1])
    return 0


def single_run(path: Path, bbox: tuple) -> dict:
    cpu_before = _proc_stat_idle_total()
    mem_before = rss_kb()
    io_before  = io_read_bytes()

    t0  = time.perf_counter()
    gdf = gpd.read_file(str(path), bbox=bbox)
    elapsed = time.perf_counter() - t0

    cpu_after = _proc_stat_idle_total()
    mem_after = rss_kb()
    io_after  = io_read_bytes()

    return {
        "time_s":       elapsed,
        "cpu_pct":      cpu_delta_percent(cpu_before, cpu_after),
        "delta_rss_kb": mem_after - mem_before,
        "read_bytes":   io_after  - io_before,
        "n_features":   len(gdf),
    }


def iqr_bounds(values: list[float]) -> tuple[float, float]:
    s = sorted(values)
    n = len(s)
    q1 = statistics.median(s[:n // 2])
    q3 = statistics.median(s[n - n // 2:])
    iqr = q3 - q1
    return q1 - 1.5 * iqr, q3 + 1.5 * iqr


def aggregate(metrics: list[dict]) -> dict:
    times = [m["time_s"] for m in metrics]

    if len(times) >= 4:
        lo, hi = iqr_bounds(times)
        valid    = [m for m in metrics if lo <= m["time_s"] <= hi]
        excluded = len(metrics) - len(valid)
        if excluded:
            log.debug("  Виявлено та виключено аномальних вимірювань: %d з %d",
                      excluded, len(metrics))
    else:
        valid    = metrics
        excluded = 0

    def _mean(key):
        return statistics.mean(m[key] for m in valid)

    def _stdev(key):
        vals = [m[key] for m in valid]
        return statistics.stdev(vals) if len(vals) > 1 else 0.0

    def _median(key):
        return statistics.median(m[key] for m in valid)

    def _pct(key, p):
        vals = sorted(m[key] for m in valid)
        idx = max(0, min(len(vals) - 1, int(len(vals) * p / 100)))
        return vals[idx]

    valid_times = sorted(m["time_s"] for m in valid)

    return {
        "n_valid":        len(valid),
        "n_excluded":     excluded,
        "mean_time_s":    _mean("time_s"),
        "stdev_time_s":   _stdev("time_s"),
        "median_time_s":  _median("time_s"),
        "p10_time_s":     _pct("time_s", 10),
        "p90_time_s":     _pct("time_s", 90),
        "min_time_s":     valid_times[0],
        "max_time_s":     valid_times[-1],
        "mean_cpu_pct":   _mean("cpu_pct"),
        "mean_rss_kb":    _mean("delta_rss_kb"),
        "mean_io_bytes":  _mean("read_bytes"),
        "n_features":     valid[0]["n_features"] if valid else 0,
    }


def log_file_info():
    log.info("=" * 68)
    log.info("Характеристики вхідних файлів")
    log.info("=" * 68)
    for name, path in DATASETS.items():
        if not path.exists():
            log.warning("  %s — файл не знайдено: %s", name, path)
            continue
        size_mb = path.stat().st_size / 1024 / 1024
        try:
            with fiona.open(str(path)) as src:
                count  = len(src)
                bounds = src.bounds
                try:
                    crs = src.crs.to_epsg() or str(src.crs)
                except AttributeError:
                    crs = src.crs.get("init", str(src.crs)) if src.crs else "невідомо"
        except Exception as exc:
            count = bounds = crs = f"помилка відкриття: {exc}"
        log.info("  %-12s  %.2f МБ  об'єктів=%s  межі=%s  CRS=EPSG:%s",
                 name, size_mb, count, bounds, crs)
    log.info("=" * 68)


FIELDNAMES = [
    "dataset", "bbox",
    "runs_total", "n_valid", "n_excluded",
    "mean_time_s", "stdev_time_s", "median_time_s",
    "p10_time_s", "p90_time_s", "min_time_s", "max_time_s",
    "mean_cpu_pct", "mean_rss_kb", "mean_io_bytes",
    "n_features",
]


def save_csv(rows: list[dict]):
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    log.debug("  Результати збережено: %s (%d записів)", CSV_PATH, len(rows))


def run_benchmark():
    log.info("Початок експерименту")
    log.info("Файл журналу:     %s", LOG_PATH)
    log.info("Файл результатів: %s", CSV_PATH)

    log_file_info()

    rows: list[dict] = []
    total      = len(DATASETS) * len(BBOXES)
    combo_idx  = 0
    wall_start = time.perf_counter()

    for dataset, path in DATASETS.items():
        if not path.exists():
            log.error("Формат %s пропущено — файл не знайдено", dataset)
            continue

        for bbox_name, bbox in BBOXES.items():
            combo_idx += 1
            combo = (dataset, bbox_name)
            if combo in GEOJSON_COMBOS:
                runs, warmup = RUNS_GEOJSON, WARMUP_GEOJSON
            else:
                runs, warmup = RUNS_INDEXED, WARMUP_INDEXED

            log.info("-" * 68)
            log.info("[%d/%d]  формат=%-12s  діапазон=%-16s  вимірювань=%d  стабілізацій=%d",
                     combo_idx, total, dataset, bbox_name, runs, warmup)

            log.info("  Стабілізаційні зчитування (%d шт.) ...", warmup)
            for w in range(warmup):
                t0 = time.perf_counter()
                gpd.read_file(str(path), bbox=bbox)
                log.debug("    стабілізація %d/%d  %.3f с", w + 1, warmup,
                          time.perf_counter() - t0)

            log.info("  Вимірювальні зчитування (%d шт.) ...", runs)
            metrics: list[dict] = []
            for i in range(runs):
                m = single_run(path, bbox)
                metrics.append(m)
                log.info("    вимірювання %2d/%d  час=%.4f с  CPU=%.1f%%  "
                         "RSS=%+d кБ  В/В=%d б  об'єктів=%d",
                         i + 1, runs,
                         m["time_s"], m["cpu_pct"],
                         m["delta_rss_kb"], m["read_bytes"], m["n_features"])

            agg = aggregate(metrics)
            row = {
                "dataset":    dataset,
                "bbox":       bbox_name,
                "runs_total": runs,
                **agg,
            }
            rows.append(row)
            save_csv(rows)

            log.info("  Статистика:  середнє=%.4f±%.4f с  медіана=%.4f с  "
                     "P10=%.4f с  P90=%.4f с",
                     agg["mean_time_s"], agg["stdev_time_s"],
                     agg["median_time_s"], agg["p10_time_s"], agg["p90_time_s"])
            log.info("  Прийнято вимірювань: %d/%d  CPU=%.1f%%  "
                     "В/В=%.0f кБ  RSS=%.0f кБ",
                     agg["n_valid"], runs,
                     agg["mean_cpu_pct"],
                     agg["mean_io_bytes"] / 1024,
                     agg["mean_rss_kb"])

    wall_total = time.perf_counter() - wall_start
    log.info("=" * 68)
    log.info("Експеримент завершено.  Тривалість: %.1f хв (%.0f с)",
             wall_total / 60, wall_total)
    log.info("Результати: %s", CSV_PATH)
    log.info("Журнал:     %s", LOG_PATH)
    log.info("=" * 68)

    log.info("ЗВЕДЕНІ РЕЗУЛЬТАТИ (середній час зчитування, с):")
    log.info("  %-12s  %-16s  %10s  %10s  %10s",
             "формат", "діапазон", "середнє", "медіана", "об'єктів")
    for r in rows:
        log.info("  %-12s  %-16s  %10.4f  %10.4f  %10d",
                 r["dataset"], r["bbox"],
                 r["mean_time_s"], r["median_time_s"], r["n_features"])

    return rows


if __name__ == "__main__":
    run_benchmark()