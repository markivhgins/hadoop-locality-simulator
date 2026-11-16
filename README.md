# Data Locality-Aware Job Scheduler Simulator

C++20 discrete-event simulator and research study of data locality in Hadoop MapReduce
map-task scheduling. Project title: *A Practical Study of Data Locality Optimization
Techniques in Hadoop MapReduce.*

* **Objective 1:** simulate MapReduce jobs with and without data-locality awareness.
* **Objective 2:** measure the impact on job completion time and network traffic.

It simulates scheduling *policies*; it is not Hadoop, and all parameters are synthetic.

---

## 🌐 Live Interactive Web Dashboard

An interactive Streamlit + Plotly web application is included to explore the simulator and paper results live:

* **🎮 Live Simulator:** Run `blind`, `aware`, and `delay` policies concurrently with customizable cluster topologies, bandwidths, and delay thresholds. View interactive Gantt task scheduling timelines.
* **📊 Benchmark Explorer:** Explore the **78 settings** and **50 paired random seeds** (11,700 runs) with 95% confidence intervals and boxplots.
* **🔬 Hypothesis Analyzer:** Interactive trade-off curves for bandwidth sensitivity ($H_2$), cost of waiting ($H_4$), and network congestion collapse.
* **📄 Artifacts & Downloads:** Download the research paper PDF, summary statistics, and raw data directly.

### Running Locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

### Live Cloud Deployment (Streamlit Community Cloud)
1. Push this repository to GitHub.
2. Sign in to [share.streamlit.io](https://share.streamlit.io).
3. Select your repository, branch (`main`), and set Main file path to `app.py`.
4. Click **Deploy** to get a public URL (e.g., `https://<repo-name>.streamlit.app`).

---

## Policies (identical workloads, paired seeds)
| Policy | Behaviour |
|---|---|
| `blind` | round-robin over free workers, ignores block locations |
| `aware` | greedy: node-local > rack-local > off-rack among free workers, never waits |
| `delay` | per-task wait D s for node-local, 2D s for rack-local, then anywhere (D=0 == aware) |

Network models: *simple* (each remote read runs at its own bandwidth) and *shared*
(concurrent reads share a core link and per-rack links, processor sharing).

## Reproduce
    ./scripts/run_all.sh            # build, test, experiments, analysis, paper
or step by step:
    cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build -j
    ctest --test-dir build --output-on-failure
    ./build/run_matrix --seeds 50 --out results       # 78 settings x 50 seeds x 3 policies
    python3 scripts/analyze.py results                # summary.csv, tables.md, figures/
    python3 scripts/build_paper.py                    # paper/paper.md and paper.docx (needs pandoc)
Ad-hoc comparison: `./build/locality_sim --cross-bw 10 --replicas 2 --delay 2 --shared 1 --core-cap 100`.
Python needs numpy, pandas, scipy, matplotlib.

## Layout
    include/sim.hpp            types and interfaces        src/simulation.cpp   event engine, network model
    src/workload.cpp           seeded workload, HDFS-style placement   src/schedulers.cpp   the three policies
    src/main.cpp               ad-hoc CLI                  experiments/run_matrix.cpp   experiments E1-E6
    tests/test_sim.cpp         hand-calculated tests       scripts/analyze.py   paired statistics + figures
    results/                   all_runs.csv, manifest.csv, summary.csv, tables.md, figures/
    paper/                     paper_template.md (source), paper.md, paper.docx, references.bib

## Metrics
Makespan, mean job turnaround, mean task wait, remote input MiB (rack-local + off-rack),
cross-rack MiB (off-rack only), locality counts, slot utilization, core-link load.
Improvement % = (baseline - alternative) / baseline; paired 95% CI over seeds (t distribution).
