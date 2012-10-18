#include <sched.h>
#include <pthread.h>
#include <stdlib.h>
#include <unistd.h>
#include <stdio.h>

int shutdown;

void *yielder(void *data) {
	unsigned long i = 0;
	while (!shutdown) {
		sched_yield();
		++i;
	}
	return (void*)i;
}


int main(int argc, char **argv) {
	int threads = atoi(argv[2]);
	long i = 0;
	unsigned long long iterations = 0;
	pthread_t *pthreads = malloc(sizeof(pthread_t) * threads);
	for (; i != threads; ++i) {
		pthread_create(pthreads + i, NULL, yielder, NULL);
	}
	sleep(atol(argv[1]));
	shutdown = 1;
	for (i = 0; i != threads; ++i) {
		void *ret;
		pthread_join(pthreads[i], &ret);
		iterations += (unsigned long)ret;
	}
	printf("%llu\n", iterations);
	return 0;
}

