// PWMtest.c
// Runs on TM4C123
// Use PWM0/PB6 and PWM1/PB7 to generate pulse-width modulated outputs.
// Daniel Valvano
// March 28, 2014

/* This example accompanies the book
   "Embedded Systems: Real Time Interfacing to Arm Cortex M Microcontrollers",
   ISBN: 978-1463590154, Jonathan Valvano, copyright (c) 2015
   Program 6.8, section 6.3.2

   "Embedded Systems: Real-Time Operating Systems for ARM Cortex M Microcontrollers",
   ISBN: 978-1466468863, Jonathan Valvano, copyright (c) 2015
   Program 8.4, Section 8.3

 Copyright 2015 by Jonathan W. Valvano, valvano@mail.utexas.edu
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
#include <stdint.h>
#include <stdio.h>
#include "../inc/PLL.h"
#include "../inc/PWM.h"
#include "../inc/ADCSWTrigger.h"
#include "../inc/SysTickInts.h"
#include "../inc/LaunchPad.h"
#include "../inc/UART.h"

#define PWM_PERIOD 40000
#define SERVO_NEUTRAL 12000

#define SERVO_ZERO 0
#define SERVO_ONE  1

void WaitForInterrupt(void);  // low power mode

void PWM3B_Init(uint16_t period, uint16_t duty);
void PWM3B_Duty(uint16_t duty);

void Servo_Init(void) {
	PWM0A_Init(PWM_PERIOD, SERVO_NEUTRAL); // Initialize PWM0, 200 Hz, 30% duty (i.e. 1.5 ms pulse width)
	PWM3B_Init(PWM_PERIOD, SERVO_NEUTRAL);
}

// Set servo position in increments of a tenth of a degree
// 0 degrees means the servo points directly forwards (i.e. in its neutral position)
// index picks which servo to control
void Servo_SetPosition(int idx, int16_t angle) {
	if (angle < -900) angle = -900;
	if (angle >  900) angle =  900; // clamp input angle
	if (idx == 1) angle -= 50; // Compensate for motor 1 being different
	int16_t width_change = (angle * 47) >> 3; // Convert from degree/10 => PWM value from -8000 to 8000
	int16_t new_width = SERVO_NEUTRAL + width_change;
	switch (idx) {
		case SERVO_ZERO: PWM0A_Duty((uint16_t) new_width); break;
		case SERVO_ONE: PWM3B_Duty((uint16_t) new_width); break;
		default: break;
	}
}

void SysTick_Handler(void) {
	static int16_t servo1Angle = 0;
	int16_t data = ((int16_t) ADC0_InSeq3()) - 2048; // -2048 to 2047
	uint8_t buttons = LaunchPad_Input(); // Get button presses on launchpad
	int16_t angle = data / 2; // to get roughly 80 degree range each way
	if (buttons & 0x1) servo1Angle -= 50;
	if (buttons & 0x2) servo1Angle += 50;
	if (servo1Angle > 900) servo1Angle = 900;
	if (servo1Angle < -900) servo1Angle = -900;
	
  Servo_SetPosition(0, angle);
	Servo_SetPosition(1, servo1Angle);
}

int main(void){
	int32_t angle = 0;
	char incidentMic;
  PLL_Init(Bus16MHz);
	
	//PLL_Init(Bus80MHz);       // 80  MHz
	
	//NOTE: I don't know why this one needs a parameter to be passed whereas previous times it didn't. -Evelyn
	UART_Init(1);              // initialize UART
	
	Servo_Init(); // Initialize PWM control for servo
	LaunchPad_Init();
	ADC0_InitSWTriggerSeq3_Ch9();
	
	// don't need systick adc when using uart
	//SysTick_Init(1000000); // Trigger ~15 interrupts per second
	//SysTick_Start();
  while(1){
		//WaitForInterrupt();
		
		incidentMic = UART_InChar();
		angle = UART_InUDec();
		if(incidentMic == 'B'){
			angle = -angle;
		}
		Servo_SetPosition(0, angle);	//only turning horizontal motor for now
		//UART_OutString("confirm");
  }
}
