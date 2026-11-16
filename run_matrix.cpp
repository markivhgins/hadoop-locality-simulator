// run_matrix: runs the full experimental matrix (E1-E6) with paired seeds and writes
//   <out>/all_runs.csv   one row per (setting, seed, policy)
//   <out>/manifest.csv   full configuration of every setting (for reproducibility)
#include "sim.hpp"
#include <cstdio>
#include <fstream>
#include <functional>
#include <iostream>
#include <string>

using namespace sim;

struct Setting { std::string exp, id, param, value; Config cfg; };

static std::string num(double x) { char b[32]; std::snprintf(b, sizeof b, "%g", x); return b; }

int main(int argc, char** argv) {
  int seeds = 50; std::uint64_t seed0 = 1; std::string out = "results";
  for (int i = 1; i + 1 < argc; i += 2) {
    std::string k = argv[i];
    if (k == "--seeds") seeds = std::stoi(argv[i + 1]);
    else if (k == "--seed0") seed0 = std::stoull(argv[i + 1]);
    else if (k == "--out") out = argv[i + 1];
  }

  // Main evaluation cluster: 16 workers x 2 slots = 32 map slots, 4 racks, 3 replicas,
  // 128 MiB splits, 128 tasks (4x slot count) in 4 jobs released together.
  Config base;
  base.workers = 16; base.racks = 4; base.slots = 2; base.replicas = 3;
  base.jobs = 4; base.tasks_per_job = 32;

  std::vector<Setting> S;
  auto add = [&](const std::string& exp, const std::string& param, const std::string& value,
                 const std::function<void(Config&)>& mut) {
    Config c = base;
    mut(c);
    S.push_back({exp, exp + "_" + param + "=" + value, param, value, c});
  };

  // E1: baseline policy comparison (the plan's small config, and the main config).
  { Config small; // library defaults = 8 workers, 2 racks, 2 slots, 4x16 tasks
    S.push_back({"E1", "E1_small", "config", "small", small});
    S.push_back({"E1", "E1_main", "config", "main", base}); }
  // E2: network bandwidth sensitivity (per-flow cross-rack rate); block size.
  for (double b : {5., 10., 25., 50., 100., 200.}) add("E2_bw", "cross_bw", num(b), [&](Config& c) { c.cross_bw = b; });
  for (double b : {64., 128., 256.}) add("E2_block", "block_mib", num(b), [&](Config& c) { c.block_mib = b; });
  // E3: load (tasks / slots) and job arrival spacing.
  for (int f : {1, 2, 4, 8}) add("E3_load", "load_x_slots", num(f), [&](Config& c) { c.tasks_per_job = f * c.workers * c.slots / c.jobs; });
  for (double g : {0., 10., 20., 40., 80.}) add("E3_gap", "release_gap_s", num(g), [&](Config& c) { c.release_gap = g; });
  // E4: replication, rack topology, cluster size.
  for (int r : {1, 2, 3, 4}) add("E4_replicas", "replicas", num(r), [&](Config& c) { c.replicas = r; });
  for (int rk : {1, 2, 4, 8}) for (int r : {1, 2, 3})
    add("E4_grid", "racks_x_replicas", num(rk) + "x" + num(r), [&](Config& c) { c.racks = rk; c.replicas = r; });
  for (int w : {4, 8, 16, 32}) add("E4_workers", "workers", num(w), [&](Config& c) {
    c.workers = w; c.racks = 4; c.tasks_per_job = 4 * w * c.slots / c.jobs; });
  // E5: delay threshold, at the main bandwidth and at a constrained cross-rack bandwidth.
  for (double d : {0., 0.5, 1., 2., 4., 8., 16.}) {
    add("E5_main", "delay_s", num(d), [&](Config& c) { c.delay_s = d; });
    add("E5_lowbw", "delay_s", num(d), [&](Config& c) { c.delay_s = d; c.cross_bw = 10; });
    // Regimes where waiting should be least justified: light load, and fast network.
    add("E5_load1", "delay_s", num(d), [&](Config& c) { c.delay_s = d; c.tasks_per_job = c.workers * c.slots / c.jobs; });
    add("E5_highbw", "delay_s", num(d), [&](Config& c) { c.delay_s = d; c.cross_bw = 200; c.rack_bw = 400; });
  }
  // E6: shared cross-rack link capacity (processor sharing), per-flow cap stays 25 MiB/s.
  for (double cap : {25., 50., 100., 200., 400.})
    add("E6_shared", "core_cap", num(cap), [&](Config& c) { c.shared_net = true; c.core_cap = cap; });
  // E6b: shared model with a higher per-flow cap (links, not flows, are the bottleneck).
  for (double cap : {25., 50., 100., 200., 400.})
    add("E6_shared_fast", "core_cap", num(cap), [&](Config& c) { c.shared_net = true; c.core_cap = cap; c.cross_bw = 100; });

  std::ofstream f(out + "/all_runs.csv"), mf(out + "/manifest.csv");
  if (!f || !mf) { std::cerr << "cannot write into " << out << "\n"; return 1; }
  f << "experiment,setting_id,param,value,seed,policy,makespan_s,mean_turnaround_s,mean_wait_s,mean_read_s,"
       "mean_remote_read_s,remote_mib,cross_rack_mib,node_local,rack_local,off_rack,node_mib,rack_mib,off_mib,"
       "utilization,core_load\n";
  mf << "experiment,setting_id,param,value,workers,racks,slots,replicas,block_mib,local_bw,rack_bw,cross_bw,jobs,"
        "tasks_per_job,compute_s,jitter,release_gap,shared_net,core_cap,rack_cap,delay_s,seeds,seed0\n";

  const char* pol[3] = {"blind", "aware", "delay"};
  long rows = 0;
  try {
    for (const Setting& s : S) {
      const Config& c = s.cfg;
      mf << s.exp << ',' << s.id << ',' << s.param << ',' << s.value << ',' << c.workers << ',' << c.racks << ','
         << c.slots << ',' << c.replicas << ',' << c.block_mib << ',' << c.local_bw << ',' << c.rack_bw << ','
         << c.cross_bw << ',' << c.jobs << ',' << c.tasks_per_job << ',' << c.compute_s << ',' << c.compute_jitter
         << ',' << c.release_gap << ',' << c.shared_net << ',' << c.core_cap << ',' << c.rack_cap << ','
         << c.delay_s << ',' << seeds << ',' << seed0 << '\n';
      for (int k = 0; k < seeds; ++k) {
        Config cc = c; cc.seed = seed0 + k;
        Workload wl = generate_workload(cc);  // identical instance for all three policies
        for (const char* p : pol) {
          auto sch = make_scheduler(p, cc.delay_s);
          Metrics m = run(wl, *sch);
          f << s.exp << ',' << s.id << ',' << s.param << ',' << s.value << ',' << cc.seed << ',' << p << ','
            << m.makespan << ',' << m.mean_turnaround << ',' << m.mean_wait << ',' << m.mean_read_s << ','
            << m.mean_remote_read_s << ',' << m.remote_mib << ',' << m.cross_mib << ',' << m.node_local << ','
            << m.rack_local << ',' << m.off_rack << ',' << m.node_mib << ',' << m.rack_mib << ',' << m.off_mib
            << ',' << m.utilization << ',' << m.core_load << '\n';
          ++rows;
        }
      }
    }
  } catch (const std::exception& e) { std::cerr << "error: " << e.what() << "\n"; return 1; }
  std::printf("%zu settings x %d seeds x 3 policies = %ld runs -> %s/all_runs.csv\n", S.size(), seeds, rows, out.c_str());
  return 0;
}
