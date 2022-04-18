#include "driver/adc.h"
#include "hal/adc_hal.h"
#include "soc/adc_channel.h"

#define PROFILE_PIN 17
#define MIC_A_PIN 1
#define MIC_A_CHAN ADC1_GPIO35_CHANNEL
#define MIC_B_PIN 2
#define MIC_B_CHAN ADC1_GPIO36_CHANNEL

#define SAMPLING_RATE_KHZ 25
#define BUS_CLOCK_MHZ 80
#define TIMER_DIVIDER 80
#define FRAME_SIZE 100

typedef struct Message {
  uint16_t ch_1;  // sample value from mic A
  uint16_t ch_2;  // sample value from mic B
} message_t;
volatile message_t frame_msgs[FRAME_SIZE];

volatile uint8_t profile_val = 0;
volatile uint16_t interruptCounter = 0;
volatile uint32_t frameCounter = 0;
volatile uint32_t framePointer = 0;
 
hw_timer_t * timer = NULL;
portMUX_TYPE timerMux = portMUX_INITIALIZER_UNLOCKED;

uint16_t IRAM_ATTR local_adc1_read(int channel) {
  uint16_t value = 0;
  adc_hal_convert(ADC_UNIT_1, MIC_A_CHAN, &value);
  return value;
}
 
void IRAM_ATTR onTimer() {
  portENTER_CRITICAL_ISR(&timerMux);
  
  interruptCounter++;

  int x = local_adc1_read(MIC_A_CHAN);

//  frame_msgs[framePointer].ch_1 = analogRead(MIC_A_CHAN);
//  frame_msgs[framePointer].ch_2 = analogRead(MIC_B_CHAN);

  framePointer++;
  if (framePointer >= FRAME_SIZE)
    framePointer = 0;
  
  if (profile_val == LOW) profile_val = HIGH;
  else profile_val = LOW;
  digitalWrite(PROFILE_PIN, profile_val);
  
  portEXIT_CRITICAL_ISR(&timerMux);
}
 
void setup() {
 
  Serial.begin(115200);
  
  pinMode(MIC_A_PIN, INPUT);
  pinMode(MIC_B_PIN, INPUT);

  profile_val = LOW;
  pinMode(PROFILE_PIN, OUTPUT);
  digitalWrite(PROFILE_PIN, profile_val);

  interruptCounter = 0;
  frameCounter = 0;
  framePointer = 0;

  int adc_period = (BUS_CLOCK_MHZ * 1000) / (TIMER_DIVIDER * SAMPLING_RATE_KHZ);
  timer = timerBegin(0, TIMER_DIVIDER, true);
  timerAttachInterrupt(timer, &onTimer, true);
  timerAlarmWrite(timer, adc_period, true);
  timerAlarmEnable(timer);
 
}
 
void loop() {
 
  if (interruptCounter >= FRAME_SIZE) {
 
    portENTER_CRITICAL(&timerMux);
    interruptCounter = 0;
    portEXIT_CRITICAL(&timerMux);

    /*
    Serial.printf("f\n");
    for (uint32_t i = 0; i < FRAME_SIZE; i++) {
      Serial.printf("%d %d\n", frame_msgs[i].ch_1, frame_msgs[i].ch_2);
    }
    Serial.printf("\n");
 
    frameCounter++;
    */
 
  }
}
