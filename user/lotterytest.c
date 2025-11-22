#include "kernel/types.h"
#include "kernel/stat.h"
#include "kernel/pstat.h"
#include "user/user.h"

// Test the lottery scheduler by creating 3 processes with 30:20:10 ticket ratio
// and observing their CPU time allocation over a period

#define TICKET_A 30
#define TICKET_B 20
#define TICKET_C 10
#define TEST_DURATION 1000  // Time units to run the test

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
  int pid_a, pid_b, pid_c;
  struct pstat ps;
  
  printf("Lottery Scheduler Test\n");
  printf("======================\n");
  printf("Creating 3 processes with ticket ratio 30:20:10\n\n");
  
  // Create Process A (30 tickets)
  pid_a = fork();
  if(pid_a == 0) {
    // Child A
    settickets(TICKET_A);
    
    // Busy loop to consume CPU
    for(;;) {
      spin();
    }
    exit(0);  // Never reached
  }
  
  // Create Process B (20 tickets)
  pid_b = fork();
  if(pid_b == 0) {
    // Child B
    settickets(TICKET_B);
    
    // Busy loop to consume CPU
    for(;;) {
      spin();
    }
    exit(0);  // Never reached
  }
  
  // Create Process C (10 tickets)
  pid_c = fork();
  if(pid_c == 0) {
    // Child C
    settickets(TICKET_C);
    
    // Busy loop to consume CPU
    for(;;) {
      spin();
    }
    exit(0);  // Never reached
  }
  
  // Parent process: monitor and collect statistics
  printf("Process A (PID %d): %d tickets\n", pid_a, TICKET_A);
  printf("Process B (PID %d): %d tickets\n", pid_b, TICKET_B);
  printf("Process C (PID %d): %d tickets\n\n", pid_c, TICKET_C);
  
  // Let the processes run for a while
  printf("Running test for %d time units...\n", TEST_DURATION);
  pause(TEST_DURATION);
  
  // Get process information
  if(getpinfo(&ps) < 0) {
    printf("getpinfo failed\n");
    kill(pid_a);
    kill(pid_b);
    kill(pid_c);
    wait(0);
    wait(0);
    wait(0);
    exit(1);
  }
  
  // Find and print statistics for our test processes
  printf("\n======================\n");
  printf("Test Results:\n");
  printf("======================\n");
  
  int ticks_a = 0, ticks_b = 0, ticks_c = 0;
  
  for(int i = 0; i < 64; i++) {  // NPROC is typically 64
    if(ps.inuse[i]) {
      if(ps.pid[i] == pid_a) {
        ticks_a = ps.ticks[i];
        printf("Process A (PID %d): %d ticks, %d tickets\n", 
               ps.pid[i], ps.ticks[i], ps.tickets[i]);
      } else if(ps.pid[i] == pid_b) {
        ticks_b = ps.ticks[i];
        printf("Process B (PID %d): %d ticks, %d tickets\n", 
               ps.pid[i], ps.ticks[i], ps.tickets[i]);
      } else if(ps.pid[i] == pid_c) {
        ticks_c = ps.ticks[i];
        printf("Process C (PID %d): %d ticks, %d tickets\n", 
               ps.pid[i], ps.ticks[i], ps.tickets[i]);
      }
    }
  }
  
  // Calculate ratios
  int total_ticks = ticks_a + ticks_b + ticks_c;
  if(total_ticks > 0) {
    printf("\nTick Ratios:\n");
    printf("Process A: %d%% (expected 50%%)\n", (ticks_a * 100) / total_ticks);
    printf("Process B: %d%% (expected 33%%)\n", (ticks_b * 100) / total_ticks);
    printf("Process C: %d%% (expected 17%%)\n", (ticks_c * 100) / total_ticks);
    
    printf("\nExpected ratio: 30:20:10 = 3:2:1\n");
    if(ticks_b > 0) {
      printf("Actual ratio: %d:%d:%d\n", 
             ticks_a / ticks_c, ticks_b / ticks_c, 1);
    }
  }
  
  // Clean up: kill child processes
  printf("\nCleaning up...\n");
  kill(pid_a);
  kill(pid_b);
  kill(pid_c);
  
  wait(0);
  wait(0);
  wait(0);
  
  printf("Test completed.\n");
  exit(0);
}
