#define PF1       (*((volatile uint32_t *)0x40025008))
#define PF2       (*((volatile uint32_t *)0x40025010))
#define PF3       (*((volatile uint32_t *)0x40025020))
	
#define TIME_SERIES_LENGTH 20		// timer is 100Hz, last 300 samples is the last 3 seconds
																	// 100 Hz vs 500 samples --> (1 sec / 100 cycles) * 300 cycles = 3 sec

#define TIME_SERIES_FILTER_LENGTH 3  // TIME_SERIES_LENGTH / 10

