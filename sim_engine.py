import heapq
import random
from dataclasses import dataclass, field
from enum import IntEnum
from typing import List, Dict, Tuple, Optional

class Locality(IntEnum):
    NODE_LOCAL = 0
    RACK_LOCAL = 1
    OFF_RACK = 2

@dataclass
class SimConfig:
    workers: int = 16
    racks: int = 4
    slots: int = 2
    replicas: int = 3
    jobs: int = 4
    tasks_per_job: int = 32
    block_mib: float = 128.0
    compute_s: float = 5.0
    compute_jitter: float = 0.5
    local_bw: float = 200.0   # MiB/s
    rack_bw: float = 100.0    # MiB/s
    cross_bw: float = 25.0    # MiB/s
    delay_s: float = 2.0
    release_gap: float = 0.0
    shared_net: bool = False
    core_cap: float = 100.0   # MiB/s
    rack_cap: float = 200.0   # MiB/s
    seed: int = 42

@dataclass
class Task:
    id: int
    job: int
    block: int
    size_mib: float
    compute_s: float
    release: float

@dataclass
class TaskRecord:
    task_id: int
    job: int
    worker: int = -1
    slot: int = 0
    start: float = 0.0
    read_end: float = 0.0
    finish: float = 0.0
    locality: Locality = Locality.OFF_RACK
    size_mib: float = 0.0

@dataclass
class Workload:
    cfg: SimConfig
    rack_of: List[int]
    blocks: List[List[int]]   # block_id -> list of worker ids holding replicas
    tasks: List[Task]
    job_release: List[float]

@dataclass
class SimMetrics:
    makespan: float = 0.0
    mean_turnaround: float = 0.0
    mean_wait: float = 0.0
    mean_read_s: float = 0.0
    mean_remote_read_s: float = 0.0
    remote_mib: float = 0.0
    cross_mib: float = 0.0
    node_mib: float = 0.0
    rack_mib: float = 0.0
    off_mib: float = 0.0
    node_local: int = 0
    rack_local: int = 0
    off_rack: int = 0
    utilization: float = 0.0
    core_load: float = 0.0
    records: List[TaskRecord] = field(default_factory=list)

def classify(wl: Workload, worker: int, block_replicas: List[int]) -> Locality:
    if worker in block_replicas:
        return Locality.NODE_LOCAL
    w_rack = wl.rack_of[worker]
    for rep in block_replicas:
        if wl.rack_of[rep] == w_rack:
            return Locality.RACK_LOCAL
    return Locality.OFF_RACK

def read_time(cfg: SimConfig, loc: Locality, size_mib: float) -> float:
    if loc == Locality.NODE_LOCAL:
        return size_mib / cfg.local_bw
    elif loc == Locality.RACK_LOCAL:
        return size_mib / cfg.rack_bw
    else:
        return size_mib / cfg.cross_bw

def generate_workload(cfg: SimConfig) -> Workload:
    rng = random.Random(cfg.seed)
    rack_of = [w % cfg.racks for w in range(cfg.workers)]
    
    # Generate blocks and replicas
    total_tasks = cfg.jobs * cfg.tasks_per_job
    blocks = []
    for _ in range(total_tasks):
        k = min(cfg.replicas, cfg.workers)
        # HDFS placement rule:
        # 1st replica on random node
        reps = []
        w1 = rng.randrange(cfg.workers)
        reps.append(w1)
        
        if k > 1:
            # 2nd replica on different rack if possible
            r1 = rack_of[w1]
            diff_rack_workers = [w for w in range(cfg.workers) if rack_of[w] != r1]
            if diff_rack_workers:
                w2 = rng.choice(diff_rack_workers)
            else:
                w2 = rng.choice([w for w in range(cfg.workers) if w != w1])
            reps.append(w2)
            
            if k > 2:
                # 3rd replica on same rack as w2 if another node exists in that rack
                r2 = rack_of[w2]
                same_r2_workers = [w for w in range(cfg.workers) if rack_of[w] == r2 and w not in reps]
                if same_r2_workers:
                    w3 = rng.choice(same_r2_workers)
                else:
                    remain = [w for w in range(cfg.workers) if w not in reps]
                    w3 = rng.choice(remain) if remain else w1
                reps.append(w3)
                
            # any remaining replicas
            while len(reps) < k:
                remain = [w for w in range(cfg.workers) if w not in reps]
                if not remain: break
                reps.append(rng.choice(remain))
        blocks.append(reps)
        
    job_release = [j * cfg.release_gap for j in range(cfg.jobs)]
    tasks = []
    tid = 0
    for j in range(cfg.jobs):
        for _ in range(cfg.tasks_per_job):
            # compute demand uniform in compute_s * (1 +- compute_jitter)
            c = cfg.compute_s * (1.0 + rng.uniform(-cfg.compute_jitter, cfg.compute_jitter))
            tasks.append(Task(
                id=tid,
                job=j,
                block=tid,
                size_mib=cfg.block_mib,
                compute_s=c,
                release=job_release[j]
            ))
            tid += 1
            
    return Workload(cfg=cfg, rack_of=rack_of, blocks=blocks, tasks=tasks, job_release=job_release)

class BaseScheduler:
    def __init__(self, name: str):
        self.name = name
    def pick_worker(self, task: Task, wl: Workload, free_slots: List[int], now: float) -> int:
        raise NotImplementedError
    def wakeup_time(self, task: Task, now: float) -> float:
        return float('inf')

class BlindScheduler(BaseScheduler):
    def __init__(self):
        super().__init__("blind")
        self.next_w = 0
    def pick_worker(self, task: Task, wl: Workload, free_slots: List[int], now: float) -> int:
        n = len(free_slots)
        for i in range(n):
            w = (self.next_w + i) % n
            if free_slots[w] > 0:
                self.next_w = (w + 1) % n
                return w
        return -1

class AwareScheduler(BaseScheduler):
    def __init__(self):
        super().__init__("aware")
    def pick_worker(self, task: Task, wl: Workload, free_slots: List[int], now: float) -> int:
        best = -1
        rank = 3
        reps = wl.blocks[task.block]
        for w in range(len(free_slots)):
            if free_slots[w] <= 0:
                continue
            r = int(classify(wl, w, reps))
            if r < rank:
                rank = r
                best = w
                if r == 0:
                    break
        return best

class DelayScheduler(BaseScheduler):
    def __init__(self, delay_s: float):
        super().__init__("delay")
        self.D = delay_s
        self.since = {}
    def pick_worker(self, task: Task, wl: Workload, free_slots: List[int], now: float) -> int:
        if task.id not in self.since:
            self.since[task.id] = now
        waited = now - self.since[task.id]
        reps = wl.blocks[task.block]
        node, rack, off = -1, -1, -1
        for w in range(len(free_slots)):
            if free_slots[w] <= 0:
                continue
            loc = classify(wl, w, reps)
            if loc == Locality.NODE_LOCAL and node < 0:
                node = w
            elif loc == Locality.RACK_LOCAL and rack < 0:
                rack = w
            elif loc == Locality.OFF_RACK and off < 0:
                off = w
            if node >= 0:
                break
        if node >= 0:
            return node
        if waited >= self.D and rack >= 0:
            return rack
        if waited >= 2 * self.D and off >= 0:
            return off
        return -1
    def wakeup_time(self, task: Task, now: float) -> float:
        if task.id not in self.since:
            return float('inf')
        waited = now - self.since[task.id]
        if waited < self.D:
            return self.since[task.id] + self.D
        if waited < 2 * self.D:
            return self.since[task.id] + 2 * self.D
        return float('inf')

@dataclass
class Flow:
    task: int
    link: int
    rem: float
    cap: float

def run_simulation(wl: Workload, sched: BaseScheduler) -> SimMetrics:
    cfg = wl.cfg
    # Events: (time, seq, type, idx)
    # type: 0: JobArrival, 1: ReadDone, 2: TaskFinish, 3: Wakeup
    pq = []
    seq = 0
    for j, rel in enumerate(wl.job_release):
        heapq.heappush(pq, (rel, seq, 0, j))
        seq += 1
        
    free_slots = [cfg.slots] * cfg.workers
    slot_busy = [[False] * cfg.slots for _ in range(cfg.workers)]
    free_total = cfg.workers * cfg.slots
    ready = []  # list of task IDs
    
    m = SimMetrics()
    m.records = [TaskRecord(task_id=t.id, job=t.job, size_mib=t.size_mib) for t in wl.tasks]
    job_done = [0.0] * len(wl.job_release)
    flows: List[Flow] = []
    wakeups = set()
    finished = 0
    now = 0.0
    busy = 0.0
    
    def begin_compute(tid: int, t_now: float):
        r = m.records[tid]
        r.read_end = t_now
        r.finish = t_now + wl.tasks[tid].compute_s
        nonlocal seq
        heapq.heappush(pq, (r.finish, seq, 2, tid))
        seq += 1

    def dispatch():
        nonlocal free_total, seq
        i = 0
        while i < len(ready) and free_total > 0:
            tid = ready[i]
            t = wl.tasks[tid]
            w = sched.pick_worker(t, wl, free_slots, now)
            if w < 0:
                i += 1
                continue
            ready.pop(i)
            free_slots[w] -= 1
            s_idx = next(s for s in range(cfg.slots) if not slot_busy[w][s])
            slot_busy[w][s_idx] = True
            free_total -= 1
            loc = classify(wl, w, wl.blocks[t.block])
            r = m.records[tid]
            r.worker = w
            r.slot = s_idx
            r.start = now
            r.locality = loc
            
            if loc == Locality.NODE_LOCAL:
                m.node_local += 1
                m.node_mib += t.size_mib
            elif loc == Locality.RACK_LOCAL:
                m.rack_local += 1
                m.rack_mib += t.size_mib
                m.remote_mib += t.size_mib
            else:
                m.off_rack += 1
                m.off_mib += t.size_mib
                m.remote_mib += t.size_mib
                m.cross_mib += t.size_mib
                
            if loc == Locality.NODE_LOCAL or not cfg.shared_net:
                t_read = read_time(cfg, loc, t.size_mib)
                heapq.heappush(pq, (now + t_read, seq, 1, tid))
                seq += 1
            elif loc == Locality.RACK_LOCAL:
                flows.append(Flow(tid, 1 + wl.rack_of[w], t.size_mib, cfg.rack_bw))
            else:
                flows.append(Flow(tid, 0, t.size_mib, cfg.cross_bw))
                
        if free_total > 0:
            for tid in ready:
                wt = sched.wakeup_time(wl.tasks[tid], now)
                if wt < float('inf') and wt > now + 1e-12 and wt not in wakeups:
                    wakeups.add(wt)
                    heapq.heappush(pq, (wt, seq, 3, -1))
                    seq += 1

    while True:
        tq = pq[0][0] if pq else float('inf')
        cnt = [0] * (1 + cfg.racks)
        for f in flows:
            cnt[f.link] += 1
            
        def flow_rate(f: Flow):
            cap = cfg.core_cap if f.link == 0 else cfg.rack_cap
            return min(f.cap, cap / cnt[f.link])
            
        tf = float('inf')
        for f in flows:
            r = flow_rate(f)
            if r > 0:
                tf = min(tf, now + f.rem / r)
                
        tn = min(tq, tf)
        if tn == float('inf'):
            break
            
        dt = tn - now
        for f in flows:
            f.rem -= flow_rate(f) * dt
        now = tn
        
        # flows that finished
        surviving_flows = []
        for f in flows:
            if f.rem <= 1e-9:
                begin_compute(f.task, now)
            else:
                surviving_flows.append(f)
        flows = surviving_flows
        
        while pq and pq[0][0] <= now + 1e-12:
            t_evt, _, evtype, idx = heapq.heappop(pq)
            if evtype == 0:  # JobArrival
                for t in wl.tasks:
                    if t.job == idx:
                        ready.append(t.id)
            elif evtype == 1:  # ReadDone
                begin_compute(idx, now)
            elif evtype == 2:  # TaskFinish
                r = m.records[idx]
                free_slots[r.worker] += 1
                slot_busy[r.worker][r.slot] = False
                free_total += 1
                busy += (r.finish - r.start)
                j = wl.tasks[idx].job
                job_done[j] = max(job_done[j], r.finish)
                finished += 1
            elif evtype == 3:  # Wakeup
                pass
                
        dispatch()
        
    first = min(wl.job_release)
    last = max(job_done) if job_done else 0.0
    m.makespan = last - first
    m.mean_turnaround = sum(job_done[j] - wl.job_release[j] for j in range(len(job_done))) / len(job_done)
    m.mean_wait = sum(r.start - wl.tasks[r.task_id].release for r in m.records) / len(m.records)
    m.mean_read_s = sum(r.read_end - r.start for r in m.records) / len(m.records)
    remote_n = m.rack_local + m.off_rack
    m.mean_remote_read_s = sum(r.read_end - r.start for r in m.records if r.locality != Locality.NODE_LOCAL) / remote_n if remote_n > 0 else 0.0
    m.utilization = busy / (m.makespan * cfg.workers * cfg.slots) if m.makespan > 0 else 0.0
    m.core_load = m.cross_mib / (cfg.core_cap * m.makespan) if (m.makespan > 0 and cfg.core_cap > 0) else 0.0
    return m
