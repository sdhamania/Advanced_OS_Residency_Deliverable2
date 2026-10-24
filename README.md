# Advanced Shell Deliverable 2 Process Scheduling

This C++17 project extends the Deliverable 1 POSIX shell with an internal scheduler simulator. The original built-ins, external execution, process groups, foreground/background job control, and terminal handling remain available. `sched` manages simulated CPU jobs independently of host OS processes; it does not reschedule external executables or replace the host kernel's scheduler.

## Build and verify

```bash
make
make test
./build/os-shell
```

Requires a C++17 compiler, Make, Python 3 for tests, and a POSIX terminal (macOS or Linux). Verified execution results are macOS-only. The strict default build uses `-Wall -Wextra -Wpedantic -Werror`. The scheduler unit suite also passes AddressSanitizer and UndefinedBehaviorSanitizer; Clang static analysis reports no scheduler findings. The test target runs parser assertions, scheduler unit tests, the 20 inherited shell integration tests, and four scheduler integration tests. One scheduler integration test checks 40 generated workloads under both algorithms (80 comparisons) against an independent unit-at-a-time reference model.

## Scheduling commands

| Command | Meaning |
|---|---|
| `sched help` | Print syntax and conventions. |
| `sched add ID BURST PRIORITY [ARRIVAL]` | Add a simulated process; default arrival is 0. |
| `sched list` | Show the persistent workload. |
| `sched reset` | Clear the workload. |
| `sched run rr QUANTUM [TICK_MS]` | Run Round-Robin with a configurable quantum. |
| `sched run priority [TICK_MS]` | Run preemptive priority scheduling. |

IDs contain 1–32 letters, digits, underscores, or hyphens. They are simulated identifiers, not host PIDs. A smaller nonnegative priority number means higher priority. Burst, arrival, quantum, and all reported scheduling metrics use integer simulated time units. By default one simulated unit waits 10 real milliseconds with `std::this_thread::sleep_for`. `TICK_MS=0` disables waiting for fast tests and yields the same logical schedule. Idle intervals also use the timer. Printed `wall_ms` is measured separately with `steady_clock` and includes trace and timer overhead.

Workloads persist across runs, and each run starts at simulated time 0 with fresh remaining bursts and metrics. This makes comparisons fair: changing the quantum or algorithm does not accidentally reuse already-completed jobs. Duplicate IDs, invalid arguments, and oversized workloads fail without changing the workload. Scheduling commands reject `&`, since a child copy cannot change the parent scheduler state.

### Example with timed higher-priority arrivals

Enter each line inside the custom shell:

```text
sched add A 6 3 0
sched add B 2 1 2
sched add C 1 1 2
sched add D 1 3 3
sched list
sched run rr 2 10
sched run priority 10
```

At simulated t=2, B and C arrive while A still has work. Under priority scheduling, B immediately preempts A at that event boundary. B precedes C because equal priorities follow arrival order and then insertion order. A resumes before D because A arrived earlier. Under Round-Robin, new arrivals join the tail; an arrival exactly at slice expiry is admitted before the current process is requeued. A process finishing early yields immediately rather than using an entire quantum.

The priority ready queue is `std::priority_queue` (heap). Priority ties use original arrival and insertion order, including after a higher-priority job interrupts an earlier job. Equal-priority arrivals do not preempt. The Round-Robin ready queue is `std::deque`. Timed execution sleeps only until the next arrival, quantum expiry, or completion; a priority arrival never waits for an entire lower-priority burst to finish. The shell admits predeclared arrivals during the run. It does not accept live command input while the foreground simulation is executing, and makes no hard real-time claim about physical timer latency.

## Metrics and evidence

For each process:

- Turnaround = completion − arrival.
- Waiting = turnaround − CPU burst.
- Response = first dispatch − arrival.

Waiting includes time spent ready after preemption. The simulator models a single CPU, CPU-only bursts, and zero dispatch overhead, with no I/O blocking. These assumptions make the formulas valid. `Running` in an inherited host job listing remains separate from simulated dispatch state.

To reproduce the same four comparisons (RR quantum 1, 2, 4 and priority):

```bash
python3 scripts/collect_scheduling_evidence.py
```

Actual shell output is saved in `evidence/*.txt`; structured results are in `evidence/scheduling_metrics.json`. Commands are saved in `examples/*.commands`, usable in batch mode, for example:

```bash
./build/os-shell < examples/priority.commands
```

These are genuine executed text records, not native screenshots. See `screenshots/CAPTURE_INSTRUCTIONS.txt` for the required actual Terminal captures. The report should distinguish algorithm metrics in simulated units from measured elapsed wall time. Small quanta increase dispatch counts in this model; production scheduling also incurs switch costs that this simulator does not model. Static priority may starve low-priority tasks under an unbounded stream of high-priority arrivals; the finite workload always completes.

## Input and resource limits

At most 1,000 processes; burst 1–100,000; arrival and priority 0–100,000; quantum 1–100,000; tick 0–1,000 ms; total burst at most 1,000,000 units. The conservative requested-timer bound `(total burst + latest arrival) * tick_ms` must not exceed 30,000 ms; use fast mode for larger logical workloads. Host scheduling and output may add overhead beyond requested timer sleep. Integer bounds prevent overflow. No authentication, pipelines, or virtual memory is introduced in this deliverable.

## Layout

```text
include/    D1 headers and scheduler model/interface
src/        D1 shell, parser, and internal scheduler
tests/      Original regression tests and scheduling tests
examples/   Reproducible shell command input
evidence/   Actual text traces and structured metrics
report/     APA report and its builder
screenshots/ Four actual Terminal captures and capture instructions
```

## Local repository handoff

The local Git remote is configured for `sdhamania/Advanced_OS_Residency_Deliverable2`. Nothing is pushed by this project tooling. An empty public repository has been created at https://github.com/sdhamania/Advanced_OS_Residency_Deliverable2. The source remains local and uncommitted; no push has been performed.

## Inherited shell commands

`cd`, `pwd`, `exit`, `echo`, `clear`, `ls`, `cat`, `mkdir`, `rmdir`, `rm`,
`touch`, and `kill` retain Deliverable 1 behavior. `jobs`, `fg`, and `bg`
manage real external-command jobs; append `&` for background execution.
Foreground external programs receive terminal Ctrl-C/Ctrl-Z signals. The
parser supports quotes and escapes, but pipelines, redirection, command lists,
variable expansion, globbing, and command substitution remain outside these
deliverables. Simulation commands execute in the parent and reject `&`.

## Current submission status

Source, tests, executed text evidence, and the APA 7 report are prepared.
Four actual Terminal screenshots are included under screenshots/ and embedded
in Appendix B. Quantum 2 and the final priority run use 10 ms/unit; the
quantum-1 and quantum-4 captures use fast mode (tick_ms=0). Their logical
metrics match the recorded comparison; wall times come from separate runs.
Text recordings remain supplementary evidence from automated execution. Report rebuilding requires
Python 3 with python-docx; compiling and running the shell require no Python
third-party packages. The report cover uses the preparation date October 24,
2026; confirm the course due date and personal reflections before submission.
