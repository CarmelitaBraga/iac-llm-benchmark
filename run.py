"""Main entry point for IaC defect classification."""

import logging
from pathlib import Path
import sys

from config import MODELS
from classifier import IaCClassifier
from csv_processor import CSVProcessor
from logger_setup import setup_logging


# Module-level logger
logger = logging.getLogger(__name__)


def main():
    """Main execution flow."""
    # Configuration
    input_dir = Path("./inputs")
    output_base_dir = Path("./output")
    log_base_dir = Path("./logs")
    prompt_file = Path("./PROMPT.md")

    # Setup root logger first for main messages
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.INFO)

    # Get list of input CSV files
    csv_files = sorted(input_dir.glob("*.csv"))
    if not csv_files:
        logger.error(f"No CSV files found in {input_dir}")
        return 1

    logger.info(f"Found {len(csv_files)} input CSV files")

    # Load system prompt
    if not prompt_file.exists():
        logger.error(f"PROMPT.md not found at {prompt_file}")
        return 1

    system_prompt = prompt_file.read_text()
    logger.info(f"Loaded prompt from {prompt_file}")

    # Process each model with each CSV file
    for model_name, model_config in MODELS.items():
        logger.info(f"{'='*60}")
        logger.info(f"Processing model: {model_name}")
        logger.info(f"{'='*60}")

        # Setup logging for this model
        model_logger = setup_logging(log_base_dir, model_name)

        try:
            # Create output directory for this model
            model_output_dir = output_base_dir / model_name
            model_log_dir = log_base_dir / model_name
            model_output_dir.mkdir(parents=True, exist_ok=True)
            model_log_dir.mkdir(parents=True, exist_ok=True)

            # Initialize classifier
            classifier = IaCClassifier(
                model_config=model_config,
                system_prompt=system_prompt,
                output_dir=model_output_dir,
                log_dir=model_log_dir,
            )

            # Process each CSV file
            for csv_file in csv_files:
                model_logger.info(f"Processing: {csv_file.name}")

                try:
                    # Load commits from CSV
                    commits = CSVProcessor.load_commits(csv_file)

                    # Classify
                    classifications = classifier.classify(commits)

                    # Save results
                    classifier.save_results(classifications)

                    model_logger.info(f"Successfully processed {len(classifications)} commits from {csv_file.name}")

                except Exception as e:
                    model_logger.error(f"Failed to process {csv_file.name}: {e}", exc_info=True)
                    return 1

        except Exception as e:
            model_logger.error(f"Fatal error for model {model_name}: {e}", exc_info=True)
            return 1

    logger.info(f"{'='*60}")
    logger.info("All models processed successfully!")
    logger.info(f"Results saved to: {output_base_dir}")
    logger.info(f"Logs saved to: {log_base_dir}")
    logger.info(f"{'='*60}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
