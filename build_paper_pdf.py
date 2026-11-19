import os
import sys
import re
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
    Table, TableStyle, Image, KeepTogether, HRFlowable, FrameBreak, NextPageTemplate
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
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
        self.saveState()
        self.setFont("Times-Roman", 8)
        self.setFillColor(colors.HexColor("#334155"))
        
        # Header (pages 2+)
        if self._pageNumber > 1:
            self.drawString(36, 756, "SRM INSTITUTE OF SCIENCE & TECHNOLOGY — BIG DATA SYSTEMS RESEARCH")
            self.drawRightString(576, 756, "DATA LOCALITY SCHEDULING IN HADOOP MAPREDUCE")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(36, 750, 576, 750)
            
        # Footer
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(36, 38, 576, 38)
        
        self.drawString(36, 26, "IEEE Format · Research Paper · Big Data Essentials (21CSC314P)")
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(576, 26, page_text)
        self.restoreState()

def build_pdf():
    pdf_filename = "paper_ieee.pdf"
    
    margin = 36 # 0.5 inch
    gutter = 14
    page_width, page_height = letter
    col_width = (page_width - 2 * margin - gutter) / 2 # ~263 pt
    
    title_height = 140
    p1_col_height = page_height - 2 * margin - title_height
    other_col_height = page_height - 2 * margin - 15
    
    frame_title = Frame(margin, page_height - margin - title_height, page_width - 2 * margin, title_height,
                        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=4, id='F_Title')
    frame_p1_c1 = Frame(margin, margin, col_width, p1_col_height,
                        leftPadding=0, rightPadding=2, topPadding=4, bottomPadding=0, id='F_P1_C1')
    frame_p1_c2 = Frame(margin + col_width + gutter, margin, col_width, p1_col_height,
                        leftPadding=2, rightPadding=0, topPadding=4, bottomPadding=0, id='F_P1_C2')
    
    frame_c1 = Frame(margin, margin, col_width, other_col_height,
                     leftPadding=0, rightPadding=2, topPadding=6, bottomPadding=0, id='F_C1')
    frame_c2 = Frame(margin + col_width + gutter, margin, col_width, other_col_height,
                     leftPadding=2, rightPadding=0, topPadding=6, bottomPadding=0, id='F_C2')
    
    doc = BaseDocTemplate(pdf_filename, pagesize=letter, leftMargin=margin, rightMargin=margin,
                          topMargin=margin, bottomMargin=margin)
    
    p1_template = PageTemplate(id='FirstPage', frames=[frame_title, frame_p1_c1, frame_p1_c2])
    later_template = PageTemplate(id='LaterPages', frames=[frame_c1, frame_c2])
    doc.addPageTemplates([p1_template, later_template])
    
    base_styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=base_styles['Normal'],
        fontName='Times-Bold',
        fontSize=16.5,
        leading=19.5,
        alignment=1,
        textColor=colors.HexColor("#0F172A")
    )
    
    author_style = ParagraphStyle(
        'DocAuthor',
        parent=base_styles['Normal'],
        fontName='Times-Roman',
        fontSize=9.5,
        leading=12.5,
        alignment=1,
        textColor=colors.HexColor("#1E293B")
    )
    
    affil_style = ParagraphStyle(
        'DocAffil',
        parent=base_styles['Normal'],
        fontName='Times-Italic',
        fontSize=8.5,
        leading=11,
        alignment=1,
        textColor=colors.HexColor("#475569")
    )
    
    abstract_style = ParagraphStyle(
        'DocAbstract',
        parent=base_styles['Normal'],
        fontName='Times-Roman',
        fontSize=8.3,
        leading=10.8,
        alignment=4,
        textColor=colors.HexColor("#0F172A"),
        firstLineIndent=10
    )
    
    sec_style = ParagraphStyle(
        'DocSection',
        parent=base_styles['Normal'],
        fontName='Times-Bold',
        fontSize=9.5,
        leading=12.5,
        alignment=1,
        spaceBefore=7,
        spaceAfter=3,
        textColor=colors.HexColor("#0F172A")
    )
    
    subsec_style = ParagraphStyle(
        'DocSubSection',
        parent=base_styles['Normal'],
        fontName='Times-BoldItalic',
        fontSize=8.6,
        leading=11.2,
        alignment=0,
        spaceBefore=5,
        spaceAfter=2,
        textColor=colors.HexColor("#0F172A")
    )
    
    body_style = ParagraphStyle(
        'DocBody',
        parent=base_styles['Normal'],
        fontName='Times-Roman',
        fontSize=8.3,
        leading=10.8,
        alignment=4,
        firstLineIndent=9,
        spaceBefore=0,
        spaceAfter=2.5,
        textColor=colors.HexColor("#0F172A")
    )
    
    body_noindent = ParagraphStyle(
        'DocBodyNoIndent',
        parent=body_style,
        firstLineIndent=0
    )
    
    bullet_style = ParagraphStyle(
        'DocBullet',
        parent=body_style,
        firstLineIndent=0,
        leftIndent=8,
        spaceBefore=1,
        spaceAfter=1
    )
    
    code_style = ParagraphStyle(
        'DocCode',
        parent=base_styles['Normal'],
        fontName='Courier',
        fontSize=6.8,
        leading=8.5,
        alignment=0,
        spaceBefore=1,
        spaceAfter=1,
        textColor=colors.HexColor("#0F172A")
    )
    
    eq_style = ParagraphStyle(
        'DocEquation',
        parent=base_styles['Normal'],
        fontName='Times-Italic',
        fontSize=8.3,
        leading=10.8,
        alignment=1,
        spaceBefore=2.5,
        spaceAfter=2.5,
        textColor=colors.HexColor("#0F172A")
    )
    
    caption_style = ParagraphStyle(
        'DocCaption',
        parent=base_styles['Normal'],
        fontName='Times-Roman',
        fontSize=7.3,
        leading=9.2,
        alignment=1,
        spaceBefore=2,
        spaceAfter=4,
        textColor=colors.HexColor("#334155")
    )
    
    ref_style = ParagraphStyle(
        'DocRef',
        parent=base_styles['Normal'],
        fontName='Times-Roman',
        fontSize=7.2,
        leading=9,
        alignment=4,
        leftIndent=11,
        firstLineIndent=-11,
        spaceBefore=1.2,
        spaceAfter=1.2,
        textColor=colors.HexColor("#0F172A")
    )
    
    story = []
    
    # ---------------- TITLE BLOCK ----------------
    story.append(Paragraph("A Practical Study of Data Locality Optimization Techniques in Hadoop MapReduce", title_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>Vikram Singh</b> (RA2411028030010) &nbsp;&nbsp;&nbsp;&nbsp; <b>Amit Vikram Singh</b> (RA2411028030016)", author_style))
    story.append(Spacer(1, 2))
    story.append(Paragraph("Department of Computer Science & Engineering, Faculty of Engineering & Technology<br/>"
                           "SRM Institute of Science & Technology, Delhi NCR Campus, Modinagar, India<br/>"
                           "<i>Big Data Essentials (21CSC314P) Project Report & Research Study</i>", affil_style))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#94A3B8"), spaceBefore=2, spaceAfter=4))
    story.append(FrameBreak())
    
    # ---------------- PAGE 1: LEFT COLUMN ----------------
    story.append(NextPageTemplate('LaterPages'))
    
    abstract_text = (
        "<b><i>Abstract</i>—Hadoop MapReduce partitions analytical jobs into independent splits executed by parallel map tasks, "
        "while HDFS replicates blocks across heterogeneous physical machines and racks. A cluster scheduler that places a map task on "
        "a worker already holding its input block avoids network transfer; a scheduler that ignores data distribution incurs severe "
        "inter-rack bandwidth overhead. This paper presents an extensive empirical investigation into data locality optimization in "
        "MapReduce. We design and implement a discrete-event simulator in C++20 modeling HDFS rack-aware replica placement, finite worker slots, "
        "a three-tier locality hierarchy (node-local, rack-local, off-rack), and two distinct network models: independent per-transfer "
        "bandwidth and shared core-link processor sharing. Across 78 experimental configurations with 50 paired random seeds (11,700 total runs), "
        "we evaluate three scheduling policies: Locality-Blind round-robin, Greedy Locality-Aware, and Delay Scheduling. "
        "In our primary 16-worker, 4-rack cluster, greedy locality-aware scheduling reduces remote input traffic by 20.7% ± 1.5% and cross-rack "
        "traffic by 24.2% ± 3.4%, but improves makespan by only 5.7% ± 1.1%. Delay scheduling (<i>D</i> = 2 s) reduces remote traffic by "
        "72.8% ± 2.3% and cross-rack traffic by 91.3% ± 3.4%, achieving a 25.6% ± 1.4% makespan improvement. We reveal a critical "
        "architectural decoupling: as network bandwidth expands from 5 to 200 MiB/s, completion-time advantages contract from 15.8% to 0.4% "
        "despite constant byte reductions. Under shared bottlenecks, blind scheduling triggers severe congestion collapse (makespan 336.9 s "
        "vs. 47.0 s for delay scheduling). Finally, we demonstrate the 'cost of waiting', where delay scheduling inflates makespan by up to 4.5% "
        "when remote transfers are inexpensive.</b>"
    )
    story.append(Paragraph(abstract_text, abstract_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b><i>Index Terms</i>—Hadoop, MapReduce, Data Locality, HDFS, Delay Scheduling, Discrete-Event Simulation, Network Contention, Big Data Systems.</b>", abstract_style))
    story.append(Spacer(1, 5))
    
    story.append(Paragraph("I. INTRODUCTION", sec_style))
    story.append(Paragraph(
        "Modern big data processing frameworks, such as Apache Hadoop MapReduce [1] and Apache Spark, process petabyte-scale datasets "
        "by decomposing massive analytical jobs into parallel map tasks. In enterprise architectures, the input dataset resides in the Hadoop "
        "Distributed File System (HDFS) [2], which breaks files into uniform blocks (typically 64 MiB or 128 MiB) and replicates them across "
        "cluster storage nodes. By enforcing rack awareness [3], HDFS distributes replicas across distinct physical racks to guard against "
        "localized rack failures. Because compute nodes (TaskTrackers/NodeManagers) and storage nodes (DataNodes) are co-located on commodity "
        "hardware, a job scheduler can initiate a task directly on a server hosting the target data, bypassing the cluster network entirely [4].", body_style))
    
    story.append(Paragraph(
        "Network fabrics in commodity data centers exhibit significant tiered oversubscription: intra-rack bisection bandwidth is broad "
        "and affordable, whereas inter-rack core backbones are expensive and prone to transient congestion [5]. Consequently, execution locality "
        "governs three distinct physical paths: <b>node-local</b> (zero network I/O), <b>rack-local</b> (traversing Top-of-Rack switches), and "
        "<b>off-rack</b> (traversing the congested core backbone). While textbook descriptions treat locality as an unqualified virtue, production "
        "clusters face a persistent trade-off: when a task is ready to launch, its local nodes may have all computation slots fully occupied. "
        "The scheduler must choose whether to launch the task remotely without delay or hold the task in queue until a local slot frees.", body_style))
    
    story.append(Paragraph(
        "This research paper provides an extensive experimental investigation into the quantitative limits of data locality optimization. "
        "We structure our study around four research questions: "
        "<br/>• <b>RQ1:</b> How much remote and cross-rack traffic is eliminated by locality awareness under standard HDFS replica topologies? "
        "<br/>• <b>RQ2:</b> Does eliminating network bytes translate directly into proportional job completion time (makespan) speedups? "
        "<br/>• <b>RQ3:</b> How do physical network bandwidths, split sizes, and cluster load scale the utility of locality awareness? "
        "<br/>• <b>RQ4:</b> Under what operational regimes does waiting for local worker slots degrade rather than enhance overall cluster makespan?", body_style))

    story.append(Paragraph(
        "To evaluate these questions rigorously, we formulate four pre-registered hypotheses: "
        "<br/>• <b>H1:</b> Locality-aware scheduling significantly curtails remote data volume when data is not replicated everywhere. "
        "<br/>• <b>H2:</b> The completion-time advantage of locality awareness contracts as network bandwidth approaches local memory/disk throughput. "
        "<br/>• <b>H3:</b> Delay scheduling increases node-local execution at the expense of higher task queueing wait times. "
        "<br/>• <b>H4:</b> Waiting for local slots incurs a net makespan penalty under light load or high-speed network fabrics.", body_style))
    
    story.append(Paragraph(
        "<b>Contributions:</b> (i) We design and implement a high-fidelity discrete-event simulator in C++20 incorporating HDFS replica placement, "
        "slot constraints, and Generalized Processor Sharing (GPS) flow contention. (ii) We evaluate 78 experimental configurations across 50 paired "
        "random seeds (11,700 total cluster simulations), isolating policy effects with paired Student's <i>t</i>-distributions. "
        "(iii) We discover the <i>completion-time decoupling effect</i>, demonstrating that byte savings stay constant while time savings vanish as networks speed up. "
        "(iv) We provide an interactive open-source Streamlit dashboard for real-time Gantt timeline execution and research verification.", body_style))

    story.append(Paragraph("II. BACKGROUND AND SYSTEM MODEL", sec_style))
    story.append(Paragraph(
        "<b>A. Cluster and Storage Topology</b><br/>"
        "We model a cluster comprising <i>W</i> homogeneous worker nodes grouped into <i>R</i> physical racks. Each worker node <i>w</i> is mapped to rack "
        "<i>w</i> mod <i>R</i>. Each worker provides <i>m</i> computation slots, supporting a cluster concurrency of <i>W · m</i> map tasks. "
        "HDFS block placement enforces the standard Apache rack-aware heuristic: for each block <i>b</i> with replication factor <i>k</i>, the primary "
        "replica is placed on a randomly chosen worker <i>w</i><sub>1</sub>; the secondary replica is placed on a worker <i>w</i><sub>2</sub> in a separate rack; "
        "and the tertiary replica is placed on a worker <i>w</i><sub>3</sub> within the second replica's rack (<i>w</i><sub>3</sub> ≠ <i>w</i><sub>2</sub>).", body_noindent))

    story.append(Paragraph(
        "<b>B. Workload Demands and Execution Model</b><br/>"
        "Workloads consist of <i>J</i> batch jobs released at virtual times <i>r<sub>j</sub></i>. Each job comprises <i>n</i> independent map tasks. "
        "Task <i>i</i> processes an input split of size <i>S<sub>i</sub></i> MiB and demands compute time <i>C<sub>i</sub></i> drawn uniformly from "
        "<i>C̄</i>(1 ± 0.5), with base compute demand <i>C̄</i> = 5.0 s. Execution serializes input reading and CPU processing: "
        "<i>T<sub>i</sub> = T</i><sub>read,<i>i</i></sub> + <i>C<sub>i</sub></i>.", body_noindent))
    
    story.append(Paragraph(
        "Input read latency is governed by effective bandwidth <i>D</i><sub>ℓ</sub> across locality levels ℓ:", body_style))
    story.append(Paragraph("<i>T</i><sub>read,<i>i</i></sub> = <i>S<sub>i</sub></i> / <i>D</i><sub>ℓ</sub>, &nbsp;&nbsp; <i>D</i><sub>ℓ</sub> ∈ {<i>D</i><sub>local</sub>, <i>D</i><sub>rack</sub>, <i>D</i><sub>cross</sub>}", eq_style))
    story.append(Paragraph(
        "Default baseline parameters are <i>D</i><sub>local</sub> = 200 MiB/s (local disk/page cache), <i>D</i><sub>rack</sub> = 100 MiB/s (intra-rack switch), "
        "and <i>D</i><sub>cross</sub> = 25 MiB/s (cross-rack backbone). For a standard 128 MiB block, read times are 0.64 s (node-local), 1.28 s (rack-local), "
        "and 5.12 s (off-rack). These values intentionally calibrate off-rack transfer cost to match compute duration (5.12 s read vs 5.0 s compute).", body_style))

    story.append(Paragraph(
        "<b>C. Network Models: Simple vs. Contention</b><br/>"
        "In the <i>simple</i> network model, every remote read proceeds at rate <i>D</i><sub>ℓ</sub> independently without mutual interference. "
        "In the <i>shared-link</i> contention model, concurrent remote reads compete over physical links governed by Generalized Processor Sharing (GPS). "
        "Off-rack reads share a core backbone switch of capacity <i>B</i><sub>core</sub>, while rack-local reads share an intra-rack switch of capacity "
        "<i>B</i><sub>rack</sub>. When <i>n<sub>c</sub></i> flows actively traverse link <i>L</i>, each flow progresses at instantaneous rate:", body_noindent))
    story.append(Paragraph("<i>r<sub>f</sub></i>(<i>t</i>) = min(<i>c<sub>f</sub></i>, &nbsp; <i>B<sub>L</sub></i> / <i>n<sub>L</sub></i>(<i>t</i>))", eq_style))
    story.append(Paragraph(
        "where <i>c<sub>f</sub></i> is the per-flow rate cap. Whenever a transfer begins or completes, rates for all in-flight flows are recalculated analytically.", body_style))

    story.append(Paragraph("III. SCHEDULING ALGORITHMS", sec_style))
    story.append(Paragraph(
        "All policies operate over a unified FIFO queue of pending tasks. When a slot becomes available on any worker, ready tasks are offered to the scheduler:", body_style))
    story.append(Paragraph(
        "<b>1) Policy A: Locality-Blind Baseline.</b> Assigns the offered task to the next available free worker in round-robin sequence, never inspecting block metadata.", bullet_style))
    story.append(Paragraph(
        "<b>2) Policy B: Greedy Locality-Aware.</b> Inspects free workers and assigns the task to the worker offering highest locality: node-local > rack-local > off-rack. "
        "Ties are broken by lowest worker index. Crucially, it never waits: if no local slot is idle, it falls back immediately to off-rack execution.", bullet_style))
    story.append(Paragraph(
        "<b>3) Policy C: Delay Scheduling (Zaharia et al. [6]).</b> When a task cannot find a node-local slot on free workers, it is temporarily declined and sets a timer. "
        "The task waits up to <i>D</i> seconds for a node-local worker. If still unassigned after <i>D</i> s, it is permitted to accept rack-local workers. "
        "After 2<i>D</i> s, it falls back to off-rack assignment. Declined tasks do not head-of-line block subsequent tasks in the FIFO queue. Setting <i>D</i> = 0 reduces "
        "identically to Policy B.", bullet_style))

    # Pseudocode Box
    algo_text = [
        ["Algorithm 1: Delay Scheduling Logic with Per-Task Timer"],
        ["<b>Input:</b> Ready task <i>t</i>, cluster free slot vector <i>F</i>, current virtual time <i>now</i><br/>"
         "<b>Output:</b> Assigned worker index <i>w</i> ∈ [0, <i>W</i>−1], or −1 (declined)<br/>"
         "1: <b>if</b> <i>since</i>[<i>t</i>.id] < 0 <b>then</b> <i>since</i>[<i>t</i>.id] ← <i>now</i><br/>"
         "2: <i>waited</i> ← <i>now</i> − <i>since</i>[<i>t</i>.id]<br/>"
         "3: <i>node</i> ← −1, <i>rack</i> ← −1, <i>off</i> ← −1<br/>"
         "4: <b>for</b> worker <i>w</i> = 0 <b>to</b> <i>W</i>−1 <b>do</b><br/>"
         "5: &nbsp;&nbsp;&nbsp;&nbsp;<b>if</b> <i>F</i>[<i>w</i>] > 0 <b>then</b><br/>"
         "6: &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>loc</i> ← classify(<i>w</i>, <i>t</i>.block)<br/>"
         "7: &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>if</b> <i>loc</i> = NodeLocal <b>and</b> <i>node</i> < 0 <b>then</b> <i>node</i> ← <i>w</i>; <b>break</b><br/>"
         "8: &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>else if</b> <i>loc</i> = RackLocal <b>and</b> <i>rack</i> < 0 <b>then</b> <i>rack</i> ← <i>w</i><br/>"
         "9: &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>else if</b> <i>loc</i> = OffRack <b>and</b> <i>off</i> < 0 <b>then</b> <i>off</i> ← <i>w</i><br/>"
         "10: <b>if</b> <i>node</i> ≥ 0 <b>then return</b> <i>node</i><br/>"
         "11: <b>if</b> <i>waited</i> ≥ <i>D</i> <b>and</b> <i>rack</i> ≥ 0 <b>then return</b> <i>rack</i><br/>"
         "12: <b>if</b> <i>waited</i> ≥ 2<i>D</i> <b>and</b> <i>off</i> ≥ 0 <b>then return</b> <i>off</i><br/>"
         "13: <b>return</b> −1  // Task declines and sets wakeup event at <i>since</i>[<i>t</i>]+<i>D</i>"]
    ]
    t_algo = Table(algo_text, colWidths=[col_width])
    t_algo.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F1F5F9")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor("#0F172A")),
        ('FONTNAME', (0,0), (-1,0), 'Times-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 6.8),
        ('LEADING', (0,0), (-1,-1), 8.5),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#64748B")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(Spacer(1, 4))
    story.append(t_algo)
    story.append(Spacer(1, 4))

    # Add Figure 1 if available
    fig1_path = "figures/fig1_completion_time.png"
    if os.path.exists(fig1_path):
        story.append(Image(fig1_path, width=col_width, height=col_width*0.35))
        story.append(Paragraph("Fig. 1. Completion time metrics (Makespan, Turnaround, Wait) in main cluster (95% CI over 50 paired seeds).", caption_style))

    story.append(Paragraph("IV. SIMULATION METHODOLOGY & MATRIX", sec_style))
    story.append(Paragraph(
        "<b>A. Discrete-Event Simulation Engine</b><br/>"
        "The simulation engine maintains a global virtual clock and a min-priority queue of timestamped events: <code>JobArrival</code>, <code>ReadDone</code>, "
        "<code>TaskFinish</code>, and <code>Wakeup</code>. Monotonically increasing sequence counters ensure deterministic tie-breaking. "
        "Virtual time leaps forward to the timestamp of the next event, enabling rapid evaluation of full multi-job clusters without sleeping.", body_noindent))
    
    story.append(Paragraph(
        "<b>B. Paired-Seed Experimental Methodology</b><br/>"
        "To eliminate random workload variance, we employ strict <b>paired-seed experimental design</b>. For each setting, 50 random seeds (1 to 50) "
        "are executed. For a given seed, all three scheduling policies receive the exact same workload instance: identical task compute demands, identical "
        "HDFS block replica locations, and identical job release times. For any metric <i>M</i>, we compute the paired difference: "
        "Δ<sub><i>s</i></sub> = <i>M</i><sub>base,<i>s</i></sub> − <i>M</i><sub>alt,<i>s</i></sub>. "
        "We report mean difference Δ̄, 95% confidence intervals from the Student's <i>t</i>-distribution with 49 degrees of freedom, and improvement percentage "
        "<i>I</i> = 100 · Δ̄ / <i>M̄</i><sub>base</sub>.", body_style))

    # Add Figure 2 if available
    fig2_path = "figures/fig2_network_traffic.png"
    if os.path.exists(fig2_path):
        story.append(Spacer(1, 4))
        story.append(Image(fig2_path, width=col_width, height=col_width*0.42))
        story.append(Paragraph("Fig. 2. Remote input traffic and cross-rack traffic in the main cluster.", caption_style))

    story.append(Paragraph(
        "<b>C. Experimental Matrix Overview</b><br/>"
        "The primary cluster configuration comprises 16 workers, 4 racks, 2 slots/worker (32 slots), 3 replicas, 128 MiB blocks, and 128 tasks across 4 jobs. "
        "Around this baseline, we construct six systematic benchmark suites (Table I):", body_noindent))
    
    # Table of experimental settings
    table_data = [
        ["Exp", "Varied Parameter", "Values Evaluated"],
        ["E1", "Baseline Configuration", "Small (8w, 2r), Main (16w, 4r)"],
        ["E2", "Cross-Rack BW / Split Size", "5 to 200 MiB/s; 64 to 256 MiB"],
        ["E3", "Load (Tasks/Slots) / Arrival", "1×, 2×, 4×, 8×; gap 0 to 80 s"],
        ["E4", "Replicas / Topology / Workers", "k=1..4; 1..8 racks; 4..32 workers"],
        ["E5", "Delay Threshold D (s)", "D = 0, 0.5, 1, 2, 4, 8, 16 s"],
        ["E6", "Shared Core Link Cap (MiB/s)", "25, 50, 100, 200, 400 MiB/s"]
    ]
    t_matrix = Table(table_data, colWidths=[24, 115, 124])
    t_matrix.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E293B")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Times-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 7),
        ('LEADING', (0,0), (-1,-1), 8.5),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(Spacer(1, 4))
    story.append(t_matrix)
    story.append(Paragraph("TABLE I: EXPERIMENTAL FACTOR MATRIX (78 SETTINGS × 50 SEEDS = 11,700 RUNS)", caption_style))
    story.append(Spacer(1, 4))

    # Add Figure 4 if available
    fig4_path = "figures/fig4_locality_distribution.png"
    if os.path.exists(fig4_path):
        story.append(Image(fig4_path, width=col_width, height=col_width*0.42))
        story.append(Paragraph("Fig. 3. Task locality distribution breakdown across policies in main and small clusters.", caption_style))

    story.append(Paragraph("V. EXPERIMENTAL EVALUATION AND ANALYSIS", sec_style))
    story.append(Paragraph(
        "<b>A. Baseline Cluster Performance (E1)</b><br/>"
        "In our main evaluation cluster (16 workers, 4 racks, 32 slots, 128 tasks), the Locality-Blind scheduler distributes tasks uniformly across free workers, "
        "achieving only 18.5% node-local execution and sending 50.9% of all tasks across the cross-rack core link. This incurs 13,356 MiB of remote traffic "
        "and 8,348 MiB of cross-rack traffic, yielding an average makespan of 38.85 s (Table II).", body_noindent))

    story.append(Paragraph(
        "Greedy Locality-Aware scheduling elevates node-local execution to 35.4% and suppresses off-rack tasks to 38.6%. "
        "Consequently, remote traffic falls by 20.7% ± 1.5% and cross-rack traffic decreases by 24.2% ± 3.4%. Both reductions hold across 100% and 98% of paired seeds. "
        "However, because greedy scheduling falls back immediately whenever local slots are occupied, its makespan improves by only <b>5.7% ± 1.1%</b> (Table III).", body_style))

    story.append(Paragraph(
        "Delay Scheduling (<i>D</i> = 2 s) achieves profound performance gains. By permitting ready tasks to wait up to 2 seconds for a local slot to free, "
        "it achieves <b>77.8% node-local execution</b> and suppresses off-rack tasks to just <b>4.5%</b> (Fig. 3). Remote traffic drops by <b>72.8% ± 2.3%</b>, "
        "cross-rack traffic collapses by <b>91.3% ± 3.4%</b>, and makespan drops by <b>25.6% ± 1.4%</b> (from 38.85 s down to 28.90 s). "
        "Mean job turnaround time drops by 23.3% ± 1.1% (from 26.05 s to 19.97 s). In 100% of paired seeds, Delay Scheduling beats both Blind and Greedy policies. "
        "<b>Hypothesis H1 is strongly confirmed.</b>", body_style))

    # Table II: Baseline metrics
    t_base_data = [
        ["Metric", "Blind", "Aware", "Delay (D=2)"],
        ["Makespan (s)", "38.9 ± 0.4", "36.6 ± 0.4", "28.9 ± 0.5"],
        ["Mean Turnaround (s)", "26.1 ± 0.2", "23.6 ± 0.2", "20.0 ± 0.3"],
        ["Mean Task Wait (s)", "11.89 ± 0.12", "10.25 ± 0.10", "8.72 ± 0.10"],
        ["Mean Remote Read (s)", "3.68 ± 0.05", "3.58 ± 0.06", "1.97 ± 0.13"],
        ["Remote Input (MiB)", "13356 ± 142", "10586 ± 179", "3630 ± 266"],
        ["Cross-Rack (MiB)", "8348 ± 218", "6328 ± 181", "727 ± 179"],
        ["Node-Local Tasks", "23.7 ± 1.1", "45.3 ± 1.4", "99.6 ± 2.1"],
        ["Rack-Local Tasks", "39.1 ± 1.4", "33.3 ± 1.4", "22.7 ± 1.4"],
        ["Off-Rack Tasks", "65.2 ± 1.7", "49.4 ± 1.4", "5.7 ± 1.4"],
        ["Slot Utilization", "0.835 ± 0.006", "0.822 ± 0.007", "0.823 ± 0.009"]
    ]
    t_base = Table(t_base_data, colWidths=[75, 62, 62, 64])
    t_base.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E293B")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Times-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 6.5),
        ('LEADING', (0,0), (-1,-1), 8),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 1.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.5),
    ]))
    story.append(Spacer(1, 4))
    story.append(t_base)
    story.append(Paragraph("TABLE II: MAIN CLUSTER BASELINE EVALUATION (50 PAIRED SEEDS)", caption_style))

    # Table III: Paired differences
    t_diff_data = [
        ["Comparison", "Metric", "Mean Diff ± CI", "Imprv %", "Seeds"],
        ["aware vs blind", "makespan_s", "2.22 ± 0.44", "5.7% ± 1.1", "94%"],
        ["aware vs blind", "remote_mib", "2769.9 ± 199.9", "20.7% ± 1.5", "100%"],
        ["aware vs blind", "cross_mib", "2019.8 ± 282.7", "24.2% ± 3.4", "98%"],
        ["delay vs blind", "makespan_s", "9.95 ± 0.54", "25.6% ± 1.4", "100%"],
        ["delay vs blind", "remote_mib", "9725.4 ± 306.7", "72.8% ± 2.3", "100%"],
        ["delay vs blind", "cross_mib", "7621.1 ± 281.8", "91.3% ± 3.4", "100%"],
        ["delay vs aware", "makespan_s", "7.73 ± 0.52", "21.1% ± 1.4", "100%"],
        ["delay vs aware", "remote_mib", "6955.5 ± 350.1", "65.7% ± 3.3", "100%"],
        ["delay vs aware", "cross_mib", "5601.3 ± 285.0", "88.5% ± 4.5", "100%"]
    ]
    t_diff = Table(t_diff_data, colWidths=[65, 55, 62, 53, 28])
    t_diff.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E293B")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Times-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 6.5),
        ('LEADING', (0,0), (-1,-1), 8),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 1.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.5),
    ]))
    story.append(Spacer(1, 4))
    story.append(t_diff)
    story.append(Paragraph("TABLE III: PAIRED DIFFERENCES (MAIN CLUSTER, 50 SEEDS)", caption_style))

    story.append(Paragraph(
        "<b>B. Network Bandwidth Sensitivity & The Decoupling Law (E2)</b><br/>"
        "We vary the per-flow cross-rack bandwidth <i>D</i><sub>cross</sub> logarithmically across 5, 10, 25, 50, 100, and 200 MiB/s. "
        "This experiment exposes a critical insight: <i>data volume and execution time decouple</i>. "
        "As plotted in Fig. 4, the volume of data transferred over cross-rack links is entirely determined by scheduling decisions and is "
        "strictly invariant to network bandwidth: Greedy scheduling saves exactly 2,770 MiB, and Delay scheduling saves exactly 9,725 MiB across every bandwidth.", body_noindent))

    story.append(Paragraph(
        "However, the makespan improvement scales inversely with bandwidth. When the network is heavily constrained (5 MiB/s), greedy locality-aware scheduling "
        "yields a 15.8% makespan improvement. As bandwidth expands to 25 MiB/s, the gain contracts to 5.7%. At 200 MiB/s (modern 10/25GbE data centers), "
        "the makespan improvement vanishes to <b>0.4% ± 0.5%</b>. Thus, in high-bandwidth cloud environments, locality optimization must be justified "
        "primarily by core switch power and cost reduction, rather than individual job speedups. <b>Hypothesis H2 is supported.</b>", body_style))

    # Add Figure 3 if available
    fig3_path = "figures/fig3_bandwidth_sensitivity.png"
    if os.path.exists(fig3_path):
        story.append(Spacer(1, 4))
        story.append(Image(fig3_path, width=col_width, height=col_width*0.35))
        story.append(Paragraph("Fig. 4. Sensitivity of makespan, remote traffic, and improvement to cross-rack bandwidth.", caption_style))

    # Table IV: Bandwidth Sensitivity detailed table
    t_bw_data = [
        ["BW (MiB/s)", "Blind (s)", "Aware (s)", "Delay (s)", "Delay Imprv %"],
        ["5", "96.4 ± 1.1", "81.2 ± 0.9", "31.8 ± 0.5", "67.0% ± 0.6"],
        ["10", "59.2 ± 0.6", "52.4 ± 0.5", "29.9 ± 0.5", "49.5% ± 0.9"],
        ["25", "38.9 ± 0.4", "36.6 ± 0.4", "28.9 ± 0.5", "25.6% ± 1.4"],
        ["50", "31.7 ± 0.3", "30.9 ± 0.3", "28.5 ± 0.4", "10.1% ± 1.5"],
        ["100", "28.1 ± 0.3", "27.9 ± 0.3", "28.3 ± 0.4", "−0.7% ± 1.5"],
        ["200", "26.3 ± 0.3", "26.2 ± 0.3", "28.2 ± 0.4", "−7.2% ± 1.6"]
    ]
    t_bw = Table(t_bw_data, colWidths=[42, 54, 54, 54, 59])
    t_bw.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E293B")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Times-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 6.5),
        ('LEADING', (0,0), (-1,-1), 8),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 1.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.5),
    ]))
    story.append(Spacer(1, 4))
    story.append(t_bw)
    story.append(Paragraph("TABLE IV: MAKESPAN SENSITIVITY ACROSS CROSS-RACK BANDWIDTHS (E2)", caption_style))

    story.append(Paragraph(
        "<b>C. Shared Link Contention & Congestion Collapse (E6)</b><br/>"
        "In simple network models, remote transfers experience no mutual contention. In real data center networks, concurrent off-rack reads compete "
        "for shared core switch capacity. We model this via processor sharing with core capacities ranging from 25 to 400 MiB/s (Fig. 5).", body_noindent))

    story.append(Paragraph(
        "When link capacity is constrained to 25 MiB/s, the Locality-Blind scheduler triggers catastrophic <b>congestion collapse</b>: "
        "dozens of concurrent remote flows divide the core capacity into fractions of a MiB/s, causing makespan to explode to <b>336.9 s</b>. "
        "Under the identical workload and network, Delay Scheduling confines cross-rack transfers to 4.5% of tasks, bypassing the core link entirely and maintaining "
        "a makespan of <b>47.0 s</b>—an 86.1% improvement. Even at 100 MiB/s core capacity, delay scheduling preserves a 34.2% completion-time lead.", body_style))

    # Add Figure 9 if available
    fig9_path = "figures/fig9_contention.png"
    if os.path.exists(fig9_path):
        story.append(Spacer(1, 4))
        story.append(Image(fig9_path, width=col_width, height=col_width*0.35))
        story.append(Paragraph("Fig. 5. Makespan under shared core link capacity constraints showing congestion collapse.", caption_style))

    story.append(Paragraph(
        "<b>D. The Cost of Waiting in Delay Scheduling (E5)</b><br/>"
        "Delay scheduling operates on the premise that waiting for a local slot is faster than transferring data over the network. "
        "We test whether this assumption holds across delay thresholds <i>D</i> ∈ [0, 16] s under two adversarial regimes: "
        "(1) high-bandwidth networks (<i>D</i><sub>cross</sub> = 200 MiB/s), and (2) light cluster load (tasks/slots = 1.0).", body_noindent))

    story.append(Paragraph(
        "As predicted by Hypothesis <b>H4</b>, under a fast network fabric, a 128 MiB split reads off-rack in only 0.64 s. Setting <i>D</i> = 2 s "
        "forces tasks to wait up to 4 s before falling back, creating unnecessary idle time on worker slots. Consequently, delay scheduling "
        "<b>increases makespan by 4.5%</b> relative to the greedy policy. Similarly, under light load where idle slots exist across the cluster, "
        "waiting leaves slots starved of work. Thus, delay scheduling requires dynamic tuning: <i>D</i> must be bounded strictly below the "
        "expected remote read penalty.", body_style))

    # Add Figure 8 if available
    fig8_path = "figures/fig8_delay_threshold.png"
    if os.path.exists(fig8_path):
        story.append(Spacer(1, 4))
        story.append(Image(fig8_path, width=col_width, height=col_width*0.95))
        story.append(Paragraph("Fig. 6. Multi-panel delay threshold sensitivity across four distinct operational regimes (E5).", caption_style))

    # Add Figure 5 if available
    fig5_path = "figures/fig5_tradeoff.png"
    if os.path.exists(fig5_path):
        story.append(Spacer(1, 4))
        story.append(Image(fig5_path, width=col_width, height=col_width*0.75))
        story.append(Paragraph("Fig. 7. Traffic reduction vs makespan improvement across all 78 experimental configurations.", caption_style))

    # Add Figure 6 if available
    fig6_path = "figures/fig6_load.png"
    if os.path.exists(fig6_path):
        story.append(Spacer(1, 4))
        story.append(Image(fig6_path, width=col_width, height=col_width*0.35))
        story.append(Paragraph("Fig. 8. Scaling of makespan and traffic reduction across cluster load ratios (1x to 8x slot capacity).", caption_style))

    # Add Figure 7 if available
    fig7_path = "figures/fig7_replication_racks.png"
    if os.path.exists(fig7_path):
        story.append(Spacer(1, 4))
        story.append(Image(fig7_path, width=col_width, height=col_width*0.35))
        story.append(Paragraph("Fig. 9. Heatmap of percentage improvement across replication factor (1-3) and rack topology (1-8).", caption_style))

    story.append(Paragraph(
        "<b>E. Replication and Grid Topology Scaling (E4)</b><br/>"
        "Evaluating replication factors from <i>k</i> = 1 to 4 confirms that three replicas represent an optimal sweet spot. Increasing <i>k</i> "
        "from 1 to 3 increases greedy node-locality from 12.5% to 35.4%. Moving from 3 to 4 replicas yields diminishing returns (< 5% locality gain), "
        "validating Hadoop's default configuration of 3 replicas (Fig. 9).", body_noindent))

    # Add Figure 10 if available
    fig10_path = "figures/fig10_block_workers_gap.png"
    if os.path.exists(fig10_path):
        story.append(Spacer(1, 4))
        story.append(Image(fig10_path, width=col_width, height=col_width*0.35))
        story.append(Paragraph("Fig. 10. Makespan improvement across split sizes, worker scaling (4-32), and arrival gaps (0-80s).", caption_style))

    story.append(Paragraph(
        "<b>F. Block Size, Scale, and Job Arrival Spacing (E2, E3, E4)</b><br/>"
        "Evaluating block sizes from 64 to 256 MiB shows that larger blocks increase the absolute time penalty of off-rack reads, thereby amplifying the "
        "relative advantage of locality awareness (Fig. 10). Scaling cluster size from 4 to 32 workers shows that larger clusters decrease random locality under "
        "the Blind policy, making locality-aware schedulers even more essential. Staggering job arrivals (gap 0 to 80 s) reduces peak slot contention, "
        "allowing greedy scheduling to achieve higher natural locality without waiting.", body_style))

    story.append(Paragraph("VI. RELATED WORK", sec_style))
    story.append(Paragraph(
        "The challenge of shared resource contention and performance isolation has been widely explored in computer systems. "
        "In CPU scheduling, Constant Bandwidth Servers (CBS) [7] and resource reservation algorithms [8] enforce temporal isolation. "
        "In multi-core architectures, MemGuard [9] provides hardware PMC-regulated memory bandwidth reservation and dynamic budget reclaiming across cores sharing DRAM controllers. "
        "Our work addresses similar resource contention, but focuses on the network tier of distributed Big Data processing clusters.", body_style))

    story.append(Paragraph(
        "In distributed big data scheduling, Zaharia et al. [6] introduced delay scheduling in the Hadoop Fair Scheduler, demonstrating that "
        "a few seconds of delay achieved nearly 100% data locality. Isard et al. [10] developed Quincy, mapping task scheduling with data locality to a "
        "min-cost max-flow graph optimization problem. Wang and Ying [11] investigated data locality from a queueing network perspective, analyzing throughput-optimal "
        "policies under heavy traffic limits. In production frameworks, YARN [12] and modern resource managers [13] implement multi-level queue locality mechanisms. "
        "Our work complements these foundational papers by presenting a fully transparent, open-source discrete-event simulation matrix that quantitatively decouples "
        "data volume mitigation from job completion time benefits across both simple and congested network models.", body_style))

    story.append(Paragraph("VII. CONCLUSION AND FUTURE WORK", sec_style))
    story.append(Paragraph(
        "This paper presented a comprehensive empirical study of data locality optimization in Hadoop MapReduce using a rigorous discrete-event simulator. "
        "Across 11,700 simulation runs spanning 78 configurations and 50 paired seeds, we demonstrated that while greedy locality-aware scheduling yields modest completion-time "
        "speedups (5.7%), delay scheduling delivers dramatic improvements (25.6% makespan, 72.8% remote traffic, and 91.3% cross-rack traffic reduction). "
        "Crucially, our experiments established the <i>completion-time decoupling effect</i>, proved the risk of shared-link congestion collapse, and identified "
        "operational regimes where waiting for locality causes an adverse 4.5% makespan penalty.", body_style))

    story.append(Paragraph(
        "Future research directions include extending the simulator to model reduce-side shuffle traffic, supporting heterogeneous worker compute profiles, "
        "and implementing reinforcement-learning-driven adaptive delay thresholds (<i>D</i>) that dynamically adjust to real-time network telemetry.", body_style))

    story.append(Paragraph("ACKNOWLEDGMENT", sec_style))
    story.append(Paragraph(
        "The authors express sincere gratitude to Mr. Tapas Kumar Mishra (Assistant Professor) and Dr. Neelam Singh (Head of the Department), "
        "Department of Computer Science & Engineering, SRM Institute of Science & Technology, Delhi NCR Campus, Modinagar, for their academic guidance, "
        "valuable feedback, and course support during the Big Data Essentials (21CSC314P) curriculum.", body_noindent))

    story.append(Paragraph("REFERENCES", sec_style))
    refs = [
        "[1] J. Dean and S. Ghemawat, 'MapReduce: Simplified data processing on large clusters,' <i>Communications of the ACM</i>, vol. 51, no. 1, pp. 107–113, 2008.",
        "[2] K. Shvachko, H. Kuang, S. Radia, and R. Chansler, 'The Hadoop Distributed File System,' in <i>Proc. IEEE MSST</i>, 2010, pp. 1–10.",
        "[3] Apache Software Foundation, 'HDFS Architecture Guide: Rack Awareness,' <i>Apache Hadoop Documentation</i>, 2024.",
        "[4] T. White, <i>Hadoop: The Definitive Guide</i>, 4th ed. O'Reilly Media, 2015.",
        "[5] A. Greenberg et al., 'VL2: A scalable and flexible data center network,' in <i>Proc. ACM SIGCOMM</i>, 2009, pp. 51–62.",
        "[6] M. Zaharia, D. Borthakur, J. Sen Sarma, K. Elmeleegy, S. Shenker, and I. Stoica, 'Delay scheduling: A simple technique for achieving locality and fairness in cluster scheduling,' in <i>Proc. ACM EuroSys</i>, 2010, pp. 265–278.",
        "[7] L. Abeni and G. Buttazzo, 'Integrating multimedia applications in hard real-time systems,' in <i>Proc. IEEE RTSS</i>, 1998, pp. 4–13.",
        "[8] M. Caccamo, G. Buttazzo, and L. Sha, 'Capacity sharing for overrun control,' in <i>Proc. IEEE RTSS</i>, 2000, pp. 295–304.",
        "[9] H. Yun, G. Yao, R. Pellizzoni, M. Caccamo, and L. Sha, 'MemGuard: Memory bandwidth reservation system for efficient performance isolation in multi-core platforms,' in <i>Proc. IEEE RTAS</i>, 2013, pp. 55–64.",
        "[10] M. Isard, V. Prabhakaran, J. Currey, U. Wieder, K. Talwar, and A. Goldberg, 'Quincy: Fair scheduling for distributed computing clusters,' in <i>Proc. ACM SOSP</i>, 2009, pp. 261–276.",
        "[11] W. Wang and L. Ying, 'On data locality in MapReduce: A network perspective,' <i>IEEE/ACM Transactions on Networking</i>, vol. 24, no. 3, pp. 1475–1487, 2016.",
        "[12] V. K. Vavilapalli et al., 'Apache Hadoop YARN: Yet Another Resource Negotiator,' in <i>Proc. ACM SoCC</i>, 2013, pp. 1–16.",
        "[13] F. Hedayati, F. Rahimian, and A. H. Payberah, 'A survey on resource scheduling in big data processing systems,' <i>ACM Computing Surveys</i>, vol. 55, no. 9, 2023.",
        "[14] B. Akesson, K. Goossens, and M. Ringhofer, 'Predator: A predictable SDRAM memory controller,' in <i>Proc. CODES+ISSS</i>, 2007, pp. 251–256.",
        "[15] J. Reineke, I. Liu, H. D. Patel, S. Kim, and E. A. Lee, 'PRET DRAM controller: Bank privatization for predictability,' in <i>Proc. CODES+ISSS</i>, 2011, pp. 125–130."
    ]
    for r in refs:
        story.append(Paragraph(r, ref_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated {pdf_filename}!")

if __name__ == '__main__':
    build_pdf()
