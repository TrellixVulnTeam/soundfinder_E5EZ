

#define PROFILE_PIN 17

#define SAMPLING_RATE_KHZ 25
#define BUS_CLOCK_MHZ 80
#define TIMER_DIVIDER 80
#define FRAME_SIZE 5000

typedef struct Message {
  uint16_t ch_1;  // sample value from mic A
  uint16_t ch_2;  // sample value from mic B
} message_t;
volatile message_t frame_msgs[FRAME_SIZE];

volatile uint8_t profile_val;
volatile uint16_t interruptCounter;
volatile uint32_t frameCounter;
volatile uint32_t framePointer;
 
hw_timer_t * timer = NULL;
portMUX_TYPE timerMux = portMUX_INITIALIZER_UNLOCKED;
 
void IRAM_ATTR onTimer() {
  portENTER_CRITICAL_ISR(&timerMux);
  
  interruptCounter++;

  frame_msgs[framePointer].ch_1 = 3;
  frame_msgs[framePointer].ch_2 = 4;

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
    
    Serial.printf("f\n");
    for (uint32_t i = 0; i < FRAME_SIZE; i++) {
      Serial.printf("%d %d\n", frame_msgs[i].ch_1, frame_msgs[i].ch_2);
    }
    Serial.printf("\n");
 
    frameCounter++;
 
  }
}
