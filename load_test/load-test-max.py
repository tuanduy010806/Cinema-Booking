"""Run progressively larger Locust stages and stop at the first unsafe stage.

This finds an operational load limit; it does not deliberately crash the host.
Run from the project checkout after starting FastAPI and PostgreSQL.

Required environment:
    BOOKING_ADMIN_TOKEN (or BOOKING_ACCESS_TOKEN): JWT for an ADMIN account

Optional environment:
    BOOKING_MOVIE_ID: existing movie ID (default: 1)
    BOOKING_TOTAL_SEATS: seats on each generated test showtime (default: 500)
    BOOKING_SEAT_START: first direct-booking seat (default: 1)
"""

from __future__ import annotations

import argparse
import csv
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean

import psutil
import psycopg
import requests
from dotenv import load_dotenv
from sqlalchemy.engine import make_url


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOCUST_SCENARIO = PROJECT_ROOT / "load_test" / "load_test.py"
RESULT_ROOT = PROJECT_ROOT / "benchmark_results" / "load_test_max"
load_dotenv(PROJECT_ROOT / ".env")


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be a positive integer")
    return parsed


class SystemMonitor:
    """Sample whole-machine CPU/RAM and PostgreSQL activity once per second."""

    def __init__(self, interval: float, cpu_limit: float, cpu_limit_seconds: int):
        self.interval = interval
        self.cpu_limit = cpu_limit
        self.cpu_limit_seconds = cpu_limit_seconds
        self.samples: list[dict[str, float]] = []
        self.stop_event = threading.Event()
        self.cpu_limit_hit = threading.Event()
        self.thread: threading.Thread | None = None
        self.initial_ram_mb = psutil.virtual_memory().used / (1024 * 1024)
        self._cpu_high_since: float | None = None

    def _connect_db(self):
        database_url = os.getenv("DATABASE_URL", "").strip()
        if not database_url:
            return None
        url = make_url(database_url)
        return psycopg.connect(
            host=url.host or "127.0.0.1",
            port=url.port or 5432,
            dbname=url.database,
            user=url.username,
            password=url.password,
            autocommit=True,
        )

    @staticmethod
    def _database_stats(conn) -> tuple[int, int, int]:
        if conn is None:
            return 0, 0, 0
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT count(*) FROM pg_stat_activity "
                    "WHERE datname = current_database()"
                )
                active = int(cur.fetchone()[0])
                cur.execute(
                    "SELECT xact_commit, xact_rollback "
                    "FROM pg_stat_database WHERE datname = current_database()"
                )
                commits, rollbacks = cur.fetchone()
            return active, int(commits), int(rollbacks)
        except Exception:
            return 0, 0, 0

    def _run(self) -> None:
        conn = None
        try:
            conn = self._connect_db()
        except Exception:
            pass

        started = time.monotonic()
        psutil.cpu_percent(interval=None)
        while not self.stop_event.is_set():
            cpu = psutil.cpu_percent(interval=self.interval)
            now = time.monotonic()
            memory = psutil.virtual_memory()
            active, commits, rollbacks = self._database_stats(conn)
            ram_mb = memory.used / (1024 * 1024)
            self.samples.append({
                "elapsed_seconds": now - started,
                "cpu_percent": cpu,
                "ram_used_mb": ram_mb,
                "ram_growth_mb": max(0.0, ram_mb - self.initial_ram_mb),
                "db_active_connections": active,
                "db_commits": commits,
                "db_rollbacks": rollbacks,
            })

            if cpu >= self.cpu_limit:
                if self._cpu_high_since is None:
                    self._cpu_high_since = now
                elif now - self._cpu_high_since >= self.cpu_limit_seconds:
                    self.cpu_limit_hit.set()
            else:
                self._cpu_high_since = None

        if conn is not None:
            conn.close()

    def start(self) -> None:
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()
        if self.thread is not None:
            self.thread.join()


def create_fresh_showtime(
    host: str, admin_token: str, movie_id: int, seats: int
) -> int:
    start_time = (
        datetime.now(timezone.utc) + timedelta(days=30)
    ).replace(tzinfo=None).isoformat()
    response = requests.post(
        f"{host.rstrip('/')}/api/v1/showtimes",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"movie_id": movie_id, "start_time": start_time, "total_seats": seats},
        timeout=20,
    )
    response.raise_for_status()
    return int(response.json()["id"])


def stop_reason_for(
    result: dict[str, float | int | str],
    args: argparse.Namespace,
) -> str | None:
    reasons = []
    if float(result["error_rate_percent"]) > args.max_error_percent:
        reasons.append(
            f"error rate {result['error_rate_percent']:.2f}% "
            f"> {args.max_error_percent:.2f}%"
        )
    if float(result["p95_ms"]) >= args.max_p95_ms:
        reasons.append(
            f"p95 {result['p95_ms']:.0f} ms >= {args.max_p95_ms:.0f} ms"
        )
    if result["stop_reason"]:
        reasons.append(str(result["stop_reason"]))
    return "; ".join(reasons) if reasons else None


def read_aggregated_stats(prefix: Path) -> dict[str, float | int] | None:
    stats_file = Path(f"{prefix}_stats.csv")
    if not stats_file.exists():
        return None
    with stats_file.open("r", newline="", encoding="utf-8") as file:
        rows = csv.DictReader(file)
        total = next((row for row in rows if row.get("Name") == "Aggregated"), None)
    if total is None:
        return None

    requests_count = int(float(total.get("Request Count", 0) or 0))
    failures = int(float(total.get("Failure Count", 0) or 0))
    return {
        "requests": requests_count,
        "failures": failures,
        "error_rate_percent": failures / requests_count * 100 if requests_count else 0.0,
        "requests_per_second": float(total.get("Requests/s", 0) or 0),
        "average_ms": float(total.get("Average Response Time", 0) or 0),
        "p50_ms": float(total.get("50%", 0) or 0),
        "p95_ms": float(total.get("95%", 0) or 0),
        "p99_ms": float(total.get("99%", 0) or 0),
    }


def monitor_summary(monitor: SystemMonitor) -> dict[str, float | int]:
    if not monitor.samples:
        return {
            "cpu_average_percent": 0.0,
            "cpu_peak_percent": 0.0,
            "ram_peak_mb": 0.0,
            "ram_growth_peak_mb": 0.0,
            "db_peak_connections": 0,
        }
    return {
        "cpu_average_percent": mean(row["cpu_percent"] for row in monitor.samples),
        "cpu_peak_percent": max(row["cpu_percent"] for row in monitor.samples),
        "ram_peak_mb": max(row["ram_used_mb"] for row in monitor.samples),
        "ram_growth_peak_mb": max(row["ram_growth_mb"] for row in monitor.samples),
        "db_peak_connections": int(max(row["db_active_connections"] for row in monitor.samples)),
    }


def run_stage(users: int, stage_number: int, args: argparse.Namespace,
              admin_token: str, movie_id: int, seats: int, seat_start: int) -> dict:
    # Conservatively reserve two unique seats per configured Locust user.
    if seat_start + 2 * users > seats:
        raise ValueError(
            f"Stage {users} requires at least {seat_start + 2 * users} seats; "
            f"configured capacity is {seats}. Increase --seats or lower --stages."
        )

    showtime_id = create_fresh_showtime(args.host, admin_token, movie_id, seats)
    stage_dir = RESULT_ROOT / f"stage_{stage_number:02d}_{users}_users"
    stage_dir.mkdir(parents=True, exist_ok=True)
    csv_prefix = stage_dir / "locust"
    log_path = stage_dir / "locust.log"

    env = os.environ.copy()
    env.update({
        "BOOKING_ADMIN_TOKEN": admin_token,
        "BOOKING_ACCESS_TOKEN": admin_token,
        "BOOKING_SHOWTIME_ID": str(showtime_id),
        "BOOKING_TOTAL_SEATS": str(seats),
        "BOOKING_MOVIE_ID": str(movie_id),
        "BOOKING_SEAT_START": str(seat_start),
    })

    command = [
        sys.executable, "-m", "locust",
        "-f", str(LOCUST_SCENARIO),
        "--host", args.host,
        "--headless",
        "-u", str(users),
        "-r", str(args.spawn_rate),
        "-t", args.duration,
        "--csv", str(csv_prefix),
        "--csv-full-history",
        "--only-summary",
    ]

    monitor = SystemMonitor(
        interval=1.0,
        cpu_limit=args.cpu_limit_percent,
        cpu_limit_seconds=args.cpu_limit_seconds,
    )
    health_failures = 0
    stop_reason = ""
    monitor.start()
    started = time.monotonic()

    with log_path.open("w", encoding="utf-8") as log_file:
        process = subprocess.Popen(
            command,
            cwd=str(PROJECT_ROOT),
            env=env,
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )
        while process.poll() is None:
            if monitor.cpu_limit_hit.is_set():
                stop_reason = (
                    f"whole-machine CPU >= {args.cpu_limit_percent:.0f}% "
                    f"for {args.cpu_limit_seconds}s"
                )
                process.terminate()
                break

            try:
                health = requests.get(f"{args.host.rstrip('/')}/docs", timeout=2)
                health.raise_for_status()
                health_failures = 0
            except requests.RequestException:
                health_failures += 1
                if health_failures >= args.health_failures:
                    stop_reason = f"API health check failed {health_failures} times in a row"
                    process.terminate()
                    break
            time.sleep(1)

        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            stop_reason = stop_reason or "Locust did not stop cleanly"

    elapsed_seconds = time.monotonic() - started
    monitor.stop()

    stats = read_aggregated_stats(csv_prefix) or {
        "requests": 0,
        "failures": 0,
        "error_rate_percent": 0.0,
        "requests_per_second": 0.0,
        "average_ms": 0.0,
        "p50_ms": 0.0,
        "p95_ms": 0.0,
        "p99_ms": 0.0,
    }
    resources = monitor_summary(monitor)
    row = {
        "stage": stage_number,
        "users": users,
        "showtime_id": showtime_id,
        "elapsed_seconds": round(elapsed_seconds, 1),
        **stats,
        **resources,
        "locust_exit_code": process.returncode,
        "stop_reason": stop_reason,
        "results_directory": str(stage_dir),
    }

    monitor_file = stage_dir / "system_monitor.csv"
    if monitor.samples:
        with monitor_file.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=list(monitor.samples[0].keys()))
            writer.writeheader()
            writer.writerows(monitor.samples)
    return row


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ramp Locust load in stages and stop at configured safety thresholds."
    )
    parser.add_argument("--host", default=os.getenv("LOAD_TEST_HOST", "http://127.0.0.1:8000"))
    parser.add_argument("--stages", default="50,75,100,125,150,175,200")
    parser.add_argument("--duration", default="90s", help="Duration per stage, e.g. 90s or 2m")
    parser.add_argument("--spawn-rate", type=positive_int, default=5)
    parser.add_argument("--seats", type=positive_int, default=int(os.getenv("BOOKING_TOTAL_SEATS", "500")))
    parser.add_argument("--movie-id", type=positive_int, default=int(os.getenv("BOOKING_MOVIE_ID", "1")))
    parser.add_argument("--seat-start", type=positive_int, default=int(os.getenv("BOOKING_SEAT_START", "1")))
    parser.add_argument("--max-error-percent", type=float, default=1.0)
    parser.add_argument("--max-p95-ms", type=positive_int, default=2000)
    parser.add_argument("--cpu-limit-percent", type=float, default=90.0)
    parser.add_argument("--cpu-limit-seconds", type=positive_int, default=15)
    parser.add_argument("--health-failures", type=positive_int, default=3)
    args = parser.parse_args()

    admin_token = os.getenv("BOOKING_ADMIN_TOKEN", os.getenv("BOOKING_ACCESS_TOKEN", "")).strip()
    if not admin_token:
        parser.error("set BOOKING_ADMIN_TOKEN (or BOOKING_ACCESS_TOKEN) to an ADMIN JWT")
    if not LOCUST_SCENARIO.exists():
        parser.error(f"Locust scenario not found: {LOCUST_SCENARIO}")

    try:
        stages = [positive_int(item.strip()) for item in args.stages.split(",") if item.strip()]
    except argparse.ArgumentTypeError as exc:
        parser.error(f"invalid --stages: {exc}")
    if not stages:
        parser.error("--stages must contain at least one user count")
    if args.max_error_percent < 0 or args.cpu_limit_percent <= 0:
        parser.error("error and CPU thresholds must be positive")

    RESULT_ROOT.mkdir(parents=True, exist_ok=True)
    print(f"Host: {args.host}")
    print(f"Logical CPU cores: {os.cpu_count()}")
    print(f"Stages: {stages}; duration per stage: {args.duration}")
    print(
        "Stop thresholds: error rate > "
        f"{args.max_error_percent:.2f}%, p95 >= {args.max_p95_ms} ms, "
        f"CPU >= {args.cpu_limit_percent:.0f}% for {args.cpu_limit_seconds}s, "
        f"or {args.health_failures} failed health checks."
    )

    results: list[dict] = []
    for index, users in enumerate(stages, start=1):
        print(f"\n=== Stage {index}/{len(stages)}: {users} virtual users ===")
        row = run_stage(
            users=users,
            stage_number=index,
            args=args,
            admin_token=admin_token,
            movie_id=args.movie_id,
            seats=args.seats,
            seat_start=args.seat_start,
        )
        results.append(row)

        print(
            f"requests={row['requests']}, failures={row['failures']} "
            f"({row['error_rate_percent']:.2f}%), "
            f"RPS={row['requests_per_second']:.2f}, "
            f"p95={row['p95_ms']:.0f} ms, "
            f"CPU peak={row['cpu_peak_percent']:.1f}%, "
            f"RAM peak={row['ram_peak_mb']:.0f} MB, "
            f"DB connections peak={row['db_peak_connections']}"
        )

        reason = stop_reason_for(row, args)
        if reason:
            row["stop_reason"] = "; ".join(filter(None, [row["stop_reason"], reason]))
            print(f"Stopping before the next stage: {row['stop_reason']}")
            break
        if row["requests"] == 0:
            row["stop_reason"] = "No aggregated Locust stats were produced"
            print("Stopping: Locust did not produce an aggregated stats row.")
            break

    summary_file = RESULT_ROOT / "summary.csv"
    if results:
        with summary_file.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=list(results[0].keys()))
            writer.writeheader()
            writer.writerows(results)

    print(f"\nSummary: {summary_file}")
    print(f"Stage CSV/log files: {RESULT_ROOT}")
    print("A fresh showtime and a separate results directory were used for each stage.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
