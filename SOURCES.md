# Sources and implementation lineage

## Methods and upstream code inspected

- [POPPER official repository](https://github.com/snap-stanford/POPPER), inspected at commit `59611864e09dd15d7528e240ad87c7ddbb4a701c`: `popper/agent.py` (`e_value_kappa_calibrator`), benchmark agents and DiscoveryBench runner. We use its design→execute→record separation and independently implement the fixed kappa=.5 p-to-e transform. The full agent implementation is not copied. Sequential evidence guarantees are not inherited by this demo.
- [DiscoveryBench official repository](https://github.com/allenai/discoverybench), inspected at commit `c31fcf011e070f021a5f5b906896d0821f6880e8`: [original table](https://github.com/allenai/discoverybench/blob/c31fcf011e070f021a5f5b906896d0821f6880e8/discoverybench/real/test/introduction_pathways_non-native_plants/temporal_trends_contingency_table.csv), local file `agt/data/pathways.tsv` (original delimiter is tab). [Metadata](https://github.com/allenai/discoverybench/blob/c31fcf011e070f021a5f5b906896d0821f6880e8/discoverybench/real/test/introduction_pathways_non-native_plants/metadata_0.json). Original upstream licensing and data-source terms continue to apply.
- [Qwen3.5 official serving examples](https://huggingface.co/Qwen/Qwen3.5-35B-A3B/blob/main/README.md): OpenAI-compatible chat endpoint and `chat_template_kwargs.enable_thinking`. Actual deployment uses the user-authorized campus `Qwen/Qwen3.8-27B` ID, verified separately in the remote run manifest; Qwen3.5 documentation is API integration context, not evidence that 3.8 weights were independently inspected.
- [SciPy Pearson reference](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html), [chi-square contingency reference](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.chi2_contingency.html): deterministic allowlisted tests. p-value assumptions are preserved in records.

## NVIDIA reported revenue data

Unit: USD millions. Values are human-transcribed factual table entries; no simulated financial data are used. Dates refer to release dates, availability cutoffs in the demo are conservative following-day UTC.

| Quarter | Revenue | Public release | Supporting source |
| --- | ---: | --- | --- |
| FY2024Q1 | 7192 | 2023-05-24 | [Q2 FY2024 release comparison column](https://nvidianews.nvidia.com/news/nvidia-announces-financial-results-for-second-quarter-fiscal-2024) |
| FY2024Q2 | 13507 | 2023-08-23 | [Q2 FY2024 release](https://nvidianews.nvidia.com/news/nvidia-announces-financial-results-for-second-quarter-fiscal-2024) |
| FY2024Q3 | 18120 | 2023-11-21 | [Q3 FY2024 release](https://nvidianews.nvidia.com/news/nvidia-announces-financial-results-for-third-quarter-fiscal-2024) |
| FY2024Q4 | 22103 | 2024-02-21 | [Q4 FY2024 release](https://nvidianews.nvidia.com/news/nvidia-announces-financial-results-for-fourth-quarter-and-fiscal-2024) |
| FY2025Q1 | 26044 | 2024-05-22 | [Q1 FY2025 release](https://nvidianews.nvidia.com/news/nvidia-announces-financial-results-for-first-quarter-fiscal-2025) |

`nvda_fy24.csv` includes only the first four entries. `nvda_fy25q1.csv` adds the fifth. Runtime text is a human-normalized factual excerpt of the actual Q1 announcement, not a generated news article.

The later dataset overlaps the earlier four quarters. They are not independent samples or independent evidence factors. No investment recommendation or causal claim is inferred from this small descriptive table.
