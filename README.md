# 🎙️ Podcast Belief Extraction Pipeline

Extract and classify belief statements from diarized podcast transcripts using a 30-question belief matrix and AI-powered classification.

## 🎯 Features

- **Multi-Level Extraction**: Process transcripts at 10 abstraction levels to capture beliefs across all scales
- **Two-Stage Classification**: Filter statements, then classify beliefs in detail
- **30-Question Belief Matrix**: Comprehensive framework for belief analysis
- **Hierarchical Belief Tiers**: From Core Axioms to Casual Jokes
- **Advanced Analytics**: Derived metrics, graph analysis, and auto-generated insights
- **Interactive Dashboard**: Web-based analytics dashboard with Plotly visualizations
- **W&B Integration**: Full experiment tracking and visualization
- **Cost-Optimized**: Two-stage approach saves ~60% vs single-stage
- **Cheap Mode**: Test on first 1000 words before processing full transcripts

## 📊 Belief Matrix Schema

### Core Fields

| Column | Description | Example |
|--------|-------------|---------|
| `belief_id` | Unique identifier | b_0001 |
| `speaker_id` | Speaker from transcript | SPEAKER_A |
| `episode_id` | Episode identifier | e_jre_2404 |
| `timestamp` | Time in transcript | 00:12:34 |
| `statement_text` | The belief statement | "No one is coming to save you..." |
| `importance` | Tier ranking (1-10) | 2 |
| `tier_name` | Belief tier | Worldview Pillars |
| `category` | Domain category | moral |
| `conviction_score` | Speaker conviction (0-1) | 0.96 |
| `stability_score` | Long-term stability (0-1) | 0.92 |
| `parent_hint` | Higher-level belief | "Individuals are solely responsible..." |
| `parent_belief_id` | Parent belief ID | NULL or b_0001 |

### Multi-Level Fields (NEW!)

| Column | Description | Example |
|--------|-------------|---------|
| `discovery_level` | Which level found this belief | 3 |
| `chunk_id` | Chunk identifier | L3_C0012 |
| `chunk_size` | Utterances in chunk | 4 |
| `reinforcement_count` | Times found across levels | 3 |
| `reinforcement_levels` | Levels that found it | "1,2,4" |
| `duplicate_group_id` | Duplicate cluster ID | dup_0005 |

### Derived Metrics (Analytics)

| Metric | Formula | Purpose |
|--------|---------|---------|
| `belief_strength` | conviction × stability | Overall robustness |
| `foundational_weight` | (11 - importance) × conviction | How foundational |
| `rigidity_score` | conviction × stability × (11 - importance) | Resistance to change |
| `certainty_gap` | conviction - stability | Potential instability |
| `influence_score` | child_count × conviction | Impact on other beliefs |

## 🏗️ Belief Tiers (Hierarchical)

1. **Core Axioms** - Foundational, cross-domain, highly defended
2. **Worldview Pillars** - Big-picture moral/political/economic frames
3. **Identity-Defining Values** - "This is who I am"
4. **Meta-Principles** - Rules for choosing/updating beliefs
5. **Cross-Domain Rules & Heuristics** - Applied across contexts
6. **Stable Domain Beliefs** - Consistent stance within one topic
7. **Repeated Strategies & Playbooks** - Endorsed tactics
8. **Concrete Claims & Predictions** - Testable assertions
9. **Situational Opinions** - Context-specific views
10. **Loose Takes / Jokes / Vibes** - Casual, exploratory

## 🚀 Quick Start

### Installation

```bash
# Clone repository
cd ~/github
git clone [repository-url]
cd podcast-belief-extraction

# Set up environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### Basic Usage

#### Single-Level Extraction (Original)

```bash
# Extract beliefs from transcript
python run_extraction.py --transcript tests/test_sample.txt --episode-id e_test_001

# Cheap mode (test on first 1000 words)
python run_extraction.py --transcript input.txt --cheap-mode

# Skip W&B logging
python run_extraction.py --transcript input.txt --no-wandb

# Custom output format
python run_extraction.py --transcript input.txt --format json --output beliefs.json
```

#### Multi-Level Extraction (NEW!)

Process transcripts at multiple abstraction levels to capture beliefs that only emerge at different scales:

```bash
# Multi-level extraction with default exponential levels [1,2,4,8,16,32,64,128,256,512]
python run_multilevel_extraction.py --transcript input.txt --episode-id e_001

# Test with cheap mode and limited levels
python run_multilevel_extraction.py --transcript input.txt --cheap-mode --levels "1,2,4,8"

# Skip deduplication or linking steps
python run_multilevel_extraction.py --transcript input.txt --no-dedup
python run_multilevel_extraction.py --transcript input.txt --no-linking

# Adjust deduplication threshold
python run_multilevel_extraction.py --transcript input.txt --dedup-threshold 0.9
```

**Outputs**:
- `beliefs_multilevel_*.csv` - Raw beliefs from all levels
- `beliefs_deduplicated_*.csv` - Merged beliefs with reinforcement scores
- `beliefs_linked_*.csv` - Final output with parent-child relationships

#### Belief Analysis & Insights (NEW!)

Analyze extracted beliefs to calculate derived metrics and generate insights:

```bash
# Analyze beliefs and show summary
python analyze_beliefs.py output/beliefs_linked_e_001.csv

# Show keystone beliefs and patterns
python analyze_beliefs.py output/beliefs.csv --show-keystone 10 --show-patterns

# Export metrics and insights
python analyze_beliefs.py output/beliefs.csv --export-metrics --export-report --export-graph

# Custom output directory
python analyze_beliefs.py output/beliefs.csv --export-metrics --output-dir results/
```

**Outputs**:
- `belief_metrics_*.csv` - Beliefs with all derived metrics
- `belief_insights_*.md` - Auto-generated markdown report
- `belief_graph_*.json` - Graph structure for visualization
- `belief_graph_*.graphml` - For Gephi/Cytoscape analysis

#### Interactive Dashboard (NEW!)

Open `dashboard_analytics.html` in your browser and drag/drop any beliefs CSV to explore:
- Real-time metric calculations
- Interactive Plotly visualizations
- Keystone belief identification
- Vulnerability detection
- Distribution analysis

### Viewing Rankings with Weights

```bash
# View formatted rankings table
python view_rankings.py output/beliefs_episode.csv

# Sort by conviction (strongest beliefs first)
python view_rankings.py output/beliefs_episode.csv --sort conviction

# Sort by stability
python view_rankings.py output/beliefs_episode.csv --sort stability

# Show only top 10 beliefs
python view_rankings.py output/beliefs_episode.csv --top 10

# Filter by speaker
python view_rankings.py output/beliefs_episode.csv --speaker SPEAKER_A

# Filter by tier and category
python view_rankings.py output/beliefs_episode.csv --tier "Core Axioms" --category political

# Export filtered results
python view_rankings.py output/beliefs_episode.csv --min-conviction 0.8 --export high_conviction.csv

# Output as markdown table
python view_rankings.py output/beliefs_episode.csv --format markdown
```

### Input Format

Transcripts must be diarized in this format:
```
SPEAKER_A | 00:00:00 | 00:00:26 | Statement text here...
SPEAKER_B | 00:00:26 | 00:00:35 | Another statement...
```

## 💰 Cost Estimates

### Single-Level Extraction (Original)

**Cheap Test Mode (720 words)**
- Stage 1 filters: ~15 statements × $0.0003 = $0.0045
- Stage 2 classifies: ~5 beliefs × $0.01 = $0.05
- **Total: ~$0.05-0.10**

**Full Podcast (9,000 words)**
- Stage 1 filters: ~200 statements × $0.0003 = $0.06
- Stage 2 classifies: ~60 beliefs × $0.01 = $0.60
- **Total: ~$0.80-1.50**

### Multi-Level Extraction (10 Levels)

**Full Podcast (9,000 words) × 10 Levels**
- 10 levels × ~$0.07-0.10 per level
- **Total: ~$0.70-1.00 per episode**

**Cost Efficiency**:
- Each level processes different chunk sizes
- Deduplication identifies beliefs found at multiple levels
- Analytics phase is negligible (local computation)

### Cost Savings Strategy
1. Always use **cheap mode** first to validate prompts
2. Two-stage filtering eliminates ~70% of statements
3. Stage 1 prompt is short and cheap
4. Stage 2 only runs on confirmed beliefs
5. For multi-level: test with `--levels "1,2,4"` before full 10-level run

## 📊 W&B Dashboard

The pipeline logs comprehensive metrics and visualizations to Weights & Biases:

### Metrics Tracked
- Total beliefs extracted
- Beliefs per speaker
- Average conviction/stability scores
- Token usage and costs
- Processing time

### Visualizations
- **Tier Distribution** - Bar chart of beliefs by tier
- **Category Distribution** - Pie chart of belief categories
- **Speaker Comparison** - Beliefs count + avg conviction
- **Conviction vs Stability** - Scatter plot by tier
- **Tier-Category Heatmap** - Cross-tabulation

### Interactive Tables
- Full belief matrix with all fields
- Sortable and filterable
- Exportable to CSV

## 🛠️ Configuration

Edit `config/settings.yaml`:

```yaml
openai:
  model: gpt-4o-mini  # or gpt-4o for higher quality
  temperature: 0.1
  max_tokens: 1500

extraction:
  two_stage: true
  batch_size: 10
  min_conviction_threshold: 0.3
  stage1_filter_enabled: true

multilevel:
  enabled: true
  chunking_strategy: exponential  # exponential, linear, semantic, time-based
  levels: [1, 2, 4, 8, 16, 32, 64, 128, 256, 512]
  deduplication_enabled: true
  deduplication_threshold: 0.85
  belief_linking_enabled: true
  linking_threshold: 0.6

analytics:
  enabled: true
  calculate_derived_metrics: true
  build_belief_graph: true
  generate_insights: true
  export_formats: [csv, json, graphml]

wandb:
  project: podcast-belief-extraction
  entity: your-username
  log_artifacts: true
  log_tables: true

output:
  format: csv  # csv, json, or parquet
  directory: output
```

## 📁 Project Structure

```
podcast-belief-extraction/
├── config/
│   └── settings.yaml               # Configuration (with multilevel & analytics settings)
├── prompts/
│   ├── stage1_filter.txt           # Is this a belief? (Q1-4)
│   └── stage2_classify.txt         # Classify belief (Q5-30)
├── src/
│   ├── transcript_parser.py        # Parse diarized transcripts
│   ├── classifier.py               # Two-stage belief classifier
│   ├── extractor.py                # Single-level pipeline logic
│   ├── chunker.py                  # Multi-level chunking (NEW!)
│   ├── multilevel_extractor.py     # Multi-level extraction orchestrator (NEW!)
│   ├── belief_merger.py            # Deduplication via semantic similarity (NEW!)
│   ├── belief_linker.py            # Parent-child relationship linking (NEW!)
│   ├── belief_analyzer.py          # Derived metrics calculation (NEW!)
│   ├── belief_graph.py             # NetworkX graph construction (NEW!)
│   ├── insight_generator.py        # Auto-generated insights (NEW!)
│   └── wandb_logger.py             # W&B integration
├── tests/
│   └── test_sample.txt             # 720-word test transcript
├── output/                          # Generated belief matrices
│   └── analysis/                    # Analytics outputs (NEW!)
├── run_extraction.py               # Single-level CLI script
├── run_multilevel_extraction.py    # Multi-level CLI script (NEW!)
├── analyze_beliefs.py              # Analytics CLI script (NEW!)
├── view_rankings.py                # View formatted rankings with weights
├── dashboard_analytics.html        # Interactive web dashboard (NEW!)
├── requirements.txt
└── README.md
```

## 🔬 How It Works

### Stage 1: Filter (Questions 1-4)
Quickly determines if a statement is a belief:
1. Is this a single clear statement?
2. Is it a belief vs narration/quote?
3. Is it endorsed by the speaker?
4. Is it non-trivial?

**Result**: `is_belief: true/false` + confidence score

### Stage 2: Classify (Questions 5-30)
For confirmed beliefs, detailed classification:
- **Q5-7**: Conviction indicators
- **Q8-13**: Belief type identification
- **Q14-15**: Claim vs casual statement
- **Q16-26**: Tier assignment
- **Q27-28**: Conviction & stability scoring
- **Q29-31**: Category, parent hint, outgroup definition

**Result**: Full belief record with 12 structured fields

## 🎯 Use Cases

- **Podcast Analysis**: Map host/guest belief systems
- **Speaker Profiling**: Identify core values and worldviews
- **Belief Evolution**: Track how beliefs change over time
- **Comparative Analysis**: Compare beliefs across speakers/episodes
- **Research**: Academic studies on belief formation
- **Content Understanding**: Extract key themes and values

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 Example Output

```csv
belief_id,speaker_id,episode_id,timestamp,statement_text,importance,tier_name,category,conviction_score,stability_score,parent_hint,parent_belief_id
b_0001,SPEAKER_B,e_test_001,00:02:28,"He's definitely in a different place politically",9,Situational Opinions,political,0.65,0.40,"Political positions evolve over time",NULL
b_0002,SPEAKER_C,e_test_001,00:03:01,"This is such a weird era for America",9,Situational Opinions,social,0.70,0.50,"Current times are unprecedented",NULL
```

## 🐛 Troubleshooting

### Missing API Key
```
Error: OPENAI_API_KEY not found
Solution: Create .env file with OPENAI_API_KEY=your-key
```

### W&B Not Logging
```
Solution: Set WANDB_API_KEY in .env or run with --no-wandb flag
```

### JSON Parsing Errors
```
Solution: Check prompts for formatting issues, or use higher temperature (0.2-0.3)
```

### High Costs
```
Solution: Always test with --cheap-mode first. Adjust max_words to control scope.
```

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- OpenAI API for LLM classification
- Weights & Biases for experiment tracking
- GraphRAG project for inspiration

## 📧 Support

For issues, questions, or feature requests, please open an issue on GitHub.

---

**Made with ❤️ for understanding beliefs in conversations**

