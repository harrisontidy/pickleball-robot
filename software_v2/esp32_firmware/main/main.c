#include <stdint.h>

#include "driver/gpio.h"
#include "driver/ledc.h"
#include "esp_err.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#define SERVO_FREQUENCY_HZ      50
#define SERVO_PERIOD_US          20000U
#define SERVO_TIMER_BITS         LEDC_TIMER_14_BIT
#define SERVO_TIMER_MAX_DUTY     ((1U << 14) - 1U)
#define STARTUP_SAFETY_DELAY_MS  5000
#define SERVO_OUTPUTS_ENABLED    0

static const char *TAG = "servo_center";

typedef struct {
    const char *header;
    gpio_num_t gpio;
    ledc_channel_t channel;
    uint32_t target_us;
} servo_output_t;

static const servo_output_t servos[] = {
    {"J3 / MS62 main swing", GPIO_NUM_25, LEDC_CHANNEL_0, 1500U},
    {"J4 / unused MG996", GPIO_NUM_26, LEDC_CHANNEL_1, 1500U},
    {"J5 / paddle MG996", GPIO_NUM_27, LEDC_CHANNEL_2, 1110U},
    {"J9 / camera MG90", GPIO_NUM_21, LEDC_CHANNEL_3, 1300U},
};

static uint32_t pulse_us_to_duty(uint32_t pulse_us)
{
    return (uint32_t)(((uint64_t)pulse_us * SERVO_TIMER_MAX_DUTY) /
                      SERVO_PERIOD_US);
}

void app_main(void)
{
    if (!SERVO_OUTPUTS_ENABLED) {
        ESP_LOGI(TAG, "Safe idle: all servo PWM outputs are disabled");
        while (true) {
            vTaskDelay(pdMS_TO_TICKS(5000));
        }
    }

    ESP_LOGI(TAG, "Waiting 5 seconds before enabling servo outputs");
    vTaskDelay(pdMS_TO_TICKS(STARTUP_SAFETY_DELAY_MS));

    const ledc_timer_config_t timer = {
        .speed_mode = LEDC_HIGH_SPEED_MODE,
        .duty_resolution = SERVO_TIMER_BITS,
        .timer_num = LEDC_TIMER_0,
        .freq_hz = SERVO_FREQUENCY_HZ,
        .clk_cfg = LEDC_AUTO_CLK,
    };
    ESP_ERROR_CHECK(ledc_timer_config(&timer));

    ESP_LOGI(TAG, "Applying calibrated servo positions simultaneously");

    for (unsigned int i = 0; i < sizeof(servos) / sizeof(servos[0]); ++i) {
        const ledc_channel_config_t output = {
            .gpio_num = servos[i].gpio,
            .speed_mode = LEDC_HIGH_SPEED_MODE,
            .channel = servos[i].channel,
            .intr_type = LEDC_INTR_DISABLE,
            .timer_sel = LEDC_TIMER_0,
            .duty = pulse_us_to_duty(servos[i].target_us),
            .hpoint = 0,
            .flags.output_invert = 0,
        };

        ESP_ERROR_CHECK(ledc_channel_config(&output));
        ESP_LOGI(TAG, "%s on GPIO %d enabled at %lu us",
                 servos[i].header, servos[i].gpio,
                 (unsigned long)servos[i].target_us);
    }

    ESP_LOGI(TAG, "All four servo outputs are holding their target positions");
    while (true) {
        vTaskDelay(pdMS_TO_TICKS(5000));
    }
}
