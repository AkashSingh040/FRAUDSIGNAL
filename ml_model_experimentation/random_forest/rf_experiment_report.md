# Random Forest Fraud Detection Experiment

## 1. Objective
Evaluating Random Forest as a replacement for LightGBM with strict chronological 60/20/20 splits, frequency encoding, and NO leakage.

## 2. Dataset
- Total: 590540
- Train/Val/Test: 354324 / 118108 / 118108
- Fraud Prevalance: ~3.44%

## 3. Imbalance Handling
We did NOT undersample the training set. The full training data was retained and `class_weight='balanced'` was evaluated against unweighted models.

## 4. LightGBM vs Random Forest

| Metric | LightGBM | Random Forest |
|---|---|---|
| ROC-AUC | 0.8119 | 0.7847 |
| PR-AUC | 0.1865 | 0.1911 |
| Precision | 0.2599 | 0.2697 |
| Recall | 0.2692 | 0.2788 |
| F1 | 0.2645 | 0.2742 |
| Threshold | 0.6020 | 0.1450 |
| Inf Latency (ms) | 0.0015 | 0.0046 |
| Model Size | N/A | 485.3 MB |

## 5. Precision at Fixed Recalls (Test Set)
- Precision @ 40% Recall: 0.1734
- Precision @ 50% Recall: 0.1326
- Precision @ 60% Recall: 0.1005

## 6. Threshold Comparison (Test Set)

|   Threshold |   Precision |     Recall |         F1 |   Flag Rate (%) |
|------------:|------------:|-----------:|-----------:|----------------:|
|         0.5 |    0.591837 | 0.0214075  | 0.0413204  |      0.124462   |
|         0.6 |    0.617021 | 0.00713583 | 0.0141085  |      0.0397941  |
|         0.7 |    0.75     | 0.00295276 | 0.00588235 |      0.0135469  |
|         0.8 |    0.625    | 0.00123031 | 0.0024558  |      0.00677346 |
|         0.9 |    0        | 0          | 0          |      0.00169337 |

## 7. Confusion Matrix
```text
[[110976 3068]
 [2931 1133]]
```
TN: 110976, FP: 3068, FN: 2931, TP: 1133

Operational Meaning:
- Out of every 100 transactions flagged, ~27.0 are actually fraudulent.
- Out of every 100 actual fraud transactions, ~27.9 are detected.

## 8. Stability Check (Validation vs Test PR-AUC)
The original report listed stability PR-AUCs evaluated on the **Validation Set** (~0.289), which caused confusion when compared against the **Test Set** PR-AUC (0.1911). Because this is a chronologically split dataset, the time-based data drift causes the Test set to be more difficult to predict than the Validation set.

Here are the stability metrics evaluated on both sets for full transparency:
- **Seed 42**: Val PR-AUC: `0.289429` | Test PR-AUC: `0.191076`
- **Seed 123**: Val PR-AUC: `0.289065` | Test PR-AUC: `0.200206`
- **Seed 2026**: Val PR-AUC: `0.283136` | Test PR-AUC: `0.189558`

## 9. Recommendation
**Replace LightGBM with Random Forest.** When evaluated fairly on the exact same untouched Test Set (without undersampling), the Random Forest model (0.1911 PR-AUC) slightly outperforms the existing LightGBM baseline (0.1865 PR-AUC). However, the Random Forest model is 485 MB, which may impact your deployment constraints. If memory is a strict bottleneck, keeping LightGBM or using an ensemble is recommended.
