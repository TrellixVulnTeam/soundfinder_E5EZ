#include <stdio.h>
#include <string.h>
#include <unistd.h>

#include "driver/gpio.h"
#include "esp_log.h"
#include "esp_sleep.h"
#include "esp_system.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "sdkconfig.h"

static void sampling_timer_callback(void* arg);
static void oneshot_timer_callback(void* arg);

static const char* TAG = "whereisthesound";

#define LED_PIN GPIO_SEL_5

static int i = 0;

void app_main(void) {
	// configure led
	i = 0;
	gpio_pad_select_gpio(LED_PIN);
	gpio_set_direction(LED_PIN, GPIO_MODE_OUTPUT);

	// create timer
	const esp_timer_create_args_t sampling_timer_args = {
		.callback = &sampling_timer_callback,
		.name = "sampling_timer"};
	esp_timer_handle_t sampling_timer;
	ESP_ERROR_CHECK(esp_timer_create(&sampling_timer_args, &sampling_timer));

	// start timer
	ESP_ERROR_CHECK(esp_timer_start_periodic(sampling_timer, 40));	// period in microseconds (500000us ==> 0.5s ==> 2Hz, 40us ==> 25kHz)
	// ESP_LOGI(TAG, "Started timers, time since boot: %lld us", esp_timer_get_time());

	// continue
	while (1) {
		usleep(20000);
	}

	/*
	for (int i = 0; i < 5; ++i) {
		ESP_ERROR_CHECK(esp_timer_dump(stdout));
		usleep(2000000);
	}
	usleep(2000000);
	ESP_ERROR_CHECK(esp_timer_stop(sampling_timer));
	ESP_ERROR_CHECK(esp_timer_delete(sampling_timer));
	ESP_LOGI(TAG, "Stopped and deleted timers");
	*/
}

static void sampling_timer_callback(void* arg) {
	// int64_t time_since_boot = esp_timer_get_time();
	// ESP_LOGI(TAG, "Sampling timer called, time since boot: %lld us", time_since_boot);

	if (i == 0)
		i = 1;
	else
		i = 0;
	gpio_set_level(LED_PIN, i);
}