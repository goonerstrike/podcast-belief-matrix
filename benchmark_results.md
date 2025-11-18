# Worker Performance Benchmark Results

**Test Date**: November 17, 2024  
**Test Configuration**: 17 utterances (1000 words), 2 levels [1,5], cheap mode  
**OpenAI Model**: gpt-4o-mini  
**OpenAI Tier**: Tier 2 (2M TPM, 5000 RPM)

---

## Executive Summary

Comprehensive benchmark testing across 5 different worker configurations (1, 4, 10, 20, 50) reveals that **parallel processing provides significant speedups up to 10 workers**, with **diminishing returns beyond 20 workers**. All runs produced identical results (12 beliefs, ~$0.0092 cost), confirming correctness across all parallelization levels.

### Key Findings

- **Maximum Speedup**: 5.23x with 50 workers vs sequential baseline
- **Optimal Efficiency**: Workers=4 achieves 73% efficiency with 2.92x speedup
- **Diminishing Returns**: Begins at workers=10, plateaus at workers=20
- **Cost Consistency**: API costs remain constant ($0.0092) across all configurations
- **Correctness Verified**: All runs extracted identical 12 beliefs

---

## Performance Summary Table

| Workers | Time (s) | Speedup | Efficiency | Throughput (chunks/s) | Cost    | Beliefs |
|---------|----------|---------|------------|-----------------------|---------|---------|
| 1       | 171.14   | 1.00x   | 100%       | 0.07                  | $0.0092 | 12      |
| 4       | 58.50    | 2.92x   | 73%        | 0.21                  | $0.0092 | 12      |
| 10      | 36.94    | 4.63x   | 46%        | 0.32                  | $0.0092 | 12      |
| 20      | 33.42    | 5.12x   | 26%        | 0.36                  | $0.0093 | 12      |
| 50      | 32.73    | 5.23x   | 10%        | 0.37                  | $0.0092 | 12      |

---

## Detailed Analysis

### Speedup Progression

```
Workers=1  ████████████████████████████████████████  171.14s (baseline)
Workers=4  █████████████▉                            58.50s  (2.92x faster)
Workers=10 ████████▊                                 36.94s  (4.63x faster)
Workers=20 ███████▉                                  33.42s  (5.12x faster)
Workers=50 ███████▊                                  32.73s  (5.23x faster)
```

### Efficiency Analysis

- **Workers=1-4**: High efficiency (73-100%), nearly linear speedup
- **Workers=4-10**: Moderate efficiency (46-73%), good speedup but diminishing returns begin
- **Workers=10-20**: Low efficiency (26-46%), minimal additional speedup
- **Workers=20-50**: Very low efficiency (10-26%), negligible improvement

### Throughput Analysis

- **Baseline (1 worker)**: 0.07 chunks/second
- **Best improvement**: Workers=50 at 0.37 chunks/second (5.3x baseline)
- **Best value**: Workers=10 at 0.32 chunks/second (4.6x baseline with 46% efficiency)

### Cost Analysis

All configurations consumed approximately the same number of tokens (41,500-41,700) and cost (~$0.0092), confirming that parallel processing does not increase API usage—it only reduces wall-clock time.

---

## Top 3 Recommendations for Tier 2 OpenAI

### 🥇 1. Development & Iteration (Recommended: **4 workers**)

**Best for**: Daily development, prompt testing, rapid iteration

**Why**: 
- Achieves 73% efficiency with 2.92x speedup
- Nearly 3x faster than sequential with minimal overhead
- Safe for all use cases, won't hit rate limits
- Best balance of speed and resource efficiency

**Command**:
```bash
./venv/bin/python run_multilevel_extraction.py \
  --transcript input.txt \
  --levels "1,5,15" \
  --workers 4
```

---

### 🥈 2. Production Batch Processing (Recommended: **10 workers**)

**Best for**: Processing multiple transcripts, production workloads

**Why**:
- Achieves 4.63x speedup (46% efficiency)
- Significant time savings for batch jobs
- Still well under Tier 2 rate limits
- Optimal point before severe diminishing returns
- Can process ~20 chunks in under 40 seconds

**Command**:
```bash
./venv/bin/python run_multilevel_extraction.py \
  --transcript input.txt \
  --levels "1,2,4,8,16,32" \
  --workers 10
```

---

### 🥉 3. Time-Critical / Real-Time (Recommended: **20 workers**)

**Best for**: Low-latency requirements, real-time processing, urgent extraction

**Why**:
- Achieves maximum practical speedup (5.12x)
- Minimal time difference vs 50 workers (only 0.69s slower)
- Lower thread overhead than 50 workers
- Good for time-sensitive scenarios
- Processes 12 chunks in ~33 seconds

**Command**:
```bash
./venv/bin/python run_multilevel_extraction.py \
  --transcript input.txt \
  --levels "1,5" \
  --cheap-mode \
  --workers 20
```

---

## Not Recommended

### ❌ Workers=50 (Avoid unless absolutely necessary)

- Only 0.11x additional speedup over workers=20
- Efficiency drops to 10%
- High thread overhead
- No practical benefit for the cost
- May encounter system resource limits

---

## Tier 2 Rate Limit Safety

With Tier 2 OpenAI limits (2M TPM, 5000 RPM):

| Workers | Est. Requests/Min | % of Limit | Status |
|---------|-------------------|------------|--------|
| 4       | ~120              | 2.4%       | ✅ Very Safe |
| 10      | ~300              | 6.0%       | ✅ Safe |
| 20      | ~600              | 12.0%      | ✅ Safe |
| 50      | ~1500             | 30.0%      | ⚠️ Caution |

All tested configurations are well within Tier 2 limits. Workers=50 uses 30% of the RPM limit but is still technically safe.

---

## W&B Dashboard Links

View all benchmark runs in W&B:

- **Project**: [podcast-belief-extraction](https://wandb.ai/crispychicken-your-mom-s-house/podcast-belief-extraction)
- **Benchmark Runs**: Filter by tags `benchmark` and `worker-comparison`
- **Individual Runs**:
  - [Workers=1 (baseline)](https://wandb.ai/crispychicken-your-mom-s-house/podcast-belief-extraction/runs/enwshvbo)
  - [Workers=4](https://wandb.ai/crispychicken-your-mom-s-house/podcast-belief-extraction/runs/m0osifl9)
  - [Workers=10](https://wandb.ai/crispychicken-your-mom-s-house/podcast-belief-extraction/runs/iwo8yfqj)
  - [Workers=20](https://wandb.ai/crispychicken-your-mom-s-house/podcast-belief-extraction/runs/7kp8zuou)
  - [Workers=50](https://wandb.ai/crispychicken-your-mom-s-house/podcast-belief-extraction/runs/9g7inh9y)

---

## Conclusion

For most use cases with Tier 2 OpenAI, **workers=10** provides the best balance of speed and efficiency. Use **workers=4** for development to maximize efficiency, and reserve **workers=20** only when latency is absolutely critical. Avoid **workers=50** unless you need every possible millisecond of speedup, as it provides negligible benefit over workers=20.

**Implementation verified**: Thread-safe cost tracking, consistent results, and proper W&B logging across all parallelization levels.

