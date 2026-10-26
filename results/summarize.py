"""Recompute mean/min/max per scenario from latency-samples.csv (standard library only)."""
import csv, statistics, collections

rows = collections.defaultdict(list)
with open("latency-samples.csv", newline="") as f:
    for r in csv.DictReader(f):
        rows[r["scenario"]].append(float(r["rtt_ms"]))

base = statistics.mean(rows["1_native_mpls"])
print(f"{'scenario':<20}{'n':>3}{'mean':>8}{'min':>8}{'max':>8}{'stdev':>8}{'vs S1':>9}")
for name, v in rows.items():
    m = statistics.mean(v)
    print(f"{name:<20}{len(v):>3}{m:>8.1f}{min(v):>8.1f}{max(v):>8.1f}{statistics.stdev(v):>8.1f}{(m-base)/base*100:>+8.1f}%")
print("\nOnly 5 samples per scenario: indicative values, no significance test.")
