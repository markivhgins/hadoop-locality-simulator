import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_margins(cell, top=60, bottom=60, left=100, right=100):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def set_cell_background(cell, hex_color):
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)

def create_paper_docx():
    doc = docx.Document()
    
    # 0.5 inch margins for IEEE format
    s1 = doc.sections[0]
    s1.top_margin = Inches(0.5)
    s1.bottom_margin = Inches(0.5)
    s1.left_margin = Inches(0.5)
    s1.right_margin = Inches(0.5)
    
    styles = doc.styles
    normal_style = styles['Normal']
    normal_style.font.name = 'Times New Roman'
    normal_style.font.size = Pt(8.5)
    normal_style.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
    normal_style.paragraph_format.line_spacing = 1.05
    normal_style.paragraph_format.space_after = Pt(2)
    
    # Title Block (Full width)
    p_t = doc.add_paragraph()
    p_t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_t = p_t.add_run("A Practical Study of Data Locality Optimization Techniques in Hadoop MapReduce")
    r_t.bold = True
    r_t.font.size = Pt(17)
    
    p_a = doc.add_paragraph()
    p_a.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_a.paragraph_format.space_before = Pt(4)
    p_a.paragraph_format.space_after = Pt(2)
    r_a = p_a.add_run("Vikram Singh (RA2411028030010)       Amit Vikram Singh (RA2411028030016)")
    r_a.bold = True
    r_a.font.size = Pt(10)
    
    p_aff = doc.add_paragraph()
    p_aff.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_aff.paragraph_format.space_after = Pt(8)
    r_aff = p_aff.add_run(
        "Department of Computer Science & Engineering, Faculty of Engineering & Technology\n"
        "SRM Institute of Science & Technology, Delhi NCR Campus, Modinagar, India\n"
        "Big Data Essentials (21CSC314P) Project Report & Research Study"
    )
    r_aff.italic = True
    r_aff.font.size = Pt(8.5)
    r_aff.font.color.rgb = RGBColor(0x47, 0x55, 0x69)
    
    # Switch to 2 columns
    s2 = doc.add_section()
    s2.top_margin = Inches(0.5)
    s2.bottom_margin = Inches(0.5)
    s2.left_margin = Inches(0.5)
    s2.right_margin = Inches(0.5)
    
    cols = s2._sectPr.xpath('./w:cols')
    if cols:
        cols[0].set(qn('w:num'), '2')
        cols[0].set(qn('w:space'), '720')
    else:
        new_cols = parse_xml(f'<w:cols {nsdecls("w")} w:num="2" w:space="720"/>')
        s2._sectPr.append(new_cols)
        
    # Abstract
    p_abs = doc.add_paragraph()
    p_abs.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r_ab = p_abs.add_run(
        "Abstract—Hadoop MapReduce partitions data into splits processed by concurrent map tasks, "
        "while HDFS replicates blocks across heterogeneous machines and racks. A job scheduler that allocates a map "
        "task to a node already storing its input block avoids network transfers; a scheduler that ignores data distribution "
        "induces substantial network saturation. This paper investigates the empirical performance boundaries of data locality "
        "optimization in MapReduce. We design and implement a discrete-event simulator in C++20 modeling HDFS rack-aware replica "
        "placement, finite worker slots, a three-tier locality hierarchy (node-local, rack-local, off-rack), and two network models: "
        "independent bandwidth and shared core-link processor sharing. Across 78 experimental configurations with 50 paired random seeds "
        "(11,700 runs), we evaluate three scheduling policies: Locality-Blind round-robin, Greedy Locality-Aware, and Delay Scheduling. "
        "In our main 16-worker, 4-rack cluster, greedy locality-aware scheduling reduces remote input traffic by 20.7% ± 1.5% and cross-rack "
        "traffic by 24.2% ± 3.4%, but improves makespan by only 5.7% ± 1.1%. Delay scheduling (D = 2 s) reduces remote traffic by "
        "72.8% ± 2.3% and cross-rack traffic by 91.3% ± 3.4%, yielding a 25.6% ± 1.4% makespan improvement. We reveal a critical "
        "decoupling: as network bandwidth increases from 5 to 200 MiB/s, completion-time advantages fall from 15.8% to 0.4% despite constant "
        "byte reductions. Under shared bottlenecks, blind scheduling incurs severe congestion collapse (makespan 336.9 s vs. 47.0 s for delay "
        "scheduling). Finally, we demonstrate the 'cost of waiting', where delay scheduling inflates makespan by up to 4.5% when remote reads "
        "are cheap."
    )
    r_ab.bold = True
    r_ab.italic = True
    r_ab.font.size = Pt(8.2)
    
    p_idx = doc.add_paragraph()
    p_idx.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r_id = p_idx.add_run("Index Terms—Hadoop, MapReduce, Data Locality, HDFS, Delay Scheduling, Discrete-Event Simulation, Network Contention, Big Data Systems.")
    r_id.bold = True
    r_id.font.size = Pt(8.2)
    
    def add_h1(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(3)
        r = p.add_run(text)
        r.bold = True
        r.font.size = Pt(9.5)
        return p
        
    def add_h2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(5)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(text)
        r.bold = True
        r.italic = True
        r.font.size = Pt(8.7)
        return p
        
    def add_p(text, indent=True):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        if indent:
            p.paragraph_format.first_line_indent = Inches(0.15)
        r = p.add_run(text)
        r.font.size = Pt(8.3)
        return p
        
    # I. INTRODUCTION
    add_h1("I. INTRODUCTION")
    add_p("Modern big data frameworks, notably Apache Hadoop MapReduce [1] and Apache Spark, process petabyte-scale datasets by decomposing massive analytical jobs into parallel map tasks. In enterprise architectures, the input dataset resides within the Hadoop Distributed File System (HDFS) [2], which partitions files into uniform blocks (typically 64–256 MiB) and replicates them across cluster storage nodes. By enforcing rack awareness [3], HDFS distributes replicas across distinct physical racks to guard against localized rack failures. Because compute nodes (TaskTrackers/NodeManagers) and storage nodes (DataNodes) are co-located on commodity physical servers, an intelligent scheduler can assign a map task directly to a server hosting its input block, eliminating network transfer entirely [4].")
    add_p("Network topologies in commodity data centers exhibit significant tiered oversubscription: intra-rack bandwidth is broad and non-blocking, whereas inter-rack core backbones are oversubscribed and prone to severe congestion [5]. Consequently, execution locality governs three distinct physical tiers: node-local (zero network transfer), rack-local (intra-rack switch traversal), and off-rack (traversal across core switches). While data locality is widely cited as fundamental to MapReduce efficiency, production clusters face severe slot contention: when a task arrives, nodes holding its data may have all computation slots fully occupied. The scheduler must choose whether to launch the task remotely without delay or hold the task in queue until a local slot frees.")
    add_p("This research resolves four primary research questions: RQ1: How much remote and cross-rack traffic is eliminated by locality awareness under standard HDFS replica topologies? RQ2: Does eliminating network bytes translate directly into proportional job completion time (makespan) speedups? RQ3: How do physical network bandwidths, split sizes, and cluster load scale the utility of locality awareness? RQ4: Under what operational regimes does waiting for local worker slots degrade rather than enhance overall cluster makespan?")
    add_p("To evaluate these questions rigorously, we formulate four pre-registered hypotheses: H1: Locality-aware scheduling significantly curtails remote data volume when data is not fully replicated. H2: The completion-time advantage of locality awareness contracts as network bandwidth approaches local memory/disk throughput. H3: Delay scheduling increases node-local execution at the expense of higher task queueing wait times. H4: Waiting for local slots incurs a net makespan penalty under light load or high-speed network fabrics.")
    add_p("Contributions: We design and implement a discrete-event simulator in C++20 incorporating HDFS rack-aware placement, finite worker slots, and Generalized Processor Sharing (GPS) flow contention. We evaluate 78 experimental configurations across 50 paired random seeds (11,700 total cluster simulations), isolating policy effects with paired Student's t-distributions. We provide an interactive open-source Streamlit dashboard for real-time Gantt timeline execution and research verification.")

    # II. BACKGROUND AND SYSTEM MODEL
    add_h1("II. BACKGROUND AND SYSTEM MODEL")
    add_h2("A. Cluster and Storage Topology")
    add_p("We model a cluster comprising W homogeneous worker nodes grouped into R physical racks. Each worker node w is mapped to rack w mod R. Each worker provides m computation slots, supporting a cluster concurrency of W · m map tasks. HDFS block placement enforces the standard Apache rack-aware heuristic: for each block b with replication factor k, the primary replica is placed on a randomly chosen worker w1; the secondary replica is placed on a worker w2 in a separate rack; and the tertiary replica is placed on a worker w3 within the second replica's rack (w3 != w2).", indent=False)
    
    add_h2("B. Workload Demands and Execution Model")
    add_p("Workloads consist of J batch jobs released at virtual times r_j. Each job comprises n independent map tasks. Task i processes an input split of size S_i MiB and demands compute time C_i drawn uniformly from C_mean*(1 +- 0.5), with base compute demand C_mean = 5.0 s. Execution serializes input reading and CPU processing: T_i = T_read,i + C_i. Input read latency is governed by effective bandwidth D_l across locality levels l: T_read,i = S_i / D_l, where D_l in {D_local, D_rack, D_cross}. Default baseline parameters are D_local = 200 MiB/s, D_rack = 100 MiB/s, and D_cross = 25 MiB/s.", indent=False)

    add_h2("C. Network Contention: Shared-Link Model")
    add_p("In the simple network model, every remote read proceeds at rate D_l independently without mutual interference. In the shared-link contention model, concurrent remote reads compete over physical links governed by Generalized Processor Sharing (GPS). Off-rack reads share a core backbone switch of capacity B_core, while rack-local reads share an intra-rack switch of capacity B_rack. When n_L flows actively traverse link L, each flow progresses at instantaneous rate r_f(t) = min(c_f, B_L / n_L(t)), where c_f is the per-flow rate cap. Rates are recalculated dynamically whenever any transfer begins or completes.", indent=False)

    # III. SCHEDULING ALGORITHMS
    add_h1("III. SCHEDULING ALGORITHMS")
    add_p("All policies operate over a unified FIFO queue of pending tasks. When a slot becomes available on any worker, ready tasks are offered to the scheduler:")
    add_p("1) Policy A: Locality-Blind Baseline. Assigns the offered task to the next available free worker in round-robin sequence, never inspecting block metadata.")
    add_p("2) Policy B: Greedy Locality-Aware. Inspects free workers and assigns the task to the worker offering highest locality: node-local > rack-local > off-rack. Ties are broken by lowest worker index. Crucially, it never waits: if no local slot is idle, it falls back immediately to off-rack execution.")
    add_p("3) Policy C: Delay Scheduling (Zaharia et al. [6]). When a task cannot find a node-local slot on free workers, it is temporarily declined and sets a timer. The task waits up to D seconds for a node-local worker. If still unassigned after D s, it accepts rack-local workers. After 2D s, it falls back to off-rack assignment. Declined tasks do not head-of-line block subsequent tasks in the FIFO queue.")

    # IV. SIMULATION METHODOLOGY & MATRIX
    add_h1("IV. SIMULATION METHODOLOGY & MATRIX")
    add_p("The discrete-event simulation engine maintains a global virtual clock and a min-priority queue of timestamped events: JobArrival, ReadDone, TaskFinish, and Wakeup. Monotonically increasing sequence counters ensure deterministic tie-breaking. Virtual time leaps forward to the timestamp of the next event, enabling rapid evaluation of full multi-job clusters without sleeping.")
    add_p("Paired-Seed Methodology: For each setting, 50 random seeds (1 to 50) are executed. For a given seed, all three scheduling policies receive the exact same workload instance: identical task compute demands, identical HDFS block replica locations, and identical job release times. We report mean difference, 95% confidence intervals from the Student's t-distribution with 49 degrees of freedom, and improvement percentages.")

    # V. RESULTS AND ANALYSIS
    add_h1("V. RESULTS AND ANALYSIS")
    add_h2("A. Baseline Cluster Performance (E1)")
    add_p("In our main evaluation cluster (16 workers, 4 racks, 32 slots, 128 tasks), the Locality-Blind scheduler achieves only 18.5% node-local execution and sends 50.9% of all tasks across core switches. This generates 13,356 MiB of remote traffic and 8,348 MiB of cross-rack traffic, yielding an average makespan of 38.85 s. Greedy Locality-Aware scheduling elevates node-local execution to 35.4% and suppresses off-rack tasks to 38.6%, reducing remote traffic by 20.7% +- 1.5% and cross-rack traffic by 24.2% +- 3.4%. However, because greedy scheduling falls back immediately, makespan improves by only 5.7% +- 1.1%.")
    add_p("Delay Scheduling (D = 2s) achieves profound performance gains: it reaches 77.8% node-local execution and suppresses off-rack tasks to just 4.5%. Remote traffic plunges by 72.8% +- 2.3%, cross-rack traffic collapses by 91.3% +- 3.4%, and makespan drops by 25.6% +- 1.4% (from 38.85 s down to 28.90 s). Turnaround drops by 23.3% +- 1.1% across all 50 seeds.")

    add_h2("B. Network Bandwidth Sensitivity & Decoupling (E2)")
    add_p("We vary cross-rack bandwidth logarithmically from 5 to 200 MiB/s. We discover that network traffic volume and completion times decouple: the volume of bytes saved by locality-aware scheduling is invariant to network bandwidth, whereas completion time improvements scale inversely with bandwidth. At 5 MiB/s, greedy scheduling saves 15.8% in makespan; at 200 MiB/s, the gain contracts to 0.4% +- 0.5%. Thus, in high-bandwidth cloud fabrics, locality optimization is primarily justified by network offloading and cost reduction rather than raw speedup.")

    add_h2("C. Shared Link Contention & Congestion Collapse (E6)")
    add_p("Under our processor-sharing core model, when link capacity is constrained to 25 MiB/s, Locality-Blind scheduling triggers catastrophic congestion collapse: makespan explodes to 336.9 s. In contrast, Delay Scheduling confines cross-rack transfers to 4.5% of tasks, maintaining a makespan of 47.0 s—an 86.1% improvement.")

    add_h2("D. The Cost of Waiting in Delay Scheduling (E5)")
    add_p("Under fast network fabrics (200 MiB/s) or light cluster loads (tasks/slots = 1.0), waiting for local slots incurs a net penalty. Because remote transfers require only 0.64 s, delaying tasks by D = 2 s causes slots to sit idle, increasing makespan by up to 4.5% relative to greedy scheduling. Thus, delay thresholds must be bounded strictly below the expected remote read penalty.")

    # VI. RELATED WORK
    add_h1("VI. RELATED WORK")
    add_p("Resource reservation and performance isolation have been extensively studied. In CPU scheduling, Constant Bandwidth Servers (CBS) [7] and overrun control algorithms [8] provide temporal isolation. In multi-core platforms, MemGuard [9] regulates memory bandwidth via hardware performance counters. In big data clusters, Zaharia et al. [6] pioneered delay scheduling in Hadoop, while Isard et al. [10] developed Quincy via min-cost flow graph optimization. Wang and Ying [11] analyzed data locality from a queueing network perspective. Our work complements these papers by delivering a transparent, paired discrete-event simulation matrix evaluating both independent and shared-link contention models.")

    # VII. CONCLUSION
    add_h1("VII. CONCLUSION AND FUTURE WORK")
    add_p("This paper presented a rigorous simulation study of data locality optimization in Hadoop MapReduce across 11,700 runs. We demonstrated that while greedy scheduling provides modest gains (5.7% makespan), delay scheduling delivers dramatic optimization (25.6% makespan, 72.8% remote traffic, 91.3% cross-rack traffic reduction). We established the Completion-Time Decoupling Law, proved shared link congestion collapse, and quantified the cost of waiting in high-speed fabrics.")

    # ACKNOWLEDGMENT
    add_h1("ACKNOWLEDGMENT")
    add_p("The authors express sincere gratitude to Mr. Tapas Kumar Mishra (Assistant Professor) and Dr. Neelam Singh (Head of the Department), Department of Computer Science & Engineering, SRM Institute of Science & Technology, Delhi NCR Campus, Modinagar, for their academic guidance and support.", indent=False)

    # REFERENCES
    add_h1("REFERENCES")
    refs = [
        "[1] J. Dean and S. Ghemawat, 'MapReduce: Simplified data processing on large clusters,' Communications of the ACM, vol. 51, no. 1, pp. 107-113, 2008.",
        "[2] K. Shvachko, H. Kuang, S. Radia, and R. Chansler, 'The Hadoop Distributed File System,' in Proc. IEEE MSST, 2010, pp. 1-10.",
        "[3] Apache Software Foundation, 'HDFS Architecture Guide: Rack Awareness,' Apache Hadoop Documentation, 2024.",
        "[4] T. White, Hadoop: The Definitive Guide, 4th ed. O'Reilly Media, 2015.",
        "[5] A. Greenberg et al., 'VL2: A scalable and flexible data center network,' in Proc. ACM SIGCOMM, 2009, pp. 51-62.",
        "[6] M. Zaharia et al., 'Delay scheduling: A simple technique for achieving locality and fairness in cluster scheduling,' in Proc. ACM EuroSys, 2010, pp. 265-278.",
        "[7] L. Abeni and G. Buttazzo, 'Integrating multimedia applications in hard real-time systems,' in Proc. IEEE RTSS, 1998, pp. 4-13.",
        "[8] M. Caccamo, G. Buttazzo, and L. Sha, 'Capacity sharing for overrun control,' in Proc. IEEE RTSS, 2000, pp. 295-304.",
        "[9] H. Yun, G. Yao, R. Pellizzoni, M. Caccamo, and L. Sha, 'MemGuard: Memory bandwidth reservation system for efficient performance isolation in multi-core platforms,' in Proc. IEEE RTAS, 2013, pp. 55-64.",
        "[10] M. Isard et al., 'Quincy: Fair scheduling for distributed computing clusters,' in Proc. ACM SOSP, 2009, pp. 261-276.",
        "[11] W. Wang and L. Ying, 'On data locality in MapReduce: A network perspective,' IEEE/ACM Transactions on Networking, vol. 24, no. 3, pp. 1475-1487, 2016.",
        "[12] V. K. Vavilapalli et al., 'Apache Hadoop YARN: Yet Another Resource Negotiator,' in Proc. ACM SoCC, 2013, pp. 1-16.",
        "[13] F. Hedayati et al., 'A survey on resource scheduling in big data processing systems,' ACM Computing Surveys, vol. 55, no. 9, 2023.",
        "[14] B. Akesson et al., 'Predator: A predictable SDRAM memory controller,' in Proc. CODES+ISSS, 2007, pp. 251-256.",
        "[15] J. Reineke et al., 'PRET DRAM controller: Bank privatization for predictability,' in Proc. CODES+ISSS, 2011, pp. 125-130."
    ]
    for r in refs:
        p_r = doc.add_paragraph()
        p_r.paragraph_format.left_indent = Inches(0.18)
        p_r.paragraph_format.first_line_indent = Inches(-0.18)
        run_r = p_r.add_run(r)
        run_r.font.size = Pt(7.2)
        
    doc.save("paper_ieee.docx")
    print("Successfully generated paper_ieee.docx!")

if __name__ == '__main__':
    create_paper_docx()
