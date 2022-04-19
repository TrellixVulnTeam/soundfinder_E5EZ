// Where is the Sound
// Microphone audio processor

#include <stdint.h>
#include "../inc/ADCSWTrigger.h"
#include "../inc/tm4c123gh6pm.h"
#include "../inc/PLL.h"
#include "../inc/LaunchPad.h"
#include "../inc/CortexM.h"
#include "../inc/TExaS.h"

#include "Main.h"

void LogicAnalyzerTask(void){
  UART0_DR_R = 0x80|GPIO_PORTF_DATA_R; // sends at 10kHz
}
// measures analog voltage on PD3
void ScopeTask(void){  // called 10k/sec
  UART0_DR_R = (ADC1_SSFIFO3_R>>4); // send ADC to TExaSdisplay
}

uint32_t ADCvalue[2];
uint32_t ADCdiff;
uint8_t time_series_1_index = 0;
uint8_t time_series_1[TIME_SERIES_LENGTH];
uint8_t time_series_1_last_filter = 0;

uint8_t time_series_2_index = 0;
uint8_t time_series_2[TIME_SERIES_LENGTH];
uint8_t time_series_2_last_filter = 0;
void Timer0A_Init1KHzInt(void) {
  volatile uint32_t delay;
  DisableInterrupts();
  // **** general initialization ****
  SYSCTL_RCGCTIMER_R |= 0x01;      // activate timer0
  delay = SYSCTL_RCGCTIMER_R;      // allow time to finish activating
  TIMER0_CTL_R &= ~TIMER_CTL_TAEN; // disable timer0A during setup
  TIMER0_CFG_R = 0;                // configure for 32-bit timer mode
  // **** timer0A initialization ****
                                   // configure for periodic mode
  TIMER0_TAMR_R = TIMER_TAMR_TAMR_PERIOD;
  TIMER0_TAILR_R = 7999;         // start value for 1 KHz interrupts (was 79999)
  TIMER0_IMR_R |= TIMER_IMR_TATOIM;// enable timeout (rollover) interrupt
  TIMER0_ICR_R = TIMER_ICR_TATOCINT;// clear timer0A timeout flag
  TIMER0_CTL_R |= TIMER_CTL_TAEN;  // enable timer0A 32-b, periodic, interrupts
  // **** interrupt initialization ****
                                   // Timer0A=priority 2
  NVIC_PRI4_R = (NVIC_PRI4_R&0x00FFFFFF)|0x40000000; // top 3 bits
  NVIC_EN0_R = 1<<19;              // enable interrupt 19 in NVIC
}

volatile uint8_t val = 1;
volatile uint8_t signal = 0;
volatile uint8_t counter = 0;

int8_t direction = 0;	// which way to turn; negative = left, positive = right
void Timer0A_Handler(void) {
  TIMER0_ICR_R = TIMER_ICR_TATOCINT;    // acknowledge timer0A timeout
  //PF2 ^= 0x04;                   // profile
  //ADCvalue = ADC0_InSeq3();
	
	//ADCvalue[0] = ADC0_InSeq3();
	//from valvanoware ADC2channel code
	//ADC_In89 fills in ADCvalue[0] and [1] (i think)
	 ADC_In89(ADCvalue);   // take two samples, executes in about 18.64 us
		ADCdiff = ADCvalue[1] - ADCvalue[0];
    //PF2 = 0x00;
    //Clock_Delay(678);     // roughly 10,000 Hz sampling, to account for 18.64 us sample time)
  //
	
	time_series_1[time_series_1_index] = (uint8_t) ADCvalue[0];
	time_series_1_index++;
	
	time_series_2[time_series_2_index] = (uint8_t) ADCvalue[1];
	time_series_2_index++;
	//2nd mic on PE5
	/*uint16_t j = 0;
	if (time_series_1_index + 1 > TIME_SERIES_FILTER_LENGTH)
		j = (time_series_1_index + 1) - TIME_SERIES_FILTER_LENGTH;
	else j = TIME_SERIES_LENGTH + (time_series_1_index + 1 - TIME_SERIES_FILTER_LENGTH);
	uint32_t new_last_filter_val = 0;
	for (uint16_t i = 0; i < TIME_SERIES_FILTER_LENGTH; i++) {
		//new_last_filter_val += ;
		// avg the last few values
		//wrap around j even if i keeps going
	}*/
	if (time_series_1_index >= TIME_SERIES_LENGTH)
		time_series_1_index = 0;
	if (time_series_2_index >= TIME_SERIES_LENGTH)
		time_series_2_index = 0;
	//**evelyn's code**
	// assuming mic 1 is left, mic 2 is on right
	//average the adc values
	uint16_t mic_1_avg = 0;
	uint16_t mic_2_avg = 0;
	for(int i = 0; i < time_series_1_index; i++){
		mic_1_avg += time_series_1[i];
	}
	mic_1_avg /= time_series_1_index;
	
	for(int i = 0; i < time_series_2_index; i++){
		mic_2_avg += time_series_2[i];
	}
	mic_2_avg /= time_series_2_index;
	//repeat above block for each microphone, each with its own mic avg value
	//compare averages
	direction = mic_2_avg - mic_1_avg;
	//turn(direction);
	//PF1 = 0;
	if(direction > 0){
		PF1 = 0x02;	//red
		PF2 = 0;
	}
	else{
		PF1 = 0;
		PF2 = 0x04;	//blue
	}
	//repeat for up and down mics?
	
	/*
	if (ADCvalue > 275) {
		if (val == 0) {
			val = 1;
			signal = 1;
		} else {
			val--;
		}
	} else {
		if (val == 0) {
			val = 1;
			if (signal == 1) {
				counter++;
			}
			signal = 0;
		} else {
			val--;
		}
	}
	*/
}


int main(void) {
	// pick one of the following three lines, all three set PLL to 80 MHz
  //PLL_Init(Bus80MHz);              // 1) call to have no TExaS debugging
  //TExaS_SetTask(&LogicAnalyzerTask); // 2) call to activate logic analyzer
  TExaS_SetTask(&ScopeTask);       // or 3) call to activate analog scope PD3
  
  LaunchPad_Init();                  // activate port F
  ADC0_InitSWTriggerSeq3_Ch9();      // allow time to finish activating
	ADC_Init89(); 	//from valvanoware	pe4 and pe5
  Timer0A_Init1KHzInt();            // set up Timer0A for 100 Hz interrupts
  PF2 = 0;                           // turn off LED
  EnableInterrupts();
  while(1) {
    //PF1 ^= 0x02;  // toggles when running in main
  }
}


