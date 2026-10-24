#!/usr/bin/env python3
"""Execute the real shell and save reproducible traces and scheduling metrics."""
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKLOAD = [dict(id='A', burst=6, priority=3, arrival=0),
            dict(id='B', burst=2, priority=1, arrival=2),
            dict(id='C', burst=1, priority=1, arrival=2),
            dict(id='D', burst=1, priority=3, arrival=3)]
TICK_MS = 10


def collect():
    evidence = ROOT / 'evidence'
    evidence.mkdir(exist_ok=True)
    cases = {}
    for label, mode in [('rr_q1', 'rr 1'), ('rr_q2', 'rr 2'), ('rr_q4', 'rr 4'), ('priority', 'priority')]:
        setup = ''.join(f"sched add {p['id']} {p['burst']} {p['priority']} {p['arrival']}\n" for p in WORKLOAD)
        commands = setup + f'sched run {mode} {TICK_MS}\nexit 0\n'
        result = subprocess.run([str(ROOT/'build/os-shell')], input=commands, text=True,
                                capture_output=True, timeout=10)
        if result.returncode or result.stderr:
            raise RuntimeError(result.stderr or 'shell failed')
        (evidence/f'{label}.txt').write_text(result.stdout)
        (ROOT/'examples'/f'{label}.commands').write_text(commands)
        active, metrics = False, []
        keys = ['arrival', 'burst', 'priority', 'first_start', 'completion', 'waiting', 'turnaround', 'response']
        for line in result.stdout.splitlines():
            if line.startswith('ID ARRIVAL BURST PRIORITY FIRST COMPLETION WAIT TURNAROUND RESPONSE'):
                active = True
            elif active and line.startswith('AVERAGE'):
                active = False
            elif active:
                fields = line.split()
                metrics.append(dict(id=fields[0], **dict(zip(keys,map(int,fields[1:])))))
        summary = re.search(r'SUMMARY finish=(\d+) dispatches=(\d+) preemptions=(\d+) wall_ms=([\d.]+)',result.stdout)
        if len(metrics) != len(WORKLOAD) or summary is None:
            raise RuntimeError('missing scheduling metrics')
        cases[label] = dict(command=f'sched run {mode} {TICK_MS}', tick_ms=TICK_MS,
                            metrics=metrics,
                            average={key:sum(m[key] for m in metrics)/len(metrics)
                                     for key in ['waiting','turnaround','response']},
                            finish=int(summary[1]), dispatches=int(summary[2]),
                            preemptions=int(summary[3]), wall_ms=float(summary[4]))
    data = dict(units='simulated CPU units', timer_ms_per_unit=TICK_MS,
                note='Logical metrics exclude host timer/output overhead; wall_ms is separately measured.',
                workload=WORKLOAD, cases=cases)
    path=evidence/'scheduling_metrics.json'
    path.write_text(json.dumps(data,indent=2)+'\n')
    print(path)
    for label, case in cases.items():
        print(label,case['average'],'dispatches=',case['dispatches'],'preemptions=',case['preemptions'])


if __name__=='__main__':
    collect()
