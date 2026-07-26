# Benchmarking LLMs against the ACID Rule-Based Baseline for IaC Defect Detection: A Semantic and Failure Taxonomy Analysis

A scientific-grade system for detecting and classifying Infrastructure as Code (IaC) defects, initially using state-of-the-art LLMs (DeepSeek-v3, GPT-5.2, and Qwen3-coder) with deterministic, reproducible analysis designed for rigorous empirical research. This repository serves as the public replication package, featuring the Augmented 132-ECM Evaluation Corpus and a two-level failure taxonomy.

## Overview

This project aims to analyze how Large Language Models perform at detecting defects in Infrastructure as Code. The system processes IaC commits, classifies them into 9 (Gang of Eight's taxonomy, including a `NO_DEFECT` label) defect categories using LLMs, and compares model outputs with oracle (ground truth) classifications and evolved ACID tool baseline. Manual analysis supports semantic requirement verification and label certainty validation.

The research identifies Zero-shot classification as the primary experimental condition; all qualitative analyses and research question (RQ) evaluations are derived from zero-shot outputs.

### Augmented 132-ECM Evaluation Corpus

This project utilizes and extends the Oracle-validated dataset from Oliveira et al. (2025). The original 132 Enhanced Commit Messages (ECMs) have been augmented with multi-dimensional manual annotations, including:
- Semantic Requirement: The level of reasoning needed to classify the defect.
- Label Certainty: The clarity of the evidence supporting the Oracle label.
- Qualitative Failure Attribution: Root-cause analysis for every model divergence

### Key Features

- **Multi-Model Support**: Gemini, OpenAI GPT, Alibaba Qwen, DeepSeek with deterministic settings
- **Reproducible Research**: Temperature=0, explicit seeds, checkpoint recovery, comprehensive logging
- **Rigorous Validation**: Response parsing, output consistency checks, oracle comparison
- **Manual Analysis**: Semantic requirement assessment per ECM (Error Classification Model), label certainty, and LLM error analysis
- **Batch Processing**: Efficient API usage with configurable batch sizes and retry logic
- **Zero-shot & Few-shot**: Support for both prompt strategies with separate output directories
- **Granular Metrics**: Utilization of Misclassification (MC) to isolate semantic reasoning gaps from taxonomy mapping errors.

> Note: While Google Gemini is supported by the pipeline for cross-validation, the primary benchmark and research findings reported in the paper focus on DeepSeek-v3, GPT-5.2, and Qwen3-coder.

## Repository Structure

### `/` (Root - Core Application)

**Main Scripts:**
- `run.py` - Entry point for classification pipeline
- `config.py` - Model configurations and global processing parameters
- `models.py` - LLM provider implementations (Gemini, OpenAI, Qwen, DeepSeek)
- `classifier.py` - Main orchestration logic and response validation
- `csv_processor.py` - Data structures and CSV I/O operations
- `logger_setup.py` - Centralized logging configuration
- `evaluation_pipeline.py` - Framework for comparing LLM outputs against the pre-computed ACID baseline results and the Oracle ground truth.

**Configuration:**
- `PROMPT.md` - Classification instructions (system prompt for all models)
- `.env.example` - API key template
- `requirements.txt` - Python dependencies

### `/inputs`

Raw input CSV files containing commits to be classified. Each file has columns:
- `hash` - Commit identifier
- `link` - Repository URL
- `commit-diff` - Full diff output
- `commit-message` - Commit message with metadata

### `/01-zero-shot-output`

Results from zero-shot classification (no examples in prompt):
```
01-zero-shot-output/
├── {model-name}/
│   ├── classifications.csv      # Final results: hash, defect_category, reason
│   ├── params.json              # Execution metadata
│   └── intermediate_*.csv       # Checkpoints every 50 batches
```

Models included:
- `deepseek-v3` - DeepSeek V3 model
- `gpt-5.2` - OpenAI GPT-5.2
- `qwen3-coder` - Alibaba Qwen 3 Coder

### `/02-few-shot-output`

Results from few-shot classification (examples included in prompt):
```
02-few-shot-output/
├── deepseek-v3.2_2026-04-23T13:46:31.534979/
│   ├── classifications.csv
│   ├── params.json
│   └── intermediate_*.csv
├── gpt-5.2_2026-04-23T13:52:44.008913/
│   └── ...
├── qwen3-coder-30b-a3b-v1.0_2026-04-23T13:56:33.052359/
│   └── ...
└── PROMPT.md                    # Few-shot classification instructions
└── model_registry.json          # Model metadata
```

Models tested include DeepSeek-v3, GPT-5.2, and Qwen3-coder with timestamped runs.

### `/oracle`

Ground truth data and oracle classification results:
- `oracle_dataset.csv` - Complete dataset with oracle labels
- `oracle_dataset_without_answers.csv` - Input format (oracle labels removed)
- `oracle_acid_answers.csv` - Oracle classifications in standard format
- `final-oracle-go8-replication.csv` - Verified oracle replication
- `final-data-off-brief.xlsx` - Summary data with brief defect descriptions
- `generate_oracle_csvs.py` - Utility to generate oracle CSV formats

### `/results`
Houses the quantitative benchmarking results for RQ1, providing a comparative performance analysis of the LLMs against the ACID baseline across the Go8 taxonomy using precision, recall, and Misclassification (MC) metrics.

### `/manual-analysis`

**Manual Analysis Results:**
- `main.py` - Script for performing manual analysis output with semantic requirements, label certainty, and LLM error categorization
- `manual_analysis_result.py` - Detailed RQ results related to computed research metrics (previous file)
- `/error-analysis` - Detailed Error Categorization and Analysis. This folder contains the qualitative data mapping each model failure to the two-level error taxonomy and the augmented evaluation corpus
- `/rq-outputs` - Aggregated statistics and metrics for the research questions (RQ2 and RQ3)

> While raw metrics (Precision/Recall) provide the "what," the files in /error-analysis provide the "why". This folder contains the evidence-based justifications for every classification failure, supporting the paper's finding that true failure rates are significantly lower (≈17–26%) than raw metrics suggest once contestable cases are isolated.

**What is Manual Analysis?**
- **Semantic Requirement**: Each commit is assessed for semantic requirements that affect correctness (Syntactic, Semantic, Ambiguous)
- **Label Certainty**: Confidence level in the ground truth label assignment (Clear, Ambiguous)
- **LLM Error Categories**: Systematic categorization of where and why LLMs diverged from oracle:
  - Semantic Reasoning Failure (Causal Misunderstanding, Scope Confusion, Implicit Context Missing)
  - Taxonomy Mapping Failure (Boundary Ambiguity, Over-Generalization, Wrong Addressing)
  - Input Dependence Failure (Keywork Over-Reliance, Entity Confusion, Degenerate Output)
  - Contestable Case* (Defect vs. Feature, Taxonomy Overlap, Specific Defect)
- **Validation**: Manual verification of defect categories, evidence quality, and semantic correctness

> *Important: 'Contestable Cases' identify Oracle ambiguity and are explicitly excluded from 'True Error' counts in the research analysis.

### `/models-answer`

Consolidated model classification results in standard format:
- `deepseek_v3_defect_classification.csv` - DeepSeek V3 classifications
- `gpt5_2_defect_classification.csv` - GPT-5.2 classifications
- `qwen3_defect_classification.csv` - Qwen3-coder classifications

Each CSV follows the standard format: hash, defect_category, reason

### `/logs`

Execution logs from classification runs:
```
logs/
├── {model-name}_YYYYMMDD_HHMMSS.log
```

Logs contain:
- DEBUG level: Detailed internal operations
- INFO level: Major milestones and progress
- ERROR level: Failures with context

## Getting Started

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `openai>=1.0.0` - OpenAI API
- `google-genai>=1.5.0` - Google Gemini
- `pandas>=2.0.0` - CSV processing
- `python-dotenv>=1.0.0` - Environment variables
- `tenacity>=8.2.0` - Retry logic

### 2. Configure API Keys

Create a `.env` file in the root directory:

```bash
GOOGLE_API_KEY=your_google_api_key
OPENAI_API_KEY=your_openai_api_key
QWEN_API_KEY=your_qwen_api_key
```

Or set environment variables directly:
```bash
export GOOGLE_API_KEY=your_key
export OPENAI_API_KEY=your_key
export QWEN_API_KEY=your_key
```

### 3. Prepare Input Data

Place CSV files in `./inputs/` with required columns:
- `hash` - Commit identifier
- `link` - Repository URL
- `commit-diff` - Full diff output
- `commit-message` - Commit message

### 4. Run Classification

```bash
python run.py
```

This processes all CSV files in `./inputs/` using all configured models and saves results to `output/{model-name}/`.

## Defect Categories

The system classifies IaC commits into 9 categories:

1. **CONFIGURATION_DATA** - Erroneous config data in IaC scripts (storage, filesystem, network, credentials, caching)
2. **DEPENDENCY** - Missing or incorrectly specified artifacts (files, packages, modules)
3. **DOCUMENTATION** - Incorrect information in comments, notes, or README files
4. **CONDITIONAL** - Erroneous logic or conditional values
5. **SERVICE** - Improper service provisioning or inadequate resource availability
6. **IDEMPOTENCY** - Violations of the idempotency property (non-deterministic results)
7. **SECURITY** - Confidentiality, integrity, or availability violations (hardcoded secrets, weak SSL, etc.)
8. **SYNTAX** - Syntax errors in IaC scripts
9. **NO_DEFECT** - No detected defect

## Configuration

### Models (config.py)

Three models configured for deterministic classification:

| Model | Provider | API Key | Notes |
|-------|----------|---------|-------|
| `deepseek-v3.2` | DeepSeek | `GOOGLE_API_KEY` | DeepSeek-v3.2 release |
| `gpt-5.2-2025-12-11` | OpenAI | `OPENAI_API_KEY` | GPT-5.2 release |
| `qwen3-coder-plus` | Alibaba | `QWEN_API_KEY` | OpenAI-compatible endpoint |

### Deterministic Settings

All models use:
- `temperature=0` - Maximum determinism
- `max_tokens=2048` - Sufficient for classifications

### Processing Settings

- `BATCH_SIZE=10` - Commits per API request
- `CHECKPOINT_FREQUENCY=50` - Save intermediate results every N batches
- `DEFAULT_DELAY_BETWEEN_REQUESTS=0.5s` - Rate limiting between requests
- `max_retries=3` - Attempts before failure
- Exponential backoff: 1s, 2s, 4s delays

## Output Format

Each `classifications.csv` contains:
```csv
hash,defect_category,reason
a1b2c3d4...,SECURITY,Removed hardcoded AWS secret from terraform.tfvars (line 15)
e5f6g7h8...,NO_DEFECT,Refactored module structure without functionality changes
```

- `hash` - Original commit hash
- `defect_category` - One of the 9 categories or NO_DEFECT
- `reason` - Evidence-based justification (≤200 characters)

## Error Handling & Validation

### Response Validation

The classifier validates:
- ✓ All input commits are present in response
- ✓ No unknown hashes in response
- ✓ Row count matches input
- ✓ Categories are from allowed list
- ✓ Reasons are ≤200 characters

### Retry Logic

Automatic exponential backoff on API errors:
1. Wait 1s, retry
2. Wait 2s, retry
3. Wait 4s, final attempt
4. If still failing, exception raised and logged

## Scientific Reproducibility

### Determinism Guarantees

1. **Temperature=0** - Model always selects highest probability token
2. **Explicit random seeds** - When supported by API
3. **Batch size consistency** - Same commits processed in same batches
4. **No shuffling** - Input order preserved throughout
5. **Checkpoint recovery** - Can resume from intermediate states
6. **Environment parity** - Same API keys and versions

### Run Metadata

Each execution records in `params.json`:
- Model name and version
- Timestamp (ISO 8601)
- Total commits processed
- Completion rate
- Total batches

## Manual Analysis Workflow

The `/manual-analysis` directory contains comprehensive manual verification and analysis of classifications:

**Running the Analysis:**
```bash
python manual-analysis/main.py
```

**Components:**
- **Semantic Requirement Assessment**: Each commit is evaluated for semantic properties affecting correctness:
  - **Syntactic**: detectable via static patterns
  - **Semantic**: requires contextual reasoning
  - **Ambiguous**: dependent on developer intent
- **Label Certainty**: Confidence levels in ground truth assignments, helping identify edge cases:
  - **Clear**: clearly supports the Oracle's single label
  - **Ambiguous**: multiple labels or interpretations are plausible
- **Error Root-Cause Analysis**: Systematic categorization of LLM failures with specific failure modes:
  - **Semantic Reasoning Failure** - Causal Misunderstanding, Scope Confusion, Implicit Context Missing
  - **Taxonomy Mapping Failure** - Boundary Ambiguity, Over-Generalization, Wrong Addressing
  - **Input Dependence Failure** - Keyword Over-Reliance, Entity Confusion, Degenerate Output
  - **Contestable Case** - Defect vs. Feature distinction, Taxonomy Overlap, Specific Defect ambiguity (These are documented in the analysis but not counted as model errors)
- **Research Question Evaluation**: Aggregate statistics computed across all research questions in `/rq-outputs`

**Output:**
- Per-commit analysis in `manual_analysis_result.py`
- Error categorization details in `/error-analysis`
- Aggregated research metrics in `/rq-outputs`

## Performance Considerations

- **Batch processing**: Reduces API calls (10 commits per request)
- **Checkpointing**: Every 50 batches, allows partial recovery
- **Rate limiting**: 0.5s delay between requests prevents throttling
- **Retry mechanism**: Handles transient API errors gracefully

## Troubleshooting

### Missing API Keys
```
ValueError: Missing GOOGLE_API_KEY environment variable
```
**Solution**: Set environment variables or update .env file

### Invalid Category in Response
```
ValueError: Invalid category: UNKNOWN
```
**Solution**: Model may be returning unexpected category. Check PROMPT.md for allowed categories.

### Incomplete Classifications
```
ValueError: Not all commits were classified. Missing: 5
```
**Solution**: Model failed to classify all commits. Check logs for details. May indicate prompt too long for batch.

### Rate Limiting / API Errors

Automatic retry with exponential backoff. If persists:
1. Increase `initial_delay` in config.py
2. Reduce `BATCH_SIZE` for smaller requests
3. Check API service status

## Extending the System

### Add New Model

1. Create model class in `models.py` extending `BaseModel`
2. Implement `classify()` method
3. Add to `MODELS` dict in `config.py`

Example:
```python
# In models.py
class NewProviderModel(BaseModel):
    def classify(self, commit_data: str) -> str:
        # Your implementation
        pass

# In config.py
MODELS = {
    'new-model-name': ModelConfig(
        name='new-model-name',
        provider='new-provider',
        ...
    ),
}
```

### Modify Prompt

Edit `PROMPT.md` to change classification instructions. Changes apply to all models on next run.

### Adjust Processing Parameters

Edit `config.py`:
- Change `BATCH_SIZE` for larger/smaller requests
- Adjust `DEFAULT_DELAY_BETWEEN_REQUESTS` for rate limiting
- Modify `CHECKPOINT_FREQUENCY` for more/fewer checkpoints

## Credits & Dataset Attribution

The evaluation corpus consists of 132 ECMs from the Oracle-validated dataset established by Oliveira et al. (2025).

## License

This project is licensed under the MIT License. This repository serves as the public replication package for the study "Benchmarking LLMs against the ACID Rule-Based Baseline for IaC Defect Detection: A Semantic and Failure Taxonomy Analysis", ensuring reproducibility and supporting future research
