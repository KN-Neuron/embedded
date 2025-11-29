#include "ADS.h"

uint8_t regData[24];
int stat_1;
int32_t channelData[8];

uint8_t SPI_transmit(uint8_t data) {
	uint8_t rx = 0;
	HAL_SPI_TransmitReceive(&hspi1, &data, &rx, sizeof(rx), 1000);
	return rx;
}

void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin) {
	if (GPIO_Pin == DRDY_Pin)
		DRDY_Exti();
}

void ADS_RESET() {
	uint8_t send = _RESET;
	HAL_GPIO_WritePin(CS_GPIO_Port, CS_Pin, GPIO_PIN_RESET);
	HAL_SPI_Transmit(&hspi1, &send, 1, 100);
	HAL_GPIO_WritePin(CS_GPIO_Port, CS_Pin, GPIO_PIN_SET);
}

void ADS_SDATAC() {
	uint8_t send = _SDATAC;
	HAL_GPIO_WritePin(CS_GPIO_Port, CS_Pin, GPIO_PIN_RESET);
	HAL_SPI_Transmit(&hspi1, &send, 1, 100);
	HAL_GPIO_WritePin(CS_GPIO_Port, CS_Pin, GPIO_PIN_SET);
}

uint8_t ADS_RREG(uint8_t _address) {
	puts("Using RREG command\r\n");
	// uint8_t regData;
	uint8_t opcode1 = _address + 0x20;
	HAL_GPIO_WritePin(CS_GPIO_Port, CS_Pin, GPIO_PIN_RESET);
	SPI_transmit(opcode1);
	SPI_transmit(0);
	regData[_address] = SPI_transmit(0);
	HAL_GPIO_WritePin(CS_GPIO_Port, CS_Pin, GPIO_PIN_SET);
	return regData[_address];
}

static void ADS_RREGS(uint8_t _address, uint8_t _numRegistersMinusOne) {
	int i;
	uint8_t opcode1 = _address + 0x20;
	HAL_GPIO_WritePin(CS_GPIO_Port, CS_Pin, GPIO_PIN_RESET);
	SPI_transmit(opcode1);
	SPI_transmit(_numRegistersMinusOne);
	for (i = 0; i <= _numRegistersMinusOne; i++) {
		regData[_address + i] = SPI_transmit(0);
	}
	HAL_GPIO_WritePin(CS_GPIO_Port, CS_Pin, GPIO_PIN_SET);
}

uint8_t ADS_GetID() {
	uint8_t data = ADS_RREG(0);
	printf("ID: %d\r\n", data);
	return data;
}

static void ADS_WREG(uint8_t _address, uint8_t _value) {
//	puts("Using WREG command\n\r");
	uint8_t opcode1 = _address + 0x40;
	HAL_GPIO_WritePin(CS_GPIO_Port, CS_Pin, GPIO_PIN_RESET);
	SPI_transmit(opcode1);
	SPI_transmit(0);
	SPI_transmit(_value);
	HAL_GPIO_WritePin(CS_GPIO_Port, CS_Pin, GPIO_PIN_SET);
	regData[_address] = _value;
}

static void ADS_START() {
	HAL_GPIO_WritePin(CS_GPIO_Port, CS_Pin, GPIO_PIN_RESET);
	SPI_transmit(_START);
	HAL_GPIO_WritePin(CS_GPIO_Port, CS_Pin, GPIO_PIN_SET);
}

static void ADS_STOP() {
	HAL_GPIO_WritePin(CS_GPIO_Port, CS_Pin, GPIO_PIN_RESET);
	SPI_transmit(_STOP);
	HAL_GPIO_WritePin(CS_GPIO_Port, CS_Pin, GPIO_PIN_SET);
}

void Init_ADS() {
	puts("Start INIT ADS\r\n");
	ADS_RESET();
	puts("Send RESET command\r\n");
	HAL_Delay(500);
	ADS_SDATAC();
	puts("Send SDATAC command\r\n");
	HAL_Delay(1100);
	uint8_t id = ADS_GetID();
	UNUSED(id);
	ADS_WREG(CONFIG1, 0x06);
	HAL_Delay(10);
	ADS_WREG(CONFIG2, 0x10);
	HAL_Delay(100);
	ADS_WREG(CONFIG3, 0xDC);
	HAL_Delay(100);
	ADS_WREG(LOFF, 0x03);
	HAL_Delay(10);
	ADS_WREG(CH1SET, 0x50);
	HAL_Delay(10);
	ADS_WREG(CH2SET, 0x50);
	HAL_Delay(10);
	ADS_WREG(CH3SET, 0x50);
	HAL_Delay(10);
	ADS_WREG(CH4SET, 0x50);
	HAL_Delay(10);
	ADS_WREG(CH5SET, 0x55);
	HAL_Delay(10);
	ADS_WREG(CH6SET, 0x55);
	HAL_Delay(10);
	// ADS_WREG(CH7SET,0x65);
// HAL_Delay(10);
	// ADS_WREG(CH8SET,0x65);
// HAL_Delay(10);
	ADS_WREG(BIAS_SENSP, 0x00);
	HAL_Delay(10);
	ADS_WREG(BIAS_SENSN, 0x00);
	HAL_Delay(10);
	ADS_WREG(LOFF_SENSP, 0xFF);
	HAL_Delay(10);
	ADS_WREG(LOFF_SENSN, 0x02);
	HAL_Delay(10);
	ADS_WREG(LOFF_FLIP, 0x00);
	HAL_Delay(10);
	ADS_WREG(LOFF_STATP, 0xF1);
	HAL_Delay(10);
	ADS_WREG(LOFF_STATN, 0x00);
	HAL_Delay(10);
	ADS_WREG(GPIO, 0x00);
	HAL_Delay(10);
	ADS_WREG(MISC1, 0x00);
	HAL_Delay(10);
	ADS_WREG(MISC2, 0xF0);
	HAL_Delay(10);
	ADS_WREG(CONFIG4, 0x22);
	HAL_Delay(10);
	ADS_WREG(0x18, 0x0A);
	HAL_Delay(10);
	ADS_WREG(0x19, 0xE3);
	HAL_Delay(10);
	ADS_RREGS(0, 17);
	HAL_Delay(1000);
	ADS_START();
	HAL_Delay(100);
}

static void ADS_RDATA() {
	uint8_t inByte, inByte1, inByte2, inByte3;
	int i;//, j; UNUSED(j);
	int nchan = 6;
	stat_1 = 0;

	for (i = 0; i < nchan; i++)
		channelData[i] = 0;
	HAL_GPIO_WritePin(CS_GPIO_Port, CS_Pin, GPIO_PIN_RESET);
	SPI_transmit(_RDATA);
	for (i = 0; i < 3; i++) {
		inByte = SPI_transmit(0);
		stat_1 = (stat_1 << 8) | inByte;
	}
	for (i = 0; i < 8; i++) {
		inByte1 = SPI_transmit(0);
		inByte2 = SPI_transmit(0);
		inByte3 = SPI_transmit(0);
		channelData[i] = (inByte1 << 16) | (inByte2 << 8) | inByte3;
	}
	HAL_GPIO_WritePin(CS_GPIO_Port, CS_Pin, GPIO_PIN_SET);
	/*
	printf("ADS: %ld, %ld, %ld, %ld, %ld, %ld, %ld, %ld \r\n",
			channelData[0], channelData[1], channelData[2], channelData[3],
			channelData[4], channelData[5], channelData[6], channelData[7]);
			*/
	printf("ADS: %ld, %ld, %ld\r\n", channelData[0], channelData[1], channelData[2]);
}
void DRDY_Exti() {
	ADS_RDATA();
	ADS_START();
}
