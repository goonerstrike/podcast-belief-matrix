# 🚀 Quick Start Guide

## Setup (5 minutes)

```bash
# 1. Navigate to repository
cd ~/github/podcast-belief-extraction

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure API key
cp .env.example .env
# Edit .env and add: OPENAI_API_KEY=your-key-here
nano .env  # or use your preferred editor
```

## Run Your First Extraction (2 minutes)

```bash
# Extract beliefs from test sample (720 words, ~$0.05-0.10)
python run_multilevel_extraction.py --transcript tests/test_sample.txt --levels 1 --cheap-mode

# View results in formatted table
python view_rankings.py output/beliefs_linked_test_sample.csv
```

## Expected Output

### Terminal Output:
```
================================================================================
🌐 Multi-Level Podcast Belief Extraction Pipeline
================================================================================

⚙️  Configuration:
   Transcript: tests/test_sample.txt
   Episode ID: test_sample
   Model: gpt-4o-mini
   Cheap mode: Yes (1000 words)
   Levels: [1]

🚀 Starting multi-level extraction...
📊 Level 1: Processing 17 chunks...
✅ Found 3 beliefs out of 17 statements

📊 Summary:
   Total beliefs (raw): 3
   After deduplication: 3
   Final output: 3

💰 Cost:
   Total tokens: 2,456
   Total cost: $0.0534
```

### Generated Files:
- `output/beliefs_multilevel_test_sample.csv` - Raw beliefs
- `output/beliefs_deduplicated_test_sample.csv` - After deduplication
- `output/beliefs_linked_test_sample.csv` - Final with parent-child links
- W&B Dashboard - Interactive visualizations (if enabled)

## View Rankings

```bash
# See all beliefs with weights
python view_rankings.py output/beliefs_test_sample.csv

# Sort by conviction (strongest beliefs)
python view_rankings.py output/beliefs_test_sample.csv --sort conviction

# Top 5 beliefs
python view_rankings.py output/beliefs_test_sample.csv --top 5
```

### Sample Rankings Output:
```
╒═════════════╤════════════╤════════╤═══════════════════════╤════════════╤══════╤══════╤══════════════════════════════════╕
│ ID          │ Speaker    │   Rank │ Tier                  │ Category   │ Conv │ Stab │ Statement                        │
╞═════════════╪════════════╪════════╪═══════════════════════╪════════════╪══════╪══════╪══════════════════════════════════╡
│ b_0001      │ SPEAKER_B  │      9 │ Situational Opinions  │ political  │ 0.65 │ 0.40 │ He's definitely in a different...│
│ b_0002      │ SPEAKER_C  │      9 │ Situational Opinions  │ social     │ 0.70 │ 0.50 │ This is such a weird era for ...│
╘═════════════╧════════════╧════════╧═══════════════════════╧════════════╧══════╧══════╧══════════════════════════════════╛
```

## Next Steps

### Test on Your Own Transcript

```bash
# 1. Prepare your transcript (diarized format)
#    SPEAKER_A | 00:00:00 | 00:00:26 | Statement text...

# 2. Run cheap mode first (test with single-level)
python run_multilevel_extraction.py --transcript your_transcript.txt --levels 1 --cheap-mode

# 3. If satisfied, run full multi-level extraction
python run_multilevel_extraction.py --transcript your_transcript.txt --episode-id e_your_podcast_001

# Or single-level only
python run_multilevel_extraction.py --transcript your_transcript.txt --levels 1 --episode-id e_your_podcast_001
```

### Explore Advanced Features

```bash
# Filter high-conviction beliefs only
python view_rankings.py output/beliefs.csv --min-conviction 0.8

# Compare speakers
python view_rankings.py output/beliefs.csv --speaker SPEAKER_A
python view_rankings.py output/beliefs.csv --speaker SPEAKER_B

# Export Core Axioms only
python view_rankings.py output/beliefs.csv --tier "Core Axioms" --export core_axioms.csv

# Generate markdown report
python view_rankings.py output/beliefs.csv --format markdown > report.md
```

## Cost Management

| Scenario | Cost | Use Case |
|----------|------|----------|
| **Cheap test** (720 words) | $0.05-0.10 | Validate prompts, test pipeline |
| **Full podcast** (9k words) | $0.80-1.50 | Production extraction |
| **Batch 10 podcasts** | $8-15 | Large-scale analysis |

**Pro Tip**: Always run `--cheap-mode` first!

## Troubleshooting

### Missing API Key
```bash
# Check if .env exists
cat .env

# Should contain:
OPENAI_API_KEY=sk-...
```

### W&B Not Working
```bash
# Option 1: Disable W&B
python run_multilevel_extraction.py --transcript input.txt --levels 1 --no-wandb

# Option 2: Set W&B API key
echo "WANDB_API_KEY=your-wandb-key" >> .env
```

### Import Errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

## What's Next?

1. ✅ Extract beliefs from your podcasts
2. 📊 Analyze belief patterns across speakers
3. 🔍 Track belief evolution over episodes
4. 📈 Build belief hierarchies (parent-child relationships)
5. 🎯 Compare worldviews between guests

**Happy belief hunting! 🎙️**
