# 🎙️ Podcast Belief Extraction Pipeline

Extract and classify belief statements from diarized podcast transcripts using a 30-question belief matrix and AI-powered classification.

---

## 📑 Table of Contents

- [🎯 Features](#-features)
- [📊 Belief Matrix Schema](#-belief-matrix-schema)
  - [Core Fields](#core-fields)
  - [Multi-Level Fields](#multi-level-fields-new)
  - [Derived Metrics](#derived-metrics-analytics)
- [🏗️ Belief Tiers (Hierarchical)](#️-belief-tiers-hierarchical)
- [🚀 Quick Start](#-quick-start)
  - [Installation](#installation)
  - [Basic Usage](#basic-usage)
  - [Viewing Rankings](#viewing-rankings-with-weights)
  - [Input Format](#input-format)
- [💰 Cost Estimates](#-cost-estimates)
- [📊 W&B Dashboard](#-wb-dashboard)
- [🛠️ Configuration](#️-configuration)
- [📁 Project Structure](#-project-structure)
- [🔬 How It Works: Step-by-Step](#-how-it-works-step-by-step)
  - [Phase 1: Input & Initialization](#-phase-1-input--initialization)
  - [Phase 2: Transcript Parsing](#-phase-2-transcript-parsing)
  - [Phase 3: AI Classification](#-phase-3-ai-classification-the-core-loop)
  - [Phase 4: Data Processing & Output](#-phase-4-data-processing--output)
  - [Phase 5: Analytics & Visualization](#-phase-5-analytics--visualization)
  - [Multi-Level Extraction (Advanced)](#-multi-level-extraction-advanced)
  - [Key Optimizations](#-key-optimizations)
  - [Data Flow Summary](#-data-flow-summary)
  - [Example Processing](#-example-processing)
- [🎯 Use Cases](#-use-cases)
- [🤝 Contributing](#-contributing)
- [📝 Example Output](#-example-output)
- [🐛 Troubleshooting](#-troubleshooting)
- [📄 License](#-license)
- [🙏 Acknowledgments](#-acknowledgments)
- [📧 Support](#-support)

---

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

## 🔬 How It Works: Step-by-Step

### Overview
The pipeline processes podcast transcripts through a multi-stage AI-powered analysis system that identifies, classifies, and organizes belief statements into a hierarchical matrix.

### 📥 Phase 1: Input & Initialization

1. **Parse CLI Arguments** - Script reads command-line options like transcript path, episode ID, model choice, and output format
2. **Load API Credentials** - Retrieves OpenAI API key from `.env` file to authenticate with GPT models
3. **Initialize W&B Tracking** - Sets up Weights & Biases experiment tracking for logging metrics and visualizations
4. **Load Configuration** - Reads `config/settings.yaml` for model parameters, thresholds, and output preferences

### 📄 Phase 2: Transcript Parsing

5. **Parse Transcript File** - Reads diarized transcript and splits each line into speaker ID, timestamps, and text content using regex patterns
   ```
   Input:  SPEAKER_A | 00:01:23 | 00:01:45 | This is what they said
   Output: Utterance(speaker_id='SPEAKER_A', start_time='00:01:23', ...)
   ```
6. **Create Utterance Objects** - Wraps each parsed line into a structured dataclass with speaker, time, and text fields
7. **Apply Truncation (Optional)** - If cheap mode is enabled, limits processing to first N words for cost-effective testing

### 🤖 Phase 3: AI Classification (The Core Loop)

For **each utterance**, the system runs a two-stage classification:

#### Stage 1: Belief Filter (Fast & Cheap)

8. **Build Stage 1 Prompt** - Inserts utterance details into the filter prompt template asking 4 yes/no questions:
   - Does this contain an identifiable belief or value judgment?
   - Does it reveal what the speaker believes (even implicitly)?
   - Is it endorsed or sympathetically discussed by the speaker?
   - Does it reveal anything about their worldview or preferences?

9. **Call OpenAI API (Stage 1)** - Sends prompt to GPT model (default: `gpt-4o-mini`) requesting JSON response
   ```json
   {
     "is_belief": true,
     "confidence": 0.85,
     "reasoning": "Speaker expresses trust in Elon..."
   }
   ```

10. **Parse Filter Response** - Extracts `is_belief` flag and confidence score from JSON response

11. **Skip Non-Beliefs** - If statement isn't a belief, skips Stage 2 (saving ~70% of costs) and moves to next utterance

#### Stage 2: Detailed Classification (Only for Beliefs)

12. **Build Stage 2 Prompt** - Inserts confirmed belief into classification prompt with 31 detailed questions covering:
    - **Conviction Indicators (Q5-7)**: Strength of commitment, consistency, defense of belief
    - **Belief Type (Q8-13)**: Fundamental nature, epistemic, moral, cross-domain, systems, domain-specific
    - **Claim Type (Q14-15)**: Testable/concrete vs casual/exploratory
    - **Tier Classification (Q16-26)**: Which of 10 hierarchical tiers best fits
    - **Scoring (Q27-28)**: Conviction score (0-1) and stability score (0-1)
    - **Categorization (Q29-31)**: Domain category, parent belief hint, outgroup definition

13. **Call OpenAI API (Stage 2)** - Sends comprehensive prompt requesting detailed analysis
    ```json
    {
      "tier_name": "Stable Domain Beliefs",
      "importance": 6,
      "conviction_score": 0.7,
      "stability_score": 0.6,
      "category": "political",
      "parent_hint": "Moral responsibility of influential figures",
      ...
    }
    ```

14. **Extract Classification Data** - Parses JSON response containing all 27+ fields of belief analysis

15. **Create BeliefClassification Object** - Wraps all extracted data into structured result with both stage responses

16. **Track API Costs** - Records tokens used and calculates cost: `(prompt_tokens × $0.00015 + completion_tokens × $0.0006) / 1000`

### 📊 Phase 4: Data Processing & Output

17. **Filter Beliefs Only** - Keeps only utterances where `is_belief=True`, discarding non-beliefs (~70-80% filtered out)

18. **Convert to DataFrame** - Transforms belief objects into pandas DataFrame with standardized 12-column schema:
    ```
    belief_id | speaker_id | episode_id | timestamp | statement_text | 
    importance | tier_name | category | conviction_score | stability_score | 
    parent_hint | parent_belief_id
    ```

19. **Save to File** - Exports DataFrame as CSV/JSON/Parquet with all belief data organized and structured

### 📈 Phase 5: Analytics & Visualization

20. **Calculate Statistics** - Computes summary metrics like total beliefs, per-speaker counts, average conviction/stability scores

21. **Generate Visualizations** - Creates interactive Plotly charts:
    - Tier distribution bar chart
    - Category breakdown pie chart
    - Speaker comparison (count + conviction)
    - Conviction vs stability scatter plot
    - Tier-category heatmap

22. **Log to W&B** - Uploads beliefs table, metrics, cost data, and visualizations to Weights & Biases dashboard

23. **Upload Artifacts** - Saves input transcript and output CSV as W&B artifacts for reproducibility

24. **Print Summary** - Displays console output with belief count, speakers, scores, tokens, and total cost

25. **Finish W&B Run** - Closes tracking session and provides link to view results in dashboard

### 🔄 Multi-Level Extraction (Advanced)

For multi-level extraction (`run_multilevel_extraction.py`), the process repeats at different abstraction levels:

26. **Chunk Transcript** - Splits utterances into chunks of varying sizes (1, 2, 4, 8, 16, 32, 64, 128, 256, 512 utterances)

27. **Extract Per Level** - Runs full extraction pipeline on each chunk size independently

28. **Deduplicate Beliefs** - Uses semantic similarity to identify duplicate beliefs found across multiple levels

29. **Link Parent-Child** - Analyzes `parent_hint` fields to establish hierarchical relationships between beliefs

30. **Calculate Derived Metrics** - Computes advanced analytics:
    - `belief_strength` = conviction × stability
    - `foundational_weight` = (11 - importance) × conviction
    - `rigidity_score` = conviction × stability × (11 - importance)
    - `certainty_gap` = conviction - stability
    - `influence_score` = child_count × conviction

### 💡 Key Optimizations

- **Two-Stage Design**: Stage 1 filters ~70-80% of statements, saving significant API costs
- **JSON Mode**: Forces structured output for reliable parsing
- **Cost Tracking**: Real-time monitoring of token usage and expenses
- **Batch Processing**: Processes utterances sequentially with progress tracking
- **Cheap Mode**: Test with first 1000 words before committing to full transcripts
- **Caching Prompts**: Loads prompt templates once at initialization

### 🎯 Data Flow Summary

```
Transcript File
    ↓
Parse → Utterance Objects [191 items]
    ↓
For each utterance:
    ↓
Stage 1 Filter (4 questions) → is_belief: true/false
    ↓ (if true)
Stage 2 Classify (31 questions) → Full belief data
    ↓
Filter beliefs only [4 found]
    ↓
Convert to DataFrame
    ↓
Save CSV + Generate Analytics + Upload to W&B
    ↓
Done! ($0.0282 for 191 utterances)
```

### 🧪 Example Processing

**Input Utterance:**
```
SPEAKER_B | 00:12:04 | "I think Elon is genuine and does actual good work..."
```

**Stage 1 Output:**
```json
{"is_belief": true, "confidence": 0.85}
```

**Stage 2 Output:**
```json
{
  "tier_name": "Stable Domain Beliefs",
  "importance": 6,
  "conviction_score": 0.7,
  "stability_score": 0.6,
  "category": "political",
  "parent_hint": "Belief in moral responsibility of influential figures"
}
```

**Final Record:**
```csv
b_0001,SPEAKER_B,e_jre,00:12:04,"I think Elon is genuine...",6,Stable Domain Beliefs,political,0.7,0.6,"Belief in moral responsibility",NULL
```

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

