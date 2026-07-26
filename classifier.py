"""Main classifier orchestrating model requests and result processing."""

import logging
import time
import re
from pathlib import Path
from typing import List, Tuple
from datetime import datetime

from config import ModelConfig, CATEGORIES, BATCH_SIZE, CHECKPOINT_FREQUENCY, DEFAULT_DELAY_BETWEEN_REQUESTS
from models import create_model
from csv_processor import (
    CommitData, Classification, CSVProcessor, PromptBuilder
)


logger = logging.getLogger(__name__)


class ResponseParser:
    """Parse model responses and extract classifications."""

    # Expected CSV format: hash,defect_category,reason
    CSV_PATTERN = re.compile(
        r'([a-f0-9]{40})\s*,\s*([A-Za-z_]+)\s*,\s*(.+?)(?=\n|$)',
        re.MULTILINE | re.DOTALL
    )

    @staticmethod
    def parse_classifications(response: str, input_commits: List[CommitData]) -> List[Classification]:
        """
        Parse model response and extract classifications.

        Expected format: hash,defect_category,reason (CSV)
        Validates that all input commits are classified.
        """
        classifications = []
        input_hashes = {commit.hash for commit in input_commits}
        found_hashes = set()

        # Try to find CSV pattern
        matches = ResponseParser.CSV_PATTERN.findall(response)

        if not matches:
            logger.error("Failed to parse CSV format from response")
            raise ValueError("No valid CSV format detected in response")

        for hash_val, category, reason in matches:
            # Normalize category
            category = category.upper()

            # Validate category - only valid categories
            if category not in CATEGORIES:
                logger.error(f"Invalid category '{category}' for hash {hash_val}")
                raise ValueError(f"Invalid category: {category}")

            # Truncate reason to 200 chars
            reason = reason.strip()[:200]

            found_hashes.add(hash_val)
            classifications.append(
                Classification(hash_val, category, reason)
            )

        # Check if all input hashes were classified
        missing_hashes = input_hashes - found_hashes
        if missing_hashes:
            logger.error(f"Missing classifications for hashes: {missing_hashes}")
            raise ValueError(f"Not all commits were classified. Missing: {len(missing_hashes)}")

        # Check for unknown hashes in response
        extra_hashes = found_hashes - input_hashes
        if extra_hashes:
            logger.error(f"Unknown hashes in response: {extra_hashes}")
            raise ValueError(f"Response contains unknown hashes: {len(extra_hashes)}")

        # Check if row count matches
        if len(classifications) != len(input_commits):
            logger.error(f"Row count mismatch: {len(classifications)} vs {len(input_commits)}")
            raise ValueError(f"Row count mismatch: {len(classifications)} vs {len(input_commits)}")

        return classifications


class IaCClassifier:
    """Main classifier that orchestrates the classification process."""

    def __init__(
        self,
        model_config: ModelConfig,
        system_prompt: str,
        output_dir: Path,
        log_dir: Path,
    ):
        self.config = model_config
        self.model = create_model(model_config)
        self.prompt_builder = PromptBuilder(system_prompt)
        self.output_dir = output_dir
        self.log_dir = log_dir
        self.timestamp = datetime.now().isoformat()

        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized classifier for model: {model_config.name}")

    def classify(self, commits: List[CommitData]) -> List[Classification]:
        """
        Classify all commits.

        Args:
            commits: List of CommitData to classify

        Returns:
            List of Classification results
        """
        logger.info(f"Starting classification of {len(commits)} commits with {self.config.name}")

        all_classifications = []
        total_batches = (len(commits) + BATCH_SIZE - 1) // BATCH_SIZE

        for batch_num in range(total_batches):
            start_idx = batch_num * BATCH_SIZE
            end_idx = min(start_idx + BATCH_SIZE, len(commits))
            batch_commits = commits[start_idx:end_idx]

            logger.info(
                f"Processing batch {batch_num + 1}/{total_batches} "
                f"({len(batch_commits)} commits)"
            )

            try:
                # Build prompt
                prompt = self.prompt_builder.build_batch_prompt(batch_commits)

                # Call model
                response = self.model.classify(prompt)

                # Parse response
                batch_classifications = ResponseParser.parse_classifications(
                    response,
                    batch_commits
                )

                all_classifications.extend(batch_classifications)

                # Save intermediate checkpoint
                if (batch_num + 1) % CHECKPOINT_FREQUENCY == 0:
                    checkpoint_path = (
                        self.output_dir / f"intermediate_{batch_num + 1}.csv"
                    )
                    CSVProcessor.save_intermediate(
                        checkpoint_path,
                        all_classifications,
                        batch_num + 1,
                    )

                # Add delay between requests
                if batch_num < total_batches - 1:
                    time.sleep(DEFAULT_DELAY_BETWEEN_REQUESTS)

            except Exception as e:
                logger.error(f"Failed to process batch {batch_num + 1}: {e}")
                raise

        logger.info(f"Completed classification of {len(all_classifications)} commits")
        return all_classifications

    def save_results(self, classifications: List[Classification]) -> None:
        """Save classification results and metadata."""
        # Save main classifications CSV
        classifications_path = self.output_dir / "classifications.csv"
        CSVProcessor.save_classifications(classifications_path, classifications)

        # Save metadata with model configuration
        metadata_path = self.output_dir / "params.json"
        CSVProcessor.save_metadata(
            metadata_path,
            model_name=self.config.name,
            total_commits=len(classifications),
            processed_commits=len(classifications),
            total_batches=(len(classifications) + BATCH_SIZE - 1) // BATCH_SIZE,
            timestamp=self.timestamp,
            model_config=self.config,
        )

        logger.info(f"Results saved to {self.output_dir}")
