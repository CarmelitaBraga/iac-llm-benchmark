import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# -------------------------
# Config
# -------------------------
ORACLE_FILE = "oracle/oracle_acid_answers.csv"
MODELS_DIR = "output"
RESULTS_DIR = "results"

ANSWER_COL = "oracle-normalized"
ACID_COL = "acid-normalized"

os.makedirs(RESULTS_DIR, exist_ok=True)

CATEGORY_MAP = {
    "no defect": "NO_DEFECT",
    "service": "SERVICE",
    "security": "SECURITY",
    "syntax": "SYNTAX",
    "configuration data": "CONFIGURATION_DATA",
    "dependency": "DEPENDENCY",
    "documentation": "DOCUMENTATION",
    "conditional": "CONDITIONAL",
    "idempotency": "IDEMPOTENCY",
}

CATEGORIES = [
    "NO_DEFECT",
    "CONDITIONAL",
    "CONFIGURATION_DATA",
    "DEPENDENCY",
    "DOCUMENTATION",
    "IDEMPOTENCY",
    "SECURITY",
    "SERVICE",
    "SYNTAX",
]

# -------------------------
# Normalization
# -------------------------
def normalize_category(series):
    return (
        series.astype(str)
        .str.lower()
        .str.strip()
        .map(CATEGORY_MAP)
    )

# -------------------------
# Load Base Data
# -------------------------
def load_oracle():
    df = pd.read_csv(ORACLE_FILE)

    df["oracle"] = normalize_category(df[ANSWER_COL])
    df["acid"] = normalize_category(df[ACID_COL])

    return df[["hash", "oracle", "acid"]].copy()

# -------------------------
# Load Models
# -------------------------
def load_and_merge_models(base_df):
    final_df = base_df.copy()

    # Iterate through subdirectories in MODELS_DIR (one per model)
    for model_dir in os.listdir(MODELS_DIR):
        model_path = os.path.join(MODELS_DIR, model_dir)

        # Skip if not a directory
        if not os.path.isdir(model_path):
            continue

        classifications_file = os.path.join(model_path, "classifications.csv")

        # Check if classifications.csv exists
        if not os.path.exists(classifications_file):
            print(f"[WARN] Skipping {model_dir}: classifications.csv not found")
            continue

        # Read classifications
        df = pd.read_csv(classifications_file)

        if not {"hash", "defect_category"}.issubset(df.columns):
            raise ValueError(f"[ERROR] Invalid schema in {classifications_file}")

        df[model_dir] = (
            df["defect_category"]
            .astype(str)
            .str.upper()
            .str.strip()
        )

        df = df[["hash", model_dir]]

        final_df = final_df.merge(df, on="hash", how="left")

    return final_df

# -------------------------
# Metrics Computation
# -------------------------
def compute_metrics(df, answer_col="oracle"):
    model_cols = [
        c for c in df.columns
        if c != "hash" and c != answer_col
    ]

    all_results = {}
    summary_rows = []

    for model in model_cols:
        df_eval = df.copy()
        df_eval[model] = df_eval[model].fillna("UNKNOWN")

        rows = []
        total_precision = 0
        total_recall = 0

        for cat in CATEGORIES:
            tp = ((df_eval[model] == cat) & (df_eval[answer_col] == cat)).sum()
            fp = ((df_eval[model] == cat) & (df_eval[answer_col] != cat)).sum()
            fn = ((df_eval[model] != cat) & (df_eval[answer_col] == cat)).sum()

            occurrences = (df_eval[answer_col] == cat).sum()

            precision = tp / (tp + fp) if (tp + fp) else 0
            recall = tp / (tp + fn) if (tp + fn) else 0

            rows.append({
                "category": cat,
                "occurrences": occurrences,
                "precision": precision,
                "recall": recall
            })

            total_precision += precision
            total_recall += recall

        metrics_df = pd.DataFrame(rows)

        macro_precision = total_precision / len(CATEGORIES)
        macro_recall = total_recall / len(CATEGORIES)

        total_occ = metrics_df["occurrences"].sum()

        weighted_precision = (
            (metrics_df["precision"] * metrics_df["occurrences"]).sum() / total_occ
            if total_occ else 0
        )

        weighted_recall = (
            (metrics_df["recall"] * metrics_df["occurrences"]).sum() / total_occ
            if total_occ else 0
        )

        all_results[model] = metrics_df

        summary_rows.append({
            "model": model,
            "macro_precision": macro_precision,
            "macro_recall": macro_recall,
            "weighted_precision": weighted_precision,
            "weighted_recall": weighted_recall
        })

        print(f"\nPer-Category Metrics: {model}")
        print(metrics_df)
        print("----------------")
        print(f"Precision: {macro_precision:.4f}")
        print(f"Recall:    {macro_recall:.4f}")

    summary_df = pd.DataFrame(summary_rows)
    return all_results, summary_df

# -------------------------
# Save Outputs
# -------------------------
def save_results(final_df, metrics_dict, summary_df):
    final_df.to_csv(f"{RESULTS_DIR}/final_comparison.csv", index=False)

    for model, df in metrics_dict.items():
        df.to_csv(f"{RESULTS_DIR}/{model}_metrics.csv", index=False)

    summary_df.to_csv(f"{RESULTS_DIR}/models_summary.csv", index=False)

# -------------------------
# Plot Per-Category Lines
# -------------------------
def plot_per_category(metrics_dict):
    for metric in ["precision", "recall"]:
        plt.figure()

        for model, df in metrics_dict.items():
            plt.plot(
                CATEGORIES,
                df.set_index("category").loc[CATEGORIES][metric],
                marker="o",
                label=model
            )

        plt.ylim(0, 1)
        plt.xticks(rotation=45)
        plt.title(f"{metric.capitalize()} per Category")
        plt.legend()
        plt.tight_layout()

        plt.savefig(f"{RESULTS_DIR}/{metric}_chart.png")
        plt.close()

# -------------------------
# Plot Overall Comparison
# -------------------------
def plot_summary(summary_df):
    summary_df = summary_df.sort_values(by="weighted_precision", ascending=False)

    x = range(len(summary_df))
    width = 0.35

    plt.figure()

    bars_p = plt.bar(
        [i - width/2 for i in x],
        summary_df["weighted_precision"],
        width=width,
        label="Precision"
    )

    bars_r = plt.bar(
        [i + width/2 for i in x],
        summary_df["weighted_recall"],
        width=width,
        label="Recall"
    )

    for bars in [bars_p, bars_r]:
        for bar in bars:
            h = bar.get_height()
            plt.text(
                bar.get_x() + bar.get_width()/2,
                h + 0.01,
                f"{h:.2f}",
                ha="center",
                va="bottom",
                fontsize=9
            )

    plt.xticks(x, summary_df["model"], rotation=45)
    plt.ylim(0, 1)
    plt.title("Overall Model Performance (Weighted)")
    plt.legend()
    plt.tight_layout()

    plt.savefig(f"{RESULTS_DIR}/overall_comparison.png")
    plt.close()

# -------------------------
# Plot Confusion Matrices
# -------------------------
def plot_confusion_matrices(df, answer_col="oracle"):
    model_cols = [
        c for c in df.columns
        if c != "hash" and c != answer_col
    ]

    for model in model_cols:
        df_eval = df.copy()
        df_eval[model] = df_eval[model].fillna("UNKNOWN")

        cm = pd.crosstab(
            df_eval[answer_col],
            df_eval[model],
            rownames=["Actual"],
            colnames=["Predicted"],
            dropna=False
        )

        # Ensure consistent ordering
        cm = cm.reindex(index=CATEGORIES, columns=CATEGORIES, fill_value=0)

        plt.figure(figsize=(10, 7))

        sns.heatmap(
            cm,
            annot=True,
            fmt="d",
            cmap="Blues",
            cbar=True
        )

        plt.title(f"Confusion Matrix - {model}")
        plt.ylabel("Actual")
        plt.xlabel("Predicted")
        plt.xticks(rotation=45)
        plt.yticks(rotation=0)
        plt.tight_layout()

        plt.savefig(f"{RESULTS_DIR}/{model}_confusion_matrix.png")
        plt.close()

def plot_metric_heatmaps(metrics_dict):
    """
    Creates two heatmaps:
    - Precision (categories x models)
    - Recall (categories x models)
    """

    # -------------------------
    # Build matrices (categories as rows)
    # -------------------------
    precision_data = {}
    recall_data = {}

    for model, df in metrics_dict.items():
        df_indexed = df.set_index("category").reindex(CATEGORIES)

        precision_data[model] = df_indexed["precision"]
        recall_data[model] = df_indexed["recall"]

    # Categories as rows (NO transpose)
    precision_df = pd.DataFrame(precision_data)
    recall_df = pd.DataFrame(recall_data)

    # -------------------------
    # Precision Heatmap
    # -------------------------
    plt.figure(figsize=(10, 7))

    sns.heatmap(
        precision_df,
        annot=True,
        fmt=".2f",
        cmap="Blues",
        cbar=True,
        vmin=0,
        vmax=1
    )

    plt.title("Precision Heatmap (Defect Categories vs Models)")
    plt.xlabel("Model")
    plt.ylabel("Category")
    plt.xticks(rotation=45)
    plt.yticks(rotation=0)
    plt.tight_layout()

    plt.savefig(f"{RESULTS_DIR}/precision_heatmap.png")
    plt.close()

    # -------------------------
    # Recall Heatmap
    # -------------------------
    plt.figure(figsize=(10, 7))

    sns.heatmap(
        recall_df,
        annot=True,
        fmt=".2f",
        cmap="Blues",
        cbar=True,
        vmin=0,
        vmax=1
    )

    plt.title("Recall Heatmap (Defect Categories vs Models)")
    plt.xlabel("Model")
    plt.ylabel("Category")
    plt.xticks(rotation=45)
    plt.yticks(rotation=0)
    plt.tight_layout()

    plt.savefig(f"{RESULTS_DIR}/recall_heatmap.png")
    plt.close()


# -------------------------
# Plot Categories Distribution
# -------------------------
def plot_category_distribution(df, answer_col="oracle"):
    model_cols = [
        c for c in df.columns
        if c != "hash" and c != answer_col
    ]

    distribution_data = {}

    # -------------------------
    # Oracle distribution (GROUND TRUTH)
    # -------------------------
    oracle_counts = (
        df[answer_col]
        .value_counts()
        .reindex(CATEGORIES, fill_value=0)
    )
    distribution_data["oracle"] = oracle_counts

    # -------------------------
    # Model distributions
    # -------------------------
    for model in model_cols:
        counts = (
            df[model]
            .fillna("UNKNOWN")
            .value_counts()
            .reindex(CATEGORIES, fill_value=0)
        )
        distribution_data[model] = counts

    dist_df = pd.DataFrame(distribution_data)

    # Normalize to proportions (recommended)
    dist_df = dist_df.div(dist_df.sum(axis=0), axis=1)

    # -------------------------
    # Plot
    # -------------------------
    plt.figure(figsize=(12, 6))

    x = range(len(CATEGORIES))
    width = 0.8 / len(dist_df.columns)

    for i, col in enumerate(dist_df.columns):
        plt.bar(
            [j + i * width for j in x],
            dist_df[col],
            width=width,
            label=col
        )

    plt.xticks(
        [j + width * (len(dist_df.columns) / 2) for j in x],
        CATEGORIES,
        rotation=45
    )

    plt.ylim(0, 1)
    plt.ylabel("Proportion")
    plt.title("Category Distribution: Oracle vs Models")
    plt.legend(title="Source")
    plt.tight_layout()

    plt.savefig(f"{RESULTS_DIR}/category_distribution.png")
    plt.close()

# -------------------------
# Orchestrator
# -------------------------
def run_pipeline():
    print("[1] Loading oracle...")
    base_df = load_oracle()

    print("[2] Merging models...")
    final_df = load_and_merge_models(base_df)

    print("[3] Computing metrics...")
    metrics_dict, summary_df = compute_metrics(final_df)

    print("[4] Saving results...")
    save_results(final_df, metrics_dict, summary_df)

    print("[5] Plotting...")
    plot_per_category(metrics_dict)
    plot_summary(summary_df)

    print("[6] Confusion matrices...")
    plot_confusion_matrices(final_df)

    print("[7] Metric heatmaps...")
    plot_metric_heatmaps(metrics_dict)

    print("[8] Category distribution...")
    plot_category_distribution(final_df)

    print("\n[OK] Pipeline complete. Results in /results")

# -------------------------
# Entry Point
# -------------------------
if __name__ == "__main__":
    run_pipeline()