---
title: "A Practical Study of Data Locality Optimization Techniques in Hadoop MapReduce"
subtitle: "Project: Data Locality-Aware Job Scheduler Simulator"
author: "[Author names, course, institution]"
date: "November 2026"
---

# Abstract

Hadoop MapReduce divides its input into splits that are processed by map tasks, and HDFS stores replicas of every block on different machines and racks. A scheduler that places a map task on a machine that already holds its input avoids a network transfer; a scheduler that ignores block locations does not. This paper studies how much that distinction matters. We built a discrete-event simulator in C++20 that models HDFS block placement with rack awareness, finite map slots, three locality levels (node-local, rack-local, off-rack), and two network models (independent per-transfer bandwidth and a shared cross-rack link). We compare three policies on *identical* workloads using paired random seeds: a locality-blind round-robin baseline, a greedy locality-aware scheduler with immediate fallback, and a delay-based locality scheduler. Across 78 experimental settings with 50 paired seeds each, we measure job completion time (makespan and mean turnaround), remote input traffic and cross-rack traffic.

In the main 16-worker, 4-rack configuration the greedy locality-aware policy reduced remote input traffic by 20.7% ± 1.5% and cross-rack traffic by 24.2% ± 3.4%, but improved makespan by only 5.7% ± 1.1%. The delay policy (D = 2 s) reduced remote traffic by 72.8% ± 2.3%, cross-rack traffic by 91.3% ± 3.4% and makespan by 25.6% ± 1.4%. The completion-time benefit depends strongly on the cost of remote reads: the greedy policy's makespan gain fell from 15.8% to 0.4% as per-flow cross-rack bandwidth rose from 5 to 200 MiB/s, while the *bytes* saved stayed constant. When cross-rack transfers share a finite link, ignoring locality caused congestion collapse (makespan 336.9 s for the blind policy versus 47.0 s for delay scheduling at a 25 MiB/s core link). Waiting for locality is not free: on a fast network, or under light load, the delay policy eliminated up to 100% of remote traffic yet *increased* makespan by up to 4.5%. These results come from a simulator with synthetic parameters, not from a Hadoop cluster, and should be read as a controlled comparison of scheduling policies under stated assumptions.

**Keywords:** Hadoop, MapReduce, data locality, HDFS, scheduling, delay scheduling, discrete-event simulation

# 1. Introduction

MapReduce [@dean2008] processes large datasets by splitting the input and running one map task per split. In Hadoop, the input resides in HDFS [@shvachko2010], which stores each block on several DataNodes and, through rack awareness, spreads replicas across racks [@hdfsguide]. Because compute and storage are co-located, a scheduler can start a task on a node that already holds its block and avoid reading the input over the network [@hadooptutorial]. Traffic inside a rack and traffic between racks have different costs, so locality has three levels: node-local, rack-local and off-rack.

The assignment behind this paper has two objectives:

1. **Simulate** MapReduce jobs with and without data-locality awareness.
2. **Measure** the impact of locality on job completion time and network traffic.

We pursue them through four research questions.

| ID | Research question | Main measurements |
|---|---|---|
| RQ1 | How much remote traffic does locality-aware scheduling avoid? | Remote input bytes, cross-rack bytes |
| RQ2 | Does locality-aware scheduling reduce job completion time? | Makespan, per-job turnaround |
| RQ3 | How does the benefit change with network bandwidth and block size? | Completion time, bytes transferred |
| RQ4 | How do replication, rack topology and cluster load affect the benefit? | Locality ratios, waiting, utilization |

We test four hypotheses that were fixed before running experiments: **H1** locality-aware scheduling reduces remote traffic when data is not replicated everywhere; **H2** its completion-time advantage grows when remote transfers are expensive relative to local reads and computation; **H3** more replicas create more opportunities for node-local execution, with a magnitude that depends on placement and free slots; **H4** waiting for local workers can reduce traffic but increase completion time when the locality benefit does not justify the wait.

**Contributions.** This is a comparative study; we do not claim a new scheduling algorithm. Our contributions are (i) a transparent, tested C++20 simulator with explicit cost and traffic definitions; (ii) a controlled paired-seed comparison of three policies across bandwidth, block size, load, replication, rack topology, cluster size and job arrival patterns; (iii) a shared-link contention model that separates the effect of avoided *bytes* from the effect of avoided *congestion*; and (iv) a measured demonstration of the traffic/completion-time trade-off in delay scheduling. All code, configurations, seeds and raw results are provided for reproduction.

# 2. Background and Related Work

**MapReduce and HDFS.** A MapReduce job runs map tasks over input splits and reduce tasks over grouped intermediate data [@dean2008; @hadooptutorial]. HDFS stores files as large blocks replicated across DataNodes; with rack awareness the default placement puts replicas on more than one rack so that data survive a rack failure, which also determines what network path a remote read needs [@shvachko2010; @hdfsguide]. Our simulator models this placement rule (first replica on a random node, second on a different rack, third on the second replica's rack).

**Locality-aware scheduling.** Surveys classify Hadoop scheduling work by objective (completion time, fairness, locality, resource utilization) and by the baselines used [@hedayati2023]. Delay scheduling [@zaharia2010] observes that a strict fair-share or FIFO policy can force the next job to launch a non-local task, and proposes letting a job wait briefly for a local slot while other jobs run; a short wait substantially increases locality. Our Policy C follows this idea in a simplified per-task form.

**Network perspective.** Wang and Ying study data locality in MapReduce from a network perspective [@wang2016], motivating the view that task placement and network constraints should be analysed together rather than treating locality as a stand-alone goal. Our shared-link experiments (Section 7.6) are in this spirit but are simulation experiments, not a reproduction of that paper's analysis.

**Positioning.** Production Hadoop schedulers already contain locality logic, so our "locality-blind" baseline is not a model of Hadoop's default behaviour. It is a deliberately simple lower bound that isolates what is gained by *using* block locations at all. Likewise, our delay policy omits the fairness machinery of the original proposal. We therefore describe the program as a simulator of scheduling *policies*, not as Hadoop.

# 3. System Model

**Cluster.** *W* homogeneous workers are assigned to *R* racks (worker *w* to rack *w*  mod  *R*). Each worker has *m* map slots; a task occupies one slot from its start until it finishes, including the time it spends reading input. Storage metadata records which workers hold a replica of each block.

**Workload.** A workload has *J* jobs released at times *r*~j~; each job has *n* map tasks. Every task *i* has an input block of size *S*~i~ MiB, a compute demand *C*~i~ seconds, and a release time. Compute demands are drawn uniformly from *C*̄(1 ± 0.5) with *C*̄ = 5 s. Each block has *k* replicas placed with the HDFS-style rule above. Tasks enter a single FIFO ready queue in a fixed order (job, then task index). For every comparison, **one workload instance is generated per seed and given verbatim to every policy**, so differences come from the policy only.

**Locality levels and replica choice.** For a task executing on worker *w*: *node-local* if *w* holds a replica; *rack-local* if another worker in *w*'s rack does; *off-rack* otherwise. The nearest replica is used.

**Cost model.** Task duration is *T*~i~ = *T*~read,*i*~ + *C*~i~ (read and compute are serialized). With effective bandwidths *D*~ℓ~ per locality level,

$$T_{\text{read},i} = S_i / D_\ell,\quad D_\ell \in \{D_{\text{local}}, D_{\text{rack}}, D_{\text{cross}}\}.$$

Defaults are *D*~local~ = 200, *D*~rack~ = 100 and *D*~cross~ = 25 MiB/s, so a 128 MiB split reads in 0.64 s, 1.28 s and 5.12 s respectively. These are synthetic parameters chosen so that a cross-rack read costs about as much as the compute time; they are not measurements of a Hadoop cluster, and Section 7 varies them.

**Shared-link network model.** In the *simple* model every remote read proceeds at its own rate *D*~ℓ~. In the *shared* model concurrent remote reads compete for capacity under processor sharing: off-rack reads share one core link of capacity *B*~core~, and rack-local reads in a rack share that rack's link of capacity *B*~rack~. With *n* active flows on a link, each flow proceeds at min(*D*~ℓ~, *B*/*n*), recomputed whenever a flow starts or ends. Node-local reads do not use the network. This is a fluid model of a single bottleneck; it does not model individual switches or TCP dynamics.

**Traffic accounting.** Remote input traffic is the sum of input bytes of rack-local and off-rack tasks; cross-rack traffic is the sum for off-rack tasks only. Node-local tasks add zero to both. Reduce-side shuffle is out of scope. Under a fixed placement of tasks, bytes do not depend on bandwidth: bandwidth changes duration, not volume.

**Metrics.** *Makespan* = last job completion minus first release. *Job turnaround* = job completion minus its own release; we report the mean over jobs. *Mean task wait* = task start minus release. *Slot utilization* = busy slot-seconds (including reading) over *W* *m* × makespan. For policy *A* against baseline *B* on a metric where lower is better,
$$\text{Improvement} = \frac{\bar M_B - \bar M_A}{\bar M_B} \times 100\%,$$
reported as "not applicable" when *M*̄~B~ = 0.

# 4. Scheduling Algorithms

All policies share the FIFO ready order; when a slot frees, the engine offers ready tasks in order and the policy returns a worker with a free slot or declines.

**Policy A: locality-blind.** Assign the task to the next worker with a free slot in round-robin order, never inspecting block locations.

**Policy B: greedy locality-aware.** Among workers with a free slot, choose a node-local worker if one exists, otherwise a rack-local worker, otherwise any worker (lowest index breaks ties). It never waits: if no local slot is free it falls back immediately.

**Policy C: delay-based.** A task that cannot run node-locally on a free worker waits. Waiting time is measured from the first moment a free slot existed for it. After *D* seconds it may run rack-locally; after 2*D* seconds it may run anywhere. Declined tasks do not block later tasks. With *D* = 0 the policy is identical to Policy B (verified by a unit test). Unless stated, *D* = 2 s.

# 5. Implementation

The simulator is written in C++20 using only the standard library and CMake; scheduling policies are separate from cluster mechanics behind a `Scheduler` interface (`pick_worker`, `wakeup_time`). The engine keeps a virtual clock and a `std::priority_queue` of events (job arrival, read completion, task completion, wake-up) ordered by time with a sequence-number tie-breaker, and advances virtual time instead of sleeping. In the shared network model it also tracks in-flight flows and computes the next flow completion analytically. Workload generation uses a platform-independent SplitMix64 generator so that a seed reproduces the same workload on any compiler. A `run_matrix` program executes every experiment and writes one CSV row per (setting, seed, policy) plus a manifest of all configurations; a Python script computes paired statistics and figures.

**Validation.** An automated suite (CTest) checks hand-calculated cases: a one-worker cluster (zero remote bytes, makespan 24 s); full replication (all tasks node-local); off-rack and rack-local reads with exact byte and time totals; slot limits; per-job turnaround with different release times; identical totals across policies; bit-identical output for a repeated seed; monotone read time in bandwidth; *D*=0 delay equals greedy; the delay trade-off on a two-task example; and shared-link sharing (two concurrent 128 MiB reads on a 64 MiB/s link take 4 s instead of 2 s). Every task finishes exactly once and locality counts sum to the number of tasks.

# 6. Experimental Methodology

**Paired design.** For each setting we run seeds 1 to 50. Within a seed all three policies see the same workload, placement, compute demands and cluster. For each metric we compute the per-seed difference between a baseline and an alternative policy and report its mean with a 95% confidence interval from the *t* distribution (49 degrees of freedom), and the fraction of seeds in which the alternative was better. "Improvement" percentages divide the mean difference by the mean baseline value; their intervals are the interval on the difference scaled the same way. We call an effect distinguishable from zero only when its interval excludes zero.

**Configurations.** The *main cluster* has 16 workers, 4 racks, 2 slots per worker (32 slots), 3 replicas, 128 MiB splits and 128 map tasks (4 times the slot count) in 4 jobs released together. The *small baseline* from the project plan has 8 workers, 2 racks, 2 slots and 64 tasks. Table 0 lists the factors varied one at a time around the main cluster.

| Experiment | Factor | Values |
|---|---|---|
| E1 | Baseline comparison | small and main cluster |
| E2 | Per-flow cross-rack bandwidth (MiB/s); split size (MiB) | 5, 10, 25, 50, 100, 200; 64, 128, 256 |
| E3 | Load (tasks / slots); job arrival gap (s) | 1, 2, 4, 8; 0, 10, 20, 40, 80 |
| E4 | Replicas; racks x replicas; workers | 1 to 4; {1,2,4,8} x {1,2,3}; 4, 8, 16, 32 |
| E5 | Delay threshold *D* (s) in four regimes | 0, 0.5, 1, 2, 4, 8, 16 |
| E6 | Shared core-link capacity (MiB/s), per-flow cap 25 and 100 | 25, 50, 100, 200, 400 |

Table 0. Experimental factors. 78 settings, 50 seeds, 3 policies: 11,700 simulation runs.

# 7. Results and Discussion

All numbers below are generated by `scripts/analyze.py` from `results/all_runs.csv`; intervals are 95% confidence intervals.

## 7.1 Baseline comparison (RQ1, RQ2)



**Table 1. Baseline, main cluster (mean ± 95% CI over 50 seeds)**

| Metric | Blind | Aware | Delay (D=2) |
|---|---|---|---|
| Makespan (s) | 38.9 ± 0.4 | 36.6 ± 0.4 | 28.9 ± 0.5 |
| Mean turnaround (s) | 26.1 ± 0.2 | 23.6 ± 0.2 | 20.0 ± 0.3 |
| Mean task wait (s) | 11.89 ± 0.12 | 10.25 ± 0.10 | 8.72 ± 0.10 |
| Mean remote read (s) | 3.68 ± 0.05 | 3.58 ± 0.06 | 1.97 ± 0.13 |
| Remote input (MiB) | 13356 ± 142 | 10586 ± 179 | 3630 ± 266 |
| Cross-rack (MiB) | 8348 ± 218 | 6328 ± 181 | 727 ± 179 |
| Node-local tasks | 23.7 ± 1.1 | 45.3 ± 1.4 | 99.6 ± 2.1 |
| Rack-local tasks | 39.1 ± 1.4 | 33.3 ± 1.4 | 22.7 ± 1.4 |
| Off-rack tasks | 65.2 ± 1.7 | 49.4 ± 1.4 | 5.7 ± 1.4 |
| Slot utilization | 0.835 ± 0.006 | 0.822 ± 0.007 | 0.823 ± 0.009 |





**Table 2. Paired differences, main cluster** (diff = base − alt; positive favours the second policy)

| Comparison | Metric | Base | Alt | Mean diff ± CI | Improvement % | Seeds better |
|---|---|---|---|---|---|---|
| aware vs blind | makespan_s | 38.85 | 36.63 | 2.22 ± 0.44 | 5.7% ± 1.1 | 94% |
| aware vs blind | mean_turnaround_s | 26.05 | 23.60 | 2.45 ± 0.23 | 9.4% ± 0.9 | 100% |
| aware vs blind | mean_wait_s | 11.89 | 10.25 | 1.64 ± 0.10 | 13.8% ± 0.9 | 100% |
| aware vs blind | mean_remote_read_s | 3.68 | 3.58 | 0.10 ± 0.08 | 2.8% ± 2.2 | 62% |
| aware vs blind | remote_mib | 13355.52 | 10585.60 | 2769.92 ± 199.89 | 20.7% ± 1.5 | 100% |
| aware vs blind | cross_rack_mib | 8348.16 | 6328.32 | 2019.84 ± 282.67 | 24.2% ± 3.4 | 98% |
| delay vs blind | makespan_s | 38.85 | 28.90 | 9.95 ± 0.54 | 25.6% ± 1.4 | 100% |
| delay vs blind | mean_turnaround_s | 26.05 | 19.97 | 6.08 ± 0.29 | 23.3% ± 1.1 | 100% |
| delay vs blind | mean_wait_s | 11.89 | 8.72 | 3.17 ± 0.11 | 26.7% ± 0.9 | 100% |
| delay vs blind | mean_remote_read_s | 3.68 | 1.97 | 1.71 ± 0.15 | 46.5% ± 3.9 | 100% |
| delay vs blind | remote_mib | 13355.52 | 3630.08 | 9725.44 ± 306.69 | 72.8% ± 2.3 | 100% |
| delay vs blind | cross_rack_mib | 8348.16 | 727.04 | 7621.12 ± 281.80 | 91.3% ± 3.4 | 100% |
| delay vs aware | makespan_s | 36.63 | 28.90 | 7.73 ± 0.52 | 21.1% ± 1.4 | 100% |
| delay vs aware | mean_turnaround_s | 23.60 | 19.97 | 3.64 ± 0.31 | 15.4% ± 1.3 | 100% |
| delay vs aware | mean_wait_s | 10.25 | 8.72 | 1.53 ± 0.10 | 15.0% ± 1.0 | 100% |
| delay vs aware | mean_remote_read_s | 3.58 | 1.97 | 1.61 ± 0.15 | 45.0% ± 4.2 | 100% |
| delay vs aware | remote_mib | 10585.60 | 3630.08 | 6955.52 ± 350.12 | 65.7% ± 3.3 | 100% |
| delay vs aware | cross_rack_mib | 6328.32 | 727.04 | 5601.28 ± 284.97 | 88.5% ± 4.5 | 100% |



![Figure 1. Makespan, mean job turnaround and mean task wait in the main cluster (error bars: 95% CI over 50 seeds).](../results/figures/fig1_completion_time.png)

![Figure 2. Remote input traffic and cross-rack traffic in the main cluster.](../results/figures/fig2_network_traffic.png)

In the main cluster the blind policy ran 18.5% of tasks node-locally and 50.9% off-rack. The greedy policy raised node-local execution to 35.4% and cut off-rack execution to 38.6%, reducing remote input traffic by 20.7% ± 1.5% and cross-rack traffic by 24.2% ± 3.4%; remote traffic fell in all 50 paired seeds and cross-rack traffic in 98% of them. Its makespan improved by 5.7% ± 1.1% (better in 94% of seeds) and mean job turnaround by 9.4% ± 0.9%. Delay scheduling reached 77.8% node-local and 4.5% off-rack execution, with remote traffic down 72.8% ± 2.3%, cross-rack traffic down 91.3% ± 3.4%, makespan down 25.6% ± 1.4% and turnaround down 23.3% ± 1.1%. **H1 is supported:** both locality-aware policies reduce remote input traffic whenever data are not replicated on every node.

The traffic reduction is far larger than the time reduction for the greedy policy. Two reasons are visible in the data. First, greedy placement only chooses among workers that happen to be free at the moment a task is dispatched, so at 4 times load it often has no local option (Section 7.3). Second, a rack-local read in this model costs 1.28 s against 0.64 s for a local read, so converting rack-local reads to node-local ones saves bytes but little time. In the small cluster (2 racks, 3 replicas) every worker has a same-rack copy of every block, so cross-rack traffic was zero for all policies and the greedy policy improved makespan by only 0.9% ± 0.6% while still cutting remote traffic by 21.1% ± 3.8%. This shows that task-count or byte-count locality alone can overstate the performance benefit.

![Figure 3. Share of tasks executed node-local, rack-local and off-rack. Splits have uniform size, so byte-weighted shares are identical.](../results/figures/fig4_locality_distribution.png)

## 7.2 Network bandwidth and split size (RQ3)



**Table 3. Cross-rack bandwidth sweep (MiB/s per flow)**

| Cross BW | Makespan blind | aware | delay | Aware: time impr. | Delay: time impr. | Aware: remote red. | Delay: remote red. |
|---|---|---|---|---|---|---|---|
| 5 | 92.1 | 77.5 | 44.9 | 15.8% ± 1.7 | 51.3% ± 2.9 | 20.0% ± 1.7 | 71.6% ± 2.2 |
| 10 | 58.3 | 52.4 | 33.5 | 10.2% ± 1.6 | 42.5% ± 2.6 | 19.8% ± 1.4 | 72.1% ± 2.5 |
| 25 | 38.9 | 36.6 | 28.9 | 5.7% ± 1.1 | 25.6% ± 1.4 | 20.7% ± 1.5 | 72.8% ± 2.3 |
| 50 | 32.0 | 30.9 | 28.0 | 3.6% ± 0.8 | 12.7% ± 0.9 | 20.4% ± 1.3 | 73.6% ± 2.1 |
| 100 | 28.8 | 28.5 | 27.6 | 1.3% ± 0.4 | 4.1% ± 0.9 | 19.5% ± 1.6 | 73.0% ± 2.0 |
| 200 | 27.6 | 27.5 | 27.6 | 0.4% ± 0.5 | -0.0% ± 1.0 | 20.5% ± 1.7 | 73.4% ± 2.6 |



![Figure 4. Bandwidth sensitivity: makespan, remote traffic and improvement versus per-flow cross-rack bandwidth.](../results/figures/fig3_bandwidth_sensitivity.png)

Remote traffic reduction is flat in bandwidth (about 20% for the greedy policy and about 73% for delay), as expected because bandwidth changes durations, not bytes. The completion-time benefit is not flat: the greedy policy's makespan gain fell from 15.8% ± 1.7% at 5 MiB/s to 3.6% ± 0.8% at 50 MiB/s and 0.4% ± 0.5% at 200 MiB/s; the delay policy's fell from 51.3% ± 2.9% to indistinguishable from zero (−0.0% ± 1.0%). **H2 is supported.** The same bytes saved are worth much more when each byte is slow to move.



**Table 4. Split size**

| MiB | Makespan blind | aware | delay | Aware: time impr. | Delay: time impr. | Aware: remote red. | Delay: remote red. |
|---|---|---|---|---|---|---|---|
| 64 | 31.1 | 29.8 | 26.2 | 4.1% ± 1.0 | 15.6% ± 0.9 | 19.9% ± 1.4 | 75.2% ± 2.3 |
| 128 | 38.9 | 36.6 | 28.9 | 5.7% ± 1.1 | 25.6% ± 1.4 | 20.7% ± 1.5 | 72.8% ± 2.3 |
| 256 | 54.3 | 49.6 | 37.0 | 8.5% ± 1.1 | 31.8% ± 2.3 | 21.1% ± 1.8 | 67.3% ± 3.0 |



Larger splits increased the benefit (greedy 4.1% → 5.7% → 8.5% and delay 15.6% → 25.6% → 31.8% for 64, 128 and 256 MiB), because remote read time scales with split size while compute demand is held fixed.

## 7.3 Load and job arrivals (RQ4)



**Table 5. Load (tasks / slots)**

| Load | Makespan blind | aware | delay | Aware: time impr. | Delay: time impr. | Aware: remote red. | Delay: remote red. |
|---|---|---|---|---|---|---|---|
| 1 | 12.3 | 10.1 | 10.9 | 18.3% ± 3.6 | 11.9% ± 4.0 | 81.4% ± 2.7 | 88.1% ± 2.3 |
| 2 | 22.5 | 19.5 | 16.5 | 13.6% ± 1.2 | 26.6% ± 1.5 | 40.9% ± 2.2 | 77.3% ± 2.8 |
| 4 | 38.9 | 36.6 | 28.9 | 5.7% ± 1.1 | 25.6% ± 1.4 | 20.7% ± 1.5 | 72.8% ± 2.3 |
| 8 | 71.0 | 68.9 | 52.4 | 3.0% ± 0.8 | 26.2% ± 0.7 | 10.4% ± 1.0 | 71.0% ± 1.6 |



![Figure 5. Effect of load (map tasks per map slot).](../results/figures/fig6_load.png)

With one task per slot, the greedy policy reduced remote traffic by 81.4% ± 2.7% and makespan by 18.3% ± 3.6%, because many slots are free and a local one is usually available. As load increases to 8 times the slot count, its traffic reduction shrinks to 10.4% ± 1.0% and its makespan gain to 3.0% ± 0.8%: with few free slots at each dispatch there is little choice. The delay policy keeps a large traffic reduction (71.0% ± 1.6% at 8 times load) and a makespan gain of about 26% at loads of 2 times and above, because waiting creates local opportunities that greedy placement cannot find. This contradicts a simple expectation that heavier load always raises the locality benefit for a greedy policy; the measurement shows the opposite for greedy and a plateau for delay. At light load (1 time) delay scheduling was *worse* than greedy: with *D* = 2 s its makespan was 0.78 s ± 0.61 s longer in the paired comparison (11.9% ± 4.0% improvement over blind versus 18.3% ± 3.6% for greedy), which anticipates Section 7.5.



**Table 6. Job arrival gap**

| Gap (s) | Makespan blind | aware | delay | Aware: time impr. | Delay: time impr. | Aware: remote red. | Delay: remote red. |
|---|---|---|---|---|---|---|---|
| 0 | 38.9 | 36.6 | 28.9 | 5.7% ± 1.1 | 25.6% ± 1.4 | 20.7% ± 1.5 | 72.8% ± 2.3 |
| 10 | 44.0 | 40.8 | 40.7 | 7.2% ± 1.3 | 7.5% ± 1.2 | 79.3% ± 1.7 | 88.0% ± 1.5 |
| 20 | 72.3 | 70.1 | 70.8 | 3.1% ± 0.6 | 2.1% ± 0.5 | 81.1% ± 1.2 | 87.9% ± 1.1 |
| 40 | 132.3 | 130.1 | 130.8 | 1.7% ± 0.3 | 1.1% ± 0.3 | 81.1% ± 1.2 | 87.9% ± 1.1 |
| 80 | 252.3 | 250.1 | 250.8 | 0.9% ± 0.2 | 0.6% ± 0.1 | 81.1% ± 1.2 | 87.9% ± 1.1 |



When jobs arrive 20 s or more apart, the cluster drains between jobs and all policies converge; makespan improvements shrink to 3.1% for greedy and 2.1% for delay at a 20 s gap. Delay is indistinguishable from greedy at a 10 s gap (0.13 s ± 0.64 s in its favour) and slightly worse at gaps of 20 s or more (0.73 s ± 0.51 s longer makespan), since waiting only costs time when the cluster is not backlogged.

## 7.4 Replication, racks and cluster size (RQ4, H3)



**Table 7. Replica count**

| Replicas | Makespan blind | aware | delay | Aware: time impr. | Delay: time impr. | Aware: remote red. | Delay: remote red. |
|---|---|---|---|---|---|---|---|
| 1 | 42.6 | 39.7 | 36.5 | 6.8% ± 0.9 | 14.4% ± 1.0 | 16.3% ± 0.9 | 37.2% ± 1.6 |
| 2 | 38.6 | 36.8 | 31.0 | 4.6% ± 1.1 | 19.7% ± 1.4 | 17.8% ± 1.4 | 56.9% ± 2.4 |
| 3 | 38.9 | 36.6 | 28.9 | 5.7% ± 1.1 | 25.6% ± 1.4 | 20.7% ± 1.5 | 72.8% ± 2.3 |
| 4 | 36.1 | 34.4 | 27.6 | 4.9% ± 1.3 | 23.7% ± 1.4 | 20.8% ± 1.9 | 83.0% ± 2.3 |





**Table 8. Racks x replicas**

| Racks x repl. | Makespan blind | aware | delay | Aware: time impr. | Delay: time impr. | Aware: remote red. | Delay: remote red. |
|---|---|---|---|---|---|---|---|
| 1x1 | 29.2 | 28.8 | 28.5 | 1.1% ± 0.2 | 2.2% ± 0.5 | 15.0% ± 1.1 | 34.9% ± 1.8 |
| 1x2 | 29.0 | 28.6 | 28.1 | 1.4% ± 0.3 | 3.2% ± 0.8 | 19.4% ± 1.4 | 52.1% ± 2.3 |
| 1x3 | 29.0 | 28.5 | 28.0 | 1.6% ± 0.4 | 3.4% ± 0.8 | 20.0% ± 1.5 | 66.8% ± 2.6 |
| 2x1 | 39.1 | 37.0 | 34.2 | 5.3% ± 1.1 | 12.6% ± 1.4 | 15.6% ± 1.0 | 35.4% ± 1.9 |
| 2x2 | 29.0 | 28.6 | 28.1 | 1.5% ± 0.3 | 3.1% ± 0.8 | 18.0% ± 1.3 | 48.1% ± 2.3 |
| 2x3 | 28.9 | 28.5 | 27.9 | 1.4% ± 0.4 | 3.7% ± 0.8 | 20.4% ± 2.0 | 69.5% ± 2.6 |
| 4x1 | 42.6 | 39.7 | 36.5 | 6.8% ± 0.9 | 14.4% ± 1.0 | 16.3% ± 0.9 | 37.2% ± 1.6 |
| 4x2 | 38.6 | 36.8 | 31.0 | 4.6% ± 1.1 | 19.7% ± 1.4 | 17.8% ± 1.4 | 56.9% ± 2.4 |
| 4x3 | 38.9 | 36.6 | 28.9 | 5.7% ± 1.1 | 25.6% ± 1.4 | 20.7% ± 1.5 | 72.8% ± 2.3 |
| 8x1 | 44.1 | 41.4 | 37.7 | 6.1% ± 0.5 | 14.6% ± 1.0 | 15.5% ± 0.7 | 38.0% ± 1.8 |
| 8x2 | 42.2 | 39.5 | 33.5 | 6.5% ± 0.8 | 20.7% ± 1.6 | 18.7% ± 1.2 | 57.0% ± 2.8 |
| 8x3 | 42.4 | 39.2 | 30.2 | 7.5% ± 0.8 | 28.8% ± 1.5 | 19.5% ± 1.9 | 81.0% ± 2.9 |



![Figure 6. Improvement versus replica count and number of racks.](../results/figures/fig7_replication_racks.png)

Replication helps the delay policy monotonically: its remote traffic reduction rose from 37.2% ± 1.6% with 1 replica to 56.9% with 2, 72.8% with 3 and 83.0% ± 2.3% with 4. For the greedy policy it stayed within 16% to 21% regardless of replica count, and its makespan gain was not monotone (6.8%, 4.6%, 5.7%, 4.9%). **H3 is therefore partly supported:** more replicas create more node-local opportunities, but exploiting them required waiting; an immediate-fallback policy did not capture them.

Placement and topology matter as much as the count. With one rack the greedy policy's makespan gain was 1.1% to 1.6% and delay's 2.2% to 3.4%, since all remote reads are cheap rack-local reads. With two racks and two or more replicas every rack holds every block, so no off-rack read is ever necessary and gains were again small (greedy 1.4% to 1.5%, delay 3.1% to 3.7%); with two racks and a single replica an off-rack read is often unavoidable and gains rose to 5.3% and 12.6%. The largest gains appeared with many racks and three replicas (8 racks: greedy 7.5%, delay 28.8%), where most workers have no copy in their own rack. 

**Table 9. Cluster size**

| Workers | Makespan blind | aware | delay | Aware: time impr. | Delay: time impr. | Aware: remote red. | Delay: remote red. |
|---|---|---|---|---|---|---|---|
| 4 | 31.5 | 30.0 | 25.9 | 4.6% ± 2.9 | 17.8% ± 2.1 | 29.0% ± 11.7 | 99.5% ± 9.7 |
| 8 | 37.8 | 35.3 | 27.5 | 6.6% ± 1.8 | 27.2% ± 1.7 | 25.5% ± 4.8 | 89.1% ± 3.7 |
| 16 | 38.9 | 36.6 | 28.9 | 5.7% ± 1.1 | 25.6% ± 1.4 | 20.7% ± 1.5 | 72.8% ± 2.3 |
| 32 | 39.3 | 37.0 | 30.3 | 5.8% ± 0.7 | 22.8% ± 1.4 | 20.4% ± 0.8 | 58.5% ± 2.2 |



Cluster size had little systematic effect on the greedy policy (4.6% to 6.6% for 4 to 32 workers) and a mild downward trend for delay (27.2% at 8 workers to 22.8% at 32), while delay's traffic reduction fell from 99.5% to 58.5% as the cluster grew with load held at 4 times the slot count. We did not find that a larger cluster automatically increases the benefit.

![Figure 7. Improvement versus split size, cluster size and job arrival gap.](../results/figures/fig10_block_workers_gap.png)

## 7.5 Delay-based locality and the traffic/time trade-off (H4)



**Table 10. Delay threshold, cross 25 MiB/s**

| D (s) | Makespan blind | aware | delay | Aware: time impr. | Delay: time impr. | Aware: remote red. | Delay: remote red. |
|---|---|---|---|---|---|---|---|
| 0 | 38.9 | 36.6 | 36.6 | 5.7% ± 1.1 | 5.7% ± 1.1 | 20.7% ± 1.5 | 20.7% ± 1.5 |
| 0.5 | 38.9 | 36.6 | 33.3 | 5.7% ± 1.1 | 14.2% ± 1.3 | 20.7% ± 1.5 | 50.2% ± 1.8 |
| 1 | 38.9 | 36.6 | 31.3 | 5.7% ± 1.1 | 19.4% ± 1.6 | 20.7% ± 1.5 | 58.2% ± 2.1 |
| 2 | 38.9 | 36.6 | 28.9 | 5.7% ± 1.1 | 25.6% ± 1.4 | 20.7% ± 1.5 | 72.8% ± 2.3 |
| 4 | 38.9 | 36.6 | 27.6 | 5.7% ± 1.1 | 29.0% ± 1.0 | 20.7% ± 1.5 | 89.6% ± 1.8 |
| 8 | 38.9 | 36.6 | 27.4 | 5.7% ± 1.1 | 29.6% ± 0.9 | 20.7% ± 1.5 | 99.8% ± 1.1 |
| 16 | 38.9 | 36.6 | 27.4 | 5.7% ± 1.1 | 29.5% ± 0.9 | 20.7% ± 1.5 | 100.0% ± 1.1 |





**Table 11b. Delay threshold, light load (1x slots)**

| D (s) | Makespan blind | aware | delay | Aware: time impr. | Delay: time impr. | Aware: remote red. | Delay: remote red. |
|---|---|---|---|---|---|---|---|
| 0 | 12.3 | 10.1 | 10.1 | 18.3% ± 3.6 | 18.3% ± 3.6 | 81.4% ± 2.7 | 81.4% ± 2.7 |
| 0.5 | 12.3 | 10.1 | 11.3 | 18.3% ± 3.6 | 8.8% ± 4.0 | 81.4% ± 2.7 | 86.2% ± 2.2 |
| 1 | 12.3 | 10.1 | 12.2 | 18.3% ± 3.6 | 1.4% ± 4.4 | 81.4% ± 2.7 | 86.2% ± 2.2 |
| 2 | 12.3 | 10.1 | 10.9 | 18.3% ± 3.6 | 11.9% ± 4.0 | 81.4% ± 2.7 | 88.1% ± 2.3 |
| 4 | 12.3 | 10.1 | 11.1 | 18.3% ± 3.6 | 9.8% ± 2.6 | 81.4% ± 2.7 | 94.3% ± 2.1 |
| 8 | 12.3 | 10.1 | 11.1 | 18.3% ± 3.6 | 9.8% ± 2.7 | 81.4% ± 2.7 | 100.0% ± 1.9 |
| 16 | 12.3 | 10.1 | 11.1 | 18.3% ± 3.6 | 9.8% ± 2.7 | 81.4% ± 2.7 | 100.0% ± 1.9 |





**Table 11c. Delay threshold, fast network (cross 200, rack 400 MiB/s)**

| D (s) | Makespan blind | aware | delay | Aware: time impr. | Delay: time impr. | Aware: remote red. | Delay: remote red. |
|---|---|---|---|---|---|---|---|
| 0 | 26.2 | 26.3 | 26.3 | -0.2% ± 0.2 | -0.2% ± 0.2 | 21.2% ± 1.6 | 21.2% ± 1.6 |
| 0.5 | 26.2 | 26.3 | 26.4 | -0.2% ± 0.2 | -0.6% ± 0.5 | 21.2% ± 1.6 | 51.6% ± 2.1 |
| 1 | 26.2 | 26.3 | 26.5 | -0.2% ± 0.2 | -1.2% ± 0.6 | 21.2% ± 1.6 | 61.0% ± 2.3 |
| 2 | 26.2 | 26.3 | 26.8 | -0.2% ± 0.2 | -2.1% ± 0.7 | 21.2% ± 1.6 | 74.6% ± 2.5 |
| 4 | 26.2 | 26.3 | 27.1 | -0.2% ± 0.2 | -3.5% ± 0.6 | 21.2% ± 1.6 | 89.6% ± 1.9 |
| 8 | 26.2 | 26.3 | 27.4 | -0.2% ± 0.2 | -4.4% ± 0.8 | 21.2% ± 1.6 | 99.8% ± 1.2 |
| 16 | 26.2 | 26.3 | 27.4 | -0.2% ± 0.2 | -4.5% ± 0.8 | 21.2% ± 1.6 | 100.0% ± 1.2 |



![Figure 8. Delay threshold sweeps in four regimes. Dashed lines: blind and greedy policies.](../results/figures/fig8_delay_threshold.png)

When remote reads are costly (25 or 10 MiB/s cross-rack) and load is high, waiting pays: makespan fell monotonically with *D* and saturated near 29% improvement at *D* ≥ 4 s (25 MiB/s) and 53% (10 MiB/s), with remote traffic reduction approaching 100%. In the two regimes where waiting is least justified the trade-off appears. On a fast network (cross-rack 200 MiB/s, rack 400 MiB/s) the greedy and blind policies were equivalent (greedy −0.2% ± 0.2%), while delay removed up to 100% of remote traffic but lengthened makespan by 4.4% ± 0.8% at *D* = 8 s, as tasks waited for local slots that a fast remote read would have made unnecessary. Under light load (one task per slot), waiting raised the mean task wait from 0 s (greedy) to 0.45 s at *D* = 8 s, and for *D* ≥ 4 s the delay policy's makespan gain over blind was 9.8% ± 2.7% against 18.3% ± 3.6% for greedy (delay 1.05 s ± 0.44 s slower than greedy in the paired comparison). **H4 is supported:** reduced traffic does not imply reduced completion time, and the right threshold depends on bandwidth and load.

![Figure 9. Trade-off between remote-traffic reduction and makespan improvement, one point per setting relative to the blind policy.](../results/figures/fig5_tradeoff.png)

## 7.6 Shared-link contention (RQ3, RQ4)



**Table 12. Shared core link, per-flow 25**

| Core cap | Makespan blind | aware | delay | Aware: time impr. | Delay: time impr. | Aware: remote red. | Delay: remote red. |
|---|---|---|---|---|---|---|---|
| 25 | 336.9 | 259.9 | 47.0 | 22.8% ± 3.1 | 86.1% ± 3.3 | 20.4% ± 1.5 | 71.6% ± 2.6 |
| 50 | 171.9 | 129.2 | 34.2 | 24.8% ± 3.4 | 80.1% ± 3.0 | 20.7% ± 1.7 | 72.1% ± 2.5 |
| 100 | 88.6 | 71.4 | 29.4 | 19.4% ± 2.9 | 66.8% ± 2.5 | 20.1% ± 1.3 | 72.1% ± 2.5 |
| 200 | 48.6 | 42.5 | 28.9 | 12.6% ± 2.2 | 40.6% ± 1.9 | 20.2% ± 1.9 | 72.7% ± 2.0 |
| 400 | 39.0 | 36.7 | 28.9 | 6.1% ± 1.1 | 26.0% ± 1.5 | 20.9% ± 1.6 | 72.9% ± 2.1 |



![Figure 10. Makespan and improvement under a shared core link.](../results/figures/fig9_contention.png)



**Table 14. Contention diagnostics: mean remote read time (s) and offered core load**

| Exp | Core cap | read blind | read aware | read delay | load blind | load aware | load delay |
|---|---|---|---|---|---|---|---|
| E6_shared | 25 | 90.9 | 77.8 | 8.9 | 0.98 | 0.97 | 0.60 |
| E6_shared | 50 | 42.5 | 34.7 | 4.3 | 0.96 | 0.94 | 0.42 |
| E6_shared | 100 | 18.2 | 15.6 | 2.4 | 0.92 | 0.87 | 0.24 |
| E6_shared | 200 | 6.6 | 5.9 | 2.0 | 0.83 | 0.73 | 0.12 |
| E6_shared | 400 | 3.8 | 3.6 | 2.0 | 0.53 | 0.43 | 0.06 |
| E6_shared_fast | 25 | 90.9 | 77.8 | 8.9 | 0.98 | 0.97 | 0.60 |
| E6_shared_fast | 50 | 42.5 | 35.6 | 4.2 | 0.96 | 0.94 | 0.41 |
| E6_shared_fast | 100 | 18.2 | 15.8 | 2.1 | 0.93 | 0.88 | 0.24 |
| E6_shared_fast | 200 | 6.4 | 5.2 | 1.5 | 0.85 | 0.76 | 0.12 |
| E6_shared_fast | 400 | 2.2 | 1.6 | 1.3 | 0.64 | 0.53 | 0.06 |



With a shared core link, remote reads slow each other down. At a core capacity of 400 MiB/s the shared and simple models agree (makespan 39.0 s versus 38.9 s for the blind policy), which cross-validates the two implementations. As capacity falls, the blind policy saturates the link (offered core load 0.98 at 25 MiB/s), the mean remote read grows from 3.7 s to 90.9 s and makespan reaches 336.9 s, against 259.9 s for greedy (22.8% ± 3.1% better) and 47.0 s for delay (86.1% ± 3.3% better). Because delay scheduling removes most off-rack reads it keeps the link lightly loaded (0.60 at 25 MiB/s and 0.24 at 100 MiB/s). The completion-time benefit of locality in this regime comes from avoiding congestion, not just from avoiding bytes, a distinction the simple per-transfer model cannot show. The shared-link results are produced by a separate, simplified model and should be treated as qualitative evidence about congestion.

## 7.7 Summary against the hypotheses

| Hypothesis | Verdict | Evidence |
|---|---|---|
| H1 | Supported | Remote traffic reduced in all settings with partial replication (10% to 100%) |
| H2 | Supported | Greedy makespan gain 15.8% to 0.4% as bandwidth rises 5 to 200 MiB/s; bytes saved constant |
| H3 | Partly supported | Delay's traffic reduction 37% to 83% with 1 to 4 replicas; greedy's flat at 16% to 21% |
| H4 | Supported | On a fast network delay cut 100% of remote traffic but worsened makespan by up to 4.5%; also worse at light load |

# 8. Limitations and Future Work

**Model scope.** The simulator covers map-task input locality only. It omits reduce-side shuffle, speculative execution, failures, heterogeneous nodes, data skew, multi-block tasks, disk and CPU contention, and compute/read overlap (reads and compute are serialized). Task durations are synthetic, uniform in a ± 50% band.

**Parameters.** Bandwidths, block sizes and compute times are illustrative, not measured on a Hadoop deployment. Absolute times should not be compared with real clusters; the contribution is the relative behaviour of policies and its direction as parameters vary.

**Baselines.** The blind policy is a lower bound, not Hadoop's default; production schedulers include locality preferences. The greedy and delay policies are simplified and the delay policy omits job-level fairness and per-job skip counts. Results for delay scheduling therefore illustrate the trade-off but do not evaluate the original algorithm.

**Network.** The shared model is a fluid single-bottleneck model; per-rack uplinks, oversubscription ratios and transport dynamics are not modelled. Conclusions under congestion are qualitative.

**Statistics.** Fifty paired seeds per setting give narrow intervals for most metrics, but intervals are computed per setting without correction for the many comparisons reported, and they describe variation over synthetic workloads, not real-world variation.

**Future work.** Validate against a real or trace-driven cluster, add reduce-side shuffle, model heterogeneous nodes and stragglers, implement fairness-aware delay scheduling, and study adaptive delay thresholds that depend on measured bandwidth.

# 9. Conclusion

Within this simulator, data-locality-aware scheduling consistently reduced remote input traffic, but the effect on job completion time was conditional. A greedy locality-aware policy with immediate fallback cut remote traffic by about a fifth and makespan by 5.7% in the main configuration, with larger gains when cross-rack reads were slow and almost none when they were fast. A delay-based policy converted replication into locality far more effectively (72.8% less remote traffic and 25.6% shorter makespan in the main configuration, 86.1% shorter makespan under a congested core link) yet increased makespan on a fast network and under light load. The practical lessons are that locality should be evaluated with both bytes and time, that the benefit depends on the bandwidth, replica placement, rack topology and load, and that waiting for locality needs a threshold tied to the cost of the remote read it avoids.

# Reproducibility

Source code, tests, configurations, per-run CSV output and analysis scripts are in the project repository. From a clean checkout: `cmake -S . -B build && cmake --build build -j && ctest --test-dir build`, then `./build/run_matrix --seeds 50 --out results` and `python3 scripts/analyze.py results`. Every run is identified by (setting, seed, policy) in `results/all_runs.csv`, and `results/manifest.csv` records the full configuration of every setting.

# References
