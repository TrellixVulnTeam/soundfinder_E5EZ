/* WhereIsTheSound_sample_capture
	EE464 FH16 - Where Is The Sound
*/

#include <stdio.h>
#include <stdint.h>
#include "../inc/ADCSWTrigger.h"
#include "../inc/tm4c123gh6pm.h"
#include "../inc/PLL.h"
#include "../inc/LaunchPad.h"
#include "../inc/CortexM.h"

/* debugging profile */
#define DEBUG_ON
#undef DEBUG_ON  // comment this line out to enable debugging with TExaSdisplay
#ifndef DEBUG_ON
#include "../inc/uart.h"
#else
#include "../inc/TExaS.h"
// logic analyzer - records digital signals ie. PWM on PF0-6
void LogicAnalyzerTask(void){
  UART0_DR_R = 0x80|GPIO_PORTF_DATA_R; // sends at 10kHz to TExaSdisplay
}
// scope - measures analog voltage on PD3
void ScopeTask(void){  // called 10k/sec
  UART0_DR_R = (ADC1_SSFIFO3_R>>4); // send ADC to TExaSdisplay
}
#endif

/* sample frame data structure */
typedef struct Message {
	//uint16_t id;  // removed to increase frame size
	uint16_t ch_1;  // sample value from mic A
	uint16_t ch_2;  // sample value from mic B
} message_t;
// frame size (in samples)
uint16_t numSamples; // TODO: set by python code via UART

/* ADC */
uint8_t ADCMailbox;
uint32_t ADCvalue[2];
uint32_t ADCPeriod;
uint32_t count;
// sampling timer
void Timer0A_InitVarKHzInt(uint16_t sampling_rate_khz, uint32_t bus_clock_mhz) {
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
  ADCPeriod = ((bus_clock_mhz * 1000) / (sampling_rate_khz)) - 1;
  TIMER0_TAILR_R = ADCPeriod;      // 39999 = 2 khz, 9999 = 8 KHz, 2499 = 32 KHz, 1665 = 48 KHz, 79999 = 1 KHz, 4999 = 16 KHz
  TIMER0_IMR_R |= TIMER_IMR_TATOIM;// enable timeout (rollover) interrupt
  TIMER0_ICR_R = TIMER_ICR_TATOCINT;// clear timer0A timeout flag
  TIMER0_CTL_R |= TIMER_CTL_TAEN;  // enable timer0A 32-b, periodic, interrupts
  // **** interrupt initialization ****
                                   // Timer0A=priority 2
  NVIC_PRI4_R = (NVIC_PRI4_R&0x00FFFFFF)|0x40000000; // top 3 bits
  NVIC_EN0_R = 1<<19;              // enable interrupt 19 in NVIC
}
// ISR for sampling
void Timer0A_Handler(void) {
	PF1 = 0x02;
	TIMER0_ICR_R = TIMER_ICR_TATOCINT;
	ADC_In89(ADCvalue);
	ADCMailbox = 1;
	count++;
	PF1 = 0x00;
}


/* entry point */
int main(void) {
	// debugging profile
#ifndef DEBUG_ON
	PLL_Init(Bus80MHz);
	LaunchPad_Init();
	//ADC0_InitSWTriggerSeq3_Ch9();  // 1 channel (PE4)
	ADC_Init89(); 	// 2 channels (PE4,PE5)
	//Timer0A_Init1KHzInt();  // hardware timer
	Timer0A_InitVarKHzInt(48, 80);  // hardware timer
	UART_Init();  // serial
#else
	// pick one of the following three lines, all three set PLL to 80 MHz
  //PLL_Init(Bus80MHz);                 // 1) call to have no TExaS debugging
  //TExaS_SetTask(&LogicAnalyzerTask);  // 2) call to activate logic analyzer on PF0-6
  TExaS_SetTask(&ScopeTask);            // 3) call to activate analog scope PD3
	LaunchPad_Init();  // required
#endif
	PF1 = 0;
	PF2 = 0;
	PF3 = 0;
	
	// adc
	count = 0;
	ADCMailbox = 0;

	// start sampling timer
	EnableInterrupts();
	
#ifndef DEBUG_ON
	// stream mic samples to python over serial
	message_t dataArr[192];
	uint16_t dataArrIndex = 0;
	while (1) {
		// if there's data, transmit it
		//numSamples = UART_InUDec();
		numSamples = 192;
		while(dataArrIndex < numSamples){
			// wait for array to fill up
			if(ADCMailbox == 1){
				PF2 = 0x04;
				//dataArr[dataArrIndex].id = count;
			
				dataArr[dataArrIndex].ch_1 = ADCvalue[0];
				dataArr[dataArrIndex].ch_2 = ADCvalue[1];
				dataArrIndex++;
				ADCMailbox = 0;
			}
		}
		dataArrIndex = 0;
		//if (ADCMailbox == 1) {
			PF2 = 0x04; // profile
			// send to pc with printf
			char message_out[50];
			DisableInterrupts();
			UART_OutChar('\n');
			UART_OutChar('s');
			UART_OutChar('\n');
			for(int i = 0; i < numSamples; i++){
				
				sprintf(message_out, "%d %d\n", dataArr[i].ch_1, dataArr[i].ch_2);
			
			// printf("%d %d %d \n", count, ADCvalue[0], ADCvalue[1]);
			
				UART_OutString(message_out);
			}
			EnableInterrupts();
			// UART_OutUDec(count);
			// UART_OutChar('a');
			
//			UART_OutChar('n');
//			UART_OutUDec(count);
//			UART_OutChar('a');
//			UART_OutUDec(ADCvalue[0]);
//			UART_OutChar('b');
//			UART_OutUDec(ADCvalue[1]);
//			UART_OutChar('\n');
			
			PF2 = 0x00; // profile
			
			//ADCMailbox = 0;
			
		//}
	}
#else
	while (1) {
		PF1 ^= 0x02;
	}
#endif
}
