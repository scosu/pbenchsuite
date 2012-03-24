#include <sched.h>
#include <pthread.h>
#include <stdlib.h>

long iterations;

void *yielder(void *data) {
	long i = iterations;
	while (i--) {
		sched_yield();
	}
	return NULL;
}


int main(int argc, char **argv) {
	int threads = atoi(argv[2]);
	long i = 0;
	pthread_t *pthreads = malloc(sizeof(pthread_t) * threads);
	iterations = atol(argv[1]);
	iterations = iterations / threads;
	for (; i != threads; ++i) {
		pthread_create(pthreads + i, NULL, yielder, NULL);
	}
	for (i = 0; i != threads; ++i) {
		void *ret;
		pthread_join(pthreads[i], &ret);
	}
	return 0;
}

