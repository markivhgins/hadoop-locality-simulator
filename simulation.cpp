#include "sim.hpp"
#include <algorithm>
#include <cassert>
#include <list>
#include <queue>
#include <set>

namespace sim {
namespace {
enum class EvType { JobArrival, ReadDone, TaskFinish, Wakeup };
struct Event {
  double t; std::uint64_t seq; EvType type; int idx;
  bool operator>(const Event& o) const { return t != o.t ? t > o.t : seq > o.seq; }
};
// A remote read in flight (shared-network model only). link 0 = core, 1+r = rack r.
struct Flow { int task; int link; double rem; double cap; };
constexpr double kEps = 1e-9;
}  // namespace

Metrics run(const Workload& wl, Scheduler& sched) {
  const Config& c = wl.cfg;
  std::priority_queue<Event, std::vector<Event>, std::greater<>> pq;
  std::uint64_t seq = 0;
  for (int j = 0; j < static_cast<int>(wl.job_release.size()); ++j)
    pq.push({wl.job_release[j], seq++, EvType::JobArrival, j});

  std::vector<int> free_slots(c.workers, c.slots);
  int free_total = c.workers * c.slots;
  std::list<int> ready;  // task ids, FIFO in fixed workload order
  Metrics m;
  m.records.resize(wl.tasks.size());
  std::vector<double> job_done(wl.job_release.size(), 0.0);
  std::vector<Flow> flows;
  std::set<double> wakeups;
  int finished = 0;
  double now = 0, busy = 0;

  auto begin_compute = [&](int tid) {
    TaskRecord& r = m.records[tid];
    r.read_end = now;
    r.finish = now + wl.tasks[tid].compute_s;
    pq.push({r.finish, seq++, EvType::TaskFinish, tid});
  };

  auto dispatch = [&] {
    for (auto it = ready.begin(); it != ready.end() && free_total > 0;) {
      const Task& t = wl.tasks[*it];
      int w = sched.pick_worker(t, SchedulerView{wl, free_slots, now});
      if (w < 0) { ++it; continue; }  // declined: later tasks may still run
      assert(free_slots[w] > 0);
      it = ready.erase(it);
      --free_slots[w]; --free_total;
      Locality l = classify(wl, w, wl.blocks[t.block]);
      m.records[t.id].worker = w; m.records[t.id].start = now; m.records[t.id].loc = l;
      if (l == Locality::NodeLocal) { ++m.node_local; m.node_mib += t.size_mib; }
      else if (l == Locality::RackLocal) { ++m.rack_local; m.rack_mib += t.size_mib; m.remote_mib += t.size_mib; }
      else { ++m.off_rack; m.off_mib += t.size_mib; m.remote_mib += t.size_mib; m.cross_mib += t.size_mib; }
      if (l == Locality::NodeLocal || !c.shared_net) {
        pq.push({now + read_time(c, l, t.size_mib), seq++, EvType::ReadDone, t.id});
      } else if (l == Locality::RackLocal) {
        flows.push_back({t.id, 1 + wl.rack_of[w], t.size_mib, c.rack_bw});
      } else {
        flows.push_back({t.id, 0, t.size_mib, c.cross_bw});
      }
    }
    if (free_total > 0)  // declined tasks may become schedulable by timeout alone
      for (int tid : ready) {
        double wt = sched.wakeup_time(wl.tasks[tid], now);
        if (wt < kInf && wt > now + 1e-12 && wakeups.insert(wt).second)
          pq.push({wt, seq++, EvType::Wakeup, -1});
      }
  };

  while (true) {
    double tq = pq.empty() ? kInf : pq.top().t;
    // Processor-sharing rates: each flow gets min(per-flow cap, link capacity / #flows on link).
    std::vector<int> cnt(1 + c.racks, 0);
    for (const Flow& f : flows) ++cnt[f.link];
    auto rate = [&](const Flow& f) {
      double cap = f.link == 0 ? c.core_cap : c.rack_cap;
      return std::min(f.cap, cap / cnt[f.link]);
    };
    double tf = kInf;
    for (const Flow& f : flows) tf = std::min(tf, now + f.rem / rate(f));
    double tn = std::min(tq, tf);
    if (tn == kInf) break;
    double dt = tn - now;
    for (Flow& f : flows) f.rem -= rate(f) * dt;
    now = tn;
    for (auto it = flows.begin(); it != flows.end();) {
      if (it->rem <= kEps) { begin_compute(it->task); it = flows.erase(it); } else ++it;
    }
    // Drain every event at this timestamp before dispatching.
    while (!pq.empty() && pq.top().t <= now + 1e-12) {
      Event e = pq.top(); pq.pop();
      switch (e.type) {
        case EvType::JobArrival:
          for (const Task& t : wl.tasks) if (t.job == e.idx) ready.push_back(t.id);
          break;
        case EvType::ReadDone: begin_compute(e.idx); break;
        case EvType::TaskFinish: {
          const TaskRecord& r = m.records[e.idx];
          ++free_slots[r.worker]; ++free_total;
          busy += r.finish - r.start;
          int j = wl.tasks[e.idx].job;
          job_done[j] = std::max(job_done[j], r.finish);
          ++finished;
          break;
        }
        case EvType::Wakeup: break;
      }
    }
    dispatch();
  }
  assert(finished == static_cast<int>(wl.tasks.size()));
  assert(m.node_local + m.rack_local + m.off_rack == finished);

  double first = *std::min_element(wl.job_release.begin(), wl.job_release.end());
  double last = *std::max_element(job_done.begin(), job_done.end());
  m.makespan = last - first;
  for (size_t j = 0; j < job_done.size(); ++j) {
    m.job_turnaround.push_back(job_done[j] - wl.job_release[j]);
    m.mean_turnaround += m.job_turnaround.back() / job_done.size();
  }
  int remote_n = m.rack_local + m.off_rack;
  for (const Task& t : wl.tasks) {
    const TaskRecord& r = m.records[t.id];
    m.mean_wait += (r.start - t.release) / wl.tasks.size();
    m.mean_read_s += (r.read_end - r.start) / wl.tasks.size();
    if (r.loc != Locality::NodeLocal) m.mean_remote_read_s += (r.read_end - r.start) / remote_n;
  }
  m.utilization = m.makespan > 0 ? busy / (m.makespan * c.workers * c.slots) : 0;
  m.core_load = m.makespan > 0 ? m.cross_mib / (c.core_cap * m.makespan) : 0;
  return m;
}
}  // namespace sim
