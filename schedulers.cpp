#include "sim.hpp"

namespace sim {
namespace {
// Policy A: round-robin over free workers, never inspects block locations.
class Blind : public Scheduler {
  int next_ = 0;
 public:
  std::string name() const override { return "blind"; }
  int pick_worker(const Task&, const SchedulerView& v) override {
    int n = static_cast<int>(v.free_slots.size());
    for (int i = 0; i < n; ++i) {
      int w = (next_ + i) % n;
      if (v.free_slots[w] > 0) { next_ = (w + 1) % n; return w; }
    }
    return -1;
  }
};
// Policy B: greedy. Best locality among free workers (node > rack > off); ties -> lowest id.
class Aware : public Scheduler {
 public:
  std::string name() const override { return "aware"; }
  int pick_worker(const Task& t, const SchedulerView& v) override {
    int best = -1, rank = 3;
    const Block& b = v.wl.blocks[t.block];
    for (int w = 0; w < static_cast<int>(v.free_slots.size()); ++w) {
      if (v.free_slots[w] <= 0) continue;
      int r = static_cast<int>(classify(v.wl, w, b));
      if (r < rank) { rank = r; best = w; if (r == 0) break; }
    }
    return best;
  }
};
// Policy C: delay scheduling (Zaharia et al., EuroSys 2010), simplified to a per-task timer.
// A task that cannot run node-locally waits D s (measured from the first moment a slot was free
// for it), then may run rack-locally; after 2D s it may run anywhere. Other tasks keep running
// meanwhile. D = 0 reduces exactly to Policy B.
class Delay : public Scheduler {
  double D_;
  std::vector<double> since_;
 public:
  explicit Delay(double d) : D_(d) {}
  std::string name() const override { return "delay"; }
  int pick_worker(const Task& t, const SchedulerView& v) override {
    if (since_.size() < v.wl.tasks.size()) since_.assign(v.wl.tasks.size(), -1.0);
    if (since_[t.id] < 0) since_[t.id] = v.now;
    double waited = v.now - since_[t.id];
    const Block& b = v.wl.blocks[t.block];
    int node = -1, rack = -1, off = -1;
    for (int w = 0; w < static_cast<int>(v.free_slots.size()); ++w) {
      if (v.free_slots[w] <= 0) continue;
      switch (classify(v.wl, w, b)) {
        case Locality::NodeLocal: if (node < 0) node = w; break;
        case Locality::RackLocal: if (rack < 0) rack = w; break;
        default: if (off < 0) off = w;
      }
      if (node >= 0) break;
    }
    if (node >= 0) return node;
    if (waited >= D_ && rack >= 0) return rack;
    if (waited >= 2 * D_ && off >= 0) return off;
    return -1;
  }
  double wakeup_time(const Task& t, double now) const override {
    if (t.id >= static_cast<int>(since_.size()) || since_[t.id] < 0) return kInf;
    double waited = now - since_[t.id];
    if (waited < D_) return since_[t.id] + D_;
    if (waited < 2 * D_) return since_[t.id] + 2 * D_;
    return kInf;
  }
};
}  // namespace

std::unique_ptr<Scheduler> make_scheduler(const std::string& n, double delay_s) {
  if (n == "blind") return std::make_unique<Blind>();
  if (n == "aware") return std::make_unique<Aware>();
  if (n == "delay") return std::make_unique<Delay>(delay_s);
  return nullptr;
}
}  // namespace sim
