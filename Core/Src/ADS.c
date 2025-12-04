/**
 * @file 	ADS.c
 * @brief	ADS1299 driver
 *
 * This file contains the implementation of the ADS functions.
 * The Init_ADS function is the entrypoint for configuration of the ADS,
 * and ADS_RDATA is then used to read the received data.
 *
 * For reference, see the ADS datasheet
 * https://www.ti.com/lit/ds/symlink/ads1299.pdf
 *
 */

#include "ADS.h"

/*** ADS RESPONSE VARIABLES ***/
volatile int stat;

#define DATA_SIZE_BYTES 25
uint8_t channelDatabytes[DATA_SIZE_BYTES];

/*** SPI FUNCTIONS ***/

void SPI_Set() {
	HAL_GPIO_WritePin(CS_GPIO_Port, CS_Pin, GPIO_PIN_SET);
}

void SPI_Clear() {
	HAL_GPIO_WritePin(CS_GPIO_Port, CS_Pin, GPIO_PIN_RESET);
}

uint8_t SPI_Receive() {
	uint8_t rx = 0;
	HAL_SPI_Receive(&hspi1, &rx, sizeof(rx), 1000);
	return rx;
}

void SPI_Transmit(uint8_t data) {
	HAL_SPI_Transmit(&hspi1, &data, 1, 1000);
}

/*** ADS FUNCTIONS ***/

void ADS_Transmit(uint8_t data) {
	SPI_Clear();
	SPI_Transmit(data);
	SPI_Set();
}

static void ADS_START() {
	ADS_Transmit(_START);
}

static void ADS_WREG(uint8_t _address, uint8_t _value) {
	// puts("Using WREG command\n\r");
	uint8_t opcode1 = _address + 0x40;
	SPI_Clear();
	SPI_Transmit(opcode1);
	SPI_Receive();
	SPI_Transmit(_value);
	SPI_Set();
}

/* Read data from the ADS. */
static void ADS_RDATA() {
	uint8_t inByte = 0;
	int i;
	stat = 0;

	SPI_Clear();
	SPI_Transmit(_RDATA);

	/**
	 * Read the status bit.
	 * Bits 20:23 - Header (1100)
	 * Bits 12:19 - Positive lead off
	 * Bits 4:11 - Negative lead off
	 * Bits 0:3 - GPIO bits 4:7
	 */
	for (i = 0; i < 3; i++) {
		inByte = SPI_Receive();
		stat = (stat << 8) | inByte;
	}
	// printf("Status: %d\r\n", stat);

	/* Receive all channel data at the same time */
	for (i = 1; i < DATA_SIZE_BYTES; i++) {
		channelDatabytes[i] = SPI_Receive();
	}
	SPI_Set();

	HAL_UART_Transmit(&huart3, channelDatabytes, DATA_SIZE_BYTES,
			HAL_MAX_DELAY);
}

/* Initialize the ADS. */
void ADS_Init() {
	/* 0x50 = powered on, 12x gain, SRB2 open, normal input */
	// int mode = 0b01010000;
	__disable_irq();
	int mode = 0;
	channelDatabytes[0] = 'A'; //A

	// puts("Start INIT ADS\r\n");
	ADS_Transmit(_RESET);
	// puts("Send RESET command\r\n");
	ADS_Transmit(_SDATAC);
	// puts("Send SDATAC command\r\n");
	ADS_WREG(CONFIG1, 0x06);
	ADS_WREG(CONFIG2, 0x10);
	ADS_WREG(CONFIG3, 0xDC);
	ADS_WREG(LOFF, 0x03);
	ADS_WREG(CH1SET, mode);
	ADS_WREG(CH2SET, mode);
	ADS_WREG(CH3SET, mode);
	ADS_WREG(CH4SET, mode);
	ADS_WREG(CH5SET, mode);
	ADS_WREG(CH6SET, mode);
	ADS_WREG(CH7SET, mode);
	ADS_WREG(CH8SET, mode);
	ADS_WREG(BIAS_SENSP, 0x00);
	ADS_WREG(BIAS_SENSN, 0x00);
	ADS_WREG(LOFF_SENSP, 0xFF);
	ADS_WREG(LOFF_SENSN, 0x02);
	ADS_WREG(LOFF_FLIP, 0x00);
	ADS_WREG(LOFF_STATP, 0xF1);
	ADS_WREG(LOFF_STATN, 0x00);
	ADS_WREG(GPIO, 0x00);
	ADS_WREG(MISC1, 0x00);
	ADS_WREG(MISC2, 0xF0);
	ADS_WREG(CONFIG4, 0x22);
	ADS_WREG(0x18, 0x0A);
	ADS_WREG(0x19, 0xE3);
	ADS_START();
	__enable_irq();
}

/*** EXTI CALLBACK (DRDY RESPONSE) ***/
#if defined(STM32C0)
void HAL_GPIO_EXTI_Falling_Callback(uint16_t GPIO_Pin) {
#elif defined(STM32H7)
void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin) {
#endif
	if (GPIO_Pin == DRDY_Pin) {
		ADS_RDATA();
		ADS_START();
	}
}
