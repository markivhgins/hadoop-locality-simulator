import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sim_engine import (
    SimConfig, generate_workload, run_simulation,
    BlindScheduler, AwareScheduler, DelayScheduler, Locality
)

st.set_page_config(
    page_title="Hadoop MapReduce Data Locality Simulator",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished research-grade UI
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 14px;
        text-align: center;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 18px;
        font-weight: 600;
        border-radius: 6px;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- DATA LOADERS -----------------
@st.cache_data
def load_benchmark_data():
    all_runs_path = "all_runs.csv"
    summary_path = "summary.csv"
    df_runs = pd.read_csv(all_runs_path) if os.path.exists(all_runs_path) else None
    df_summary = pd.read_csv(summary_path) if os.path.exists(summary_path) else None
    return df_runs, df_summary

df_runs, df_summary = load_benchmark_data()

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/0/0e/Hadoop_logo.svg", width=160)
    st.markdown("### **Navigation**")
    page = st.radio(
        "Select Module:",
        [
            "🎮 Live Interactive Simulator",
            "📊 Benchmark Matrix (78 Settings)",
            "🔬 Hypothesis & Trade-off Analyzer",
            "📄 Research Paper & Downloads"
        ],
        index=0
    )
    
    st.markdown("---")
    st.markdown("#### **Research Overview**")
    st.markdown("""
    - **Engine:** C++20 / Python Discrete-Event
    - **Workloads:** Paired-seed MapReduce tasks
    - **Policies:**
      - `Blind`: Round-robin (no locality)
      - `Aware`: Greedy locality (Node > Rack > Off)
      - `Delay`: Zaharia et al. timer wait ($D$)
    """)
    st.info("💡 **Tip:** Changes in the live simulator use exact paired workloads to isolate policy effects.")

# =========================================================================
# PAGE 1: LIVE INTERACTIVE SIMULATOR
# =========================================================================
if page == "🎮 Live Interactive Simulator":
    st.markdown('<div class="main-title">🎮 Live Discrete-Event Simulator</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-title">Configure cluster topology, network bandwidths, and delay timers. '
        'Run <b>Blind</b>, <b>Aware</b>, and <b>Delay</b> policies concurrently on identical synthetic workloads.</div>',
        unsafe_allow_html=True
    )
    
    col_ctrl1, col_ctrl2, col_ctrl3, col_ctrl4 = st.columns(4)
    with col_ctrl1:
        st.markdown("##### 🖥️ Cluster Topology")
        workers = st.selectbox("Workers (W)", [4, 8, 16, 32], index=2)
        racks = st.selectbox("Racks (R)", [1, 2, 4, 8], index=2)
        slots = st.selectbox("Slots / Worker (m)", [1, 2, 4], index=1)
        replicas = st.slider("HDFS Replicas (k)", 1, min(workers, 4), 3)

    with col_ctrl2:
        st.markdown("##### 📦 Workload Demands")
        jobs = st.slider("Jobs (J)", 1, 8, 4)
        tasks_per_job = st.slider("Tasks / Job", 8, 64, 32, step=8)
        block_mib = st.selectbox("Split Size (MiB)", [64.0, 128.0, 256.0], index=1)
        compute_s = st.slider("Mean Compute Demand (s)", 1.0, 15.0, 5.0, step=0.5)

    with col_ctrl3:
        st.markdown("##### 🌐 Network Model")
        shared_net = st.checkbox("Shared Link (Contention)", value=False, help="Concurrent remote flows compete for core link bandwidth under processor sharing.")
        cross_bw = st.slider("Cross-Rack Bandwidth (MiB/s)", 5.0, 200.0, 25.0, step=5.0)
        core_cap = st.slider("Core Link Capacity (MiB/s)", 25.0, 400.0, 100.0, step=25.0, disabled=not shared_net)
        rack_bw = st.slider("Rack Bandwidth (MiB/s)", 20.0, 400.0, 100.0, step=20.0)

    with col_ctrl4:
        st.markdown("##### ⏱️ Schedulers & Seed")
        delay_s = st.slider("Delay Threshold D (s)", 0.0, 10.0, 2.0, step=0.5, help="Task waits up to D s for node-local, 2D s for rack-local.")
        seed = st.number_input("Random Seed", value=42, step=1)
        st.write("")
        run_btn = st.button("🚀 Run Live Simulation", type="primary", use_container_width=True)

    cfg = SimConfig(
        workers=workers,
        racks=racks,
        slots=slots,
        replicas=replicas,
        jobs=jobs,
        tasks_per_job=tasks_per_job,
        block_mib=block_mib,
        compute_s=compute_s,
        local_bw=200.0,
        rack_bw=rack_bw,
        cross_bw=cross_bw,
        delay_s=delay_s,
        shared_net=shared_net,
        core_cap=core_cap,
        rack_cap=rack_bw * 2,
        seed=seed
    )

    wl = generate_workload(cfg)
    
    # Run simulations
    m_blind = run_simulation(wl, BlindScheduler())
    m_aware = run_simulation(wl, AwareScheduler())
    m_delay = run_simulation(wl, DelayScheduler(delay_s))

    total_tasks = len(wl.tasks)
    
    st.markdown("---")
    st.subheader("📊 Comparative Performance Summary")

    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    
    makespan_imp = (m_blind.makespan - m_delay.makespan) / m_blind.makespan * 100
    remote_imp = (m_blind.remote_mib - m_delay.remote_mib) / m_blind.remote_mib * 100 if m_blind.remote_mib > 0 else 0
    cross_imp = (m_blind.cross_mib - m_delay.cross_mib) / m_blind.cross_mib * 100 if m_blind.cross_mib > 0 else 0

    with kpi1:
        st.metric(
            label="Makespan (Delay vs Blind)",
            value=f"{m_delay.makespan:.2f} s",
            delta=f"{makespan_imp:+.1f}% vs Blind",
            delta_color="normal"
        )
    with kpi2:
        st.metric(
            label="Remote Traffic Saved",
            value=f"{m_delay.remote_mib:.0f} MiB",
            delta=f"-{remote_imp:.1f}%",
            delta_color="inverse"
        )
    with kpi3:
        st.metric(
            label="Cross-Rack Traffic",
            value=f"{m_delay.cross_mib:.0f} MiB",
            delta=f"-{cross_imp:.1f}%",
            delta_color="inverse"
        )
    with kpi4:
        st.metric(
            label="Node-Local Tasks",
            value=f"{m_delay.node_local} / {total_tasks}",
            delta=f"{m_delay.node_local/total_tasks*100:.1f}% Locality"
        )
    with kpi5:
        st.metric(
            label="Slot Utilization",
            value=f"{m_delay.utilization*100:.1f}%",
            delta=f"Wait: {m_delay.mean_wait:.2f}s"
        )

    # Detailed metrics comparison table
    summary_table = pd.DataFrame([
        {
            "Policy": "Locality-Blind (Baseline)",
            "Makespan (s)": round(m_blind.makespan, 2),
            "Mean Turnaround (s)": round(m_blind.mean_turnaround, 2),
            "Mean Wait (s)": round(m_blind.mean_wait, 2),
            "Remote Traffic (MiB)": round(m_blind.remote_mib, 1),
            "Cross-Rack (MiB)": round(m_blind.cross_mib, 1),
            "Node-Local %": round(m_blind.node_local / total_tasks * 100, 1),
            "Rack-Local %": round(m_blind.rack_local / total_tasks * 100, 1),
            "Off-Rack %": round(m_blind.off_rack / total_tasks * 100, 1),
            "Slot Utilization %": round(m_blind.utilization * 100, 1)
        },
        {
            "Policy": "Greedy Locality-Aware",
            "Makespan (s)": round(m_aware.makespan, 2),
            "Mean Turnaround (s)": round(m_aware.mean_turnaround, 2),
            "Mean Wait (s)": round(m_aware.mean_wait, 2),
            "Remote Traffic (MiB)": round(m_aware.remote_mib, 1),
            "Cross-Rack (MiB)": round(m_aware.cross_mib, 1),
            "Node-Local %": round(m_aware.node_local / total_tasks * 100, 1),
            "Rack-Local %": round(m_aware.rack_local / total_tasks * 100, 1),
            "Off-Rack %": round(m_aware.off_rack / total_tasks * 100, 1),
            "Slot Utilization %": round(m_aware.utilization * 100, 1)
        },
        {
            "Policy": f"Delay Scheduling (D = {delay_s}s)",
            "Makespan (s)": round(m_delay.makespan, 2),
            "Mean Turnaround (s)": round(m_delay.mean_turnaround, 2),
            "Mean Wait (s)": round(m_delay.mean_wait, 2),
            "Remote Traffic (MiB)": round(m_delay.remote_mib, 1),
            "Cross-Rack (MiB)": round(m_delay.cross_mib, 1),
            "Node-Local %": round(m_delay.node_local / total_tasks * 100, 1),
            "Rack-Local %": round(m_delay.rack_local / total_tasks * 100, 1),
            "Off-Rack %": round(m_delay.off_rack / total_tasks * 100, 1),
            "Slot Utilization %": round(m_delay.utilization * 100, 1)
        }
    ])
    st.dataframe(summary_table, use_container_width=True)

    # Visualizations row
    ch_col1, ch_col2, ch_col3 = st.columns(3)
    
    with ch_col1:
        st.markdown("##### ⏱️ Makespan & Turnaround (s)")
        fig_time = go.Figure()
        fig_time.add_trace(go.Bar(
            name="Makespan",
            x=["Blind", "Aware", "Delay"],
            y=[m_blind.makespan, m_aware.makespan, m_delay.makespan],
            marker_color=["#94A3B8", "#3B82F6", "#F97316"]
        ))
        fig_time.add_trace(go.Bar(
            name="Mean Turnaround",
            x=["Blind", "Aware", "Delay"],
            y=[m_blind.mean_turnaround, m_aware.mean_turnaround, m_delay.mean_turnaround],
            marker_color=["#CBD5E1", "#93C5FD", "#FDBA74"]
        ))
        fig_time.update_layout(barmode="group", margin=dict(l=20, r=20, t=30, b=20), height=300)
        st.plotly_chart(fig_time, use_container_width=True)

    with ch_col2:
        st.markdown("##### 🌐 Network Traffic (MiB)")
        fig_net = go.Figure()
        fig_net.add_trace(go.Bar(
            name="Rack-Local Traffic",
            x=["Blind", "Aware", "Delay"],
            y=[m_blind.rack_mib, m_aware.rack_mib, m_delay.rack_mib],
            marker_color="#F59E0B"
        ))
        fig_net.add_trace(go.Bar(
            name="Cross-Rack Traffic",
            x=["Blind", "Aware", "Delay"],
            y=[m_blind.cross_mib, m_aware.cross_mib, m_delay.cross_mib],
            marker_color="#EF4444"
        ))
        fig_net.update_layout(barmode="stack", margin=dict(l=20, r=20, t=30, b=20), height=300)
        st.plotly_chart(fig_net, use_container_width=True)

    with ch_col3:
        st.markdown("##### 🎯 Locality Distribution (%)")
        loc_df = pd.DataFrame([
            {"Policy": "Blind", "Level": "Node-Local", "Count": m_blind.node_local},
            {"Policy": "Blind", "Level": "Rack-Local", "Count": m_blind.rack_local},
            {"Policy": "Blind", "Level": "Off-Rack", "Count": m_blind.off_rack},
            {"Policy": "Aware", "Level": "Node-Local", "Count": m_aware.node_local},
            {"Policy": "Aware", "Level": "Rack-Local", "Count": m_aware.rack_local},
            {"Policy": "Aware", "Level": "Off-Rack", "Count": m_aware.off_rack},
            {"Policy": "Delay", "Level": "Node-Local", "Count": m_delay.node_local},
            {"Policy": "Delay", "Level": "Rack-Local", "Count": m_delay.rack_local},
            {"Policy": "Delay", "Level": "Off-Rack", "Count": m_delay.off_rack},
        ])
        fig_loc = px.bar(
            loc_df, x="Policy", y="Count", color="Level",
            color_discrete_map={"Node-Local": "#10B981", "Rack-Local": "#F59E0B", "Off-Rack": "#EF4444"},
            barmode="stack"
        )
        fig_loc.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=300)
        st.plotly_chart(fig_loc, use_container_width=True)

    # Interactive Execution Timeline (Gantt Chart)
    st.markdown("---")
    st.subheader("📅 Interactive Task Scheduling Timeline (Gantt Chart)")
    col_tl1, col_tl2 = st.columns([2, 1])
    with col_tl1:
        chosen_sched_name = st.radio("Inspect policy execution timeline:", ["Delay Scheduling", "Greedy Aware", "Locality-Blind"], horizontal=True)
    with col_tl2:
        lane_mode = st.radio("Group By:", ["Worker Slots (Detailed)", "Worker Nodes"], horizontal=True)

    active_m = m_delay if chosen_sched_name == "Delay Scheduling" else (m_aware if chosen_sched_name == "Greedy Aware" else m_blind)

    gantt_rows = []
    loc_names = {Locality.NODE_LOCAL: "Node-Local", Locality.RACK_LOCAL: "Rack-Local", Locality.OFF_RACK: "Off-Rack"}
    for r in active_m.records:
        if lane_mode == "Worker Slots (Detailed)":
            lane = f"Worker {r.worker:02d} [R{wl.rack_of[r.worker]}] - Slot {r.slot}"
        else:
            lane = f"Worker {r.worker:02d} [Rack {wl.rack_of[r.worker]}]"
        
        gantt_rows.append({
            "Lane": lane,
            "Start": r.start,
            "Finish": r.finish,
            "Duration": round(r.finish - r.start, 2),
            "Read Time": round(r.read_end - r.start, 2),
            "Task ID": f"Task {r.task_id} (Job {r.job})",
            "Locality": loc_names[r.locality]
        })
    gantt_df = pd.DataFrame(gantt_rows).sort_values("Lane", ascending=False)

    fig_gantt = go.Figure()
    color_map = {"Node-Local": "#10B981", "Rack-Local": "#F59E0B", "Off-Rack": "#EF4444"}
    for loc in ["Node-Local", "Rack-Local", "Off-Rack"]:
        sub = gantt_df[gantt_df["Locality"] == loc]
        if len(sub) > 0:
            fig_gantt.add_trace(go.Bar(
                name=loc,
                y=sub["Lane"],
                x=sub["Duration"],
                base=sub["Start"],
                orientation="h",
                marker=dict(color=color_map[loc], line=dict(color="#1E293B", width=0.5)),
                customdata=np.stack((sub["Task ID"], sub["Start"], sub["Read Time"], sub["Duration"]), axis=-1),
                hovertemplate="<b>%{customdata[0]}</b><br>" +
                              "Locality: " + loc + "<br>" +
                              "Start: %{customdata[1]:.2f}s<br>" +
                              "Read Phase: %{customdata[2]:.2f}s<br>" +
                              "Total Duration: %{customdata[3]:.2f}s<extra></extra>"
            ))

    chart_height = max(450, len(gantt_df["Lane"].unique()) * 22)
    fig_gantt.update_layout(
        barmode="overlay",
        xaxis=dict(title="Execution Time (seconds)", showgrid=True, zeroline=True),
        yaxis=dict(title="Cluster Worker / Slot Lane", automargin=True),
        height=min(chart_height, 750),
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_gantt, use_container_width=True)

# =========================================================================
# PAGE 2: BENCHMARK MATRIX EXPLORER
# =========================================================================
elif page == "📊 Benchmark Matrix (78 Settings)":
    st.markdown('<div class="main-title">📊 Benchmark Matrix Explorer</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-title">Explore the <b>78 experimental settings</b> and <b>50 paired random seeds</b> '
        '(11,700 runs) evaluated in the paper.</div>',
        unsafe_allow_html=True
    )

    if df_runs is None or df_summary is None:
        st.error("Data files (`all_runs.csv` / `summary.csv`) not found in workspace.")
    else:
        exp_list = sorted(df_runs["experiment"].unique().tolist())
        col_f1, col_f2, col_f3 = st.columns([1.5, 1.5, 1])
        with col_f1:
            sel_exp = st.selectbox("Select Experiment Suite:", exp_list, index=0)
        with col_f2:
            metrics_avail = [
                ("makespan_s", "Makespan (s)"),
                ("mean_turnaround_s", "Mean Turnaround (s)"),
                ("remote_mib", "Remote Input Traffic (MiB)"),
                ("cross_rack_mib", "Cross-Rack Traffic (MiB)"),
                ("mean_wait_s", "Mean Queueing Wait (s)")
            ]
            sel_metric = st.selectbox("Select Metric:", metrics_avail, format_func=lambda x: x[1])[0]
        with col_f3:
            plot_type = st.radio("View Mode:", ["Means + 95% CI", "Raw Seed Distribution (Boxplot)"])

        sub_df = df_runs[df_runs["experiment"] == sel_exp]
        sub_summary = df_summary[(df_summary["experiment"] == sel_exp) & (df_summary["metric"] == sel_metric)]

        st.markdown(f"#### Experiment `{sel_exp}`: Parameter Variation")

        if plot_type == "Means + 95% CI":
            # Group by param value and policy
            # check if param value is numeric
            sub_df_copy = sub_df.copy()
            sub_df_copy["numeric_val"] = pd.to_numeric(sub_df_copy["value"], errors="coerce")
            is_numeric = sub_df_copy["numeric_val"].notna().all()

            if is_numeric:
                sub_df_copy = sub_df_copy.sort_values("numeric_val")
                x_col = "numeric_val"
            else:
                x_col = "value"

            agg = sub_df_copy.groupby([x_col, "policy"])[sel_metric].agg(["mean", "std", "count"]).reset_index()
            agg["ci95"] = 1.96 * agg["std"] / np.sqrt(agg["count"])

            fig_m = px.line(
                agg,
                x=x_col,
                y="mean",
                color="policy",
                error_y="ci95",
                markers=True,
                color_discrete_map={"blind": "#94A3B8", "aware": "#3B82F6", "delay": "#F97316"},
                labels={x_col: sub_df["param"].iloc[0], "mean": sel_metric},
                title=f"{sel_metric} across {sub_df['param'].iloc[0]} with 95% Confidence Intervals"
            )
            fig_m.update_layout(height=420)
            st.plotly_chart(fig_m, use_container_width=True)

        else:
            fig_box = px.box(
                sub_df,
                x="value",
                y=sel_metric,
                color="policy",
                color_discrete_map={"blind": "#94A3B8", "aware": "#3B82F6", "delay": "#F97316"},
                labels={"value": sub_df["param"].iloc[0]},
                title=f"Distribution across 50 Seeds for {sel_metric}"
            )
            fig_box.update_layout(height=420)
            st.plotly_chart(fig_box, use_container_width=True)

        st.markdown("##### 📋 Paired Improvements & Hypothesis Statistics")
        st.dataframe(
            sub_summary[[
                "setting_id", "param", "value", "comparison", "mean_base", "mean_alt",
                "improvement_pct", "ci95_pct", "frac_seeds_better"
            ]].rename(columns={
                "mean_base": "Baseline Mean",
                "mean_alt": "Alternative Mean",
                "improvement_pct": "Improvement %",
                "ci95_pct": "± 95% CI %",
                "frac_seeds_better": "Frac Seeds Superior"
            }),
            use_container_width=True
        )

# =========================================================================
# PAGE 3: HYPOTHESIS & TRADE-OFF ANALYZER
# =========================================================================
elif page == "🔬 Hypothesis & Trade-off Analyzer":
    st.markdown('<div class="main-title">🔬 Hypothesis & Trade-off Analyzer</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-title">Verification of the research hypotheses formulated in the study.</div>',
        unsafe_allow_html=True
    )

    t1, t2, t3 = st.tabs([
        "H2: Bandwidth Sensitivity",
        "H4: The Cost of Waiting",
        "Congestion Collapse (Shared Link)"
    ])

    with t1:
        st.markdown("### **Hypothesis 2 (H2): Network Bandwidth Sensitivity**")
        st.markdown("""
        > *Locality-aware scheduling's completion-time advantage grows when remote transfers are expensive relative to compute.*
        """)
        if df_summary is not None:
            e2 = df_summary[(df_summary["experiment"] == "E2_bw") & (df_summary["metric"] == "makespan_s")].copy()
            e2["bandwidth"] = pd.to_numeric(e2["value"])
            e2 = e2.sort_values("bandwidth")

            fig_e2 = px.line(
                e2,
                x="bandwidth",
                y="improvement_pct",
                color="comparison",
                error_y="ci95_pct",
                markers=True,
                log_x=True,
                title="Makespan Improvement vs Cross-Rack Bandwidth (Log Scale)",
                labels={"bandwidth": "Cross-Rack Bandwidth (MiB/s)", "improvement_pct": "Improvement over Baseline (%)"}
            )
            fig_e2.update_layout(height=400)
            st.plotly_chart(fig_e2, use_container_width=True)
            st.success("✅ **Finding:** As cross-rack bandwidth increases from 5 to 200 MiB/s, greedy aware improvement drops from 15.8% to 0.4%, while bytes saved remain identical.")

    with t2:
        st.markdown("### **Hypothesis 4 (H4): The Cost of Waiting in Delay Scheduling**")
        st.markdown("""
        > *Waiting for local workers reduces network traffic, but can increase completion time when the benefit does not justify the wait.*
        """)
        if df_summary is not None:
            e5 = df_summary[(df_summary["experiment"].isin(["E5_main", "E5_highbw", "E5_load1"])) & (df_summary["metric"] == "makespan_s")].copy()
            e5["delay"] = pd.to_numeric(e5["value"])
            e5 = e5.sort_values("delay")
            e5_delay = e5[e5["comparison"] == "delay_vs_aware"]

            fig_e5 = px.line(
                e5_delay,
                x="delay",
                y="improvement_pct",
                color="experiment",
                markers=True,
                title="Delay Policy vs Greedy Aware across Delay Threshold D",
                labels={"delay": "Delay Parameter D (s)", "improvement_pct": "Improvement % (Negative = Delay is slower)"}
            )
            fig_e5.add_hline(y=0, line_dash="dash", line_color="gray")
            fig_e5.update_layout(height=400)
            st.plotly_chart(fig_e5, use_container_width=True)
            st.warning("⚠️ **Finding:** In `E5_highbw` (fast network) or `E5_load1` (light load), delay scheduling eliminates remote traffic but **increases makespan by up to 4.5%** because waiting exceeds transfer times.")

    with t3:
        st.markdown("### **Contention & Congestion Collapse (Processor Sharing Model)**")
        st.markdown("""
        > *When cross-rack traffic shares a finite link, ignoring locality leads to severe queueing and congestion collapse.*
        """)
        if df_runs is not None:
            e6 = df_runs[df_runs["experiment"] == "E6_shared"].copy()
            e6["core_cap"] = pd.to_numeric(e6["value"])
            e6_agg = e6.groupby(["core_cap", "policy"])["makespan_s"].mean().reset_index()

            fig_e6 = px.line(
                e6_agg,
                x="core_cap",
                y="makespan_s",
                color="policy",
                markers=True,
                title="Makespan under Shared Core Link Capacity Constraints",
                labels={"core_cap": "Core Link Capacity (MiB/s)", "makespan_s": "Makespan (s)"},
                color_discrete_map={"blind": "#EF4444", "aware": "#3B82F6", "delay": "#10B981"}
            )
            fig_e6.update_layout(height=400)
            st.plotly_chart(fig_e6, use_container_width=True)
            st.error("🚨 **Finding:** At 25 MiB/s core capacity, locality-blind scheduling causes makespan to explode to **336.9s** due to contention, compared to **47.0s** for delay scheduling.")

# =========================================================================
# PAGE 4: RESEARCH PAPER & DOWNLOADS
# =========================================================================
elif page == "📄 Research Paper & Downloads":
    st.markdown('<div class="main-title">📄 Research Paper & Artifacts</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-title">Read the formal paper, theoretical model, and download dataset artifacts.</div>',
        unsafe_allow_html=True
    )

    col_p1, col_p2 = st.columns([2.5, 1])

    with col_p1:
        st.markdown("""
        ### **A Practical Study of Data Locality Optimization Techniques in Hadoop MapReduce**
        
        #### **Abstract**
        Hadoop MapReduce divides its input into splits that are processed by map tasks, and HDFS stores replicas of every block on different machines and racks. A scheduler that places a map task on a machine that already holds its input avoids a network transfer; a scheduler that ignores block locations does not. This paper studies how much that distinction matters.
        
        We built a discrete-event simulator that models HDFS block placement with rack awareness, finite map slots, three locality levels (node-local, rack-local, off-rack), and two network models (independent per-transfer bandwidth and a shared cross-rack link). We compare three policies on identical workloads using paired random seeds:
        1. **Locality-blind round-robin baseline**
        2. **Greedy locality-aware scheduler**
        3. **Delay-based locality scheduler (Zaharia et al.)**
        
        #### **Key Results:**
        * **Delay Scheduling Dominates Greedy:** In a 16-worker, 4-rack cluster, greedy locality-aware reduced remote traffic by **20.7%**, while delay scheduling reduced remote traffic by **72.8%** and cross-rack traffic by **91.3%**.
        * **The Completion-Time Decoupling:** Bandwidth alters duration, not bytes. On high-bandwidth backbones (100–200 MiB/s), locality awareness saves huge volumes of traffic while makespan gains shrink to near 0%.
        * **Link Sharing:** Under a shared core link, blind scheduling suffers congestion collapse (makespan 336.9s vs 47.0s for delay scheduling at 25 MiB/s).
        """)

    with col_p2:
        st.markdown("### 📥 Document Downloads")
        if os.path.exists("paper_ieee.pdf"):
            with open("paper_ieee.pdf", "rb") as f:
                st.download_button(
                    "📄 Research Paper (IEEE PDF - 5 Pages)",
                    data=f.read(),
                    file_name="paper_ieee_vikram_amit.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        if os.path.exists("paper_ieee.docx"):
            with open("paper_ieee.docx", "rb") as f:
                st.download_button(
                    "📝 Research Paper (IEEE DOCX)",
                    data=f.read(),
                    file_name="paper_ieee_vikram_amit.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
        if os.path.exists("big_data_project_report.pdf"):
            with open("big_data_project_report.pdf", "rb") as f:
                st.download_button(
                    "📑 SRM Project Report (PDF)",
                    data=f.read(),
                    file_name="SRM_Big_Data_Project_Report.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        if os.path.exists("big_data_project_report.docx"):
            with open("big_data_project_report.docx", "rb") as f:
                st.download_button(
                    "📘 SRM Project Report (DOCX)",
                    data=f.read(),
                    file_name="SRM_Big_Data_Project_Report.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
        if os.path.exists("summary.csv"):
            with open("summary.csv", "rb") as f:
                st.download_button(
                    "📊 Download Summary Statistics (CSV)",
                    data=f.read(),
                    file_name="summary.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        if os.path.exists("all_runs.csv"):
            with open("all_runs.csv", "rb") as f:
                st.download_button(
                    "💾 Download All 11,700 Runs (CSV)",
                    data=f.read(),
                    file_name="all_runs.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        st.markdown("---")
        st.markdown("#### 🔗 Repository Links")
        st.markdown("""
        - [GitHub Repository](https://github.com)
        - [Streamlit Cloud](https://streamlit.io/cloud)
        - [Hadoop Architecture Guide](https://hadoop.apache.org)
        """)
