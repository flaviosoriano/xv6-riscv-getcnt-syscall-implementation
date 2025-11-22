#!/usr/bin/env python3
"""
Lottery Scheduler Graph Generator

This script parses the output from the lotterytest program in xv6
and generates comprehensive graphs showing the CPU time distribution 
across processes with different ticket allocations (30:20:10 ratio).

Features:
- Bar charts for actual tick counts
- Actual vs expected CPU time percentages
- Simulated time-series showing allocation over time
- Fairness analysis over time windows

Usage:
    1. Run xv6 and execute: lotterytest > output.txt
    2. Copy the output to a file
    3. Run: python3 graph_lottery.py output.txt
"""

import sys
import re
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from collections import defaultdict

def parse_output(filename):
    with open(filename, 'r') as f:
        content = f.read()
    
    processes = {}
    
    # Support both lettered (A-F) and numbered (0-9) process formats
    pattern = r'Process ([A-F]|\d+) \(PID (\d+)\): (\d+) ticks, (\d+) tickets'
    matches = re.findall(pattern, content)
    
    for match in matches:
        label, pid, ticks, tickets = match
        processes[label] = {
            'pid': int(pid),
            'ticks': int(ticks),
            'tickets': int(tickets)
        }
    
    return processes

def simulate_time_series(processes, total_ticks):
    labels = sorted(processes.keys())
    tickets = [processes[label]['tickets'] for label in labels]
    target_ticks = [processes[label]['ticks'] for label in labels]
    
    time_series = {label: [] for label in labels}
    cumulative = {label: 0 for label in labels}
    
    total_tickets = sum(tickets)
    
    np.random.seed(42)  
    for tick in range(total_ticks):
        probs = [t / total_tickets for t in tickets]
        winner_idx = np.random.choice(len(labels), p=probs)
        winner = labels[winner_idx]
        
        cumulative[winner] += 1
        
        if tick % 10 == 0 or tick == total_ticks - 1:
            for label in labels:
                time_series[label].append(cumulative[label])
    
    return time_series, list(range(0, total_ticks, 10)) + [total_ticks - 1]

def create_comprehensive_graphs(processes):
    if not processes:
        print("No process data found in output file")
        return
    
    labels = sorted(processes.keys())
    ticks = [processes[label]['ticks'] for label in labels]
    tickets = [processes[label]['tickets'] for label in labels]
    
    total_ticks = sum(ticks)
    percentages = [(t * 100 / total_ticks) if total_ticks > 0 else 0 for t in ticks]
    
    total_tickets = sum(tickets)
    expected = [(t * 100 / total_tickets) if total_tickets > 0 else 0 for t in tickets]
    
    time_series, time_points = simulate_time_series(processes, total_ticks)
    
    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
    
    # Color mapping for both lettered and numbered processes
    color_palette = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', 
                     '#e67e22', '#34495e', '#16a085', '#c0392b']
    colors = {}
    for i, label in enumerate(sorted(processes.keys(), key=lambda x: int(x) if x.isdigit() else ord(x))):
        colors[label] = color_palette[i % len(color_palette)]
    
    ax1 = fig.add_subplot(gs[0, 0])
    x = np.arange(len(labels))
    width = 0.6
    
    bars1 = ax1.bar(x, ticks, width, color=[colors[l] for l in labels], alpha=0.8, edgecolor='black')
    ax1.set_xlabel('Process', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Ticks', fontsize=11, fontweight='bold')
    ax1.set_title('CPU Time Distribution (Absolute Ticks)', fontsize=12, fontweight='bold', pad=15)
    ax1.set_xticks(x)
    ax1.set_xticklabels([f'Process {l}\n{tickets[i]} tickets' 
                         for i, l in enumerate(labels)], fontsize=10)
    ax1.grid(axis='y', alpha=0.3, linestyle='--')
    
    for i, bar in enumerate(bars1):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}\n({percentages[i]:.1f}%)',
                ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    ax2 = fig.add_subplot(gs[0, 1])
    width = 0.35
    
    bars2 = ax2.bar(x - width/2, percentages, width, label='Actual', 
                    color=[colors[l] for l in labels], alpha=0.8, edgecolor='black')
    bars3 = ax2.bar(x + width/2, expected, width, label='Expected', 
                    color='lightgray', alpha=0.8, edgecolor='black', hatch='//')
    
    ax2.set_xlabel('Process', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Percentage (%)', fontsize=11, fontweight='bold')
    ax2.set_title('CPU Time: Actual vs Expected Distribution', fontsize=12, fontweight='bold', pad=15)
    ax2.set_xticks(x)
    ax2.set_xticklabels([f'Process {l}' for l in labels], fontsize=10)
    ax2.legend(fontsize=10, loc='upper right')
    ax2.grid(axis='y', alpha=0.3, linestyle='--')
    ax2.set_ylim(0, max(max(percentages), max(expected)) * 1.2)
    
    for bars in [bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}%',
                    ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    ax3 = fig.add_subplot(gs[1, :])
    
    for label in labels:
        ax3.plot(time_points, time_series[label], marker='o', markersize=3,
                linewidth=2.5, label=f'Process {label} ({processes[label]["tickets"]} tickets)',
                color=colors[label], alpha=0.9)
    
    for i, label in enumerate(labels):
        expected_line = [t * expected[i] / 100 for t in time_points]
        ax3.plot(time_points, expected_line, linestyle='--', linewidth=1.5,
                color=colors[label], alpha=0.5)
    
    ax3.set_xlabel('Time (ticks)', fontsize=11, fontweight='bold')
    ax3.set_ylabel('Cumulative Ticks Received', fontsize=11, fontweight='bold')
    ax3.set_title('CPU Allocation Over Time (Cumulative)', fontsize=12, fontweight='bold', pad=15)
    ax3.legend(fontsize=10, loc='upper left')
    ax3.grid(True, alpha=0.3, linestyle='--')
    
    ax3.text(0.98, 0.02, 'Solid lines: Actual | Dashed lines: Expected',
            transform=ax3.transAxes, fontsize=9, ha='right', va='bottom',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    ax4 = fig.add_subplot(gs[2, 0])
    
    window_size = max(10, len(time_points) // 20)
    for i, label in enumerate(labels):
        rolling_pct = []
        for j in range(len(time_points)):
            start_idx = max(0, j - window_size)
            window_ticks = time_series[label][j] - (time_series[label][start_idx] if start_idx < j else 0)
            total_window = sum(time_series[l][j] - (time_series[l][start_idx] if start_idx < j else 0) 
                             for l in labels)
            pct = (window_ticks * 100 / total_window) if total_window > 0 else 0
            rolling_pct.append(pct)
        
        ax4.plot(time_points, rolling_pct, linewidth=2, label=f'Process {label}',
                color=colors[label], alpha=0.9)
        ax4.axhline(y=expected[i], color=colors[label], linestyle='--', 
                   linewidth=1, alpha=0.5)
    
    ax4.set_xlabel('Time (ticks)', fontsize=11, fontweight='bold')
    ax4.set_ylabel('CPU Share (%)', fontsize=11, fontweight='bold')
    ax4.set_title(f'Fairness Over Time (Rolling Window: {window_size} ticks)', 
                 fontsize=12, fontweight='bold', pad=15)
    ax4.legend(fontsize=10, loc='best')
    ax4.grid(True, alpha=0.3, linestyle='--')
    ax4.set_ylim(0, 100)
    
    ax5 = fig.add_subplot(gs[2, 1])
    
    deviations = [percentages[i] - expected[i] for i in range(len(labels))]
    colors_dev = ['green' if d >= 0 else 'red' for d in deviations]
    
    bars5 = ax5.bar(x, deviations, width, color=colors_dev, alpha=0.7, edgecolor='black')
    ax5.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax5.set_xlabel('Process', fontsize=11, fontweight='bold')
    ax5.set_ylabel('Deviation (%)', fontsize=11, fontweight='bold')
    ax5.set_title('Deviation from Expected CPU Share', fontsize=12, fontweight='bold', pad=15)
    ax5.set_xticks(x)
    ax5.set_xticklabels([f'Process {l}' for l in labels], fontsize=10)
    ax5.grid(axis='y', alpha=0.3, linestyle='--')
    
    for bar in bars5:
        height = bar.get_height()
        label_y = height if height > 0 else height
        va = 'bottom' if height > 0 else 'top'
        ax5.text(bar.get_x() + bar.get_width()/2., label_y,
                f'{height:+.2f}%',
                ha='center', va=va, fontsize=10, fontweight='bold')
    
    fig.suptitle('Lottery Scheduler: Comprehensive CPU Allocation Analysis', 
                fontsize=16, fontweight='bold', y=0.995)
    
    plt.savefig('lottery_scheduler_comprehensive.png', dpi=300, bbox_inches='tight')
    print("Comprehensive graph saved as 'lottery_scheduler_comprehensive.png'")
    plt.close('all')
    
    print("\n" + "=" * 70)
    print("LOTTERY SCHEDULER ANALYSIS SUMMARY")
    print("=" * 70)
    for label in labels:
        p = processes[label]
        pct = (p['ticks'] * 100 / total_ticks) if total_ticks > 0 else 0
        exp_pct = (p['tickets'] * 100 / total_tickets) if total_tickets > 0 else 0
        deviation = pct - exp_pct
        print(f"\nProcess {label}:")
        print(f"  Tickets:        {p['tickets']}")
        print(f"  Ticks:          {p['ticks']}")
        print(f"  Actual %:       {pct:.2f}%")
        print(f"  Expected %:     {exp_pct:.2f}%")
        print(f"  Deviation:      {deviation:+.2f}%")
    
    print(f"\n{'-' * 70}")
    print(f"Total ticks:      {total_ticks}")
    ticket_ratio = ':'.join(str(t) for t in tickets)
    print(f"Ticket ratio:     {ticket_ratio}")
    
    # Calculate actual ratio based on the minimum tick count
    min_ticks = min(ticks)
    if min_ticks > 0:
        actual_ratio_parts = [t // min_ticks for t in ticks[:-1]]
        actual_ratio = ':'.join(str(r) for r in actual_ratio_parts) + ':1'
        print(f"Actual ratio:     {actual_ratio}")
    print("=" * 70)

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 graph_lottery.py <output_file>")
        print("\nExample:")
        print("  1. In xv6: lotterytest > output.txt")
        print("  2. Copy output.txt from xv6 to host")
        print("  3. python3 graph_lottery.py output.txt")
        sys.exit(1)
    
    filename = sys.argv[1]
    
    try:
        processes = parse_output(filename)
        create_comprehensive_graphs(processes)
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
