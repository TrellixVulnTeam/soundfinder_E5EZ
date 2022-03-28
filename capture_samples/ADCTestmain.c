// ADCTestmain.c
// Runs on LM4F120/TM4C123
// Provide a function that initializes Timer0A to trigger ADC
// SS0 conversions and request an interrupt when the conversion
// is complete.
// Daniel Valvano
// January 19, 2020

/* This example accompanies the book
   "Embedded Systems: Real Time Interfacing to Arm Cortex M Microcontrollers",
   ISBN: 978-1463590154, Jonathan Valvano, copyright (c) 2020

 Copyright 2020 by Jonathan W. Valvano, valvano@mail.utexas.edu
    You may use, edit, run or distribute this file
    as long as the above copyright notice remains
 THIS SOFTWARE IS PROVIDED "AS IS".  NO WARRANTIES, WHETHER EXPRESS, IMPLIED
 OR STATUTORY, INCLUDING, BUT NOT LIMITED TO, IMPLIED WARRANTIES OF
 MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE APPLY TO THIS SOFTWARE.
 VALVANO SHALL NOT, IN ANY CIRCUMSTANCES, BE LIABLE FOR SPECIAL, INCIDENTAL,
 OR CONSEQUENTIAL DAMAGES, FOR ANY REASON WHATSOEVER.
 For more information about my classes, my research, and my books, see
 http://users.ece.utexas.edu/~valvano/
 */

// center of X-ohm potentiometer connected to PE3/AIN0
// bottom of X-ohm potentiometer connected to ground
// top of X-ohm potentiometer connected to +3.3V through X/10-ohm ohm resistor
#include <stdint.h>
#include "../inc/tm4c123gh6pm.h"
#include "../inc/ADCT0ATrigger.h"
#include "../inc/PLL.h"
#include "../inc/CortexM.h"
#include "../inc/LaunchPad.h"

#define PERIOD 39999	// 2 khz


//debug code
//
// This program periodically samples ADC0 channel 0 and stores the
// result to a global variable that can be accessed with the JTAG
// debugger and viewed with the variable watch feature.
uint32_t ADCvalue;

// check this to see if there's 
uint8_t ADCmailbox;

void RealTimeTask(uint32_t data){
  PF3 ^= 0x08;           // toggle LED
  ADCvalue = data;
	ADCmailbox = 1;
	PF3 ^= 0x08;
}
int main0(void){
  PLL_Init(Bus80MHz);                      // 80 MHz system clock
  LaunchPad_Init();                        // activate port F
  ADC0_InitTimer0ATriggerSeq0(0, 39999,&RealTimeTask); // ADC channel 0, 2 khz
  PF2 = 0;              // turn off LED
  EnableInterrupts();
  while(1){
    // WaitForInterrupt();
		
		if (ADCmailbox == 1) {
			// send data to computer
			// reset mailbox
		}
		
    PF2 ^= 0x04;           // toggle LED
  }
}

