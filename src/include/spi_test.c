#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/spi_master.h"
#include "driver/gpio.h"
#include "esp_log.h"

static const char *TAG = "SPI_EXAMPLE";

// Define SPI host (HSPI on ESP32, check variant notes for others)
// For ESP32, ESP32-S2, ESP32-S3: SPI2_HOST is often referred to as HSPI_HOST.
// For ESP32-C3, ESP32-C6, ESP32-H2: SPI2_HOST is typically the general-purpose SPI controller.
#define SPI_HOST_ID SPI2_HOST

// Define GPIO pins for SPI communication
// These can be reconfigured to other available GPIOs.
// Make sure these pins are not used by other peripherals (e.g., JTAG, internal flash).
#define PIN_NUM_MOSI 23 // Example for ESP32 DevKitC
#define PIN_NUM_MISO 19 // Example for ESP32 DevKitC
#define PIN_NUM_SCLK 18 // Example for ESP32 DevKitC
#define PIN_NUM_CS   5  // Example for ESP32 DevKitC

// SPI device handle
spi_device_handle_t spi_device;

void app_main(void)
{
    esp_err_t ret;

    ESP_LOGI(TAG, "Initializing SPI bus...");

    // Configuration for the SPI bus
    spi_bus_config_t buscfg = {
        .mosi_io_num = PIN_NUM_MOSI,
        .miso_io_num = PIN_NUM_MISO,
        .sclk_io_num = PIN_NUM_SCLK,
        .quadwp_io_num = -1, // Not used
        .quadhd_io_num = -1, // Not used
        .max_transfer_sz = 32 // Max transfer size in bytes
    };

    // Initialize the SPI bus
    // Using SPI_DMA_CH_AUTO to automatically assign a DMA channel.
    // For ESP32, valid DMA channels for SPI2 (HSPI) are 1 or 2.
    // For ESP32-S2, SPI2_HOST can use DMA channel 1 or 2.
    // For ESP32-S3, SPI2_HOST can use any DMA channel.
    // For C and H series, check datasheets for specific DMA channel availability for SPI2.
    // If DMA is not desired, use SPI_DMA_DISABLED (0).
    ret = spi_bus_initialize(SPI_HOST_ID, &buscfg, SPI_DMA_CH_AUTO);
    ESP_ERROR_CHECK(ret); // Check for errors

    ESP_LOGI(TAG, "SPI bus initialized.");
    ESP_LOGI(TAG, "Adding SPI device...");

    // Configuration for the SPI device
    spi_device_interface_config_t devcfg = {
        .clock_speed_hz = 10 * 1000 * 1000, // Clock out at 10 MHz
        .mode = 0,                          // SPI mode 0 (CPOL=0, CPHA=0)
        .spics_io_num = PIN_NUM_CS,         // CS pin
        .queue_size = 7,                    // We want to queue 7 transactions at a time
        //.pre_cb = NULL,                   // Callback before transaction (can be NULL)
        //.post_cb = NULL,                  // Callback after transaction (can be NULL)
    };

    // Attach the device to the SPI bus
    ret = spi_bus_add_device(SPI_HOST_ID, &devcfg, &spi_device);
    ESP_ERROR_CHECK(ret);
    ESP_LOGI(TAG, "SPI device added.");

    // Prepare transaction data
    char send_buffer[32] = "Hello SPI from ESP32!";
    char recv_buffer[32] = {0}; // Initialize with zeros

    spi_transaction_t t;
    memset(&t, 0, sizeof(t)); // Zero out the transaction structure
    t.length = strlen(send_buffer) * 8; // Length is in bits
    t.tx_buffer = send_buffer;
    t.rx_buffer = recv_buffer;
    // For loopback, MOSI is connected to MISO.
    // So, what we send on tx_buffer should appear on rx_buffer.

    ESP_LOGI(TAG, "Performing SPI transaction...");
    ESP_LOGI(TAG, "Sending: %s", send_buffer);

    // Perform the SPI transaction (blocking)
    // spi_device_transmit is a wrapper around spi_device_queue_trans and spi_device_get_trans_result.
    ret = spi_device_transmit(spi_device, &t);
    ESP_ERROR_CHECK(ret); // Check for errors

    ESP_LOGI(TAG, "SPI transaction completed.");

    // For loopback, rx_buffer should now contain what was sent.
    // Note: The first few bytes received might be garbage if the slave wasn't ready or
    // if MISO was floating before the transaction started.
    // In a real loopback, it should match.
    ESP_LOGI(TAG, "Received: %s (Length: %d bits, expected %d bits)", recv_buffer, t.rxlength, t.length);

    // Validate received data (optional, for loopback)
    if (memcmp(send_buffer, recv_buffer, strlen(send_buffer)) == 0) {
        ESP_LOGI(TAG, "Loopback test successful! Sent and received data match.");
    } else {
        ESP_LOGW(TAG, "Loopback test failed or partial match.");
        // Print hex for debugging
        ESP_LOG_BUFFER_HEXDUMP(TAG, send_buffer, strlen(send_buffer), ESP_LOG_INFO);
        ESP_LOG_BUFFER_HEXDUMP(TAG, recv_buffer, t.rxlength / 8, ESP_LOG_INFO);
    }

    // To send more data, repeat the transaction process:
    // 1. Prepare spi_transaction_t
    // 2. Call spi_device_transmit() or spi_device_polling_transmit()

    // Example of using spi_device_polling_transmit (simpler for one-off transactions)
    // This function doesn't use the queue set in devcfg.queue_size.
    // It's a blocking call.
    char another_message[] = "Polling Test";
    memset(&t, 0, sizeof(t));
    t.length = sizeof(another_message) * 8; // Include null terminator for string
    t.tx_buffer = another_message;
    t.rx_buffer = recv_buffer; // Re-use recv_buffer or use another

    ESP_LOGI(TAG, "Performing another SPI transaction using polling_transmit...");
    ESP_LOGI(TAG, "Sending: %s", another_message);
    ret = spi_device_polling_transmit(spi_device, &t);
    ESP_ERROR_CHECK(ret);
    ESP_LOGI(TAG, "Polling transaction completed.");
    ESP_LOGI(TAG, "Received (polling): %s", recv_buffer);


    // When done, you might want to remove the device and free the bus
    // This is usually done if the SPI bus is no longer needed during runtime.
    // For many applications, the bus is initialized once and used throughout.
    // ESP_LOGI(TAG, "Removing SPI device...");
    // ret = spi_bus_remove_device(spi_device);
    // ESP_ERROR_CHECK(ret);
    // ESP_LOGI(TAG, "Freeing SPI bus...");
    // ret = spi_bus_free(SPI_HOST_ID);
    // ESP_ERROR_CHECK(ret);

    ESP_LOGI(TAG, "SPI example finished.");
}
