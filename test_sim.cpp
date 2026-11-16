#include "sim.hpp"
#include <cmath>
#include <cstdio>
using namespace sim;

static int fails = 0;
#define CHECK(x) do { if (!(x)) { std::printf("FAIL line %d: %s\n", __LINE__, #x); ++fails; } } while (0)
static bool eq(double a, double b) { return std::fabs(a - b) < 1e-9; }

static Workload manual(int workers, int racks, int slots, std::vector<int> block_worker) {
  Workload wl; Config& c = wl.cfg;
  c.workers = workers; c.racks = racks; c.slots = slots;
  c.local_bw = 128; c.rack_bw = 128; c.cross_bw = 64;  // 128 MiB: 1s local, 1s rack, 2s cross
  for (int w = 0; w < workers; ++w) wl.rack_of.push_back(w % racks);
  wl.job_release = {0.0};
  int id = 0;
  for (int w : block_worker) {
    wl.blocks.push_back({128, {w}});
    wl.tasks.push_back({id, 0, id, 128, 1.0, 0.0}); ++id;
  }
  return wl;
}

int main() {
  // 1. One worker: zero remote traffic, makespan = 4 * (compute 5 + 128/128).
  { Config c; c.workers = 1; c.racks = 1; c.slots = 1; c.replicas = 1; c.jobs = 1; c.tasks_per_job = 4;
    c.compute_s = 5; c.compute_jitter = 0; c.local_bw = 128;
    for (auto n : {"blind", "aware"}) { auto s = make_scheduler(n); Metrics m = run(generate_workload(c), *s);
      CHECK(eq(m.remote_mib, 0)); CHECK(eq(m.makespan, 24)); } }

  // 2. Everything replicated everywhere: aware is 100% node-local.
  { Config c; c.replicas = c.workers; auto wl = generate_workload(c); auto s = make_scheduler("aware");
    Metrics m = run(wl, *s); CHECK(m.node_local == (int)wl.tasks.size()); CHECK(eq(m.remote_mib, 0)); }

  // 3. Off-rack: 2 workers / 2 racks / 1 slot, both blocks on worker 0.
  //    t0 -> w0 local (1+1=2s); t1 -> w1 off-rack (2+1=3s). Remote=128, cross=128, makespan 3.
  { auto wl = manual(2, 2, 1, {0, 0}); auto s = make_scheduler("aware"); Metrics m = run(wl, *s);
    CHECK(m.node_local == 1 && m.off_rack == 1 && m.rack_local == 0);
    CHECK(eq(m.remote_mib, 128)); CHECK(eq(m.cross_mib, 128)); CHECK(eq(m.makespan, 3)); }

  // 4. Rack-local: same but 1 rack. Remote counted, cross-rack zero, makespan 2.
  { auto wl = manual(2, 1, 1, {0, 0}); auto s = make_scheduler("aware"); Metrics m = run(wl, *s);
    CHECK(m.rack_local == 1); CHECK(eq(m.remote_mib, 128)); CHECK(eq(m.cross_mib, 0)); CHECK(eq(m.makespan, 2)); }

  // 5. Blocks on {1,0}: blind round-robin sends t0->w0, t1->w1 (both off-rack); aware keeps both local.
  { auto wl = manual(2, 2, 1, {1, 0}); auto b = make_scheduler("blind"), a = make_scheduler("aware");
    Metrics mb = run(wl, *b), ma = run(wl, *a);
    CHECK(mb.off_rack == 2 && eq(mb.cross_mib, 256)); CHECK(ma.node_local == 2 && eq(ma.remote_mib, 0)); }

  // 6. Slot limit: 1 worker, 2 slots, 6 tasks -> never more than 2 concurrent.
  { Config c; c.workers = 1; c.racks = 1; c.slots = 2; c.replicas = 1; c.jobs = 1; c.tasks_per_job = 6;
    auto wl = generate_workload(c); auto s = make_scheduler("aware"); Metrics m = run(wl, *s);
    for (const auto& r : m.records) { int running = 0;  // concurrency at r's start instant
      for (const auto& q : m.records) if (q.start <= r.start && r.start < q.finish) ++running;
      CHECK(running <= c.slots); } }

  // 7. Multiple jobs: turnaround uses each job's own release time.
  { Config c; c.workers = 1; c.racks = 1; c.slots = 1; c.replicas = 1; c.jobs = 2; c.tasks_per_job = 1;
    c.compute_s = 1; c.compute_jitter = 0; c.local_bw = 128; c.release_gap = 10;  // each task 2s
    auto s = make_scheduler("aware"); Metrics m = run(generate_workload(c), *s);
    CHECK(eq(m.job_turnaround[0], 2)); CHECK(eq(m.job_turnaround[1], 2)); CHECK(eq(m.makespan, 12)); }

  // 8. Determinism, identical totals across policies, category counts.
  { Config c; c.seed = 42; auto w1 = generate_workload(c), w2 = generate_workload(c);
    auto s1 = make_scheduler("aware"), s2 = make_scheduler("aware"), sb = make_scheduler("blind");
    Metrics a = run(w1, *s1), b = run(w2, *s2), bl = run(w1, *sb);
    CHECK(eq(a.makespan, b.makespan) && eq(a.remote_mib, b.remote_mib));
    CHECK(a.node_local + a.rack_local + a.off_rack == (int)w1.tasks.size());
    CHECK(bl.node_local + bl.rack_local + bl.off_rack == (int)w1.tasks.size());
    CHECK(a.cross_mib <= a.remote_mib); }

  // 9. Higher bandwidth never lengthens a read; node-local zero bytes -> zero time.
  { Config c; double slow = read_time(c, Locality::OffRack, 128); c.cross_bw *= 2;
    CHECK(read_time(c, Locality::OffRack, 128) <= slow); CHECK(eq(read_time(c, Locality::NodeLocal, 0), 0)); }

  // 10. Delay scheduling trade-off (H4): both blocks on w0, D=10. t1 waits for w0 (frees at 2s)
  //     and runs node-locally at 2..4 instead of off-rack on w1 (aware: makespan 3, cross 128).
  { auto wl = manual(2, 2, 1, {0, 0}); auto s = make_scheduler("delay", 10); Metrics m = run(wl, *s);
    CHECK(m.node_local == 2 && eq(m.cross_mib, 0)); CHECK(eq(m.makespan, 4)); }

  // 11. Delay with D = 0 is exactly the greedy aware policy.
  { Config c; c.seed = 7; auto wl = generate_workload(c);
    auto d = make_scheduler("delay", 0), a = make_scheduler("aware");
    Metrics md = run(wl, *d), ma = run(wl, *a);
    CHECK(eq(md.makespan, ma.makespan) && eq(md.remote_mib, ma.remote_mib) && md.node_local == ma.node_local); }

  // 12. Shared cross-rack link: two concurrent off-rack reads (blocks {1,0}, blind) split 64 MiB/s.
  //     Each gets 32 MiB/s -> 4s read + 1s compute = 5s (simple model: 3s). Bytes unchanged.
  { auto wl = manual(2, 2, 1, {1, 0}); wl.cfg.core_cap = 64; auto s = make_scheduler("blind");
    Metrics simple = run(wl, *s);
    wl.cfg.shared_net = true; auto s2 = make_scheduler("blind"); Metrics shared = run(wl, *s2);
    CHECK(eq(simple.makespan, 3)); CHECK(eq(shared.makespan, 5));
    CHECK(eq(simple.cross_mib, shared.cross_mib));
    wl.cfg.core_cap = 1e9; auto s3 = make_scheduler("blind"); Metrics wide = run(wl, *s3);
    CHECK(eq(wide.makespan, 3)); }

  // 13. Every task finishes exactly once with monotone timestamps, all policies, shared network.
  { Config c; c.shared_net = true; c.core_cap = 50; c.seed = 3; auto wl = generate_workload(c);
    for (auto n : {"blind", "aware", "delay"}) { auto s = make_scheduler(n, 2); Metrics m = run(wl, *s);
      CHECK(m.records.size() == wl.tasks.size());
      for (const auto& r : m.records) CHECK(r.start <= r.read_end && r.read_end < r.finish && r.worker >= 0); } }

  std::puts(fails ? "TESTS FAILED" : "all tests passed");
  return fails ? 1 : 0;
}
