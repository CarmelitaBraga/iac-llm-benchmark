"""CSV processing utilities for commit data."""

import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

import pandas as pd


logger = logging.getLogger(__name__)


class CommitData:
    """Represents a single commit from the CSV."""

    def __init__(self, hash: str, link: str, commit_diff: str, commit_message: str):
        self.hash = hash
        self.link = link
        self.commit_diff = commit_diff
        self.commit_message = commit_message

    def format_for_prompt(self, system_prompt: str) -> str:
        """Format commit data as prompt for classification."""
        return f"""{system_prompt}

## Commit to Analyze

**Hash:** {self.hash}
**Link:** {self.link}

**Commit Message:**
{self.commit_message}

**Commit Diff:**
{self.commit_diff}
"""


class Classification:
    """Represents a classification result."""

    def __init__(self, hash: str, defect_category: str, reason: str):
        self.hash = hash
        self.defect_category = defect_category
        self.reason = reason

    def to_dict(self) -> Dict:
        return {
            'hash': self.hash,
            'defect_category': self.defect_category,
            'reason': self.reason,
        }


class CSVProcessor:
    """Handle CSV input/output operations."""

    REQUIRED_COLUMNS = {'hash', 'link', 'commit-diff', 'commit-message'}

    @staticmethod
    def load_commits(csv_path: Path) -> List[CommitData]:
        """Load commits from CSV file."""
        logger.info(f"Loading commits from {csv_path}")

        df = pd.read_csv(csv_path)

        # Validate columns
        missing_cols = CSVProcessor.REQUIRED_COLUMNS - set(df.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        commits = []
        for _, row in df.iterrows():
            commit = CommitData(
                hash=str(row['hash']).strip(),
                link=str(row['link']).strip(),
                commit_diff=str(row['commit-diff']),
                commit_message=str(row['commit-message']),
            )
            commits.append(commit)

        logger.info(f"Loaded {len(commits)} commits")
        return commits

    @staticmethod
    def save_classifications(
        output_path: Path,
        classifications: List[Classification],
    ) -> None:
        """Save classifications to CSV."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(
                f,
                fieldnames=['hash', 'defect_category', 'reason']
            )
            writer.writeheader()
            for cls in classifications:
                writer.writerow(cls.to_dict())

        logger.info(f"Saved {len(classifications)} classifications to {output_path}")

    @staticmethod
    def save_intermediate(
        output_path: Path,
        classifications: List[Classification],
        batch_number: int,
    ) -> None:
        """Save intermediate checkpoint of classifications."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(
                f,
                fieldnames=['hash', 'defect_category', 'reason']
            )
            writer.writeheader()
            for cls in classifications:
                writer.writerow(cls.to_dict())

        logger.debug(f"Saved intermediate checkpoint (batch {batch_number}) to {output_path}")

    @staticmethod
    def save_metadata(
        output_path: Path,
        model_name: str,
        total_commits: int,
        processed_commits: int,
        total_batches: int,
        timestamp: str,
        model_config: Optional[object] = None,
    ) -> None:
        """Save execution metadata."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        metadata = {
            'model': model_name,
            'total_commits': total_commits,
            'processed_commits': processed_commits,
            'total_batches': total_batches,
            'timestamp': timestamp,
            'completion_rate': f"{(processed_commits / total_commits * 100):.2f}%",
        }

        # Include model configuration parameters if provided
        if model_config is not None:
            metadata['config'] = {
                'provider': model_config.provider,
                'temperature': model_config.temperature,
                'top_p': model_config.top_p,
                'top_k': model_config.top_k,
                'max_tokens': model_config.max_tokens,
                'max_retries': model_config.max_retries,
                'initial_delay': model_config.initial_delay,
                'max_delay': model_config.max_delay,
            }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Saved metadata to {output_path}")


class PromptBuilder:
    """Build prompts for model requests."""

    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt

    def build_single_commit_prompt(self, commit: CommitData) -> str:
        """Build prompt for a single commit."""
        return commit.format_for_prompt(self.system_prompt)

    def build_batch_prompt(self, commits: List[CommitData]) -> str:
        """Build prompt for multiple commits in a batch."""
        prompt = self.system_prompt + "\n\n## Commits to Analyze\n"
        for i, commit in enumerate(commits, 1):
            prompt += f"\n### Commit {i}\n"
            prompt += f"**Hash:** {commit.hash}\n"
            prompt += f"**Link:** {commit.link}\n"
            prompt += f"**Commit Message:**\n{commit.commit_message}\n"
            prompt += f"**Commit Diff:**\n{commit.commit_diff}\n"
        return prompt
