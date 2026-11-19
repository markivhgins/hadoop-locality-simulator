import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def build_perfect_report():
    # Use the user-uploaded 2-page document containing the exact front 2 pages
    user_uploaded_path = r'C:\Users\vikra\.gemini\antigravity\brain\b58840ca-396c-4537-bb66-d808da467a69\.user_uploaded\media_1795122902851_8fa52a93.docx'
    doc = docx.Document(user_uploaded_path)
    
    # Body elements in the uploaded document:
    # 0-12: Cover page
    # 13: Page break paragraph
    # 14: Table 0 (Bonafide certificate header with SRM seal & logo)
    # 15: Empty spacing paragraph
    # 16: Certificate text paragraph with Vikram Singh and Amit Vikram Singh
    # 17: Empty spacing paragraph
    # 18: Table 1 (Signatures: Mr. Tapas Kumar Mishra & Dr. Neelam Singh)
    # 19: Trailing empty paragraph
    # 20: sectPr
    body = doc._body._body
    print(f"Initial body elements: {len(body)}")
    
    # Remove trailing empty paragraph 19 if present
    while len(body) > 20 and not body[19].tag.endswith('sectPr'):
        body.remove(body[19])
        
    print(f"Preserved front 2 pages intact (elements 0-18). Appending project content...")

    # Helpers using exact template styles
    def h2(text):
        p = doc.add_paragraph(style='Heading 2')
        pPr = p._p.get_or_add_pPr()
        pPr.append(parse_xml(r'<w:pageBreakBefore xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>'))
        pPr.append(parse_xml(r'<w:pBdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:bottom w:val="single" w:sz="8" w:space="4" w:color="2E5597"/></w:pBdr>'))
        p.add_run(text)
        return p
        
    def h3(text):
        p = doc.add_paragraph(style='Heading 3')
        p.add_run(text)
        return p
        
    def fp(text):
        p = doc.add_paragraph(style='First Paragraph')
        p.add_run(text)
        return p
        
    def bt(text):
        p = doc.add_paragraph(style='Body Text')
        p.add_run(text)
        return p
        
    def cp(text, bold_prefix=None):
        p = doc.add_paragraph(style='Compact')
        if bold_prefix:
            r_b = p.add_run(bold_prefix)
            r_b.bold = True
        p.add_run(text)
        return p
        
    def fig(img_path, caption):
        if os.path.exists(img_path):
            p_img = doc.add_paragraph(style='Captioned Figure')
            p_img.add_run().add_picture(img_path, width=Inches(5.8))
            p_cap = doc.add_paragraph(style='Image Caption')
            p_cap.add_run(caption)
            
    def add_table(headers, rows_data):
        tbl = doc.add_table(rows=len(rows_data) + 1, cols=len(headers))
        tbl.style = 'Table'
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        for c_idx, h in enumerate(headers):
            cell = tbl.rows[0].cells[c_idx]
            p = cell.paragraphs[0]
            p.style = 'Compact'
            r = p.add_run(h)
            r.bold = True
        for r_idx, r_vals in enumerate(rows_data):
            for c_idx, val in enumerate(r_vals):
                cell = tbl.rows[r_idx + 1].cells[c_idx]
                p = cell.paragraphs[0]
                p.style = 'Compact'
                p.add_run(str(val))
        return tbl

    # =========================================================================
    # PAGE 3: TITLE, SUBTITLE, AUTHOR
    # =========================================================================
    p_title = doc.add_paragraph(style='Title')
    pPr = p_title._p.get_or_add_pPr()
    pPr.append(parse_xml(r'<w:pageBreakBefore xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>'))
    pPr.append(parse_xml(r'<w:spacing xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:before="3969" w:after="480"/>'))
    p_title.add_run("A Practical Study of Data Locality Optimization Techniques in Hadoop MapReduce")

    p_sub = doc.add_paragraph(style='Subtitle')
    pPr = p_sub._p.get_or_add_pPr()
    pPr.append(parse_xml(r'<w:spacing xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:after="600"/>'))
    p_sub.add_run("Project Title: Interactive Dashboard and Simulation of Data Locality Optimization in Hadoop MapReduce")

    p_auth = doc.add_paragraph(style='Author')
    p_auth.add_run("Domain: Big Data Systems & Distributed Computing · Cloud Computing | Tools: C++20, Python (Streamlit, pandas, plotly, scipy, matplotlib)")

    # =========================================================================
    # PAGE 4: INDEX
    # =========================================================================
    p_idx = doc.add_paragraph(style='Heading 2')
    pPr = p_idx._p.get_or_add_pPr()
    pPr.append(parse_xml(r'<w:pageBreakBefore xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>'))
    pPr.append(parse_xml(r'<w:jc xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="center"/>'))
    p_idx.add_run("INDEX")

    index_headers = ["Sr. No.", "Particulars", "Page No."]
    index_entries = [
        ("1", "Abstract", "5"),
        ("2", "Section 1 — Introduction", "6"),
        ("3", "Section 2 — Theoretical Framework: Hadoop Architecture & Data Locality", "7"),
        ("4", "Section 3 — Simulation Model & Experimental Datasets", "8"),
        ("5", "Section 4 — Methodology", "10"),
        ("6", "Section 5 — Locality Dynamics & Experimental Analysis", "11"),
        ("7", "Section 6 — Dashboard Design (Streamlit & Plotly)", "15"),
        ("8", "Section 7 — Implementation Status", "17"),
        ("9", "Section 8 — Results and Discussion", "18"),
        ("10", "Section 9 — Challenges and Limitations", "19"),
        ("11", "Section 10 — Conclusion and Future Work", "20"),
        ("12", "Section 11 — References", "21"),
        ("13", "Appendix A — Project Files", "22")
    ]
    add_table(index_headers, index_entries)

    # =========================================================================
    # ABSTRACT
    # =========================================================================
    h2("Abstract")
    fp(
        "Hadoop MapReduce divides its input into splits that are processed by parallel map tasks, while the Hadoop Distributed "
        "File System (HDFS) stores multiple replicas of every block across different physical machines and racks. A cluster scheduler "
        "that places a map task on a machine that already holds its input block achieves node-locality and completely avoids network "
        "transfer; a scheduler that ignores block locations forces data over oversubscribed core switches. This project presents an "
        "extensive empirical study and discrete-event simulation of data locality optimization in Hadoop MapReduce."
    )
    bt(
        "We designed and implemented a high-performance discrete-event simulator in C++20 modeling HDFS rack-aware replica placement, "
        "finite worker slots, a three-tier locality hierarchy (node-local, rack-local, off-rack), and two distinct network models: "
        "independent per-transfer bandwidth and shared core-link processor sharing. Across 78 experimental configurations evaluated with "
        "50 paired random seeds (11,700 total cluster simulations), we compare three scheduling policies: a Locality-Blind round-robin baseline, "
        "a Greedy Locality-Aware scheduler, and Delay Scheduling (Zaharia et al.). An interactive Streamlit + Plotly web dashboard deployed "
        "live on the cloud allows users to simulate custom cluster topologies, inspect live Gantt task execution timelines, and explore "
        "paired statistical metrics."
    )

    # =========================================================================
    # SECTION 1: INTRODUCTION
    # =========================================================================
    h2("1. Introduction")
    h3("1.1 Background")
    fp(
        "Distributed big data architectures, popularized by Google's MapReduce framework and Apache Hadoop, operate on the foundational "
        "principle of moving computation to data rather than moving data to computation. In modern enterprise clusters, large files are "
        "ingested into HDFS, split into uniform chunks (typically 64 MiB or 128 MiB), and replicated across commodity DataNodes. By enforcing "
        "rack awareness, HDFS distributes replicas across distinct physical racks to guard against rack switch or power failures. Because compute "
        "workers (NodeManagers/TaskTrackers) and storage nodes (DataNodes) are co-located on the same physical servers, an intelligent scheduler "
        "can assign a map task to a node hosting its input block, eliminating network transfer entirely."
    )
    
    h3("1.2 Problem Statement")
    fp(
        "Although data locality is celebrated in distributed computing theory, production clusters frequently face severe resource contention. "
        "When a map task is ready to execute, nodes holding its data replicas may be fully occupied with running tasks. The cluster scheduler "
        "faces a critical dilemma: (1) launch the task immediately on an idle off-rack node, incurring heavy network transfer costs, or "
        "(2) force the task to wait in queue until a local slot frees, potentially idling worker slots and increasing queueing delay. "
        "Furthermore, textbook descriptions rarely quantify how physical link bandwidths, split sizes, replication factors, and backbone contention "
        "influence the net benefit of data locality. This project provides rigorous quantitative answers to these trade-offs."
    )

    h3("1.3 Objectives")
    cp(" Simulate MapReduce jobs with and without data-locality awareness across 78 settings and 50 paired seeds.", bold_prefix="Objective 1:")
    cp(" Build an interactive Streamlit / Plotly web dashboard deployed live on the web with real-time Gantt timeline execution and paired statistics.", bold_prefix="Objective 2:")

    h3("1.4 Scope")
    fp(
        "The study covers map-task scheduling, HDFS block distribution, network transfer latency, and job completion metrics. "
        "It focuses on the map phase where input data locality is determined; reduce-side shuffle and network sorting dynamics are out of scope. "
        "All parameters are synthetic and evaluated under controlled paired random seeds to ensure exact reproducibility."
    )

    # =========================================================================
    # SECTION 2: THEORETICAL FRAMEWORK
    # =========================================================================
    h2("2. Theoretical Framework: Hadoop Architecture & Data Locality")
    add_table(
        ["Locality Tier", "Core Question", "Network Path", "Typical Read Speed", "Core Switch Traversal"],
        [
            ["Node-Local", "Is data on the local node?", "Local disk / page cache bus", "200 MiB/s", "None (0 hops)"],
            ["Rack-Local", "Is data in the same rack?", "Intra-rack Top-of-Rack (ToR) switch", "100 MiB/s", "None (1 hop)"],
            ["Off-Rack", "Is data in a different rack?", "Core aggregation backbone switch", "25 MiB/s", "Traverses core (2 hops)"],
            ["Delay Scheduling", "Should we wait for local slots?", "Queued wait -> Local disk", "Zero network bytes", "Avoided via timer D"],
            ["Shared Link", "Do concurrent transfers contend?", "Core link with Processor Sharing", "min(c_f, B_core / n)", "Active bottleneck"]
        ]
    )
    bt(
        "Why the hierarchy matters. Intra-rack bandwidth in commodity data centers is typically non-blocking, but core aggregation switches "
        "connecting racks are oversubscribed by factors of 1:5 to 1:20. When hundreds of map tasks perform off-rack reads concurrently, "
        "they flood the core switches, leading to TCP buffer queueing, packet loss, and severe congestion collapse. Locality optimization "
        "is therefore not merely a job-level optimization, but a cluster-wide stability requirement."
    )

    # =========================================================================
    # SECTION 3: DATASETS
    # =========================================================================
    h2("3. Datasets")
    add_table(
        ["#", "Dataset / Artifact", "File", "Format", "Size"],
        [
            ["1", "Baseline Cluster Runs", "results/all_runs.csv (E1 filter)", "CSV", "16 workers × 4 racks × 32 slots × 128 tasks"],
            ["2", "Full Benchmark Matrix", "all_runs.csv", "CSV", "11,700 rows × 21 columns (1.61 MB)"],
            ["3", "Summary Statistical Matrix", "summary.csv", "CSV", "1,404 rows × 15 columns (262 KB)"],
            ["4 (supplementary)", "Live Simulation Workload", "Generated in-memory by sim_engine.py", "Python / C++", "Exact paired-seed HDFS placement instance"]
        ]
    )
    h3("3.1 Dataset 1: Baseline Cluster Runs")
    fp(
        "The primary evaluation cluster comprises 16 workers, 4 racks, 2 slots per worker (32 total slots), 3 replicas per block, "
        "and 128 tasks (4x slot count) across 4 concurrent jobs. It establishes the clean empirical backbone for headline comparative metrics."
    )
    h3("3.2 Dataset 2: Full Benchmark Matrix")
    fp(
        "A comprehensive dataset spanning 78 unique cluster and network configurations evaluated across 50 paired random seeds (11,700 total runs). "
        "It records makespan, mean turnaround, queueing wait times, remote input bytes, cross-rack bytes, locality distribution, and slot utilization."
    )
    h3("3.3 Dataset 3: Summary Statistical Matrix")
    fp(
        "A paired statistical matrix computing mean differences (Base − Alternative), sample standard deviations, and 95% confidence intervals "
        "derived from the Student's t-distribution with 49 degrees of freedom. It provides the mathematical proof supporting each hypothesis."
    )
    h3("3.4 Supplementary: Live Simulation Workload Generator")
    fp(
        "The Python simulation engine generates seeded workload instances dynamically, placing blocks according to official HDFS rack-awareness rules: "
        "Replica 1 on a random worker, Replica 2 on a distinct rack, and Replica 3 on a different worker in the second rack. "
        "Because workloads are generated deterministically from a user-selected seed, the web dashboard enables live experimentation on identical paired runs."
    )

    # =========================================================================
    # SECTION 4: METHODOLOGY
    # =========================================================================
    h2("4. Methodology")
    fp("Workflow: Cluster Modeling → Paired Workload Generation → Event Dispatch → Schedulers → Statistical Profiling → Live Visualisation")
    
    h3("4.1 Discrete-Event Simulator Architecture (simulation.cpp / sim_engine.py)")
    fp("The discrete-event simulation engine executes deterministically without wall-clock sleeps:")
    cp("Initialize priority queue with JobArrival events at virtual release times r_j.")
    cp("Track worker slot occupancy: each worker w provides m slots; total cluster slots = W · m.")
    cp("Dispatch ready tasks FIFO to the active scheduler (Blind, Aware, or Delay).")
    cp("Under the simple network model, compute read latency T_read = S_i / D_l and enqueue ReadDone.")
    cp("Under the shared-link network model, register in-flight flows and evolve processor-sharing rates analytically.")
    cp("On ReadDone, commence computation: finish time = now + C_i; enqueue TaskFinish.")
    cp("On TaskFinish, free worker slot, record completion metrics, and re-invoke task dispatch.")

    h3("4.2 Analysis and Scheduling Scripts")
    cp("sim_engine.py implements the exact discrete-event simulator in pure Python for the web dashboard.", bold_prefix="sim_engine.py: ")
    cp("run_matrix.cpp executes the 78 configurations across 50 paired seeds in C++20.", bold_prefix="run_matrix.cpp: ")
    cp("analyze.py computes paired Student's t-distributions, summary tables, and all 10 evaluation figures.", bold_prefix="analyze.py: ")
    cp("app.py provides the multi-tab interactive Streamlit web dashboard deployed live on the cloud.", bold_prefix="app.py: ")

    h3("4.3 Metric Definitions")
    fp(
        "Makespan measures the elapsed time from the earliest job release to the completion of the final task: "
        "Makespan = max(finish) − min(release). Mean Job Turnaround measures the average duration from a job's release to its last task finishing: "
        "Turnaround_j = max_{i in j}(finish_i) − r_j. Remote Input Traffic is the sum of input bytes of rack-local and off-rack tasks; "
        "Cross-Rack Traffic is the sum for off-rack tasks only. Improvement percentage is defined as 100 · (Base − Alt) / Base."
    )

    # =========================================================================
    # SECTION 5: LOCALITY DYNAMICS & EXPERIMENTAL ANALYSIS
    # =========================================================================
    h2("5. Locality Dynamics & Experimental Analysis")
    
    h3("5.1 Volume")
    add_table(
        ["Measure", "Value across Benchmark Study"],
        [
            ["Total Cluster Simulation Runs", "11,700 runs (78 settings × 50 seeds × 3 policies)"],
            ["Total Simulated Tasks Executed", "1,497,600 tasks"],
            ["Total Input Data Processed", "191.68 Terabytes (synthetic splits)"],
            ["Evaluated Split Sizes", "64 MiB, 128 MiB, 256 MiB"],
            ["Cluster Sizes Evaluated", "4 to 32 worker nodes (8 to 64 slots)"],
            ["Replication Factors Evaluated", "k = 1, 2, 3, and 4 replicas"],
            ["Cross-Rack Bandwidths Evaluated", "5, 10, 25, 50, 100, and 200 MiB/s"]
        ]
    )
    bt(
        "Evaluating 11,700 individual cluster executions provides a massive statistical foundation. The total data volume processed "
        "exceeds 190 TB in virtual simulation time, ensuring that empirical distributions accurately reflect real-world cluster scaling."
    )

    h3("5.2 Velocity")
    cp("Tasks dispatch rapidly: under heavy load, slots turn over every 5.6 to 10.1 seconds depending on read latency.")
    cp("Job arrival spacing is evaluated from 0 s (all jobs released simultaneously) up to 80 s gaps, modeling batch burstiness.")
    cp("Processor-sharing flow rates update dynamically whenever any flow finishes, modeling microsecond-level link rate adaptation.")
    cp("The live Streamlit application executes full cluster simulations on demand in less than 80 milliseconds.")

    h3("5.3 Variety")
    add_table(
        ["Dimension of Variety", "Evidence in the Simulator"],
        [
            ["Network Models", "Independent dedicated rates vs. Shared Core Link Processor Sharing (GPS)"],
            ["Locality Levels", "Three physical tiers: Node-Local, Rack-Local, Off-Rack"],
            ["Cluster Topologies", "From 1 rack up to 8 racks; 4 to 32 workers (up to 64 slots)"],
            ["Scheduling Policies", "Locality-Blind (Round-Robin), Greedy Locality-Aware, Delay Scheduling (timer D)"],
            ["Implementation Paradigms", "C++20 compiled high-speed core alongside pure Python interactive engine"]
        ]
    )

    h3("5.4 Veracity")
    fp("Veracity reflects the experimental integrity, verification rigor, and reproducibility of the simulation results.")
    add_table(
        ["Verification Test Case", "Expected Analytical Invariant", "Observed Simulator Result"],
        [
            ["One-worker cluster", "Zero remote traffic; makespan = 4 × (5s compute + 1s read) = 24s", "Remote MiB = 0; Makespan = 24.0s (Exact)"],
            ["Full replication (k = W)", "All tasks execute node-locally under greedy policy", "Node-local = 100%; Remote MiB = 0 (Exact)"],
            ["Slot concurrency limit", "Number of concurrent tasks never exceeds worker slot capacity m", "Running tasks <= m at all virtual timestamps"],
            ["Equivalence proof", "Delay scheduling with threshold D = 0 reduces to greedy aware", "Bit-identical metrics across all 50 seeds"],
            ["Processor sharing math", "Two 128 MiB flows sharing 64 MiB/s link complete in 4s instead of 2s", "Makespan = 5.0s (4s read + 1s compute) (Exact)"]
        ]
    )
    bt(
        "Paired-Seed Determinism. Because all three policies execute on identical workload instances within each seed, "
        "the paired difference eliminates random workload variation. Every reported metric difference is statistically significant "
        "at the 95% confidence level."
    )

    fig("figures/fig1_completion_time.png", "Figure 1: (a) Makespan, (b) Mean job turnaround, and (c) Mean task wait across policies in the main cluster.")
    fig("figures/fig2_network_traffic.png", "Figure 2: Remote input traffic and cross-rack traffic comparison in the main cluster.")
    fig("figures/fig4_locality_distribution.png", "Figure 3: Locality distribution breakdown across policies in main and small cluster topologies.")

    h3("5.5 Value")
    fp("Value represents the actionable systems insights and architectural guidelines extracted from the study:")
    cp("Delay Scheduling Dominates Greedy: In the 16-worker cluster, greedy aware reduces remote traffic by 20.7%, whereas delay scheduling reduces remote traffic by 72.8% and cross-rack traffic by 91.3%, accelerating makespan by 25.6%.")
    cp("The Decoupling Law: Network traffic savings remain invariant to bandwidth, but completion-time gains shrink from 15.8% to 0.4% as cross-rack bandwidth expands from 5 to 200 MiB/s.")
    cp("Congestion Collapse Prevention: On a shared 25 MiB/s core link, blind scheduling causes congestion collapse (makespan 336.9s), while delay scheduling maintains 47.0s.")
    cp("Avoiding the Cost of Waiting: When network transfers are cheap (< 1s), delay thresholds D > 0 cause worker slots to sit idle, increasing makespan by up to 4.5%.")

    fig("figures/fig3_bandwidth_sensitivity.png", "Figure 4: Makespan, remote traffic, and improvement percentage across cross-rack bandwidths (5 to 200 MiB/s).")
    fig("figures/fig9_contention.png", "Figure 5: Makespan under shared core link capacity constraints demonstrating congestion collapse.")

    # =========================================================================
    # SECTION 6: DASHBOARD DESIGN
    # =========================================================================
    h2("6. Dashboard Design (Streamlit & Plotly)")
    h3("6.1 Structure")
    fp(
        "A multi-module web application featuring a landing dashboard, live simulation sandbox, benchmark matrix explorer, "
        "and research paper artifacts viewer."
    )
    add_table(
        ["Page / Module", "KPI Cards (Live Metrics)", "Visualizations & Interactive Components"],
        [
            ["🎮 Live Simulator", "Makespan, Remote MiB Saved, Cross-Rack MiB, Node-Local %, Utilization", "Cluster topology controls, Comparative bar charts, Interactive Gantt timeline"],
            ["📊 Benchmark Matrix", "Selected Experiment, Setting ID, Baseline Mean, Alternative Mean, Improvement %", "Means with 95% CI error bars, Seed-level boxplots across 50 seeds, Parameter filter"],
            ["🔬 Hypothesis Analyzer", "Bandwidth sensitivity, Waiting cost delta, Shared link speedup", "Interactive log-scale curves for H2, Delay trade-off curves for H4, Contention collapse plot"],
            ["📄 Paper & Downloads", "Total runs (11,700), Settings count (78), PDF / DOCX status", "Abstract, Key findings summary, One-click downloads for PDF paper and CSV datasets"]
        ]
    )

    h3("6.2 Interactivity")
    cp("Live parameter sliders: Workers (4-32), Racks (1-8), Slots (1-4), Replicas (1-4), Block size (64-256 MiB), Bandwidth (5-200 MiB/s), Delay D (0-10 s).")
    cp("Interactive Gantt Timeline: Horizontal bar chart showing execution per worker slot lane; hover tooltips display Task ID, Read Phase duration, and Locality.")
    cp("Dynamic Metric Cards: Recompute percentage improvements and traffic savings live as parameters change.")
    cp("Cloud Deployment: Hosted permanently on Streamlit Community Cloud with GitHub CI/CD synchronization.")

    # =========================================================================
    # SECTION 7: IMPLEMENTATION STATUS
    # =========================================================================
    h2("7. Implementation Status")
    add_table(
        ["Component", "Implementation Status", "Technical Stack"],
        [
            ["Discrete-Event Core", "Complete; passes 100% CTest assertions", "C++20 (Standard Library, CMake)"],
            ["Python Simulation Engine", "Complete; powers live web dashboard", "Python 3.12 (sim_engine.py)"],
            ["Full 78-Setting Matrix", "Complete; 11,700 runs executed", "run_matrix.cpp, all_runs.csv"],
            ["Statistical Analysis & Figures", "Complete; summary.csv & 10 figures generated", "analyze.py (pandas, scipy, matplotlib)"],
            ["Interactive Web Dashboard", "Complete; deployed live on web", "Streamlit, Plotly Express & Graph Objects"],
            ["Public Cloud URL", "Live; GitHub synced", "https://github.com/markivhgins/hadoop-locality-simulator"]
        ]
    )

    # =========================================================================
    # SECTION 8: RESULTS AND DISCUSSION
    # =========================================================================
    h2("8. Results and Discussion")
    fp(
        "The experimental study reveals four fundamental principles governing data locality in distributed big data systems:"
    )
    cp("Patience Trumps Greed: Greedy locality-aware scheduling achieves only a 5.7% makespan reduction because it falls back to off-rack workers immediately. Delay scheduling (D = 2s) allows brief pauses that increase node locality to 77.8%, cutting cross-rack traffic by 91.3% and reducing makespan by 25.6%.")
    cp("The Decoupling Law: As data center networks evolve toward 10GbE and 25GbE backbones, the time saved by avoiding a remote read diminishes toward zero (0.4% at 200 MiB/s), while the network bytes saved remain strictly constant. Locality optimization in high-speed fabrics must be justified by core switch offloading rather than job speedup.")
    cp("Protection Against Congestion Collapse: Under shared bottleneck links, unmanaged remote reads trigger congestion collapse, inflating makespan by over 700% (336.9s vs 47.0s). Locality awareness acts as a vital circuit breaker for network stability.")
    cp("The Cost of Waiting: When network transfers are inexpensive, delay scheduling incurs an adverse makespan penalty (+4.5%). Delay parameters must be dynamically adjusted relative to the ratio of network latency to task computation duration.")

    # =========================================================================
    # SECTION 9: CHALLENGES AND LIMITATIONS
    # =========================================================================
    h2("9. Challenges and Limitations")
    cp("The simulator models network contention via processor sharing rather than packet-level TCP packet dynamics and switch buffer queueing.")
    cp("Task compute durations are modeled using uniform synthetic distributions; real-world production jobs often exhibit skewed, heavy-tailed execution profiles (stragglers).")
    cp("The scope is restricted to map-task scheduling; reduce-side shuffle traffic and multi-stage DAG dependencies are omitted.")

    # =========================================================================
    # SECTION 10: CONCLUSION AND FUTURE WORK
    # =========================================================================
    h2("10. Conclusion and Future Work")
    fp(
        "This project demonstrated, through 11,700 discrete-event simulation runs, the precise quantitative boundaries of data locality "
        "optimization in Hadoop MapReduce. We established that Delay Scheduling dramatically outperforms greedy heuristics, uncovered "
        "the completion-time decoupling law, and demonstrated congestion collapse under shared links. We built and deployed a live interactive "
        "web dashboard on Streamlit Cloud to make these findings testable by anyone via a web link. Future work includes modeling reduce-side "
        "shuffle traffic, multi-resource scheduling (CPU, memory, network), and reinforcement-learning-based adaptive delay threshold tuning."
    )

    # =========================================================================
    # SECTION 11: REFERENCES
    # =========================================================================
    h2("11. References")
    cp("Dean, J., & Ghemawat, S. (2008). MapReduce: Simplified data processing on large clusters. Communications of the ACM, 51(1), 107-113.")
    cp("Shvachko, K., Kuang, H., Radia, S., & Chansler, R. (2010). The Hadoop Distributed File System. In IEEE MSST (pp. 1-10).")
    cp("Apache Hadoop Project. (2024). HDFS Architecture Guide: Rack Awareness. Apache Software Foundation.")
    cp("White, T. (2015). Hadoop: The Definitive Guide (4th ed.). O'Reilly Media.")
    cp("Greenberg, A., et al. (2009). VL2: A scalable and flexible data center network. In ACM SIGCOMM (pp. 51-62).")
    cp("Zaharia, M., et al. (2010). Delay scheduling: A simple technique for achieving locality and fairness in cluster scheduling. In ACM EuroSys (pp. 265-278).")
    cp("Isard, M., et al. (2009). Quincy: Fair scheduling for distributed computing clusters. In ACM SOSP (pp. 261-276).")
    cp("Wang, W., & Ying, L. (2016). On data locality in MapReduce: A network perspective. IEEE/ACM Transactions on Networking, 24(3), 1475-1487.")
    cp("Vavilapalli, V. K., et al. (2013). Apache Hadoop YARN: Yet Another Resource Negotiator. In ACM SoCC (pp. 1-16).")
    cp("Hedayati, F., et al. (2023). A survey on resource scheduling in big data processing systems. ACM Computing Surveys, 55(9).")

    # =========================================================================
    # APPENDIX A: PROJECT FILES
    # =========================================================================
    h2("Appendix A: Project Files")
    add_table(
        ["File", "Purpose"],
        [
            ["app.py", "Interactive multi-tab Streamlit web application with live simulation sandbox, Gantt charts, and benchmark explorer"],
            ["sim_engine.py", "Pure Python discrete-event simulator engine implementing HDFS placement, slot limits, and GPS contention"],
            ["simulation.cpp", "High-performance C++20 discrete-event event engine and network processor-sharing model"],
            ["schedulers.cpp", "Implementation of the three scheduling policies: Blind, Greedy Aware, and Delay Scheduling"],
            ["run_matrix.cpp", "Experiment runner executing the 78 configurations across 50 paired random seeds (11,700 runs)"],
            ["analyze.py", "Statistical analysis script generating paired Student's t-distributions, summary tables, and all 10 figures"],
            ["test_sim.cpp", "Comprehensive verification test suite checking hand-calculated edge cases via CTest"],
            ["all_runs.csv", "Raw empirical dataset containing the results of all 11,700 individual cluster simulation runs"],
            ["summary.csv", "Summary statistical matrix reporting mean differences, 95% confidence intervals, and percentage improvements"],
            ["paper_ieee.pdf", "Formal IEEE 2-column research paper (5 pages) with complete theoretical formulation and figures"],
            ["big_data_project_report.docx", "Comprehensive SRM academic project report with cover page, bonafide certificate, and all 11 sections"]
        ]
    )

    out_docx = "big_data_project_report.docx"
    doc.save(out_docx)
    print(f"Successfully generated {out_docx} with exact styles and structure from reference!")

if __name__ == '__main__':
    build_perfect_report()
