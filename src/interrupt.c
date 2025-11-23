#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "driver/gpio.h"
#include <stdbool.h>
#define INPUT_PIN 15
#define LED_PIN 2
static volatile bool state = false;

/* Queue to pass GPIO numbers from ISR to a task */
static xQueueHandle gpio_evt_queue = NULL;

#define DEBOUNCE_MS 50

static void IRAM_ATTR gpio_interrupt_handler(void *args)
{
    uint32_t gpio_num = (uint32_t) args;
    BaseType_t xHigherPriorityTaskWoken = pdFALSE;
    /* send the gpio number to the queue from ISR context */
    xQueueSendFromISR(gpio_evt_queue, &gpio_num, &xHigherPriorityTaskWoken);
    if (xHigherPriorityTaskWoken == pdTRUE) {
        portYIELD_FROM_ISR();
    }
}

static void gpio_task(void *arg)
{
    uint32_t io_num;
    TickType_t last_tick = 0;
    for (;;) {
        if (xQueueReceive(gpio_evt_queue, &io_num, portMAX_DELAY)) {
            TickType_t now = xTaskGetTickCount();
            if ((now - last_tick) < pdMS_TO_TICKS(DEBOUNCE_MS)) {
                /* ignore bounces */
                continue;
            }
            last_tick = now;
            state = !state;
            gpio_set_level(LED_PIN, state);
        }
    }
}

void app_main()
{
    /* Configure LED output */
    gpio_set_direction(LED_PIN, GPIO_MODE_OUTPUT);
    gpio_set_level(LED_PIN, 0);

    /* Configure input pin
       Note: choose pull-up or pull-down according to your wiring.
       If your button connects input to GND when pressed, enable pull-up
       and use GPIO_INTR_NEGEDGE (falling). Adjust as needed.
    */
    gpio_set_direction(INPUT_PIN, GPIO_MODE_INPUT);
    gpio_pulldown_en(INPUT_PIN);
    gpio_pullup_dis(INPUT_PIN);
    gpio_set_intr_type(INPUT_PIN, GPIO_INTR_POSEDGE);

    /* Create a queue capable of holding 10 uint32_t values */
    gpio_evt_queue = xQueueCreate(10, sizeof(uint32_t));

    /* Start the task that will handle GPIO events */
    xTaskCreate(gpio_task, "gpio_task", 2048, NULL, 10, NULL);

    /* Install ISR service and add handler */
    gpio_install_isr_service(0);
    gpio_isr_handler_add(INPUT_PIN, gpio_interrupt_handler, (void *)INPUT_PIN);
}