import pandas as pd

# Input file (columns of commit-diff and commit-message adjusted)
INPUT_FILE = "final-data-off-brief.xlsx"
SHEET_NAME = "oracle"

# Mapping for normalized label columns
MAP_ORACLE_ANSWERS = {
    "Hash": "hash",
    "Oracle": "oracle-normalized",
    "ACID": "acid-normalized"
}
INPUT_ANSWERS_FILE = "final-oracle-go8-replication.csv"

# Outputs
FULL_OUTPUT = "oracle_full.csv"
ANSWERED_OUTPUT = "oracle_dataset.csv"
WITHOUT_ANSWERS_OUTPUT = "oracle_dataset_without_answers.csv"
LABELS_OUTPUT = "oracle_acid_answers.csv"

# Columns of interest
COLUMNS_STEP2 = [
    "hash",
    "link",
    "commit-message",
    "commit-diff",
    "oracle-normalized",
    "acid-normalized"
]

COLUMNS_STEP3 = [
    "hash",
    "link",
    "commit-diff",
    "commit-message",
]

COLUMNS_STEP4 = [
    "hash",
    "oracle-normalized",
    "acid-normalized"
]

def main():
    # Load Excel sheet
    df = pd.read_excel(INPUT_FILE, sheet_name=SHEET_NAME)

    # ---------------------------
    # 1. Save full dataset
    # ---------------------------
    df.to_csv(FULL_OUTPUT, index=False)
    print(f"[OK] Full dataset saved to: {FULL_OUTPUT}")

    # ---------------------------
    # 2. Save answered dataset (same data, selected columns)
    # ---------------------------
    df_answered = df[COLUMNS_STEP2]
    df_answered.to_csv(ANSWERED_OUTPUT, index=False)
    print(f"[OK] Answered dataset saved to: {ANSWERED_OUTPUT}")

    # ---------------------------
    # 3. Save without answers
    # ---------------------------
    df_without_answers = df[COLUMNS_STEP3]
    df_without_answers.to_csv(WITHOUT_ANSWERS_OUTPUT, index=False)
    print(f"[OK] Hash-only dataset saved to: {WITHOUT_ANSWERS_OUTPUT}")

    # ---------------------------
    # 4. Save labels only
    # ---------------------------
    df_labels = pd.read_csv(INPUT_ANSWERS_FILE)[list(MAP_ORACLE_ANSWERS.keys())]
    df_labels = df_labels.rename(columns=MAP_ORACLE_ANSWERS)
    df_labels.to_csv(LABELS_OUTPUT, index=False)

    # Note: This result comes directly from the data-off-brief (not updated)
    # df_labels = df[COLUMNS_STEP4]
    # df_labels.to_csv(LABELS_OUTPUT, index=False)
    # print(f"[OK] Labels-only dataset saved to: {LABELS_OUTPUT}")

    # ---------------------------
    # Distribution check
    # ---------------------------
    distribution = df["oracle-normalized"].value_counts()
    print("\n[INFO] Category distribution:")
    print(distribution)

    # ---------------------------
    # Hash uniqueness check
    # ---------------------------
    total_hashes = len(df)
    unique_hashes = df["hash"].nunique()

    print("\n[INFO] Hash uniqueness check:")
    print(f"Total hashes: {total_hashes}")
    print(f"Unique hashes: {unique_hashes}")

    if total_hashes == unique_hashes:
        print("[OK] All hashes are unique.")
    else:
        print("[WARNING] Duplicate hashes detected!")


if __name__ == "__main__":
    main()
