
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
	uint32_t id;
	uint32_t ch_1;
	uint32_t ch_2;
} message_t;



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
	TIMER0_TAILR_R = 39999;
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
	ADC0_InitSWTriggerSeq3_Ch9();
	ADC_Init89();
	Timer0A_Init1KHzInt();
	UART_Init();
	
	PF1 = 0;
	PF2 = 0;
	PF3 = 0;
	
	count = 0;
	ADCMailbox = 0;
	
	EnableInterrupts();
	
	while (1) {
		// if there's data, transmit it
		if (ADCMailbox == 1) {
			PF2 = 0x04;
			// send to pc with printf
			char message_out[50];
			
			sprintf(message_out, "%d %d %d\n", count, ADCvalue[0], ADCvalue[1]);
			
			// printf("%d %d %d \n", count, ADCvalue[0], ADCvalue[1]);
			
			UART_OutString(message_out);
			
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
			
			ADCMailbox = 0;
			
		}
	}
}
