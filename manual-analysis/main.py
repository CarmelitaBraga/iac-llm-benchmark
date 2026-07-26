import os
import csv
import pandas as pd
from colorama import Fore, Style, init

init(autoreset=True)

# -------------------------
# CONFIG
# -------------------------
ORACLE_DATASET = "../oracle/oracle_full.csv"
FINAL_COMPARISON = "../results/final_comparison.csv"
MODELS_DIR = "../models-answer"
OUTPUT_DIR = "outputs"

ECMS_ANALYSIS_FILE = os.path.join(OUTPUT_DIR, "ecms_analysis.csv")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# -------------------------
# NORMALIZATION
# -------------------------
def normalize(text):
    return str(text).strip().upper().replace(" ", "_")

# -------------------------
# LOADERS
# -------------------------
oracle_df = pd.read_csv(ORACLE_DATASET)
final_df = pd.read_csv(FINAL_COMPARISON)

model_files = {
    f.replace(".csv", ""): pd.read_csv(os.path.join(MODELS_DIR, f))
    for f in os.listdir(MODELS_DIR) if f.endswith(".csv")
}

# -------------------------
# RESUME LOGIC
# -------------------------
def get_processed_hashes():
    if not os.path.exists(ECMS_ANALYSIS_FILE):
        return set()
    df = pd.read_csv(ECMS_ANALYSIS_FILE)
    return set(df["hash"].unique())

processed_hashes = get_processed_hashes()

# -------------------------
# DIFF RENDERER
# -------------------------
def render_diff(diff_text):
    for line in str(diff_text).split("\n"):
        if line.startswith("+"):
            print(Fore.GREEN + line)
        elif line.startswith("-"):
            print(Fore.RED + line)
        else:
            print(Style.DIM + line)

# -------------------------
# NEW ANNOTATION AXES
# -------------------------
def ask_semantic_requirement():
    print("\nSemantic requirement:")
    print("1 - SYNTACTIC")
    print("2 - SEMANTIC")
    print("3 - AMBIGUOUS")
    val = input("Choice: ")
    return {
        "1": "SYNTACTIC",
        "2": "SEMANTIC",
        "3": "AMBIGUOUS"
    }.get(val, "AMBIGUOUS")

def ask_label_certainty():
    print("\nLabel certainty:")
    print("1 - CLEAR")
    print("2 - AMBIGUOUS")
    val = input("Choice: ")
    return {
        "1": "CLEAR",
        "2": "AMBIGUOUS"
    }.get(val, "AMBIGUOUS")

# -------------------------
# OUTCOME LOGIC (unchanged)
# -------------------------
def collect_outcome(pred, oracle):
    if oracle == "NO_DEFECT" and pred != "NO_DEFECT":
        return "FP"
    elif oracle != "NO_DEFECT" and pred == "NO_DEFECT":
        return "FN"
    else:
        return "MC"

# -------------------------
# MECHANISM (NEW HIERARCHY)
# -------------------------
def ask_mechanism():
    print("\nPrimary mechanism type:")
    primary_options = [
        "SEMANTIC_REASONING_FAILURE",
        "TAXONOMY_MAPPING_FAILURE",
        "INPUT_DEPENDENCE_FAILURE",
        "CONTESTABLE_CASE"
    ]

    for i, opt in enumerate(primary_options, 1):
        print(f"{i} - {opt}")

    val = input("Choice: ")
    primary = primary_options[int(val)-1] if val.isdigit() else "CONTESTABLE_CASE"

    # Subtypes mapped to primary types
    subtype_map = {
        "SEMANTIC_REASONING_FAILURE": [
            "CAUSAL_MISUNDERSTANDING",
            "SCOPE_CONFUSION",
            "IMPLICIT_CONTEXT_MISSING"
        ],
        "TAXONOMY_MAPPING_FAILURE": [
            "CATEGORY_BOUNDARY_AMBIGUITY",
            "OVER_GENERALIZATION",
            "WRONG_ADDRESSING_CATEGORY"
        ],
        "INPUT_DEPENDENCE_FAILURE": [
            "KEYWORD_OVER_RELIANCE",
            "ENTITY_CONFUSION",
            "DEGENERATE_OUTPUT"
        ],
        "CONTESTABLE_CASE": [
            "DEFECT_VS_FEATURE",
            "TAXONOMY_OVERLAP",
            "SPECIFIC_DEFECT"
        ]
    }

    print("\nSubtype:")
    options = subtype_map[primary]

    for i, opt in enumerate(options, 1):
        print(f"{i} - {opt}")

    val2 = input("Choice: ")
    subtype = options[int(val2)-1] if val2.isdigit() else options[0]

    return primary, subtype

# -------------------------
# SAVE HELPER
# -------------------------
def append_csv(file, row, header):
    write_header = not os.path.exists(file)
    with open(file, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        if write_header:
            writer.writeheader()
        writer.writerow(row)

# -------------------------
# MAIN LOOP
# -------------------------
for _, row in oracle_df.iterrows():
    hash_id = row["hash"]

    if hash_id in processed_hashes:
        continue

    print("\n" + "="*80)
    print(Fore.CYAN + f"COMMIT: {hash_id}")
    print("="*80)

    # HEADER
    print(Fore.YELLOW + "\nWhat defect story is being told here?\n")
    print(Fore.WHITE + row["commit-message"])

    # DIFF
    print("\n--- DIFF ---")
    render_diff(row["commit-diff"])

    # ORACLE
    oracle_val = normalize(
        final_df.loc[final_df["hash"] == hash_id, "oracle"].values[0]
    )
    print(Fore.MAGENTA + f"\n[ORACLE NORMALIZED]: {oracle_val}")

    # EXPLANATIONS
    print(Style.DIM + f"\nC1: {row.get('c1-explanation-english', 'N/A')}")
    print(Style.DIM + f"C2: {row.get('c2-explanation-english', 'N/A')}")

    # ACID
    acid_val = final_df.loc[final_df["hash"] == hash_id, "acid"].values[0]
    print(Fore.BLUE + f"\n[ACID]: {acid_val}")

    # -------------------------
    # NEW ANNOTATION
    # -------------------------
    semantic_req = ask_semantic_requirement()
    label_cert = ask_label_certainty()

    append_csv(
        ECMS_ANALYSIS_FILE,
        {
            "hash": hash_id,
            "oracle-normalized": oracle_val,
            "semantic_requirement": semantic_req,
            "label_certainty": label_cert,
            "overall-note": ""
        },
        ["hash", "oracle-normalized", "semantic_requirement", "label_certainty", "overall-note"]
    )

    # -------------------------
    # MODEL LOOP
    # -------------------------
    for model_name, df_model in model_files.items():
        print("\n" + "-"*60)
        print(Fore.CYAN + f"MODEL: {model_name}")
        print("-"*60)

        match = df_model[df_model["hash"] == hash_id]

        if match.empty:
            print("No answer.")
            continue

        pred = normalize(match.iloc[0]["defect_category"])
        reason = match.iloc[0]["reason"]

        print(f"Prediction: {pred}")
        print(f"Reason: {reason}")

        if pred == oracle_val:
            outcome = "TP"
            primary = ""
            secondary = ""
            note = ""
        else:
            outcome = collect_outcome(pred, oracle_val)
            primary, secondary = ask_mechanism()
            note = input("Optional note (5-10 words): ")

        out_file = os.path.join(OUTPUT_DIR, f"{model_name}_analysis.csv")

        append_csv(
            out_file,
            {
                "hash": hash_id,
                "oracle-normalized": oracle_val,
                "model-normalized": pred,
                "outcome-type": outcome,
                "mechanism-primary-tag": primary,
                "mechanism-secondary-tag": secondary,
                "word-note": note
            },
            [
                "hash",
                "oracle-normalized",
                "model-normalized",
                "outcome-type",
                "mechanism-primary-tag",
                "mechanism-secondary-tag",
                "word-note"
            ]
        )

    # -------------------------
    # OVERALL NOTE
    # -------------------------
    print("\nDecision-relevant note? (optional)")
    overall_note = input("Your note: ")

    df_tmp = pd.read_csv(ECMS_ANALYSIS_FILE)
    df_tmp.loc[df_tmp["hash"] == hash_id, "overall-note"] = str(overall_note)
    df_tmp.to_csv(ECMS_ANALYSIS_FILE, index=False)

    os.system('clear')

print("\nDONE.")