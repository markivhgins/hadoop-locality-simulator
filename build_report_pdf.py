import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, PageBreak, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class ReportNumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        # Do not draw headers/footers on cover page (page 1) or certificate (page 2)
        if self._pageNumber > 2:
            self.saveState()
            self.setFont("Times-Roman", 8.5)
            self.setFillColor(colors.HexColor("#475569"))
            
            # Running Header
            self.drawString(54, 755, "SRM INSTITUTE OF SCIENCE & TECHNOLOGY — DEPARTMENT OF CSE")
            self.drawRightString(558, 755, "BIG DATA ESSENTIALS (21CSC314P)")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 749, 558, 749)
            
            # Running Footer
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 42, 558, 42)
            self.drawString(54, 30, "Project Report · Data Locality-Aware Job Scheduler Simulator")
            page_text = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(558, 30, page_text)
            self.restoreState()

def build_report_pdf():
    pdf_filename = "big_data_project_report.pdf"
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    t_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=15,
        leading=19,
        alignment=1,
        textColor=colors.HexColor("#0F172A")
    )
    
    sub_style = ParagraphStyle(
        'CoverSub',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=11.5,
        leading=15,
        alignment=1,
        textColor=colors.HexColor("#1E293B")
    )
    
    names_style = ParagraphStyle(
        'CoverNames',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=12,
        leading=16,
        alignment=1,
        textColor=colors.HexColor("#1D4ED8")
    )
    
    dept_style = ParagraphStyle(
        'CoverDept',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=10.5,
        leading=14,
        alignment=1,
        textColor=colors.HexColor("#0F172A")
    )
    
    h1_style = ParagraphStyle(
        'RepH1',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=13,
        leading=16,
        spaceBefore=14,
        spaceAfter=6,
        textColor=colors.HexColor("#0F172A")
    )
    
    h2_style = ParagraphStyle(
        'RepH2',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=11,
        leading=14,
        spaceBefore=10,
        spaceAfter=4,
        textColor=colors.HexColor("#1E293B")
    )
    
    body_style = ParagraphStyle(
        'RepBody',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=10,
        leading=13.5,
        alignment=4,
        spaceBefore=0,
        spaceAfter=5,
        textColor=colors.HexColor("#1E293B")
    )
    
    bullet_style = ParagraphStyle(
        'RepBullet',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceBefore=2,
        spaceAfter=2
    )
    
    caption_style = ParagraphStyle(
        'RepCaption',
        parent=styles['Normal'],
        fontName='Times-Italic',
        fontSize=8.5,
        leading=11,
        alignment=1,
        spaceBefore=3,
        spaceAfter=6,
        textColor=colors.HexColor("#475569")
    )

    story = []
    
    # ---------------- PAGE 1: COVER PAGE ----------------
    if os.path.exists('extracted_report_assets/image_1.png'):
        story.append(Image('extracted_report_assets/image_1.png', width=240, height=80))
        story.append(Spacer(1, 10))
        
    story.append(Paragraph("BIG DATA ESSENTIALS PROJECT REPORT<br/>(Code 21CSC314P)", t_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("<i>B. Tech CSE (Cloud Computing) – 3rd year/5th Semester</i>", sub_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>SUBMITTED BY:</b>", sub_style))
    story.append(Spacer(1, 2))
    story.append(Paragraph("VIKRAM SINGH (RA2411028030010)<br/>AMIT VIKRAM SINGH (RA2411028030016)", names_style))
    story.append(Spacer(1, 12))
    
    if os.path.exists('extracted_report_assets/image_0.png'):
        story.append(Image('extracted_report_assets/image_0.png', width=380, height=190))
        story.append(Spacer(1, 12))
        
    story.append(Paragraph(
        "DEPARTMENT OF COMPUTER SCIENCE & ENGINEERING<br/>"
        "FACULTY OF ENGINEERING & TECHNOLOGY<br/>"
        "SRM INSTITUTE OF SCIENCE & TECHNOLOGY<br/>"
        "DELHI NCR CAMPUS, MODINAGAR<br/>"
        "Odd Semester (2026-2027)", dept_style))
    story.append(PageBreak())
    
    # ---------------- PAGE 2: BONAFIDE CERTIFICATE ----------------
    if os.path.exists('extracted_report_assets/image_5.png'):
        story.append(Image('extracted_report_assets/image_5.png', width=220, height=95))
        story.append(Spacer(1, 15))
        
    cert_title_style = ParagraphStyle(
        'CertTitle',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=15,
        leading=18,
        alignment=1,
        spaceBefore=10,
        spaceAfter=20,
        textColor=colors.HexColor("#0F172A")
    )
    story.append(Paragraph("<u>BONAFIDE CERTIFICATE</u>", cert_title_style))
    story.append(Spacer(1, 15))
    
    cert_body = (
        "Certified to be the bonafide record of work done by <b>Vikram Singh (Regd. No. RA2411028030010)</b> and "
        "<b>Amit Vikram Singh (Regd. No. RA2411028030016)</b> of 5th semester, 3rd year B.Tech degree course in "
        "<b>SRM INSTITUTE OF SCIENCE AND TECHNOLOGY</b>, Delhi-NCR Campus, Modinagar, Department of Computer Science & Engineering, "
        "in Big Data Essentials (21CSC314P), during the academic year 2026-2027.<br/><br/>"
        "Project Title: <i>'A Practical Study of Data Locality Optimization Techniques in Hadoop MapReduce'</i>"
    )
    cert_style = ParagraphStyle(
        'CertBody',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=11.5,
        leading=17,
        alignment=4,
        textColor=colors.HexColor("#1E293B")
    )
    story.append(Paragraph(cert_body, cert_style))
    story.append(Spacer(1, 80))
    
    sig_data = [
        [Paragraph("<b>___________________________<br/>Mr. Tapas Kumar Mishra</b><br/>Assistant Professor (CSE)<br/>Course Coordinator", body_style),
         Paragraph("<b>___________________________<br/>Dr. Neelam Singh</b><br/>Head of the Department (CSE)<br/>SRM IST, Delhi-NCR Campus", body_style)]
    ]
    t_sig = Table(sig_data, colWidths=[250, 250])
    t_sig.setStyle(TableStyle([
        ('ALIGN', (0,0), (0,0), 'LEFT'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(t_sig)
    story.append(PageBreak())
    
    # ---------------- PAGE 3: TITLE, METADATA & INDEX ----------------
    story.append(Paragraph("A Practical Study of Data Locality Optimization Techniques in Hadoop MapReduce", t_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("<i>Project Title: Performance Evaluation and Simulation of Data Locality-Aware Job Scheduling in Hadoop MapReduce</i>", sub_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>Domain:</b> Big Data Systems & Distributed Computing · Cloud Computing | <b>Tools:</b> C++20, Python (Streamlit, pandas, plotly, scipy)", caption_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#0F172A"), spaceBefore=4, spaceAfter=10))
    
    story.append(Paragraph("INDEX", h1_style))
    idx_data = [
        ["Sr. No.", "Particulars", "Page No."],
        ["1", "Abstract", "4"],
        ["2", "Section 1 — Introduction (Background, Problem Statement, Objectives, Scope)", "5"],
        ["3", "Section 2 — Theoretical Framework: Hadoop Architecture & Data Locality", "6"],
        ["4", "Section 3 — System Architecture & Simulation Model", "8"],
        ["5", "Section 4 — Scheduling Algorithms (Blind, Greedy Aware, Delay)", "10"],
        ["6", "Section 5 — Experimental Setup & Evaluation Matrix (78 Settings, 50 Seeds)", "12"],
        ["7", "Section 6 — Interactive Web Dashboard Design (Streamlit & Plotly Live Deployment)", "14"],
        ["8", "Section 7 — Implementation Status & Verification", "16"],
        ["9", "Section 8 — Results and Discussion (Makespan, Traffic, Decoupling, Contention)", "17"],
        ["10", "Section 9 — Challenges and Limitations", "21"],
        ["11", "Section 10 — Conclusion and Future Work", "22"],
        ["12", "Section 11 — References", "23"],
        ["13", "Appendix A — Project Files & Source Code Inventory", "24"]
    ]
    t_idx = Table(idx_data, colWidths=[50, 390, 60])
    t_idx.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E293B")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Times-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8.5),
        ('LEADING', (0,0), (-1,-1), 11),
        ('ALIGN', (0,0), (0,-1), 'CENTER'),
        ('ALIGN', (1,0), (1,-1), 'LEFT'),
        ('ALIGN', (2,0), (2,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_idx)
    story.append(PageBreak())
    
    # ---------------- PAGE 4: ABSTRACT ----------------
    story.append(Paragraph("Abstract", h1_style))
    story.append(Paragraph(
        "Hadoop MapReduce partitions data-intensive batch workloads into parallel map tasks, while the Hadoop Distributed "
        "File System (HDFS) stores multiple replicas of every input block across physically dispersed servers and racks. "
        "A job scheduler that assigns a map task to a machine already hosting its input block achieves node-locality and eliminates "
        "network transfer entirely; a scheduler that ignores data distribution forces large data blocks across Top-of-Rack and core switches. "
        "This project presents an extensive empirical study and discrete-event simulation of data locality optimization in Hadoop MapReduce.<br/><br/>"
        "We designed and implemented a high-performance discrete-event simulator in C++20 modeling HDFS rack-aware replica placement, "
        "worker node concurrency limits, a 3-tier locality hierarchy (node-local, rack-local, off-rack), and two distinct network transfer models: "
        "an independent bandwidth model and a shared core-link processor-sharing contention model. We evaluated three scheduling policies—"
        "Locality-Blind round-robin, Greedy Locality-Aware, and Delay Scheduling (Zaharia et al.)—across 78 experimental configurations "
        "using 50 paired random seeds (11,700 total cluster simulations).<br/><br/>"
        "Our experiments demonstrate that while greedy locality-aware scheduling yields a modest 5.7% makespan reduction, delay scheduling "
        "(with threshold D = 2s) reduces remote input traffic by 72.8%, cross-rack traffic by 91.3%, and improves makespan by 25.6%. "
        "Crucially, we uncover the 'completion-time decoupling effect': as cluster network speeds scale from 5 to 200 MiB/s, makespan gains "
        "drop from 15.8% to 0.4% despite constant byte savings. Under shared link constraints, locality-blind scheduling triggers catastrophic "
        "congestion collapse (makespan 336.9s vs 47.0s). Finally, we developed an interactive Streamlit and Plotly dashboard deployed live "
        "on the cloud, allowing researchers to simulate custom cluster topologies, inspect live Gantt timelines, and analyze paired statistical metrics.",
        body_style
    ))
    story.append(PageBreak())
    
    # ---------------- SECTION 1: INTRODUCTION ----------------
    story.append(Paragraph("1. Introduction", h1_style))
    story.append(Paragraph("1.1 Background", h2_style))
    story.append(Paragraph(
        "Over the past two decades, big data analytics has shifted from monolithic relational databases toward distributed scale-out architectures. "
        "Pioneered by Google's MapReduce framework and popularized by Apache Hadoop, the foundational principle of distributed big data systems "
        "is moving computation to data rather than moving data to computation. In enterprise clusters, datasets measuring terabytes or petabytes "
        "are stored in the Hadoop Distributed File System (HDFS), split into uniform blocks (64 to 256 MiB), and replicated across commodity DataNodes. "
        "By aligning computation slots directly with storage nodes, MapReduce achieves high aggregate throughput while protecting cluster network "
        "backbones from unnecessary saturation.", body_style))
    
    story.append(Paragraph("1.2 Problem Statement", h2_style))
    story.append(Paragraph(
        "Although data locality is celebrated in distributed computing theory, production clusters frequently face severe resource contention. "
        "When a map task is ready to execute, nodes holding its data replicas may be fully saturated with running tasks. "
        "The cluster scheduler faces a fundamental dilemma: (1) launch the task immediately on an idle off-rack node, incurring heavy network transfer costs, "
        "or (2) force the task to wait in queue until a local slot frees, potentially idling worker slots and increasing task wait time. "
        "Furthermore, textbook descriptions rarely quantify how physical link bandwidths, split sizes, replication factors, and backbone contention "
        "influence the net benefit of data locality. This project provides rigorous quantitative answers to these trade-offs.", body_style))

    story.append(Paragraph("1.3 Objectives", h2_style))
    story.append(Paragraph("• <b>Objective 1:</b> Simulate MapReduce jobs with and without data-locality awareness using a robust discrete-event simulation engine.", bullet_style))
    story.append(Paragraph("• <b>Objective 2:</b> Model HDFS rack-aware replica placement and network transfer models (independent vs. shared processor-sharing contention).", bullet_style))
    story.append(Paragraph("• <b>Objective 3:</b> Evaluate three core scheduling policies (Locality-Blind, Greedy Locality-Aware, and Delay Scheduling) across 78 settings and 50 paired seeds.", bullet_style))
    story.append(Paragraph("• <b>Objective 4:</b> Build and deploy an interactive live web dashboard (Streamlit + Plotly) with Gantt execution timelines and benchmark visualizers.", bullet_style))

    story.append(Paragraph("1.4 Scope", h2_style))
    story.append(Paragraph(
        "The scope of this project encompasses map-task scheduling, HDFS block distribution, network transfer latency, and job completion metrics. "
        "It focuses on the map phase where input data locality is determined; reduce-side shuffle and network sorting dynamics are out of scope. "
        "All parameters are synthetic and evaluated under controlled paired random seeds to ensure exact reproducibility.", body_style))

    # ---------------- SECTION 2: THEORETICAL FRAMEWORK ----------------
    story.append(Paragraph("2. Theoretical Framework: Hadoop Architecture & Data Locality", h1_style))
    story.append(Paragraph("2.1 MapReduce Distributed Computing Paradigm", h2_style))
    story.append(Paragraph(
        "MapReduce operates on a split-apply-combine workflow. The input file is partitioned into logical splits, each assigned to one map task. "
        "The map function transforms raw input records into intermediate key-value pairs. Because map tasks are embarrassingly parallel, the primary "
        "performance bottleneck during the map phase is the data ingestion rate: reading input splits from disk or network.", body_style))

    story.append(Paragraph("2.2 HDFS Architecture & Rack Awareness", h2_style))
    story.append(Paragraph(
        "HDFS utilizes a master-worker architecture where the NameNode manages file metadata and DataNodes store physical block replicas. "
        "To provide fault tolerance against machine crashes and entire rack power failures, HDFS implements rack awareness: "
        "the first replica is stored on a local node, the second replica on a node in a different rack, and the third replica on another node "
        "within that same second rack. This placement ensures that any block is available in at least two distinct racks, establishing the physical "
        "topology for locality-aware schedulers.", body_style))

    story.append(Paragraph("2.3 The 3-Tier Locality Model", h2_style))
    story.append(Paragraph(
        "Locality exists in three hierarchical tiers based on network switch hops:<br/>"
        "1. <b>Node-Local (Tier 0):</b> The task runs on the DataNode holding the block replica. Data is read directly from local disk/page cache with zero network overhead.<br/>"
        "2. <b>Rack-Local (Tier 1):</b> The task runs on a worker in the same rack as a replica. Data traverses the intra-rack Top-of-Rack (ToR) switch.<br/>"
        "3. <b>Off-Rack (Tier 2):</b> The task runs on a worker in a different rack. Data must traverse intra-rack switches and cluster core aggregation switches.", body_style))

    # ---------------- SECTION 3: SYSTEM ARCHITECTURE ----------------
    story.append(Paragraph("3. System Architecture & Simulation Model", h1_style))
    story.append(Paragraph("3.1 Discrete-Event Simulator Architecture", h2_style))
    story.append(Paragraph(
        "The simulation engine is implemented in modern C++20 using an event-driven architecture. The engine maintains a priority queue "
        "of discrete timestamped events: JobArrival, ReadDone, TaskFinish, and Wakeup. Virtual time advances instantaneously to the timestamp "
        "of the earliest pending event. By avoiding real-time sleeps, our engine simulates months of cluster execution in seconds.", body_style))

    story.append(Paragraph("3.2 Cluster, Worker & Slot Modeling", h2_style))
    story.append(Paragraph(
        "The cluster consists of W homogeneous workers partitioned into R racks (worker w belongs to rack w mod R). "
        "Each worker provides m map slots. A map task occupies exactly one slot from its launch until completion. "
        "Task execution is modeled as two serialized stages: (1) reading the input split, followed by (2) computation on CPU: "
        "T_i = T_read,i + C_i, where C_i is drawn uniformly from C_mean * (1 +- jitter).", body_style))

    story.append(Paragraph("3.3 Network Models: Simple vs. Contention (Processor Sharing)", h2_style))
    story.append(Paragraph(
        "We implement two network transmission models:<br/>"
        "• <b>Simple Network Model:</b> Each remote read transfers at its dedicated locality bandwidth D_l without interference.<br/>"
        "• <b>Shared-Link Contention Model:</b> All concurrent off-rack reads compete for a centralized core link of capacity B_core, "
        "and rack-local reads compete for their rack's link of capacity B_rack under Generalized Processor Sharing (GPS). "
        "With n active flows on link L, each flow progresses at rate min(c_f, B_L / n_L). Transfer rates are recomputed whenever any flow finishes or starts.", body_style))

    # ---------------- SECTION 4: SCHEDULING ALGORITHMS ----------------
    story.append(Paragraph("4. Scheduling Algorithms", h1_style))
    story.append(Paragraph("4.1 Policy A: Locality-Blind Baseline", h2_style))
    story.append(Paragraph(
        "Policy A serves as an experimental control baseline. When a slot frees, it selects ready tasks in FIFO order and assigns "
        "them to workers in strict round-robin order, completely ignoring block replica metadata. It provides an empirical lower bound "
        "on performance when block locations are disregarded.", body_style))

    story.append(Paragraph("4.2 Policy B: Greedy Locality-Aware", h2_style))
    story.append(Paragraph(
        "Policy B inspects all currently idle worker slots and assigns the offered task to the worker offering the best locality level "
        "(node-local > rack-local > off-rack). Ties are broken by lowest worker index. Crucially, Policy B never waits: if no local slot "
        "is free, it immediately accepts an off-rack worker rather than allowing the task to wait.", body_style))

    story.append(Paragraph("4.3 Policy C: Delay Scheduling (Zaharia et al.)", h2_style))
    story.append(Paragraph(
        "Policy C introduces a per-task timer threshold D. If a task cannot achieve node-locality on currently free slots, it declines assignment "
        "and records the timestamp when a slot was first offered. For the next D seconds, it will only accept a node-local worker. "
        "After D seconds have elapsed, it loosens its constraint to accept rack-local workers. After 2D seconds, it falls back to accepting off-rack workers. "
        "Declined tasks do not block other tasks in the ready queue, preserving overall cluster concurrency.", body_style))

    # ---------------- SECTION 5: EXPERIMENTAL SETUP ----------------
    story.append(Paragraph("5. Experimental Setup & Evaluation Matrix", h1_style))
    story.append(Paragraph(
        "We systematically varied cluster and network parameters across six benchmark suites (78 settings, 50 seeds, 11,700 runs):<br/>"
        "• <b>E1 (Baseline):</b> Small cluster (8w, 2r) and Main cluster (16w, 4r, 32 slots, 128 tasks).<br/>"
        "• <b>E2 (Network & Block):</b> Cross-rack bandwidth (5 to 200 MiB/s) and split size (64, 128, 256 MiB).<br/>"
        "• <b>E3 (Load & Arrival):</b> Cluster load factor (1x, 2x, 4x, 8x slot count) and job arrival spacing (0 to 80 s).<br/>"
        "• <b>E4 (Topology & Scale):</b> Replicas (1 to 4), Grid topology (1-8 racks x 1-3 replicas), and Workers (4 to 32).<br/>"
        "• <b>E5 (Delay Parameter D):</b> Delay threshold D in [0, 16] s evaluated under nominal, low bandwidth, light load, and fast networks.<br/>"
        "• <b>E6 (Shared Link):</b> Core link capacity (25 to 400 MiB/s) under processor sharing contention.", body_style))

    # ---------------- SECTION 6: WEB DASHBOARD DESIGN ----------------
    story.append(Paragraph("6. Interactive Web Dashboard Design (Streamlit & Plotly)", h1_style))
    story.append(Paragraph(
        "To make our research accessible and testable live via a web URL, we developed an interactive web application using Streamlit and Plotly. "
        "The web application integrates: (1) an exact Python discrete-event simulation engine, (2) an interactive Gantt task execution visualizer, "
        "(3) a benchmark matrix explorer covering all 11,700 runs, and (4) an interactive hypothesis trade-off analyzer.<br/><br/>"
        "The repository is published on GitHub (https://github.com/markivhgins/hadoop-locality-simulator) and deployed directly on "
        "Streamlit Community Cloud, providing a permanent public URL where academic peers and evaluators can interact with the simulator.", body_style))

    # ---------------- SECTION 7: IMPLEMENTATION STATUS ----------------
    story.append(Paragraph("7. Implementation Status & Verification", h1_style))
    story.append(Paragraph(
        "The simulation framework includes an automated CTest test suite covering hand-calculated edge cases:<br/>"
        "• Single-worker cluster: Verified 0 MiB remote traffic and exact makespan (24 s).<br/>"
        "• Full replication: Verified 100% node-locality under Greedy Aware scheduling.<br/>"
        "• Slot limits: Verified concurrency never exceeds worker slot bounds.<br/>"
        "• Equivalence proof: Verified that Delay scheduling with D = 0 produces bit-identical metrics to Greedy Aware scheduling.<br/>"
        "• Processor sharing: Verified two 128 MiB concurrent flows on a 64 MiB/s link complete in exactly 4 s rather than 2 s.", body_style))

    # ---------------- SECTION 8: RESULTS AND DISCUSSION ----------------
    story.append(Paragraph("8. Results and Discussion", h1_style))
    story.append(Paragraph(
        "In the primary 16-worker, 4-rack evaluation, the Locality-Blind baseline achieved an average makespan of 38.85 s and mean job turnaround of 26.05 s. "
        "Greedy Locality-Aware scheduling improved makespan to 36.63 s (a 5.7% ± 1.1% gain) and turnaround to 23.60 s (9.4% ± 0.9%). "
        "Delay Scheduling (D = 2s) achieved a decisive breakthrough: makespan dropped to 28.90 s (a 25.6% ± 1.4% improvement) and turnaround dropped to 19.97 s (23.3% ± 1.1%). "
        "In 100% of paired random seeds, Delay Scheduling beat both Blind and Greedy policies.", body_style))

    if os.path.exists("figures/fig1_completion_time.png"):
        story.append(Spacer(1, 4))
        story.append(Image("figures/fig1_completion_time.png", width=420, height=145))
        story.append(Paragraph("Figure 1: Makespan, mean job turnaround, and task queueing wait across policies in the main cluster.", caption_style))

    if os.path.exists("figures/fig2_network_traffic.png"):
        story.append(Spacer(1, 4))
        story.append(Image("figures/fig2_network_traffic.png", width=360, height=160))
        story.append(Paragraph("Figure 2: Remote input traffic and cross-rack traffic comparison in the main cluster.", caption_style))

    if os.path.exists("figures/fig4_locality_distribution.png"):
        story.append(Spacer(1, 4))
        story.append(Image("figures/fig4_locality_distribution.png", width=380, height=150))
        story.append(Paragraph("Figure 3: Locality distribution breakdown across policies in main and small cluster topologies.", caption_style))

    story.append(Paragraph(
        "<b>The Completion-Time Decoupling Law:</b> By varying cross-rack bandwidth from 5 to 200 MiB/s, we discovered that network traffic volume and completion times decouple: "
        "the volume of bytes saved by locality-aware scheduling is invariant to network bandwidth, whereas completion time improvements scale inversely with bandwidth. "
        "At 5 MiB/s, greedy scheduling saves 15.8% in makespan; at 200 MiB/s, the makespan gain collapses to 0.4% ± 0.5%.", body_style))

    if os.path.exists("figures/fig3_bandwidth_sensitivity.png"):
        story.append(Spacer(1, 4))
        story.append(Image("figures/fig3_bandwidth_sensitivity.png", width=420, height=135))
        story.append(Paragraph("Figure 4: Makespan, remote traffic, and improvement percentage across cross-rack bandwidths.", caption_style))

    story.append(Paragraph(
        "<b>Shared Link Contention:</b> Under our processor-sharing shared core link model, when core capacity was limited to 25 MiB/s, the Locality-Blind baseline "
        "suffered catastrophic congestion collapse, inflating makespan to 336.9 s. In contrast, Delay Scheduling confined cross-rack transfers to 4.5% of tasks, "
        "bypassing the bottleneck link and finishing in 47.0 s—an 86.1% speedup.", body_style))

    if os.path.exists("figures/fig9_contention.png"):
        story.append(Spacer(1, 4))
        story.append(Image("figures/fig9_contention.png", width=420, height=135))
        story.append(Paragraph("Figure 5: Makespan under shared core link capacity constraints demonstrating congestion collapse.", caption_style))

    # ---------------- SECTION 9: CHALLENGES & LIMITATIONS ----------------
    story.append(Paragraph("9. Challenges and Limitations", h1_style))
    story.append(Paragraph(
        "1. Discrete-Event Abstractions: The simulator models network contention via generalized processor sharing rather than packet-level TCP packet dynamics.<br/>"
        "2. Synthetic Task Durations: Real-world MapReduce jobs exhibit skewed, non-uniform compute distributions (stragglers).<br/>"
        "3. Map-Phase Scope: The present simulator focuses exclusively on the map task phase; shuffle and sort phases are not modeled.", body_style))

    # ---------------- SECTION 10: CONCLUSION ----------------
    story.append(Paragraph("10. Conclusion and Future Work", h1_style))
    story.append(Paragraph(
        "This project completed an end-to-end practical study of data locality optimization in Hadoop MapReduce. "
        "Using 11,700 simulation runs across 78 settings, we proved that Delay Scheduling achieves 25.6% makespan improvements and eliminates over 91% "
        "of cross-rack traffic. We established the Completion-Time Decoupling Law, proved shared link congestion collapse, and identified the cost of waiting. "
        "The project delivered an interactive, cloud-deployed web dashboard on Streamlit Cloud.<br/><br/>"
        "Future work will incorporate reduce-side shuffle traffic modeling, multi-tenant fairness scheduling, and reinforcement learning for adaptive delay threshold selection.",
        body_style))

    # ---------------- SECTION 11: REFERENCES ----------------
    story.append(Paragraph("11. References", h1_style))
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
        story.append(Paragraph(r, bullet_style))

    # ---------------- APPENDIX A: PROJECT FILES ----------------
    story.append(Paragraph("Appendix A: Project Files & Source Code Inventory", h1_style))
    files_list = [
        ["File Name", "Description & Purpose"],
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
    t_files = Table(files_list, colWidths=[150, 350])
    t_files.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E293B")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Times-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('LEADING', (0,0), (-1,-1), 10.5),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_files)

    doc.build(story, canvasmaker=ReportNumberedCanvas)
    print(f"Successfully generated {pdf_filename}!")

if __name__ == '__main__':
    build_report_pdf()
