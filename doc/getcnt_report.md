getcnt syscall — implementation report
=====================================

This document describes the changes made to xv6 to implement a `getcnt` syscall that returns how many times a given syscall number has been invoked.

I. Summary of the four key modifications
---------------------------------------
1) Add per-syscall counting logic in `kernel/syscall.c`.
2) Add the `SYS_getcnt` syscall number in `kernel/syscall.h`.
3) Implement the `getcnt` kernel handler and wire it into the syscall table (`syscalls[]`).
4) Add a userland program `user/getcnt.c`, update `user/usys.pl` and `Makefile` so user programs can call `getcnt` and the program is included in the disk image.

For each change below I include the `git diff` output and a discussion.

II. Diff and discussion — syscall counting data structure
--------------------------------------------------------

=== DIFF: kernel/syscall.c ===

```diff
@@
 extern uint64 sys_close(void);
+extern uint64 sys_getcnt(void);
@@
 [SYS_link]    sys_link,
 [SYS_mkdir]   sys_mkdir,
 [SYS_close]   sys_close,
+[SYS_getcnt]  sys_getcnt,
 };
 
+// Per-syscall invocation counters. Incremented on each syscall dispatch.
+// Sized to the number of entries in the `syscalls` table.
+static uint64 syscalls_count[NELEM(syscalls)];
+
+// Return the number of times the syscall with the given number
+// has been invoked. Takes one int argument: the syscall number.
+uint64
+sys_getcnt(void)
+{
+  int n;
+  argint(0, &n);
+  if(n < 0 || n >= NELEM(syscalls))
+    return -1;
+  return syscalls_count[n];
+}
@@
   num = p->trapframe->a7;
   if(num > 0 && num < NELEM(syscalls) && syscalls[num]) {
+    // Increment the syscall counter for this syscall number.
+    syscalls_count[num]++;
+
     // Use num to lookup the system call function for num, call it,
     // and store its return value in p->trapframe->a0
     p->trapframe->a0 = syscalls[num]();
```

Discussion
- Data structure: `static uint64 syscalls_count[NELEM(syscalls)]` — a simple static array where each index is the syscall number. `NELEM(syscalls)` sizes the array to match the number of function pointers in the `syscalls` table, ensuring coverage for all valid syscall numbers.
- Choice rationale: an array is compact, constant-time indexed, and straightforward to update at syscall entry.
- Possible issues: increments are not synchronized with a lock or atomic operation. On an SMP machine with multiple harts running simultaneously, concurrent increments have a race. For the assignment and simple tests this is acceptable, but a production-quality implementation would use per-cpu counters or a small spinlock around increments.

III. Diff and discussion — adding syscall number
------------------------------------------------

=== DIFF: kernel/syscall.h ===

```diff
@@
 #define SYS_link   19
 #define SYS_mkdir  20
 #define SYS_close  21
+#define SYS_getcnt 22
```

Discussion
- We added `SYS_getcnt` as syscall number 22. This follows the existing numbering convention (existing syscalls run 1..21). The exact number isn't special except that it must not collide with existing syscall numbers and that the `syscalls[]` table maps it to `sys_getcnt`.

IV. Diff and discussion — how the data structure is updated
-----------------------------------------------------------

The `syscalls_count` array is updated in `syscall()` in `kernel/syscall.c`. The relevant diff is shown above. The increment occurs immediately after validating the `num` and before dispatching the syscall handler:

```c
if (num > 0 && num < NELEM(syscalls) && syscalls[num]) {
  syscalls_count[num]++;
  p->trapframe->a0 = syscalls[num]();
}
```

Discussion
- Incrementing before the syscall handler ensures the counter reflects the invocation even if the handler fails or panics.
- The function `sys_getcnt()` reads the counter via a simple read of `syscalls_count[n]` and returns it to user space.
- Error handling: `sys_getcnt()` returns -1 for invalid syscall numbers (out of range).

V. Diff and discussion — userland wiring and program
----------------------------------------------------

=== DIFF: user/usys.pl ===

```diff
@@
 entry("sbrk");
 entry("pause");
 entry("uptime");
+entry("getcnt");
```

Discussion
- Adding `entry("getcnt")` to `user/usys.pl` makes `usys.S` include a user stub for the syscall so user programs can call `getcnt()` as a regular C function.

=== DIFF: Makefile ===

```diff
@@
 	$U/_wc\
 	$U/_zombie\
+	$U/_getcnt\
 	$U/_logstress\
```

Discussion
- Adding `$U/_getcnt` to `UPROGS` ensures the `getcnt` user program is built and placed into `fs.img`.

=== DIFF: user/user.h ===

```diff
+#define SBRK_ERROR ((char *)-1)
+
+typedef unsigned int uint;
+
+struct stat;
@@
 int uptime(void);
+int getcnt(int);
```

Discussion
- Added `int getcnt(int);` so user programs can call the syscall, and a `uint` typedef for user headers to compile cleanly in the present build environment.

VI. Diff listing (collected)
---------------------------

I collected diffs for the modified files (printed above). The four modifications showcased are:
1) `kernel/syscall.c` — counting array, increment, `sys_getcnt` implementation, syscall wiring.
2) `kernel/syscall.h` — new syscall number `SYS_getcnt`.
3) `user/usys.pl` and `user/user.h` — user syscall stub generation and declaration.
4) `user/getcnt.c` and `Makefile` — added user test program and included it in `UPROGS`.

VII. How I tested the syscall
----------------------------
- I added a simple user program `user/getcnt.c` which:
  - Reads a command-line argument `n` (the syscall number),
  - Calls `getcnt(n)` and prints the result.
- Steps to reproduce locally:
  1. Build xv6 and the fs image:
     ```bash
     make
     make qemu
     ```
  2. In the xv6 shell, run the program:
     ```sh
     getcnt 1       # prints how many times syscall 1 (fork) has been called
     getcnt 22      # prints how many times getcnt itself (22) has been called
     ```
  3. Re-run `getcnt 22` multiple times and you will see the count increment by 1 each run.

VIII. Remarks and possible improvements
--------------------------------------
- Atomicity: use per-cpu counters or lock-protected increments to avoid lost increments on SMP.
- Visibility: for convenience, provide a bulk syscall to fetch all syscall counts at once, or add a shell builtin to query counters by name.
- Permissions: consider restricting access to `getcnt` if you don't want unprivileged programs to observe kernel statistics.

IX. Files to submit
-------------------
- A zip archive of the repository (complete modified xv6).
- This documentation converted to PDF (instructions below).

Converting this document to PDF
-------------------------------
If you have `pandoc` installed you can convert:

```bash
pandoc doc/getcnt_report.md -o doc/getcnt_report.pdf
```

If `pandoc` is not available, you can print the Markdown to PDF from most editors, or I can generate the PDF for you if you request it.


---
End of report
