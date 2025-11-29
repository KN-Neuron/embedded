/**
 * @file    ADS.h
 * @brief   Header file for ADS.c
 *
 * This file contains the declaration of the ADS functions.
 *
 */

#ifndef INC_ADS_H_
#define INC_ADS_H_

#include "main.h"
#include "stdio.h"
#include "stdlib.h"
#include "string.h"


extern SPI_HandleTypeDef hspi1;


/*** COMMANDS ***/

#define _WAKEUP 0x02    // Wake-up from standby mode
#define _STANDBY 0x04   // Enter Standby mode
#define _RESET 0x06     // Reset the device registers to default
#define _START 0x08     // Start and restart (synchronize) conversions
#define _STOP 0x0A      // Stop conversion
#define _RDATAC 0x10    // Enable Read Data Continuous mode (default mode at power-up)
#define _SDATAC 0x11    // Stop Read Data Continuous mode
#define _RDATA 0x12     // Read data by command; supports multiple read back


/*** REGISTER ADDRESSES ***/

#define ID 0x00

#define CONFIG1 0x01
#define CONFIG2 0x02
#define CONFIG3 0x03
#define CONFIG4 0x17

#define LOFF 0x04
#define LOFF_SENSP 0x0F
#define LOFF_SENSN 0x10
#define LOFF_FLIP 0x11
#define LOFF_STATP 0x12
#define LOFF_STATN 0x13

#define BIAS_SENSP 0x0D
#define BIAS_SENSN 0x0E

#define CH1SET 0x05
#define CH2SET 0x06
#define CH3SET 0x07
#define CH4SET 0x08
#define CH5SET 0x09
#define CH6SET 0x0A
#define CH7SET 0x0B
#define CH8SET 0x0C

#define GPIO 0x14

#define MISC1 0x15
#define MISC2 0x16


/*** EXPOSED FUNCTIONS ***/

void ADS_Init();


#endif /* INC_ADS_H_ */
