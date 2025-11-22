#include "kernel/types.h"
#include "kernel/stat.h"
#include "kernel/pstat.h"
#include "user/user.h"

// Test the lottery scheduler by creating multiple processes with different ticket counts
// and observing their CPU time allocation over a period
// 
// NOTE: For best results, run on a single CPU (CPUS=1 in Makefile)
// With multiple CPUs, each process may monopolize one CPU, defeating the lottery scheduler

#define NUM_PROCESSES 6  // Create more processes than typical CPU count
#define TICKET_A 30
#define TICKET_B 20
#define TICKET_C 10
#define TICKET_D 30
#define TICKET_E 20
#define TICKET_F 10
#define TEST_DURATION 2000  // Time units to run the test

// Busy-wait function to consume CPU cycles
void
spin(void)
{
  int i;
  for(i = 0; i < 10000000; i++) {
    asm volatile("nop");  // Prevent compiler optimization
  }
}

int
main(int argc, char *argv[])
{
  int pids[NUM_PROCESSES];
  int tickets[NUM_PROCESSES] = {TICKET_A, TICKET_B, TICKET_C, TICKET_D, TICKET_E, TICKET_F};
  struct pstat ps;
  
  printf("Lottery Scheduler Test\n");
  printf("======================\n");
  printf("Creating %d processes to test lottery scheduler\n", NUM_PROCESSES);
  printf("Ticket allocation: 30, 20, 10, 30, 20, 10\n");
  printf("Expected ratio groups: 3:2:1 (repeated twice)\n\n");
  
  // Create child processes
  for(int i = 0; i < NUM_PROCESSES; i++) {
    pids[i] = fork();
    if(pids[i] == 0) {
      // Child process
      settickets(tickets[i]);
      
      // Busy loop to consume CPU
      for(;;) {
        spin();
      }
      exit(0);  // Never reached
    }
    printf("Process %d (PID %d): %d tickets\n", i, pids[i], tickets[i]);
  }
  
  // Let the processes run for a while
  printf("\nRunning test for %d time units...\n", TEST_DURATION);
  pause(TEST_DURATION);
  
  // Get process information
  if(getpinfo(&ps) < 0) {
    printf("getpinfo failed\n");
    for(int i = 0; i < NUM_PROCESSES; i++) {
      kill(pids[i]);
    }
    for(int i = 0; i < NUM_PROCESSES; i++) {
      wait(0);
    }
    exit(1);
  }
  
  // Find and print statistics for our test processes
  printf("\n======================\n");
  printf("Test Results:\n");
  printf("======================\n");
  
  int process_ticks[NUM_PROCESSES];
  int total_ticks = 0;
  
  // Initialize
  for(int i = 0; i < NUM_PROCESSES; i++) {
    process_ticks[i] = 0;
  }
  
  // Collect ticks for each process
  for(int i = 0; i < 64; i++) {  // NPROC is typically 64
    if(ps.inuse[i]) {
      for(int j = 0; j < NUM_PROCESSES; j++) {
        if(ps.pid[i] == pids[j]) {
          process_ticks[j] = ps.ticks[i];
          total_ticks += ps.ticks[i];
          printf("Process %d (PID %d): %d ticks, %d tickets\n", 
                 j, ps.pid[i], ps.ticks[i], ps.tickets[i]);
          break;
        }
      }
    }
  }
  
  // Calculate and display ratios
  if(total_ticks > 0) {
    printf("\n======================\n");
    printf("Tick Distribution:\n");
    printf("======================\n");
    
    // Group by ticket count and calculate totals
    int ticks_30 = process_ticks[0] + process_ticks[3];
    int ticks_20 = process_ticks[1] + process_ticks[4];
    int ticks_10 = process_ticks[2] + process_ticks[5];
    
    printf("Processes with 30 tickets: %d ticks (%d%%)\n", 
           ticks_30, (ticks_30 * 100) / total_ticks);
    printf("Processes with 20 tickets: %d ticks (%d%%)\n", 
           ticks_20, (ticks_20 * 100) / total_ticks);
    printf("Processes with 10 tickets: %d ticks (%d%%)\n", 
           ticks_10, (ticks_10 * 100) / total_ticks);
    
    printf("\nExpected: 50%%, 33%%, 17%% (3:2:1 ratio)\n");
    
    // Calculate actual ratio
    if(ticks_10 > 0) {
      int ratio_30 = ticks_30 / ticks_10;
      int ratio_20 = ticks_20 / ticks_10;
      printf("Actual ratio: %d:%d:1\n", ratio_30, ratio_20);
    }
    
    // Individual percentages
    printf("\nIndividual process percentages:\n");
    for(int i = 0; i < NUM_PROCESSES; i++) {
      printf("  Process %d: %d%% (expected ~%d%%)\n", 
             i, 
             (process_ticks[i] * 100) / total_ticks,
             (tickets[i] * 100) / (TICKET_A + TICKET_B + TICKET_C + TICKET_D + TICKET_E + TICKET_F));
    }
  }
  
  // Clean up: kill child processes
  printf("\nCleaning up...\n");
  for(int i = 0; i < NUM_PROCESSES; i++) {
    kill(pids[i]);
  }
  
  for(int i = 0; i < NUM_PROCESSES; i++) {
    wait(0);
  }
  
  printf("Test completed.\n");
  exit(0);
}
