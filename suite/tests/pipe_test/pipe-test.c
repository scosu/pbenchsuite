
// Author is Ingo Molnar, http://people.redhat.com/mingo/cfs-scheduler/tools/pipe-test-1m.c
// Modified for ptestsuite, added a sleep at the beginning to reduce impact of
// massive forks of this program before actually start benchmarking

#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <sys/wait.h>
#include <linux/unistd.h>

#define LOOPS 1000000

int main (void)
{
	unsigned long long t0, t1;
	int pipe_1[2], pipe_2[2];
	int m = 0, i;
	sleep(5);
	pipe(pipe_1);
	pipe(pipe_2);

	if (!fork()) {
		for (i = 0; i < LOOPS; i++) {
			read(pipe_1[0], &m, sizeof(int));
			write(pipe_2[1], &m, sizeof(int));
		}
	} else {
		for (i = 0; i < LOOPS; i++) {
			write(pipe_1[1], &m, sizeof(int));
			read(pipe_2[0], &m, sizeof(int));
		}
	}

	return 0;
}

