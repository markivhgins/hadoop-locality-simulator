import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
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

def create_report_docx():
    doc = docx.Document()
    
    # Set page margins to 1 inch
    for s in doc.sections:
        s.top_margin = Inches(1)
        s.bottom_margin = Inches(1)
        s.left_margin = Inches(1)
        s.right_margin = Inches(1)
        
    # Styles
    styles = doc.styles
    normal_style = styles['Normal']
    normal_style.font.name = 'Times New Roman'
    normal_style.font.size = Pt(11)
    normal_style.font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)
    normal_style.paragraph_format.line_spacing = 1.15
    normal_style.paragraph_format.space_after = Pt(4)
    
    # ---------------- COVER PAGE ----------------
    p_logo = doc.add_paragraph()
    p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if os.path.exists('extracted_report_assets/image_1.png'):
        p_logo.add_run().add_picture('extracted_report_assets/image_1.png', width=Inches(3.2))
        
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(14)
    p_title.paragraph_format.space_after = Pt(6)
    r_t1 = p_title.add_run("BIG DATA ESSENTIALS PROJECT REPORT\n(Code 21CSC314P)\n")
    r_t1.bold = True
    r_t1.font.size = Pt(15)
    r_t1.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
    
    r_deg = p_title.add_run("B. Tech CSE (Cloud Computing) – 3rd year/5th Semester\n\n")
    r_deg.font.size = Pt(12)
    r_deg.italic = True
    
    r_sub = p_title.add_run("SUBMITTED BY:\n")
    r_sub.bold = True
    r_sub.font.size = Pt(12)
    
    r_names = p_title.add_run("VIKRAM SINGH (RA2411028030010)\nAMIT VIKRAM SINGH (RA2411028030016)\n")
    r_names.bold = True
    r_names.font.size = Pt(12.5)
    r_names.font.color.rgb = RGBColor(0x1D, 0x4E, 0xD8)

    p_bldg = doc.add_paragraph()
    p_bldg.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_bldg.paragraph_format.space_before = Pt(10)
    p_bldg.paragraph_format.space_after = Pt(10)
    if os.path.exists('extracted_report_assets/image_0.png'):
        p_bldg.add_run().add_picture('extracted_report_assets/image_0.png', width=Inches(5.0))
        
    p_dept = doc.add_paragraph()
    p_dept.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_dept.paragraph_format.space_before = Pt(8)
    r_dept = p_dept.add_run(
        "DEPARTMENT OF COMPUTER SCIENCE & ENGINEERING\n"
        "FACULTY OF ENGINEERING & TECHNOLOGY\n"
        "SRM INSTITUTE OF SCIENCE & TECHNOLOGY\n"
        "DELHI NCR CAMPUS, MODINAGAR\n"
        "Odd Semester (2026-2027)"
    )
    r_dept.bold = True
    r_dept.font.size = Pt(11)
    
    doc.add_page_break()
    
    # ---------------- BONAFIDE CERTIFICATE ----------------
    p_cert_logo = doc.add_paragraph()
    p_cert_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if os.path.exists('extracted_report_assets/image_5.png'):
        p_cert_logo.add_run().add_picture('extracted_report_assets/image_5.png', width=Inches(2.8))
        
    p_cert_h = doc.add_paragraph()
    p_cert_h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cert_h.paragraph_format.space_before = Pt(16)
    p_cert_h.paragraph_format.space_after = Pt(16)
    r_cert_h = p_cert_h.add_run("BONAFIDE CERTIFICATE")
    r_cert_h.bold = True
    r_cert_h.font.size = Pt(15)
    r_cert_h.underline = True
    
    p_cert_body = doc.add_paragraph()
    p_cert_body.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_cert_body.paragraph_format.line_spacing = 1.3
    p_cert_body.paragraph_format.space_before = Pt(10)
    p_cert_body.paragraph_format.space_after = Pt(50)
    
    r_cb = p_cert_body.add_run(
        "Certified to be the bonafide record of work done by "
    )
    r_cb.font.size = Pt(11.5)
    
    r_cnames = p_cert_body.add_run("Vikram Singh (Regd. No. RA2411028030010) and Amit Vikram Singh (Regd. No. RA2411028030016) ")
    r_cnames.bold = True
    r_cnames.font.size = Pt(11.5)
    
    r_cb2 = p_cert_body.add_run(
        "of 5th semester, 3rd year B.Tech degree course in SRM INSTITUTE OF SCIENCE AND TECHNOLOGY, "
        "Delhi-NCR Campus, Modinagar, Department of Computer Science & Engineering, in Big Data Essentials (21CSC314P), "
        "during the academic year 2026-2027.\n\n"
        "Project Title: 'A Practical Study of Data Locality Optimization Techniques in Hadoop MapReduce'"
    )
    r_cb2.font.size = Pt(11.5)
    
    # Signature table
    sig_table = doc.add_table(rows=1, cols=2)
    sig_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    c0, c1 = sig_table.rows[0].cells
    c0.width = Inches(3.2)
    c1.width = Inches(3.2)
    
    p_s0 = c0.paragraphs[0]
    p_s0.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r_s0 = p_s0.add_run("\n\n___________________________\nMr. Tapas Kumar Mishra\nAssistant Professor (CSE)\nCourse Coordinator")
    r_s0.bold = True
    r_s0.font.size = Pt(11)
    
    p_s1 = c1.paragraphs[0]
    p_s1.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r_s1 = p_s1.add_run("\n\n___________________________\nDr. Neelam Singh\nHead of the Department (CSE)\nSRM IST, Delhi-NCR Campus")
    r_s1.bold = True
    r_s1.font.size = Pt(11)
    
    doc.add_page_break()
    
    # ---------------- PROJECT HEADER & METADATA ----------------
    p_meta_title = doc.add_paragraph()
    p_meta_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_meta_title.paragraph_format.space_before = Pt(6)
    p_meta_title.paragraph_format.space_after = Pt(2)
    r_mt = p_meta_title.add_run("A Practical Study of Data Locality Optimization Techniques in Hadoop MapReduce")
    r_mt.bold = True
    r_mt.font.size = Pt(14)
    r_mt.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
    
    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(4)
    r_st = p_sub.add_run("Project Title: Performance Evaluation and Simulation of Data Locality-Aware Job Scheduling in Hadoop MapReduce")
    r_st.italic = True
    r_st.font.size = Pt(11)
    
    p_dom = doc.add_paragraph()
    p_dom.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_dom.paragraph_format.space_after = Pt(14)
    r_dom = p_dom.add_run("Domain: Big Data Systems & Distributed Computing · Cloud Computing | Tools: C++20, Python (Streamlit, pandas, plotly, scipy)")
    r_dom.bold = True
    r_dom.font.size = Pt(9.5)
    r_dom.font.color.rgb = RGBColor(0x47, 0x55, 0x69)
    
    # ---------------- INDEX / TABLE OF CONTENTS ----------------
    h_idx = doc.add_heading("INDEX", level=2)
    h_idx.paragraph_format.space_before = Pt(8)
    h_idx.paragraph_format.space_after = Pt(8)
    
    idx_table = doc.add_table(rows=1, cols=3)
    idx_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    idx_table.style = 'Table Grid'
    hdr_cells = idx_table.rows[0].cells
    hdr_cells[0].text = "Sr. No."
    hdr_cells[1].text = "Particulars"
    hdr_cells[2].text = "Page No."
    for c in hdr_cells:
        set_cell_background(c, "1E293B")
        for p in c.paragraphs:
            p.runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            p.runs[0].font.bold = True
            p.runs[0].font.size = Pt(9.5)
            
    idx_data = [
        ("1", "Abstract", "4"),
        ("2", "Section 1 — Introduction (Background, Problem Statement, Objectives, Scope)", "5"),
        ("3", "Section 2 — Theoretical Framework: Hadoop Architecture & Data Locality", "6"),
        ("4", "Section 3 — System Architecture & Simulation Model", "8"),
        ("5", "Section 4 — Scheduling Algorithms (Blind, Greedy Aware, Delay)", "10"),
        ("6", "Section 5 — Experimental Setup & Evaluation Matrix (78 Settings, 50 Seeds)", "12"),
        ("7", "Section 6 — Interactive Web Dashboard Design (Streamlit & Plotly Live Deployment)", "14"),
        ("8", "Section 7 — Implementation Status & Verification", "16"),
        ("9", "Section 8 — Results and Discussion (Makespan, Traffic, Decoupling, Contention)", "17"),
        ("10", "Section 9 — Challenges and Limitations", "21"),
        ("11", "Section 10 — Conclusion and Future Work", "22"),
        ("12", "Section 11 — References", "23"),
        ("13", "Appendix A — Project Files & Source Code Inventory", "24")
    ]
    for sr, part, pg in idx_data:
        row_cells = idx_table.add_row().cells
        row_cells[0].text = sr
        row_cells[1].text = part
        row_cells[2].text = pg
        row_cells[0].width = Inches(0.8)
        row_cells[1].width = Inches(4.7)
        row_cells[2].width = Inches(0.9)
        for cell in row_cells:
            set_cell_margins(cell, top=60, bottom=60, left=100, right=100)
            for p in cell.paragraphs:
                p.runs[0].font.size = Pt(9)
                
    doc.add_page_break()
    
    # ---------------- ABSTRACT ----------------
    doc.add_heading("Abstract", level=2)
    p_abs = doc.add_paragraph()
    p_abs.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_abs.add_run(
        "Hadoop MapReduce partitions data-intensive batch workloads into parallel map tasks, while the Hadoop Distributed "
        "File System (HDFS) stores multiple replicas of every input block across physically dispersed servers and racks. "
        "A job scheduler that assigns a map task to a machine already hosting its input block achieves node-locality and eliminates "
        "network transfer entirely; a scheduler that ignores data distribution forces large data blocks across Top-of-Rack and core switches. "
        "This project presents an extensive empirical study and discrete-event simulation of data locality optimization in Hadoop MapReduce.\n\n"
        "We designed and implemented a high-performance discrete-event simulator in C++20 modeling HDFS rack-aware replica placement, "
        "worker node concurrency limits, a 3-tier locality hierarchy (node-local, rack-local, off-rack), and two distinct network transfer models: "
        "an independent bandwidth model and a shared core-link processor-sharing contention model. We evaluated three scheduling policies—"
        "Locality-Blind round-robin, Greedy Locality-Aware, and Delay Scheduling (Zaharia et al.)—across 78 experimental configurations "
        "using 50 paired random seeds (11,700 total cluster simulations).\n\n"
        "Our experiments demonstrate that while greedy locality-aware scheduling yields a modest 5.7% makespan reduction, delay scheduling "
        "(with threshold D = 2s) reduces remote input traffic by 72.8%, cross-rack traffic by 91.3%, and improves makespan by 25.6%. "
        "Crucially, we uncover the 'completion-time decoupling effect': as cluster network speeds scale from 5 to 200 MiB/s, makespan gains "
        "drop from 15.8% to 0.4% despite constant byte savings. Under shared link constraints, locality-blind scheduling triggers catastrophic "
        "congestion collapse (makespan 336.9s vs 47.0s). Finally, we developed an interactive Streamlit and Plotly dashboard deployed live "
        "on the cloud, allowing researchers to simulate custom cluster topologies, inspect live Gantt timelines, and analyze paired statistical metrics."
    )
    
    # ---------------- SECTION 1: INTRODUCTION ----------------
    doc.add_heading("1. Introduction", level=2)
    
    doc.add_heading("1.1 Background", level=3)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.add_run(
        "Over the past two decades, big data analytics has shifted from monolithic relational databases toward distributed scale-out architectures. "
        "Pioneered by Google's MapReduce framework and popularized by Apache Hadoop, the foundational principle of distributed big data systems "
        "is moving computation to data rather than moving data to computation. In enterprise clusters, datasets measuring terabytes or petabytes "
        "are stored in the Hadoop Distributed File System (HDFS), split into uniform blocks (64 to 256 MiB), and replicated across commodity DataNodes. "
        "By aligning computation slots directly with storage nodes, MapReduce achieves high aggregate throughput while protecting cluster network "
        "backbones from unnecessary saturation."
    )
    
    doc.add_heading("1.2 Problem Statement", level=3)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.add_run(
        "Although data locality is celebrated in distributed computing theory, production clusters frequently face severe resource contention. "
        "When a map task is ready to execute, nodes holding its data replicas may be fully saturated with running tasks. "
        "The cluster scheduler faces a fundamental dilemma: (1) launch the task immediately on an idle off-rack node, incurring heavy network transfer costs, "
        "or (2) force the task to wait in queue until a local slot frees, potentially idling worker slots and increasing task wait time. "
        "Furthermore, textbook descriptions rarely quantify how physical link bandwidths, split sizes, replication factors, and backbone contention "
        "influence the net benefit of data locality. This project provides rigorous quantitative answers to these trade-offs."
    )
    
    doc.add_heading("1.3 Objectives", level=3)
    p = doc.add_paragraph()
    p.add_run(
        "• Objective 1: Simulate MapReduce jobs with and without data-locality awareness using a robust discrete-event simulation engine.\n"
        "• Objective 2: Model HDFS rack-aware replica placement and network transfer models (independent vs. shared processor-sharing contention).\n"
        "• Objective 3: Evaluate three core scheduling policies (Locality-Blind, Greedy Locality-Aware, and Delay Scheduling) across 78 settings and 50 paired seeds.\n"
        "• Objective 4: Build and deploy an interactive live web dashboard (Streamlit + Plotly) with Gantt execution timelines and benchmark visualizers."
    )
    
    doc.add_heading("1.4 Scope", level=3)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.add_run(
        "The scope of this project encompasses map-task scheduling, HDFS block distribution, network transfer latency, and job completion metrics. "
        "It focuses on the map phase where input data locality is determined; reduce-side shuffle and network sorting dynamics are out of scope. "
        "All parameters are synthetic and evaluated under controlled paired random seeds to ensure exact reproducibility."
    )
    
    # ---------------- SECTION 2: THEORETICAL FRAMEWORK ----------------
    doc.add_heading("2. Theoretical Framework: Hadoop Architecture & Data Locality", level=2)
    
    doc.add_heading("2.1 MapReduce Distributed Computing Paradigm", level=3)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.add_run(
        "MapReduce operates on a split-apply-combine workflow. The input file is partitioned into logical splits, each assigned to one map task. "
        "The map function transforms raw input records into intermediate key-value pairs. Because map tasks are embarrassingly parallel, the primary "
        "performance bottleneck during the map phase is the data ingestion rate: reading input splits from disk or network."
    )
    
    doc.add_heading("2.2 HDFS Architecture & Rack Awareness", level=3)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.add_run(
        "HDFS utilizes a master-worker architecture where the NameNode manages file metadata and DataNodes store physical block replicas. "
        "To provide fault tolerance against machine crashes and entire rack power failures, HDFS implements rack awareness: "
        "the first replica is stored on a local node, the second replica on a node in a different rack, and the third replica on another node "
        "within that same second rack. This placement ensures that any block is available in at least two distinct racks, establishing the physical "
        "topology for locality-aware schedulers."
    )
    
    doc.add_heading("2.3 The 3-Tier Locality Model", level=3)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.add_run(
        "Locality exists in three hierarchical tiers based on network switch hops:\n"
        "1. Node-Local (Tier 0): The task runs on the DataNode holding the block replica. Data is read directly from local disk/page cache with zero network overhead.\n"
        "2. Rack-Local (Tier 1): The task runs on a worker in the same rack as a replica. Data traverses the intra-rack Top-of-Rack (ToR) switch.\n"
        "3. Off-Rack (Tier 2): The task runs on a worker in a different rack. Data must traverse intra-rack switches and cluster core aggregation switches."
    )
    
    doc.add_heading("2.4 Bandwidth Oversubscription in Cloud Data Centers", level=3)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.add_run(
        "In typical cloud and data center networks, intra-rack bandwidth is non-blocking (1:1 oversubscription), but core aggregation switches "
        "are oversubscribed by ratios of 1:5 to 1:20 to minimize infrastructure cost. Consequently, when hundreds of tasks simultaneously perform "
        "off-rack reads, core links saturate, leading to TCP buffer queueing, packet loss, and severe throughput degradation."
    )
    
    # ---------------- SECTION 3: SYSTEM ARCHITECTURE & SIMULATION MODEL ----------------
    doc.add_heading("3. System Architecture & Simulation Model", level=2)
    
    doc.add_heading("3.1 Discrete-Event Simulator Architecture", level=3)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.add_run(
        "The simulation engine is implemented in modern C++20 using an event-driven architecture. The engine maintains a priority queue "
        "of discrete timestamped events: JobArrival, ReadDone, TaskFinish, and Wakeup. Virtual time advances instantaneously to the timestamp "
        "of the earliest pending event. By avoiding real-time sleeps, our engine simulates months of cluster execution in seconds."
    )
    
    doc.add_heading("3.2 Cluster, Worker & Slot Modeling", level=3)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.add_run(
        "The cluster consists of W homogeneous workers partitioned into R racks (worker w belongs to rack w mod R). "
        "Each worker provides m map slots. A map task occupies exactly one slot from its launch until completion. "
        "Task execution is modeled as two serialized stages: (1) reading the input split, followed by (2) computation on CPU: "
        "Ti = Tread,i + Ci, where Ci is drawn uniformly from C_mean * (1 +- jitter)."
    )
    
    doc.add_heading("3.3 Network Models: Simple vs. Contention (Processor Sharing)", level=3)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.add_run(
        "We implement two network transmission models:\n"
        "• Simple Network Model: Each remote read transfers at its dedicated locality bandwidth D_l without interference.\n"
        "• Shared-Link Contention Model: All concurrent off-rack reads compete for a centralized core link of capacity B_core, "
        "and rack-local reads compete for their rack's link of capacity B_rack under Generalized Processor Sharing (GPS). "
        "With n active flows on link L, each flow progresses at rate min(c_f, B_L / n_L). Transfer rates are recomputed whenever any flow finishes or starts."
    )
    
    # ---------------- SECTION 4: SCHEDULING ALGORITHMS ----------------
    doc.add_heading("4. Scheduling Algorithms", level=2)
    
    doc.add_heading("4.1 Policy A: Locality-Blind Baseline", level=3)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.add_run(
        "Policy A serves as an experimental control baseline. When a slot frees, it selects ready tasks in FIFO order and assigns "
        "them to workers in strict round-robin order, completely ignoring block replica metadata. It provides an empirical lower bound "
        "on performance when block locations are disregarded."
    )
    
    doc.add_heading("4.2 Policy B: Greedy Locality-Aware", level=3)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.add_run(
        "Policy B inspects all currently idle worker slots and assigns the offered task to the worker offering the best locality level "
        "(node-local > rack-local > off-rack). Ties are broken by lowest worker index. Crucially, Policy B never waits: if no local slot "
        "is free, it immediately accepts an off-rack worker rather than allowing the task to wait."
    )
    
    doc.add_heading("4.3 Policy C: Delay Scheduling (Zaharia et al.)", level=3)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.add_run(
        "Policy C introduces a per-task timer threshold D. If a task cannot achieve node-locality on currently free slots, it declines assignment "
        "and records the timestamp when a slot was first offered. For the next D seconds, it will only accept a node-local worker. "
        "After D seconds have elapsed, it loosens its constraint to accept rack-local workers. After 2D seconds, it falls back to accepting off-rack workers. "
        "Declined tasks do not block other tasks in the ready queue, preserving overall cluster concurrency."
    )
    
    # ---------------- SECTION 5: EXPERIMENTAL SETUP & EVALUATION MATRIX ----------------
    doc.add_heading("5. Experimental Setup & Evaluation Matrix", level=2)
    
    doc.add_heading("5.1 The 78-Setting Evaluation Matrix (E1 to E6)", level=3)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.add_run(
        "We systematically varied cluster and network parameters across six benchmark suites:\n"
        "• E1 (Baseline): Small cluster (8 workers, 2 racks) and Main cluster (16 workers, 4 racks, 32 slots, 128 tasks).\n"
        "• E2 (Network & Block): Cross-rack bandwidth (5 to 200 MiB/s) and split size (64, 128, 256 MiB).\n"
        "• E3 (Load & Arrival): Cluster load factor (1x, 2x, 4x, 8x slot count) and job arrival spacing (0 to 80 s).\n"
        "• E4 (Topology & Scale): Replicas (1 to 4), Grid topology (1-8 racks x 1-3 replicas), and Workers (4 to 32).\n"
        "• E5 (Delay Parameter D): Delay threshold D in [0, 16] s evaluated under nominal, low bandwidth, light load, and fast networks.\n"
        "• E6 (Shared Link): Core link capacity (25 to 400 MiB/s) under processor sharing contention."
    )
    
    doc.add_heading("5.2 Paired-Seed Methodology (50 Paired Seeds = 11,700 Runs)", level=3)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.add_run(
        "For every configuration, we executed 50 paired random seeds (1 to 50). Across all three policies, the exact same seed generates "
        "identical workloads, block replica locations, and job release times. This isolates policy differences from stochastic noise. "
        "All improvements are reported with 95% confidence intervals using the Student's t-distribution with 49 degrees of freedom."
    )
    
    # ---------------- SECTION 6: INTERACTIVE DASHBOARD DESIGN ----------------
    doc.add_heading("6. Interactive Web Dashboard Design (Streamlit & Plotly)", level=2)
    
    doc.add_heading("6.1 Dashboard Architecture & Live Simulator Sandbox", level=3)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.add_run(
        "To make our research accessible and testable live via a web URL, we developed an interactive web application using Streamlit and Plotly. "
        "The web application integrates: (1) an exact Python discrete-event simulation engine, (2) an interactive Gantt task execution visualizer, "
        "(3) a benchmark matrix explorer covering all 11,700 runs, and (4) an interactive hypothesis trade-off analyzer."
    )
    
    doc.add_heading("6.2 Interactive Task Scheduling Timeline (Gantt Chart)", level=3)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.add_run(
        "The live dashboard generates interactive horizontal Gantt charts plotting execution timelines across every worker slot in seconds. "
        "Tasks are color-coded by locality: Green (Node-Local), Amber (Rack-Local), and Red (Off-Rack). Users can hover over any task block "
        "to inspect Task ID, Job ID, read phase latency, and total duration in real time."
    )
    
    doc.add_heading("6.3 Live Cloud Deployment", level=3)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.add_run(
        "The repository is published on GitHub (https://github.com/markivhgins/hadoop-locality-simulator) and deployed directly on "
        "Streamlit Community Cloud, providing a permanent public URL where academic peers and evaluators can interact with the simulator."
    )
    
    # ---------------- SECTION 7: IMPLEMENTATION STATUS & VERIFICATION ----------------
    doc.add_heading("7. Implementation Status & Verification", level=2)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.add_run(
        "The simulation framework includes an automated CTest test suite covering hand-calculated edge cases:\n"
        "• Single-worker cluster: Verified 0 MiB remote traffic and exact makespan (24 s).\n"
        "• Full replication: Verified 100% node-locality under Greedy Aware scheduling.\n"
        "• Slot limits: Verified concurrency never exceeds worker slot bounds.\n"
        "• Equivalence proof: Verified that Delay scheduling with D = 0 produces bit-identical metrics to Greedy Aware scheduling.\n"
        "• Processor sharing: Verified two 128 MiB concurrent flows on a 64 MiB/s link complete in exactly 4 s (32 MiB/s each) rather than 2 s."
    )
    
    # ---------------- SECTION 8: RESULTS AND DISCUSSION ----------------
    doc.add_heading("8. Results and Discussion", level=2)
    
    doc.add_heading("8.1 Completion Time & Turnaround Improvements", level=3)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.add_run(
        "In the primary 16-worker, 4-rack evaluation, the Locality-Blind baseline achieved an average makespan of 38.85 s and mean job turnaround of 26.05 s. "
        "Greedy Locality-Aware scheduling improved makespan to 36.63 s (a 5.7% ± 1.1% gain) and turnaround to 23.60 s (9.4% ± 0.9%). "
        "Delay Scheduling (D = 2s) achieved a decisive breakthrough: makespan dropped to 28.90 s (a 25.6% ± 1.4% improvement) and turnaround dropped to 19.97 s (23.3% ± 1.1%). "
        "In 100% of paired random seeds, Delay Scheduling beat both Blind and Greedy policies."
    )
    
    # Insert Figures if available
    for fpath, cap in [
        ("figures/fig1_completion_time.png", "Figure 1: Makespan, mean job turnaround, and task queueing wait across policies in the main cluster."),
        ("figures/fig2_network_traffic.png", "Figure 2: Remote input traffic and cross-rack traffic comparison in the main cluster."),
        ("figures/fig4_locality_distribution.png", "Figure 3: Locality distribution breakdown across policies in main and small cluster topologies.")
    ]:
        if os.path.exists(fpath):
            p_img = doc.add_paragraph()
            p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_img.add_run().add_picture(fpath, width=Inches(5.5))
            p_cap = doc.add_paragraph()
            p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r_c = p_cap.add_run(cap)
            r_c.font.size = Pt(9)
            r_c.italic = True

    doc.add_heading("8.2 Remote and Cross-Rack Network Traffic Reduction", level=3)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.add_run(
        "Greedy scheduling reduced remote traffic from 13,356 MiB to 10,586 MiB (20.7% ± 1.5% reduction) and cross-rack traffic from 8,348 MiB to 6,328 MiB (24.2% ± 3.4%). "
        "Delay scheduling slashed remote traffic down to 3,630 MiB (72.8% ± 2.3% reduction) and virtually eliminated cross-rack transfers, reducing cross-rack volume "
        "to just 727 MiB—a massive 91.3% ± 3.4% reduction. By preventing cross-rack transfers, delay scheduling eliminates core backbone switch saturation."
    )

    doc.add_heading("8.3 The Completion-Time Decoupling Law", level=3)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.add_run(
        "By varying cross-rack bandwidth from 5 to 200 MiB/s (Experiment E2), we discovered that network traffic volume and completion times decouple: "
        "the volume of bytes saved by locality-aware scheduling is invariant to network bandwidth, whereas completion time improvements scale inversely with bandwidth. "
        "At 5 MiB/s, greedy scheduling improves makespan by 15.8%; at 200 MiB/s, the makespan gain collapses to 0.4% ± 0.5%. "
        "In modern 10GbE/25GbE cloud fabrics, locality optimization should be deployed primarily for network power and cost efficiency, rather than raw job speedup."
    )
    if os.path.exists("figures/fig3_bandwidth_sensitivity.png"):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.add_run().add_picture("figures/fig3_bandwidth_sensitivity.png", width=Inches(5.5))
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_c = p_cap.add_run("Figure 4: Makespan, remote traffic, and improvement percentage as cross-rack bandwidth varies from 5 to 200 MiB/s.")
        r_c.font.size = Pt(9)
        r_c.italic = True

    doc.add_heading("8.4 Shared Link Contention & Congestion Collapse", level=3)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.add_run(
        "Under our processor-sharing shared core link model (Experiment E6), when core capacity was limited to 25 MiB/s, the Locality-Blind baseline "
        "suffered catastrophic congestion collapse, inflating makespan to 336.9 s. In contrast, Delay Scheduling confined cross-rack transfers to 4.5% of tasks, "
        "bypassing the bottleneck link and finishing in 47.0 s—an 86.1% speedup."
    )
    if os.path.exists("figures/fig9_contention.png"):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.add_run().add_picture("figures/fig9_contention.png", width=Inches(5.5))
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_c = p_cap.add_run("Figure 5: Makespan under shared core link capacity constraints demonstrating congestion collapse.")
        r_c.font.size = Pt(9)
        r_c.italic = True

    doc.add_heading("8.5 The 'Cost of Waiting' in High-Speed Fabrics", level=3)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.add_run(
        "Under high-bandwidth networks (200 MiB/s) or light cluster loads (tasks/slots = 1.0), waiting for local worker slots proved counterproductive. "
        "Because remote transfers required only 0.64 s, delaying tasks by D = 2 s caused slots to sit idle, increasing makespan by up to 4.5%. "
        "Thus, delay thresholds must be dynamically tuned relative to the network read penalty."
    )
    
    # ---------------- SECTION 9: CHALLENGES AND LIMITATIONS ----------------
    doc.add_heading("9. Challenges and Limitations", level=2)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.add_run(
        "1. Discrete-Event Abstractions: The simulator models network contention via generalized processor sharing rather than packet-level TCP packet dynamics.\n"
        "2. Synthetic Task Durations: Real-world MapReduce jobs exhibit skewed, non-uniform compute distributions (stragglers).\n"
        "3. Map-Phase Scope: The present simulator focuses exclusively on the map task phase; shuffle and sort phases are not modeled."
    )
    
    # ---------------- SECTION 10: CONCLUSION AND FUTURE WORK ----------------
    doc.add_heading("10. Conclusion and Future Work", level=2)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.add_run(
        "This project completed an end-to-end practical study of data locality optimization in Hadoop MapReduce. "
        "Using 11,700 simulation runs across 78 settings, we proved that Delay Scheduling achieves 25.6% makespan improvements and eliminates over 91% "
        "of cross-rack traffic. We established the Completion-Time Decoupling Law, proved shared link congestion collapse, and identified the cost of waiting. "
        "The project delivered an interactive, cloud-deployed web dashboard on Streamlit Cloud.\n\n"
        "Future work will incorporate reduce-side shuffle traffic modeling, multi-tenant fairness scheduling, and reinforcement learning for adaptive delay threshold selection."
    )
    
    # ---------------- SECTION 11: REFERENCES ----------------
    doc.add_heading("11. References", level=2)
    report_refs = [
        "1. Dean, J., & Ghemawat, S. (2008). MapReduce: Simplified data processing on large clusters. Communications of the ACM, 51(1), 107-113.",
        "2. Shvachko, K., Kuang, H., Radia, S., & Chansler, R. (2010). The Hadoop Distributed File System. In IEEE MSST (pp. 1-10).",
        "3. Apache Hadoop Project. (2024). HDFS Architecture Guide: Rack Awareness. Apache Software Foundation.",
        "4. White, T. (2015). Hadoop: The Definitive Guide (4th ed.). O'Reilly Media.",
        "5. Greenberg, A., et al. (2009). VL2: A scalable and flexible data center network. In ACM SIGCOMM (pp. 51-62).",
        "6. Zaharia, M., et al. (2010). Delay scheduling: A simple technique for achieving locality and fairness in cluster scheduling. In ACM EuroSys (pp. 265-278).",
        "7. Isard, M., et al. (2009). Quincy: Fair scheduling for distributed computing clusters. In ACM SOSP (pp. 261-276).",
        "8. Wang, W., & Ying, L. (2016). On data locality in MapReduce: A network perspective. IEEE/ACM Transactions on Networking, 24(3), 1475-1487.",
        "9. Vavilapalli, V. K., et al. (2013). Apache Hadoop YARN: Yet Another Resource Negotiator. In ACM SoCC (pp. 1-16).",
        "10. Hedayati, F., et al. (2023). A survey on resource scheduling in big data processing systems. ACM Computing Surveys, 55(9)."
    ]
    for r in report_refs:
        p_r = doc.add_paragraph()
        p_r.paragraph_format.left_indent = Inches(0.25)
        p_r.paragraph_format.first_line_indent = Inches(-0.25)
        r_run = p_r.add_run(r)
        r_run.font.size = Pt(9.5)
        
    # ---------------- APPENDIX A: PROJECT FILES ----------------
    doc.add_heading("Appendix A: Project Files & Source Code Inventory", level=2)
    app_table = doc.add_table(rows=1, cols=2)
    app_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    app_table.style = 'Table Grid'
    ahdr = app_table.rows[0].cells
    ahdr[0].text = "File Name"
    ahdr[1].text = "Description & Purpose"
    set_cell_background(ahdr[0], "1E293B")
    set_cell_background(ahdr[1], "1E293B")
    for cell in ahdr:
        cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        cell.paragraphs[0].runs[0].font.bold = True
        cell.paragraphs[0].runs[0].font.size = Pt(9.5)
        
    files_list = [
        ("app.py", "Interactive multi-tab Streamlit web application with live simulation sandbox, Gantt charts, and benchmark explorer"),
        ("sim_engine.py", "Pure Python discrete-event simulator engine implementing HDFS placement, slot limits, and GPS contention"),
        ("simulation.cpp", "High-performance C++20 discrete-event event engine and network processor-sharing model"),
        ("schedulers.cpp", "Implementation of the three scheduling policies: Blind, Greedy Aware, and Delay Scheduling"),
        ("run_matrix.cpp", "Experiment runner executing the 78 configurations across 50 paired random seeds (11,700 runs)"),
        ("analyze.py", "Statistical analysis script generating paired Student's t-distributions, summary tables, and all 10 figures"),
        ("test_sim.cpp", "Comprehensive verification test suite checking hand-calculated edge cases via CTest"),
        ("all_runs.csv", "Raw empirical dataset containing the results of all 11,700 individual cluster simulation runs"),
        ("summary.csv", "Summary statistical matrix reporting mean differences, 95% confidence intervals, and percentage improvements"),
        ("paper_ieee.pdf", "Formal IEEE 2-column research paper (5 pages) with complete theoretical formulation and figures"),
        ("big_data_project_report.docx", "Comprehensive SRM academic project report with cover page, bonafide certificate, and all 11 sections")
    ]
    for fn, desc in files_list:
        rc = app_table.add_row().cells
        rc[0].text = fn
        rc[1].text = desc
        rc[0].width = Inches(2.2)
        rc[1].width = Inches(4.3)
        set_cell_margins(rc[0], top=60, bottom=60, left=100, right=100)
        set_cell_margins(rc[1], top=60, bottom=60, left=100, right=100)
        rc[0].paragraphs[0].runs[0].font.bold = True
        rc[0].paragraphs[0].runs[0].font.size = Pt(9)
        rc[1].paragraphs[0].runs[0].font.size = Pt(9)
        
    doc.save("big_data_project_report.docx")
    print("Successfully generated big_data_project_report.docx!")

if __name__ == '__main__':
    create_report_docx()
