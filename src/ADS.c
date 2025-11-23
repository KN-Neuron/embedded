/**
 * @file 	ADS.c
 * @brief	ADS1299 driver
 * 
 * This file contains the implementation of the ADS functions.
 * The ADS_Init function is the entrypoint for configuration of the ADS,
 * and ADS_RDATA is then used to read the received data.
 * 
 * For reference, see the ADS datasheet
 * https://www.ti.com/lit/ds/symlink/ads1299.pdf
 * 
 */

#include "ADS.h"

// static const char *TAG = "ADS1299";

/*** ADS RESPONSE VARIABLES ***/

int stat;
int32_t channelData[8];

/* Queue to pass GPIO numbers from ISR to a task */
static xQueueHandle ads_evt_queue = NULL;

/* Global SPI device handle for use in ISR */
static spi_device_handle_t g_spi_dev = NULL;

/*** SPI FUNCTIONS ***/

void SPI_Transmit(uint8_t data) {
	spi_transaction_t t = {
		.length = 8,
		.tx_buffer = &data,
		.rx_buffer = NULL
	};
	spi_device_transmit(g_spi_dev, &t);
}

uint8_t SPI_Receive() {
	uint8_t rx = 0;
	spi_transaction_t t = {
		.length = 8,
		.tx_buffer = NULL,
		.rx_buffer = &rx
	};
	spi_device_transmit(g_spi_dev, &t);
	return rx;
}

void SPI_TransmitReceive(uint8_t tx_data, uint8_t *rx_data) {
	spi_transaction_t t = {
		.length = 8,
		.tx_buffer = &tx_data,
		.rx_buffer = rx_data
	};
	spi_device_transmit(g_spi_dev, &t);
}

/*** ADS FUNCTIONS ***/

void ADS_Transmit(uint8_t data) {
	gpio_set_level(PIN_NUM_CS, 0);  // CS low
	SPI_Transmit(data);
	gpio_set_level(PIN_NUM_CS, 1);  // CS high
}

static void ADS_START() {
	ADS_Transmit(_START);
}

static void ADS_WREG(uint8_t _address, uint8_t _value) {
	puts("Using WREG command\n\r");
	uint8_t opcode1 = _address + 0x40;
	gpio_set_level(PIN_NUM_CS, 0);  // CS low
	SPI_Transmit(opcode1);
	SPI_Receive();
	SPI_Transmit(_value);
	gpio_set_level(PIN_NUM_CS, 1);  // CS high
}

/* Read data from the ADS. */
static void ADS_RDATA_Internal() {
	uint8_t inByte, inByte1, inByte2, inByte3;
	int i;
	int nchan = 8;
	stat = 0;

	gpio_set_level(PIN_NUM_CS, 0);  // CS low
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

	/** Receive data from each channel. */
	for (i = 0; i < nchan; i++) {
		inByte1 = SPI_Receive();
		inByte2 = SPI_Receive();
		inByte3 = SPI_Receive();
		channelData[i] = (inByte1 << 16) | (inByte2 << 8) | inByte3;
	}

	gpio_set_level(PIN_NUM_CS, 1);  // CS high

	printf("ADS: %ld, %ld, %ld, %ld, %ld, %ld, %ld, %ld \r\n",
			channelData[0], channelData[1], channelData[2], channelData[3],
			channelData[4], channelData[5], channelData[6], channelData[7]);
}

/* Public wrapper for ADS_RDATA */
void ADS_RDATA(void) {
	ADS_RDATA_Internal();
}

/* Initialize the ADS and SPI peripheral. */
void ADS_Init(void) {
	esp_err_t ret;

	/* Initialize SPI bus (copied from spi_test.c) */
	spi_bus_config_t buscfg = {
		.mosi_io_num = PIN_NUM_MOSI,
		.miso_io_num = PIN_NUM_MISO,
		.sclk_io_num = PIN_NUM_SCLK,
		.quadwp_io_num = -1,
		.quadhd_io_num = -1,
		.max_transfer_sz = 32
	};

	ret = spi_bus_initialize(SPI_HOST_ID, &buscfg, SPI_DMA_CH_AUTO);
	ESP_ERROR_CHECK(ret);

	spi_device_interface_config_t devcfg = {
		.clock_speed_hz = 5 * 1000 * 1000, // 5 MHz
		.mode = 0,
		.spics_io_num = -1, // We'll manually control CS using GPIO
		.queue_size = 7,
	};

	ret = spi_bus_add_device(SPI_HOST_ID, &devcfg, &g_spi_dev);
	ESP_ERROR_CHECK(ret);

	/* Configure CS pin as GPIO and set high (inactive) */
	gpio_set_direction(PIN_NUM_CS, GPIO_MODE_OUTPUT);
	gpio_set_level(PIN_NUM_CS, 1);

	/* 0x50 = powered on, 12x gain, SRB2 open, normal input */
	// int mode = 0b01010000;
	int mode = 0;

	puts("Start INIT ADS\r\n");
	ADS_Transmit(_RESET);
	puts("Send RESET command\r\n");
	ADS_Transmit(_SDATAC);
	puts("Send SDATAC command\r\n");
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
}


/*** EXTI CALLBACK (DRDY RESPONSE) ***/

static void IRAM_ATTR gpio_interrupt_handler(void *args) {
	uint32_t gpio_num = (uint32_t) args;
	BaseType_t xHigherPriorityTaskWoken = pdFALSE;
	/* send the gpio number to the queue from ISR context */
	xQueueSendFromISR(ads_evt_queue, &gpio_num, &xHigherPriorityTaskWoken);
	if (xHigherPriorityTaskWoken == pdTRUE) {
		portYIELD_FROM_ISR();
	}
}

static void ads_task(void *arg) {
	uint32_t io_num;
	for (;;) {
		if (xQueueReceive(ads_evt_queue, &io_num, portMAX_DELAY)) {
			ADS_RDATA_Internal();
            // puts("Data ready interrupt received\r\n");
			/* yield briefly so the idle task and watchdog can run */
			ADS_START();
		}
	}
}

void ADS_SetupInterrupt(void) {
	/* Create a queue capable of holding 10 uint32_t values */
	ads_evt_queue = xQueueCreate(10, sizeof(uint32_t));

	/* Configure DRDY pin as input */
	gpio_set_direction(PIN_NUM_DRDY, GPIO_MODE_INPUT);
	gpio_set_intr_type(PIN_NUM_DRDY, GPIO_INTR_NEGEDGE);

	/* Start the task that will handle GPIO events */
	xTaskCreate(ads_task, "ads_task", 2048, NULL, 10, NULL);

	/* Install ISR service and add handler */
	gpio_install_isr_service(0);
	gpio_isr_handler_add(PIN_NUM_DRDY, gpio_interrupt_handler, (void *)PIN_NUM_DRDY);
}