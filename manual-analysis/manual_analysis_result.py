"""
RQ2 & RQ3 Analysis Script
Produces all tables and figures needed for qualitative analysis sections.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import numpy as np
from pathlib import Path
from itertools import combinations

# ── Config ────────────────────────────────────────────────────────────────────
ECM_FILE       = Path("error-analysis/ecms_analysis.csv")
MODEL_FILES    = {
    "GPT":      Path("error-analysis/gpt5_2_defect_classification_analysis.csv"),
    "DeepSeek": Path("error-analysis/deepseek_v3_defect_classification_analysis.csv"),
    "Qwen3":    Path("error-analysis/qwen3_defect_classification_analysis.csv"),
}
OUT_DIR = Path("rq-outputs")
OUT_DIR.mkdir(exist_ok=True)

PALETTE = {"GPT": "#4C72B0", "DeepSeek": "#DD8452", "Qwen3": "#55A868"}

ERROR_TYPES   = ["FN", "FP", "MC"]
PRIMARY_ORDER = [
    "SEMANTIC_REASONING_FAILURE",
    "TAXONOMY_MAPPING_FAILURE",
    "INPUT_DEPENDENCE_FAILURE",
    "CONTESTABLE_CASE",
]
SECONDARY_ORDER = [
    "CAUSAL_MISUNDERSTANDING", "SCOPE_CONFUSION", "IMPLICIT_CONTEXT_MISSING",
    "BOUNDARY_AMBIGUITY", "WRONG_ADDRESSING",
    "KEYWORD_OVER_RELIANCE", "ENTITY_CONFUSION", "DEGENERATE_OUTPUT",
    "DEFECT_VS_FEATURE", "TAXONOMY_OVERLAP", "SPECIFIC_DEFECT",
]

# ── Load data ─────────────────────────────────────────────────────────────────
ecms = pd.read_csv(ECM_FILE)

models: dict[str, pd.DataFrame] = {}
for name, path in MODEL_FILES.items():
    df = pd.read_csv(path)
    df["model"] = name
    models[name] = df

all_models = pd.concat(models.values(), ignore_index=True)

# Merge ECM metadata into each model frame
all_merged = all_models.merge(
    ecms[["hash", "semantic_requirement", "label_certainty", "overall-note"]],
    on="hash", how="left"
)

# ── Helper ─────────────────────────────────────────────────────────────────────
def save(fig, name):
    p = OUT_DIR / name
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved → {p}")

def label_bars(ax, fmt="{:.0f}", fontsize=8):
    for bar in ax.patches:
        h = bar.get_height()
        if h > 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2, h + 0.2,
                fmt.format(h), ha="center", va="bottom", fontsize=fontsize
            )

# ══════════════════════════════════════════════════════════════════════════════
# RQ2 — Error Pattern Analysis
# ══════════════════════════════════════════════════════════════════════════════
print("\n── RQ2 ──────────────────────────────────────────────────────────────")

errors = all_merged[all_merged["outcome-type"].isin(ERROR_TYPES)].copy()

# ── RQ2-A: Outcome type distribution per model ────────────────────────────────
print("\n[RQ2-A] Outcome type distribution per model")
N_ECMS = 132
 
outcome_dist = (
    all_merged.groupby(["model", "outcome-type"])
    .size().unstack(fill_value=0)
)
for col in ["TP", "FN", "FP", "MC"]:
    if col not in outcome_dist.columns:
        outcome_dist[col] = 0
outcome_dist = outcome_dist[["TP", "FN", "FP", "MC"]]
outcome_dist["Total Errors"] = outcome_dist[["FN", "FP", "MC"]].sum(axis=1)
outcome_dist["Error Rate"] = (outcome_dist["Total Errors"] / N_ECMS).map("{:.1%}".format)
 
# Rate table: each outcome type as % of N_ECMS
outcome_rate = outcome_dist[["TP", "FN", "FP", "MC"]].div(N_ECMS).mul(100).round(1)
outcome_rate.columns = [f"{c} (%)" for c in outcome_rate.columns]
outcome_rate["Error Rate"] = outcome_dist["Error Rate"]
 
print("\nCount table:")
print(outcome_dist.to_string())
print("\nRate table (% of 132 ECMs):")
print(outcome_rate.to_string())
 
outcome_dist.to_csv(OUT_DIR / "rq2a_outcome_distribution_counts.csv")
outcome_rate.to_csv(OUT_DIR / "rq2a_outcome_distribution_rates.csv")
 
fig, ax = plt.subplots(figsize=(7, 4))
cols = [c for c in ["TP", "FN", "FP", "MC"] if c in outcome_dist.columns]
outcome_dist[cols].plot(kind="bar", ax=ax, colormap="Set2", edgecolor="white")
ax.set_title("Outcome Type Distribution per Model")
ax.set_xlabel("")
ax.set_ylabel("Count")
ax.set_xticklabels(outcome_dist.index, rotation=0)
ax.legend(title="Outcome", bbox_to_anchor=(1, 1))
label_bars(ax)
save(fig, "rq2a_outcome_distribution.png")
 
# Rate chart
fig, ax = plt.subplots(figsize=(7, 4))
rate_cols = [c for c in outcome_rate.columns if c != "Error Rate"]
outcome_rate[rate_cols].plot(kind="bar", ax=ax, colormap="Set2", edgecolor="white")
ax.set_title("Outcome Type Rate per Model (% of 132 ECMs)")
ax.set_xlabel("")
ax.set_ylabel("Rate (%)")
ax.set_xticklabels(outcome_rate.index, rotation=0)
ax.legend(title="Outcome", bbox_to_anchor=(1, 1))
label_bars(ax, fmt="{:.1f}")
save(fig, "rq2a_outcome_distribution_rates.png")


# ── RQ2-B: Primary error mechanism per model ──────────────────────────────────
print("\n[RQ2-B] Primary error mechanism per model")
prim_dist = (
    errors.groupby(["model", "mechanism-primary-tag"])
    .size().unstack(fill_value=0)
)
# reorder columns to defined order where present
cols = [c for c in PRIMARY_ORDER if c in prim_dist.columns]
prim_dist = prim_dist[cols]
print(prim_dist.to_string())
prim_dist.to_csv(OUT_DIR / "rq2b_primary_mechanism.csv")

fig, ax = plt.subplots(figsize=(9, 4))
prim_dist.plot(kind="bar", ax=ax, colormap="tab10", edgecolor="white")
ax.set_title("Primary Error Mechanism per Model")
ax.set_xlabel("")
ax.set_ylabel("Count")
ax.set_xticklabels(prim_dist.index, rotation=0)
ax.legend(title="Primary Tag", bbox_to_anchor=(1, 1), fontsize=7)
label_bars(ax)
save(fig, "rq2b_primary_mechanism.png")


# ── RQ2-C: Secondary tag breakdown (errors only, excl. CONTESTABLE_CASE) ────────
print("\n[RQ2-C] Secondary tag breakdown (true model errors only)")
true_errors = errors[errors["mechanism-primary-tag"] != "CONTESTABLE_CASE"].copy()
sec_dist = (
    true_errors.groupby(["model", "mechanism-secondary-tag"])
    .size().unstack(fill_value=0)
)
cols = [c for c in SECONDARY_ORDER if c in sec_dist.columns]
sec_dist = sec_dist[cols]
print(sec_dist.to_string())
sec_dist.to_csv(OUT_DIR / "rq2c_secondary_mechanism.csv")

fig, ax = plt.subplots(figsize=(11, 4))
sec_dist.plot(kind="bar", ax=ax, colormap="tab20", edgecolor="white")
ax.set_title("Secondary Error Mechanism per Model (True Errors Only)")
ax.set_xlabel("")
ax.set_ylabel("Count")
ax.set_xticklabels(sec_dist.index, rotation=0)
ax.legend(title="Secondary Tag", bbox_to_anchor=(1, 1), fontsize=7)
label_bars(ax)
save(fig, "rq2c_secondary_mechanism.png")


# ── RQ2-D: Errors by semantic_requirement ─────────────────────────────────────
print("\n[RQ2-D] Error rate by semantic_requirement")
sem_table = (
    all_merged.groupby(["model", "semantic_requirement", "outcome-type"])
    .size().unstack(fill_value=0)
)
print(sem_table.to_string())
sem_table.to_csv(OUT_DIR / "rq2d_errors_by_semantic_requirement.csv")

# Error rate (errors / total) per model × semantic_requirement
sem_rate = all_merged.copy()
sem_rate["is_error"] = sem_rate["outcome-type"].isin(ERROR_TYPES).astype(int)
sem_rate_agg = (
    sem_rate.groupby(["model", "semantic_requirement"])["is_error"]
    .agg(["sum", "count"])
    .rename(columns={"sum": "errors", "count": "total"})
)

print(sem_rate_agg.to_string())
sem_rate_agg["error_rate"] = sem_rate_agg["errors"] / sem_rate_agg["total"]
print(sem_rate_agg.to_string())
sem_rate_agg.to_csv(OUT_DIR / "rq2d_error_rate_by_semantic_requirement.csv")

pivot = sem_rate_agg["error_rate"].unstack(level="semantic_requirement")
fig, ax = plt.subplots(figsize=(7, 4))
pivot.plot(kind="bar", ax=ax, color=["#4e50d0", "#ff7f00", "#B2B2B2"], edgecolor="white")
ax.set_title("Error Rate by Semantic Requirement per Model")
ax.set_xlabel("")
ax.set_ylabel("Error Rate")
ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))
ax.set_xticklabels(pivot.index, rotation=0)
ax.legend(title="Semantic Req.", bbox_to_anchor=(1, 1))
save(fig, "rq2d_error_rate_by_semantic_requirement.png")


# ── RQ2-E: Per-category error breakdown ───────────────────────────────────────
print("\n[RQ2-E] Errors per oracle category per model")
cat_err = (
    errors.groupby(["model", "oracle-normalized"])
    .size().unstack(fill_value=0)
)
print(cat_err.to_string())
cat_err.to_csv(OUT_DIR / "rq2e_errors_per_category.csv")

fig, ax = plt.subplots(figsize=(11, 4))
cat_err.T.plot(kind="bar", ax=ax,
               color=["#4e50d0", "#ff7f00", "#B2B2B2"],
            #    color=[PALETTE[m] for m in cat_err.index],
               edgecolor="white")
ax.set_title("Error Count per Oracle Category and Model")
ax.set_xlabel("Oracle Category")
ax.set_ylabel("Error Count")
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
ax.legend(title="Model")
label_bars(ax)
save(fig, "rq2e_errors_per_category.png")


# ── RQ2-F: Primary mechanism heatmap (model × category) ──────────────────────
print("\n[RQ2-F] Primary mechanism heatmap")
for primary in PRIMARY_ORDER:
    subset = errors[errors["mechanism-primary-tag"] == primary]
    if subset.empty:
        continue
    heat = (
        subset.groupby(["model", "oracle-normalized"])
        .size().unstack(fill_value=0)
    )
    fig, ax = plt.subplots(figsize=(10, 3))
    sns.heatmap(heat, annot=True, fmt="d", cmap="YlOrRd",
                linewidths=0.5, ax=ax, cbar=False)
    ax.set_title(f"Error Count — {primary}")
    ax.set_xlabel("Oracle Category")
    ax.set_ylabel("")
    fname = f"rq2f_heatmap_{primary.lower()}.png"
    save(fig, fname)


# ══════════════════════════════════════════════════════════════════════════════
# RQ3 — Ambiguity Effects
# ══════════════════════════════════════════════════════════════════════════════
print("\n── RQ3 ──────────────────────────────────────────────────────────────")

# ── RQ3-A: CONTESTABLE_CASE vs true errors per model ───────────────────────────
print("\n[RQ3-A] Contestable case vs true error counts per model")
def classify_error(row):
    if row["outcome-type"] == "TP":
        return "True positive"
    if row["mechanism-primary-tag"] == "CONTESTABLE_CASE":
        return "Contestable case"
    if row["outcome-type"] in ERROR_TYPES:
        return "True error"
    return "OTHER"

all_merged["error_class"] = all_merged.apply(classify_error, axis=1)
contest_vs_true = (
    all_merged.groupby(["model", "error_class"])
    .size().unstack(fill_value=0)
)
print(contest_vs_true.to_string())
contest_vs_true.to_csv(OUT_DIR / "rq3a_contestable_vs_true_errors.csv")

cols = [c for c in ["True positive", "Contestable case", "True error"] if c in contest_vs_true.columns]
fig, ax = plt.subplots(figsize=(7, 4))
contest_vs_true[cols].plot(kind="bar", ax=ax,
                          color=["#4e50d0", "#ff7f00", "#B2B2B2"],
                          edgecolor="white")
ax.set_title("TP vs Contestable Cases vs True Errors per Model")
ax.set_xlabel("")
ax.set_ylabel("Count")
ax.set_xticklabels(contest_vs_true.index, rotation=0)
ax.legend(bbox_to_anchor=(1, 1))
label_bars(ax)
save(fig, "rq3a_contestable_vs_true_errors.png")

# ── RQ3-B: Error rate by label_certainty ─────────────────────────────────────
print("\n[RQ3-B] Error rate by label_certainty")
cert_rate = all_merged.copy()
cert_rate["is_error"] = cert_rate["outcome-type"].isin(ERROR_TYPES).astype(int)
cert_agg = (
    cert_rate.groupby(["model", "label_certainty"])["is_error"]
    .agg(["sum", "count"])
    .rename(columns={"sum": "errors", "count": "total"})
)
cert_agg["error_rate"] = cert_agg["errors"] / cert_agg["total"]
print(cert_agg.to_string())
cert_agg.to_csv(OUT_DIR / "rq3b_error_rate_by_label_certainty.csv")

pivot_cert = cert_agg["error_rate"].unstack(level="label_certainty")
fig, ax = plt.subplots(figsize=(6, 4))
pivot_cert.plot(kind="bar", ax=ax,
                color=["#66c2a5", "#fc8d62"], edgecolor="white")
ax.set_title("Error Rate by Label Certainty per Model")
ax.set_xlabel("")
ax.set_ylabel("Error Rate")
ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))
ax.set_xticklabels(pivot_cert.index, rotation=0)
ax.legend(title="Label Certainty", bbox_to_anchor=(1, 1))
save(fig, "rq3b_error_rate_by_label_certainty.png")

# ── RQ3-C: Contestable subtype breakdown per model ─────────────────────────────
print("\n[RQ3-C] Contestable subtype breakdown")
contest_cases = all_merged[all_merged["mechanism-primary-tag"] == "CONTESTABLE_CASE"]
contest_sub = (
    contest_cases.groupby(["model", "mechanism-secondary-tag"])
    .size().unstack(fill_value=0)
)
print(contest_sub.to_string())
contest_sub.to_csv(OUT_DIR / "rq3c_contestable_subtypes.csv")

fig, ax = plt.subplots(figsize=(7, 4))
contest_sub.plot(kind="bar", ax=ax, colormap="Set1", edgecolor="white")
ax.set_title("Contestable Case Subtypes per Model")
ax.set_xlabel("")
ax.set_ylabel("Count")
ax.set_xticklabels(contest_sub.index, rotation=0)
ax.legend(title="Subtype", bbox_to_anchor=(1, 1), fontsize=8)
label_bars(ax)
save(fig, "rq3c_contestable_subtypes.png")

# ── RQ3-D: Cross-model disagreement on ambiguous ECMs ────────────────────────
print("\n[RQ3-D] Cross-model disagreement on AMBIGUOUS label_certainty ECMs")
ambig_ecms = ecms[ecms["label_certainty"] == "AMBIGUOUS"]["hash"].tolist()

disagreement_rows = []
for h in ambig_ecms:
    predictions = {}
    for mname, df in models.items():
        row = df[df["hash"] == h]
        if not row.empty:
            predictions[mname] = row.iloc[0]["model-normalized"]
    if len(set(predictions.values())) > 1:
        entry = {"hash": h}
        entry.update(predictions)
        oracle_row = ecms[ecms["hash"] == h]
        entry["oracle"] = oracle_row.iloc[0]["oracle-normalized"] if not oracle_row.empty else "?"
        disagreement_rows.append(entry)

disagreement_df = pd.DataFrame(disagreement_rows)
print(f"  ECMs with cross-model disagreement: {len(disagreement_df)}")
print(disagreement_df.to_string(index=False))
disagreement_df.to_csv(OUT_DIR / "rq3d_cross_model_disagreement.csv", index=False)

print("#########")

# ── RQ3-D: Ambiguous label_certainty ECMs flagged as CONTESTABLE_CASE ──────────
print("\n[RQ3-D] AMBIGUOUS label_certainty ECMs where models flagged CONTESTABLE_CASE")
 
ambig_ecms_hashes = set(ecms[ecms["label_certainty"] == "AMBIGUOUS"]["hash"].tolist())
 
# For each ambiguous ECM, collect which models flagged it as CONTESTABLE_CASE
# and what alternative label they assigned
revision_rows = []
for h in ambig_ecms_hashes:
    oracle_label = ecms.loc[ecms["hash"] == h, "oracle-normalized"].values[0]
    row_entry = {"hash": h, "oracle": oracle_label}
    flagged_by = []
    for mname, df in models.items():
        mrow = df[df["hash"] == h]
        if not mrow.empty:
            primary = mrow.iloc[0]["mechanism-primary-tag"]
            secondary = mrow.iloc[0]["mechanism-secondary-tag"]
            pred = mrow.iloc[0]["model-normalized"]
            row_entry[f"{mname}_pred"] = pred
            row_entry[f"{mname}_primary"] = primary
            row_entry[f"{mname}_secondary"] = secondary
            if primary == "CONTESTABLE_CASE":
                flagged_by.append(mname)
    row_entry["flagged_by"] = ", ".join(flagged_by) if flagged_by else ""
    row_entry["flagged_count"] = len(flagged_by)
    revision_rows.append(row_entry)
 
revision_df = pd.DataFrame(revision_rows).sort_values(
    ["flagged_count", "oracle"], ascending=[False, True]
)
 
# Summary counts
total_ambig = len(ambig_ecms_hashes)
flagged_any   = revision_df[revision_df["flagged_count"] >= 1]
flagged_all   = revision_df[revision_df["flagged_count"] == 3]
flagged_two   = revision_df[revision_df["flagged_count"] == 2]
flagged_one   = revision_df[revision_df["flagged_count"] == 1]
 
print(f"\n  Total AMBIGUOUS label_certainty ECMs : {total_ambig}")
print(f"  Flagged as CONTESTABLE_CASE by all 3   : {len(flagged_all)}")
print(f"  Flagged by exactly 2 models          : {len(flagged_two)}")
print(f"  Flagged by exactly 1 model           : {len(flagged_one)}")
print(f"  Flagged by at least 1 model          : {len(flagged_any)}")
print(f"  Not flagged by any model             : {total_ambig - len(flagged_any)}")
 
print("\n  ECMs flagged by all 3 models (strongest revision candidates):")
print(flagged_all[["hash", "oracle",
                    "GPT_pred", "DeepSeek_pred", "Qwen3_pred",
                    "GPT_secondary", "DeepSeek_secondary", "Qwen3_secondary"]
                  ].to_string(index=False))
 
print("\n  ECMs flagged by exactly 2 models:")
print(flagged_two[["hash", "oracle",
                   "GPT_pred", "DeepSeek_pred", "Qwen3_pred",
                   "flagged_by"]].to_string(index=False))
 
# Alternative labels suggested in contestable cases (all flagged ECMs)
contest_case_rows = all_merged[
    (all_merged["mechanism-primary-tag"] == "CONTESTABLE_CASE") &
    (all_merged["hash"].isin(ambig_ecms_hashes))
]
alt_label_dist = (
    contest_case_rows.groupby(["oracle-normalized", "model-normalized"])
    .size().unstack(fill_value=0)
)
print("\n  Alternative labels suggested (oracle × model prediction):")
print(alt_label_dist.to_string())
 
revision_df.to_csv(OUT_DIR / "rq3d_oracle_revision_candidates.csv", index=False)
alt_label_dist.to_csv(OUT_DIR / "rq3d_alternative_labels_by_oracle.csv")
print("  saved → rq-outputs/rq3d_oracle_revision_candidates.csv")


# ── RQ3-E: Oracle category distribution among AMBIGUOUS ECMs ─────────────────
print("\n[RQ3-E] Oracle category distribution among AMBIGUOUS label_certainty ECMs")
ambig_oracle = ecms[ecms["label_certainty"] == "AMBIGUOUS"]["oracle-normalized"].value_counts()
print(ambig_oracle.to_string())
ambig_oracle.to_csv(OUT_DIR / "rq3e_ambiguous_oracle_distribution.csv")

fig, ax = plt.subplots(figsize=(8, 4))
ambig_oracle.plot(kind="bar", ax=ax, color="#8da0cb", edgecolor="white")
ax.set_title("Oracle Category Distribution — AMBIGUOUS ECMs")
ax.set_xlabel("Oracle Category")
ax.set_ylabel("Count")
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
label_bars(ax)
save(fig, "rq3e_ambiguous_oracle_distribution.png")

# ── RQ3-F: Semantic requirement × label certainty interaction ─────────────────
print("\n[RQ3-F] Semantic requirement × label certainty error rate interaction")
interaction = all_merged.copy()
interaction["is_error"] = interaction["outcome-type"].isin(ERROR_TYPES).astype(int)
inter_agg = (
    interaction.groupby(["semantic_requirement", "label_certainty"])["is_error"]
    .agg(["sum", "count"])
    .rename(columns={"sum": "errors", "count": "total"})
)
inter_agg["error_rate"] = inter_agg["errors"] / inter_agg["total"]
print(inter_agg.to_string())
inter_agg.to_csv(OUT_DIR / "rq3f_semantic_x_certainty_interaction.csv")

pivot_inter = inter_agg["error_rate"].unstack(level="label_certainty")
fig, ax = plt.subplots(figsize=(7, 4))
pivot_inter.plot(kind="bar", ax=ax,
                 color=["#66c2a5", "#fc8d62"], edgecolor="white")
ax.set_title("Error Rate by Semantic Requirement × Label Certainty\n(all models combined)")
ax.set_xlabel("Semantic Requirement")
ax.set_ylabel("Error Rate")
ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))
ax.set_xticklabels(pivot_inter.index, rotation=0)
ax.legend(title="Label Certainty", bbox_to_anchor=(1, 1))
save(fig, "rq3f_semantic_x_certainty_interaction.png")

# ── RQ3-G: ACID Tool: Semantic requirement × label certainty interaction ─────────────────
print("\n[RQ3-G] ACID — Semantic requirement × label certainty error rate interaction")

ACID_FILE = Path("../oracle/oracle_acid_answers.csv")
acid = pd.read_csv(ACID_FILE)

acid_merged = acid.merge(
    ecms[["hash", "semantic_requirement", "label_certainty"]],
    on="hash", how="left"
)

# ACID has no outcome-type column — an error is simply acid-normalized != oracle-normalized
acid_merged["is_error"] = (
    acid_merged["acid-normalized"] != acid_merged["oracle-normalized"]
).astype(int)

acid_inter_agg = (
    acid_merged.groupby(["semantic_requirement", "label_certainty"])["is_error"]
    .agg(["sum", "count"])
    .rename(columns={"sum": "errors", "count": "total"})
)
acid_inter_agg["error_rate"] = acid_inter_agg["errors"] / acid_inter_agg["total"]
print(acid_inter_agg.to_string())
acid_inter_agg.to_csv(OUT_DIR / "rq3g_acid_semantic_x_certainty_interaction.csv")

acid_pivot_inter = acid_inter_agg["error_rate"].unstack(level="label_certainty")
fig, ax = plt.subplots(figsize=(7, 4))
acid_pivot_inter.plot(kind="bar", ax=ax,
                 color=["#4e50d0", "#ff7f00"], edgecolor="white")
ax.set_title("ACID Error Rate by Semantic Requirement × Label Certainty")
ax.set_xlabel("Semantic Requirement")
ax.set_ylabel("Error Rate")
ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))
ax.set_xticklabels(acid_pivot_inter.index, rotation=0)
ax.legend(title="Label Certainty", bbox_to_anchor=(1, 1))
save(fig, "rq3g_acid_semantic_x_certainty_interaction.png")

# ══════════════════════════════════════════════════════════════════════════════
# Summary tables for paper
# ══════════════════════════════════════════════════════════════════════════════
print("\n── Summary tables ───────────────────────────────────────────────────")

# Table: overall counts per model
summary = all_merged.groupby("model")["outcome-type"].value_counts().unstack(fill_value=0)
for col in ["TP", "FN", "FP", "MC"]:
    if col not in summary:
        summary[col] = 0
summary = summary[["TP", "FN", "FP", "MC"]]
summary["Total Errors"] = summary[["FN", "FP", "MC"]].sum(axis=1)
summary["Error Rate"] = (summary["Total Errors"] / summary.sum(axis=1).sub(summary["Total Errors"]).add(summary["Total Errors"])).map("{:.1%}".format)
print("\nOutcome summary:")
print(summary.to_string())
summary.to_csv(OUT_DIR / "summary_outcome_per_model.csv")

# Table: contestable share of all non-TP outcomes
non_tp = all_merged[all_merged["outcome-type"] != "TP"]
contest_share = (
    non_tp.groupby("model")
    .apply(lambda x: (x["mechanism-primary-tag"] == "CONTESTABLE_CASE").sum() / len(x))
    .rename("contestable_share_of_errors")
    .map("{:.1%}".format)
)
print("\nContestable share of non-TP outcomes per model:")
print(contest_share.to_string())
contest_share.to_csv(OUT_DIR / "summary_contestable_share.csv")

print("\n✓ All outputs written to:", OUT_DIR.resolve())


# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION_DATA Deep-Dive
# Supports the claim that CD acts as a residual/attractor label
# ══════════════════════════════════════════════════════════════════════════════
print("\n── CONFIGURATION_DATA deep-dive ─────────────────────────────────────")
 
CATEGORY = "CONFIGURATION_DATA"
 
# ── CD-1: Label certainty breakdown for Oracle = CONFIGURATION_DATA ───────────
print(f"\n[CD-1] Label certainty for Oracle == {CATEGORY}")
cd_ecms = ecms[ecms["oracle-normalized"] == CATEGORY]
cd_certainty = cd_ecms["label_certainty"].value_counts()
cd_certainty_pct = (cd_certainty / len(cd_ecms) * 100).round(1)
cd_summary = pd.DataFrame({"count": cd_certainty, "pct": cd_certainty_pct})
print(f"  Total ECMs with Oracle={CATEGORY}: {len(cd_ecms)}")
print(cd_summary.to_string())
cd_summary.to_csv(OUT_DIR / "cd1_label_certainty.csv")
 
# ── CD-2: What models predicted when Oracle = CONFIGURATION_DATA ──────────────
print(f"\n[CD-2] Model predictions when Oracle == {CATEGORY}")
cd_model = all_merged[all_merged["oracle-normalized"] == CATEGORY]
cd_pred = (
    cd_model.groupby(["model", "model-normalized"])
    .size().unstack(fill_value=0)
)
print(cd_pred.to_string())
cd_pred.to_csv(OUT_DIR / "cd2_model_predictions_for_cd.csv")
 
# Outcome type breakdown for CD oracle instances
cd_outcomes = (
    cd_model.groupby(["model", "outcome-type"])
    .size().unstack(fill_value=0)
)
print("\n  Outcome types:")
print(cd_outcomes.to_string())
cd_outcomes.to_csv(OUT_DIR / "cd2_outcome_types_for_cd.csv")
 
# ── CD-3: Contestable cases where Oracle=CD — what did models predict? ──────────
print(f"\n[CD-3] Contestable cases for Oracle == {CATEGORY}")
cd_contest = cd_model[cd_model["mechanism-primary-tag"] == "CONTESTABLE_CASE"].copy()
print(f"  Total contestable cases: {len(cd_contest)}")
 
cd_contest_detail = cd_contest[[
    "hash", "model", "oracle-normalized", "model-normalized",
    "mechanism-secondary-tag", "label_certainty", "word-note"
]].sort_values(["hash", "model"])
print(cd_contest_detail.to_string(index=False))
cd_contest_detail.to_csv(OUT_DIR / "cd3_contestable_cases_detail.csv", index=False)
 
# What alternative labels did models assign in contestable cases?
cd_contest_labels = (
    cd_contest.groupby(["model", "model-normalized"])
    .size().unstack(fill_value=0)
)
print("\n  Alternative labels assigned in contestable cases:")
print(cd_contest_labels.to_string())
cd_contest_labels.to_csv(OUT_DIR / "cd3_contestable_alternative_labels.csv")
 
# ── CD-4: Wrong predictions for CD — which categories did models assign? ───────
print(f"\n[CD-4] Misclassification targets when Oracle == {CATEGORY}")
cd_wrong = cd_model[cd_model["outcome-type"].isin(["MC", "FN"])].copy()
cd_wrong_labels = (
    cd_wrong.groupby(["model", "model-normalized"])
    .size().unstack(fill_value=0)
)
print(cd_wrong_labels.to_string())
cd_wrong_labels.to_csv(OUT_DIR / "cd4_misclassification_targets.csv")
 
# ── CD-5: Attractor check — models that assigned CD when Oracle != CD ──────────
print(f"\n[CD-5] Attractor check: model predicted {CATEGORY} but Oracle != {CATEGORY}")
cd_attractor = all_merged[
    (all_merged["model-normalized"] == CATEGORY) &
    (all_merged["oracle-normalized"] != CATEGORY)
].copy()
attractor_counts = cd_attractor.groupby(["model", "oracle-normalized"]).size().unstack(fill_value=0)
print(f"  Total false CD predictions: {len(cd_attractor)}")
print(attractor_counts.to_string())
attractor_counts.to_csv(OUT_DIR / "cd5_attractor_false_cd_predictions.csv")
 
# Summary: attractor rate per model
attractor_rate = cd_attractor.groupby("model").size().rename("false_CD_predictions")
total_cd_preds = all_merged[all_merged["model-normalized"] == CATEGORY].groupby("model").size().rename("total_CD_predictions")
attractor_summary = pd.concat([attractor_rate, total_cd_preds], axis=1).fillna(0)
attractor_summary["attractor_rate"] = (
    attractor_summary["false_CD_predictions"] / attractor_summary["total_CD_predictions"]
).map("{:.1%}".format)
print("\n  Attractor rate (false CD / total CD predictions):")
print(attractor_summary.to_string())
attractor_summary.to_csv(OUT_DIR / "cd5_attractor_rate_summary.csv")

# ── CD-6: Label certainty distribution across ALL categories ──────────────────
print("\n[CD-6] Ambiguity proportion per Oracle category (to verify CD claim)")
certainty_by_cat = (
    ecms.groupby(["oracle-normalized", "label_certainty"])
    .size().unstack(fill_value=0)
)
certainty_by_cat["total"] = certainty_by_cat.sum(axis=1)
certainty_by_cat["ambiguous_pct"] = (
    certainty_by_cat.get("AMBIGUOUS", 0) / certainty_by_cat["total"] * 100
).round(1)
certainty_by_cat = certainty_by_cat.sort_values("ambiguous_pct", ascending=False)
print(certainty_by_cat.to_string())
certainty_by_cat.to_csv(OUT_DIR / "cd6_ambiguity_pct_by_category.csv")

# ── CD-7: Outcome error rate with and without contestable cases ─────────────────
print("\n[CD-7] Error rate comparison: with vs without contestable cases")

cd_model_data = all_merged[all_merged["oracle-normalized"] == CATEGORY].copy()

results = []
for mname in ["DeepSeek", "GPT", "Qwen3"]:
    m = cd_model_data[cd_model_data["model"] == mname]
    n = len(m)

    # With contestable cases counted as errors
    errors_with = m[m["outcome-type"].isin(ERROR_TYPES)]
    rate_with = len(errors_with) / n

    # Without contestable cases (exclude CONTESTABLE_CASE from error count)
    true_errors = errors_with[
        errors_with["mechanism-primary-tag"] != "CONTESTABLE_CASE"
    ]
    rate_without = len(true_errors) / n

    # Breakdown of outcome types
    tp  = len(m[m["outcome-type"] == "TP"])
    fn  = len(m[m["outcome-type"] == "FN"])
    fp  = len(m[m["outcome-type"] == "FP"])
    mc  = len(m[m["outcome-type"] == "MC"])
    contest = len(
        errors_with[errors_with["mechanism-primary-tag"] == "CONTESTABLE_CASE"]
    )

    results.append({
        "Model":              mname,
        "N (CD ECMs)":        n,
        "TP":                 tp,
        "FN":                 fn,
        "FP":                 fp,
        "MC":                 mc,
        "Contestable Cases":  contest,
        "True Errors":        len(true_errors),
        "Error Rate (w/ AC)": f"{rate_with:.1%}",
        "Error Rate (w/o AC)":f"{rate_without:.1%}",
    })

cd7_df = pd.DataFrame(results)
print(cd7_df.to_string(index=False))
cd7_df.to_csv(OUT_DIR / "cd7_error_rate_with_without_contestable.csv", index=False)

# print("\n✓ CONFIGURATION_DATA deep-dive complete.")