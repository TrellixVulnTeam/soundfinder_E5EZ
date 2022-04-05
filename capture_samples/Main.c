
#include <stdio.h>
#include <stdint.h>
#include "../inc/ADCSWTrigger.h"
#include "../inc/tm4c123gh6pm.h"
#include "../inc/PLL.h"
#include "../inc/LaunchPad.h"
#include "../inc/CortexM.h"
#include "../inc/TExaS.h"

#include "../inc/uart.h"

uint8_t ADCMailbox;
uint32_t ADCvalue[2];
uint32_t count;

typedef struct Message {
	//uint16_t id;
	uint16_t ch_1;
	uint16_t ch_2;
} message_t;

// set by python code via UART
uint16_t numSamples;

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
  // TIMER0_TAILR_R = 79999;         // start value for 1 KHz interrupts (was 79999)
	TIMER0_TAILR_R = 1665;			//39999 is 2 khz	9999 is 8 KHz0  2499 is 32 KHz
	// 1665 = 48 KHz
  TIMER0_IMR_R |= TIMER_IMR_TATOIM;// enable timeout (rollover) interrupt
  TIMER0_ICR_R = TIMER_ICR_TATOCINT;// clear timer0A timeout flag
  TIMER0_CTL_R |= TIMER_CTL_TAEN;  // enable timer0A 32-b, periodic, interrupts
  // **** interrupt initialization ****
                                   // Timer0A=priority 2
  NVIC_PRI4_R = (NVIC_PRI4_R&0x00FFFFFF)|0x40000000; // top 3 bits
  NVIC_EN0_R = 1<<19;              // enable interrupt 19 in NVIC
}

void Timer0A_Handler(void) {
	PF1 = 0x02;
	TIMER0_ICR_R = TIMER_ICR_TATOCINT;
	ADC_In89(ADCvalue);
	ADCMailbox = 1;
	count++;
	PF1 = 0x00;
}





int main(void) {
	LaunchPad_Init();
	PLL_Init(Bus80MHz);
	//ADC0_InitSWTriggerSeq3_Ch9();
	ADC_Init89();
	Timer0A_Init1KHzInt();
	UART_Init();
	
	PF1 = 0;
	PF2 = 0;
	PF3 = 0;
	
	count = 0;
	ADCMailbox = 0;
	
	EnableInterrupts();
	
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
			PF2 = 0x04;
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
			
			PF2 = 0x00;
			
			//ADCMailbox = 0;
			
		//}
	}
}
