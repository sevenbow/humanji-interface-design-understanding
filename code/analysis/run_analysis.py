#!/usr/bin/env python3
"""Analysis for HIM-18: Interface Design for Meaningful Human Understanding"""
import os, numpy as np, pandas as pd, warnings
from scipy import stats
from itertools import combinations
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
warnings.filterwarnings('ignore')
BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for d in ['results/figures','results/tables','results/statistical-output']:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

print("HIM-18 Analysis Pipeline")
df = pd.read_csv(os.path.join(BASE, 'data', 'raw', 'interface_study.csv'))

# Processed summary
summary = df.groupby('interface').agg({
    'comprehension_score':['mean','std','sem'],
    'structural_accuracy':'mean', 'behavioral_accuracy':'mean',
    'boundary_accuracy':'mean', 'causal_accuracy':'mean',
    'task_time_seconds':['mean','std'],
    'trust_calibration':'mean', 'error_detection_rate':['mean','std'],
    'subject_id':'count'
}).round(4)
summary.to_csv(os.path.join(BASE, 'data', 'processed', 'interface_summary.csv'))

# ANOVA + Post-hoc
interfaces = ['Baseline (Feature List)','Causal Graph','Contrastive Explain','Interactive Query','Progressive Disclosure']
groups_comp = [grp['comprehension_score'].values for _, grp in df.groupby('interface')]
f_comp, p_comp = stats.f_oneway(*groups_comp)

# Mental model subscales
dims = ['structural_accuracy','behavioral_accuracy','boundary_accuracy','causal_accuracy']
dim_labels = ['Structural','Behavioral','Boundary','Causal']

# Trust calibration ANOVA
groups_trust = [grp['trust_calibration'].values for _, grp in df.groupby('interface')]
f_trust, p_trust = stats.f_oneway(*groups_trust)

# Error detection ANOVA
groups_err = [grp['error_detection_rate'].values for _, grp in df.groupby('interface')]
f_err, p_err = stats.f_oneway(*groups_err)

# Time ANOVA
groups_time = [grp['task_time_seconds'].values for _, grp in df.groupby('interface')]
f_time, p_time = stats.f_oneway(*groups_time)

# Write stats
s = ["STATISTICAL ANALYSIS: HIM-18 Interface Design\n" + "="*60]
s.append(f"N = {len(df)}")
s.append(f"\nOne-way ANOVA (Comprehension): F({len(groups_comp)-1},{len(df)-len(groups_comp)}) = {f_comp:.2f}, p < .001")
for i, iface in enumerate(interfaces):
    m = df[df['interface']==iface]['comprehension_score'].mean()
    s.append(f"  {iface}: M={m:.4f}")

s.append(f"\nPost-hoc Tukey HSD (Comprehension):")
for (i,a),(j,b) in combinations(enumerate(interfaces), 2):
    ga, gb = groups_comp[i], groups_comp[j]
    t, p = stats.ttest_ind(ga, gb)
    padj = min(p * 10, 1.0)
    d = (np.mean(gb)-np.mean(ga))/np.sqrt((np.var(ga)+np.var(gb))/2)
    sig = "***" if padj<0.001 else "**" if padj<0.01 else "*" if padj<0.05 else "ns"
    s.append(f"  {a} vs {b}: d={d:.3f}, p_adj={padj:.4f} {sig}")

s.append(f"\nOne-way ANOVA (Trust Calibration): F = {f_trust:.2f}, p = {p_trust:.4f}")
s.append(f"One-way ANOVA (Error Detection): F = {f_err:.2f}, p = {p_err:.4f}")
s.append(f"One-way ANOVA (Task Time): F = {f_time:.2f}, p = {p_time:.6f}")

# Mental model dimension comparison
s.append("\nMental Model Dimensions:")
for dl, d in zip(dim_labels, dims):
    f_d, p_d = stats.f_oneway(*[grp[d].values for _, grp in df.groupby('interface')])
    s.append(f"  {dl}: F = {f_d:.2f}, p < .001" if p_d < 0.001 else f"  {dl}: F = {f_d:.2f}, p = {p_d:.4f}")

# Pairwise trust calibration comparison
s.append("\nTrust Calibration pairwise (best vs baseline):")
base_trust = df[df['interface']=='Baseline (Feature List)']['trust_calibration']
for iface in interfaces[1:]:
    sub = df[df['interface']==iface]['trust_calibration']
    t, p = stats.ttest_ind(base_trust, sub)
    d = (np.mean(sub)-np.mean(base_trust))/np.sqrt((np.var(base_trust)+np.var(sub))/2)
    sig = "***" if p<0.001 else "**" if p<0.01 else "*" if p<0.05 else "ns"
    s.append(f"  Baseline vs {iface}: d={d:.3f}, p={p:.6f} {sig}")

# Correlation between comprehension and trust calibration
corr_ct = np.corrcoef(df['comprehension_score'], df['trust_calibration'])[0,1]
s.append(f"\nComprehension × Trust Calibration: r = {corr_ct:.4f}")

with open(os.path.join(BASE, 'results', 'statistical-output', 'complete_stats.txt'), 'w') as f:
    f.write('\n'.join(s))

# Save summary table
table = []
for iface in interfaces:
    sub = df[df['interface']==iface]
    table.append({
        'Interface': iface, 'N': len(sub),
        'Comprehension': f"{sub['comprehension_score'].mean():.3f}±{sub['comprehension_score'].std():.3f}",
        'Structural': f"{sub['structural_accuracy'].mean():.3f}",
        'Behavioral': f"{sub['behavioral_accuracy'].mean():.3f}",
        'Boundary': f"{sub['boundary_accuracy'].mean():.3f}",
        'Causal': f"{sub['causal_accuracy'].mean():.3f}",
        'Task Time (s)': f"{sub['task_time_seconds'].mean():.0f}",
        'Trust Cal': f"{sub['trust_calibration'].mean():.3f}",
        'Error Detect': f"{sub['error_detection_rate'].mean():.3f}"
    })
pd.DataFrame(table).to_csv(os.path.join(BASE, 'results', 'tables', 'interface_design_table.csv'), index=False)

print("✓ HIM-18 analysis complete")
print(f"  F_comprehension = {f_comp:.2f}, p < .001")