#include "user.h"
#include "kernel/syscall.h"

int
main(int argc, char *argv[])
{
  if(argc < 2){
    printf("usage: getcnt syscall_number\n");
    exit(1);
  }

  int n = atoi(argv[1]);
  int c = getcnt(n);
  if(c < 0){
    printf("invalid syscall number %d\n", n);
    exit(1);
  }
  printf("syscall %d has been called %d times\n", n, c);
  exit(0);
}
