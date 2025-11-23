#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/spi_master.h"
#include "driver/gpio.h"
#include "esp_log.h"
#include "esp_task_wdt.h"
#include "ADS.h"

void app_main(void)
{
    esp_task_wdt_deinit();
    ADS_Init();
    ADS_SetupInterrupt();
}
