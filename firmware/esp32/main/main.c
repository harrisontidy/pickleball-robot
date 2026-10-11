#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "driver/ledc.h"
#include "driver/uart.h"
#include "esp_err.h"
#include "esp_event.h"
#include "esp_http_server.h"
#include "esp_log.h"
#include "esp_netif.h"
#include "esp_timer.h"
#include "esp_wifi.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "nvs_flash.h"

#define LEFT_IN1_GPIO       GPIO_NUM_32
#define LEFT_IN2_GPIO       GPIO_NUM_33
#define RIGHT_IN1_GPIO      GPIO_NUM_13
#define RIGHT_IN2_GPIO      GPIO_NUM_14

#define WIFI_SSID           "PickleBot-Drive"
#define WIFI_PASSWORD       "picklebot"
#define PWM_FREQUENCY_HZ    5000
#define PWM_MAX_DUTY        1023
#define COMMAND_TIMEOUT_MS  900
#define SERVO_PULSE_US      1500U
#define SERVO_PERIOD_US     20000U
#define SERVO_MAX_DUTY      ((1U << 14) - 1U)
#define SERVO_MIN_US        500
#define SERVO_MAX_US        2500

/* The two wheel motors face opposite directions on the robot. */
#define RIGHT_MOTOR_REVERSED true

/*
 * Mechanical note (2026-08-27): the first drive version was backwards on the
 * assembled chassis. Negate both requested wheel speeds before applying the
 * per-side wiring reversal so the web page's Forward button moves forward.
 */
#define CHASSIS_DRIVE_POLARITY (-1)

enum {
    SERVO_CAMERA_PAN = 0,       /* J3 / GPIO25 */
    SERVO_SWING_TILT = 1,       /* J4 / GPIO26 */
    SERVO_MAIN_SWING = 2,       /* J5 / GPIO27 */
    SERVO_WRIST_TILT = 3,       /* J9 / GPIO21 (J7 is USB-C power) */
    SERVO_COUNT = 4,
};

extern const uint8_t index_html_start[] asm("_binary_index_html_start");
extern const uint8_t index_html_end[] asm("_binary_index_html_end");

static const char *TAG = "phone_drive";
static volatile int64_t last_command_us;
static volatile int commanded_left;
static volatile int commanded_right;
static volatile int servo_positions_us[SERVO_COUNT] = {
    SERVO_PULSE_US, SERVO_PULSE_US, SERVO_PULSE_US, SERVO_PULSE_US
};
static volatile bool swing_running;
static volatile bool swing_abort;

/* Retained only as a fallback reference while the v4 page is embedded separately. */
static const char INDEX_HTML[] __attribute__((unused)) =
"<!doctype html><html><head><meta name='viewport' content='width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no'>"
"<meta http-equiv='Cache-Control' content='no-cache,no-store,must-revalidate'><title>PickleBot Drive v2</title><style>"
"*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}html,body{margin:0;background:#0e1410;color:#fff;font-family:Arial,sans-serif;overscroll-behavior:none}"
"body{min-height:100vh;padding:14px;display:flex;justify-content:center}main{width:100%;max-width:430px;text-align:center}"
".card{background:#19231c;border:1px solid #35493b;border-radius:20px;padding:18px}h1{margin:2px 0 4px;font-size:28px}.ver{color:#8b9b90;font-size:12px}"
"#status{background:#102f1b;color:#8ff0a8;border-radius:12px;padding:11px;margin:12px 0;font-weight:bold;min-height:40px}.bad{background:#3b1717!important;color:#ff9b9b!important}"
".speed{font-size:19px;font-weight:bold;margin:14px 0 7px}input{width:100%;height:35px;accent-color:#72d58b}.presets{display:flex;gap:7px;margin:7px 0 18px}"
"button{border:0;border-radius:14px;background:#34483a;color:#fff;font-weight:bold;touch-action:none;-webkit-user-select:none;user-select:none}"
".presets button{flex:1;height:45px}.pad{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.pad button{height:88px;font-size:34px}"
"button.active{background:#4db96c;box-shadow:0 0 0 3px #9ef2b5 inset}.stop{background:#b53c3c;font-size:19px!important}.blank{visibility:hidden}"
".power{background:#302811;color:#ffe28a;border-radius:12px;padding:10px;font-size:13px;line-height:1.35;margin-top:14px}.note{color:#a8b7ac;font-size:13px;line-height:1.4}"
"</style></head><body><main><div class='card'><h1>PickleBot Drive</h1><div class='ver'>controller v2</div><div id='status'>ESP connected - stopped</div>"
"<div class='speed'>Speed: <span id='speedText'>60</span>%</div><input id='speed' type='range' min='20' max='100' value='60'>"
"<div class='presets'><button data-speed='35'>35%</button><button data-speed='55'>55%</button><button data-speed='75'>75%</button><button data-speed='100'>100%</button></div>"
"<div class='pad'><span class='blank'></span><button data-dir='f'>&#9650;</button><span class='blank'></span><button data-dir='l'>&#9664;</button>"
"<button class='stop' data-dir='s'>STOP</button><button data-dir='r'>&#9654;</button><span class='blank'></span><button data-dir='b'>&#9660;</button><span class='blank'></span></div>"
"<div class='power'>Motor voltage comes from PCB VIN/J1 through the fuse, not from ESP32 USB.</div><p class='note'>Hold a direction to drive. The green message must say ESP ACK. Releasing always stops.</p>"
"</div></main><script>"
"var speed=document.getElementById('speed'),speedText=document.getElementById('speedText'),statusBox=document.getElementById('status');var timer=0,held=null,requestNumber=0,shownNumber=0;"
"function mix(d,v){if(d==='f')return{l:v,r:v};if(d==='b')return{l:-v,r:-v};if(d==='l')return{l:-v,r:v};if(d==='r')return{l:v,r:-v};return{l:0,r:0};}"
"function command(d){var v=parseInt(speed.value,10),m=mix(d,v),n=++requestNumber,x=new XMLHttpRequest();x.open('GET','/api/drive?l='+m.l+'&r='+m.r+'&n='+n+'&t='+Date.now(),true);"
"x.onreadystatechange=function(){if(x.readyState===4&&n>=shownNumber){shownNumber=n;if(x.status===200){statusBox.className='';statusBox.textContent='ESP ACK: left '+m.l+'% / right '+m.r+'%';}else{statusBox.className='bad';statusBox.textContent='No reply - wheels will stop';}}};x.onerror=function(){statusBox.className='bad';statusBox.textContent='Connection lost - wheels stopping';};x.send();}"
"function release(){if(timer){clearInterval(timer);timer=0;}if(held){held.classList.remove('active');held=null;}command('s');}"
"function press(e){if(e)e.preventDefault();if(timer)clearInterval(timer);if(held)held.classList.remove('active');held=this;held.classList.add('active');var d=this.getAttribute('data-dir');command(d);if(d!=='s')timer=setInterval(function(){command(d);},250);}"
"var dirs=document.querySelectorAll('[data-dir]'),i;if(window.PointerEvent){for(i=0;i<dirs.length;i++)dirs[i].addEventListener('pointerdown',press);window.addEventListener('pointerup',release);window.addEventListener('pointercancel',release);}else{for(i=0;i<dirs.length;i++){dirs[i].addEventListener('touchstart',press,{passive:false});dirs[i].addEventListener('mousedown',press);}window.addEventListener('touchend',release);window.addEventListener('touchcancel',release);window.addEventListener('mouseup',release);}"
"speed.oninput=function(){speedText.textContent=speed.value;};var presets=document.querySelectorAll('[data-speed]');for(i=0;i<presets.length;i++)presets[i].onclick=function(){speed.value=this.getAttribute('data-speed');speedText.textContent=speed.value;};"
"document.addEventListener('visibilitychange',function(){if(document.hidden)release();});window.addEventListener('pagehide',release);command('s');"
"</script></body></html>";

static int clamp_percent(int value)
{
    if (value > 100) return 100;
    if (value < -100) return -100;
    return value;
}

static void set_channel(ledc_channel_t channel, uint32_t duty)
{
    ESP_ERROR_CHECK(ledc_set_duty(LEDC_LOW_SPEED_MODE, channel, duty));
    ESP_ERROR_CHECK(ledc_update_duty(LEDC_LOW_SPEED_MODE, channel));
}

static void set_one_motor(int percent, ledc_channel_t in1, ledc_channel_t in2)
{
    percent = clamp_percent(percent);
    const uint32_t duty = (uint32_t)(abs(percent) * PWM_MAX_DUTY / 100);
    if (percent > 0) {
        set_channel(in1, duty);
        set_channel(in2, 0);
    } else if (percent < 0) {
        set_channel(in1, 0);
        set_channel(in2, duty);
    } else {
        set_channel(in1, 0);
        set_channel(in2, 0);
    }
}

static void set_wheels(int left, int right)
{
    left *= CHASSIS_DRIVE_POLARITY;
    right *= CHASSIS_DRIVE_POLARITY;
    set_one_motor(left, LEDC_CHANNEL_0, LEDC_CHANNEL_1);
    set_one_motor(RIGHT_MOTOR_REVERSED ? -right : right,
                  LEDC_CHANNEL_2, LEDC_CHANNEL_3);
}

static void init_motor_pwm(void)
{
    const ledc_timer_config_t timer = {
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .duty_resolution = LEDC_TIMER_10_BIT,
        .timer_num = LEDC_TIMER_0,
        .freq_hz = PWM_FREQUENCY_HZ,
        .clk_cfg = LEDC_AUTO_CLK,
    };
    ESP_ERROR_CHECK(ledc_timer_config(&timer));

    const gpio_num_t pins[] = {
        LEFT_IN1_GPIO, LEFT_IN2_GPIO, RIGHT_IN1_GPIO, RIGHT_IN2_GPIO
    };
    for (int i = 0; i < 4; ++i) {
        const ledc_channel_config_t channel = {
            .gpio_num = pins[i],
            .speed_mode = LEDC_LOW_SPEED_MODE,
            .channel = (ledc_channel_t)i,
            .intr_type = LEDC_INTR_DISABLE,
            .timer_sel = LEDC_TIMER_0,
            .duty = 0,
            .hpoint = 0,
            .flags.output_invert = 0,
        };
        ESP_ERROR_CHECK(ledc_channel_config(&channel));
    }
    set_wheels(0, 0);
}

static void init_centered_servos(void)
{
    const ledc_timer_config_t timer = {
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .duty_resolution = LEDC_TIMER_14_BIT,
        .timer_num = LEDC_TIMER_1,
        .freq_hz = 50,
        .clk_cfg = LEDC_AUTO_CLK,
    };
    ESP_ERROR_CHECK(ledc_timer_config(&timer));

    const gpio_num_t pins[] = {
        GPIO_NUM_25, GPIO_NUM_26, GPIO_NUM_27, GPIO_NUM_21
    };
    const uint32_t center_duty =
        (uint32_t)(((uint64_t)SERVO_PULSE_US * SERVO_MAX_DUTY) /
                   SERVO_PERIOD_US);

    for (int i = 0; i < 4; ++i) {
        const ledc_channel_config_t channel = {
            .gpio_num = pins[i],
            .speed_mode = LEDC_LOW_SPEED_MODE,
            .channel = (ledc_channel_t)(LEDC_CHANNEL_4 + i),
            .intr_type = LEDC_INTR_DISABLE,
            .timer_sel = LEDC_TIMER_1,
            .duty = center_duty,
            .hpoint = 0,
            .flags.output_invert = 0,
        };
        ESP_ERROR_CHECK(ledc_channel_config(&channel));
    }
    ESP_LOGI(TAG, "All servos centered at 1500 us: GPIO25, GPIO26, GPIO27, GPIO21");
}

static int clamp_servo_us(int pulse_us)
{
    if (pulse_us < SERVO_MIN_US) return SERVO_MIN_US;
    if (pulse_us > SERVO_MAX_US) return SERVO_MAX_US;
    return pulse_us;
}

static void set_servo_us(int channel, int pulse_us)
{
    if (channel < 0 || channel >= SERVO_COUNT) return;
    pulse_us = clamp_servo_us(pulse_us);
    const uint32_t duty =
        (uint32_t)(((uint64_t)pulse_us * SERVO_MAX_DUTY) / SERVO_PERIOD_US);
    set_channel((ledc_channel_t)(LEDC_CHANNEL_4 + channel), duty);
    servo_positions_us[channel] = pulse_us;
}

static void center_all_servos(void)
{
    for (int i = 0; i < SERVO_COUNT; ++i) {
        set_servo_us(i, SERVO_PULSE_US);
    }
}

static bool swing_wait(int milliseconds)
{
    for (int elapsed = 0; elapsed < milliseconds; elapsed += 20) {
        if (swing_abort) return false;
        vTaskDelay(pdMS_TO_TICKS(20));
    }
    return !swing_abort;
}

static void set_swing_joints(int tilt_us, int main_us, int wrist_us)
{
    set_servo_us(SERVO_SWING_TILT, tilt_us);
    set_servo_us(SERVO_MAIN_SWING, main_us);
    set_servo_us(SERVO_WRIST_TILT, wrist_us);
}

static void swing_task(void *argument)
{
    const int swing_type = (int)(intptr_t)argument;
    center_all_servos();
    if (!swing_wait(120)) goto done;

    if (swing_type == 1) {
        /* Small, slow test: only +/-80 us around center on the three swing joints. */
        set_swing_joints(1460, 1420, 1540);
        if (!swing_wait(280)) goto done;
        set_swing_joints(1540, 1580, 1460);
        swing_wait(280);
    } else {
        /*
         * Larger coordinated swing requested after the mechanical redesign.
         * 1500 us is the nominal electrical center. J5 travels +/-600 us;
         * J4 and J9 travel +/-300 us. Do not extend to 3000 us until each
         * servo's actual electrical and mechanical end stops are verified.
         */
        set_swing_joints(1200, 900, 1800);
        if (!swing_wait(420)) goto done;
        set_swing_joints(1800, 2100, 1200);
        swing_wait(180);
    }

done:
    center_all_servos();
    swing_running = false;
    swing_abort = false;
    ESP_LOGI(TAG, "Swing complete; all servos holding 1500 us");
    vTaskDelete(NULL);
}

static bool start_swing(int swing_type)
{
    if (swing_running) return false;
    swing_abort = false;
    swing_running = true;
    if (xTaskCreate(swing_task, "servo_swing", 3072,
                    (void *)(intptr_t)swing_type, 8, NULL) != pdPASS) {
        swing_running = false;
        return false;
    }
    return true;
}

static void failsafe_task(void *unused)
{
    (void)unused;
    bool timed_out = false;
    while (true) {
        const int64_t age_ms = (esp_timer_get_time() - last_command_us) / 1000;
        if (age_ms > COMMAND_TIMEOUT_MS && !timed_out) {
            set_wheels(0, 0);
            commanded_left = 0;
            commanded_right = 0;
            timed_out = true;
            ESP_LOGW(TAG, "Command timeout: wheels stopped");
        } else if (age_ms <= COMMAND_TIMEOUT_MS) {
            timed_out = false;
        }
        vTaskDelay(pdMS_TO_TICKS(50));
    }
}

static esp_err_t index_handler(httpd_req_t *req)
{
    httpd_resp_set_type(req, "text/html");
    httpd_resp_set_hdr(req, "Cache-Control", "no-store");
    return httpd_resp_send(req, (const char *)index_html_start,
                           index_html_end - index_html_start);
}

static esp_err_t drive_handler(httpd_req_t *req)
{
    char query[80] = {0};
    char value[12];
    char response[96];
    int left = 0;
    int right = 0;

    if (httpd_req_get_url_query_str(req, query, sizeof(query)) == ESP_OK) {
        if (httpd_query_key_value(query, "l", value, sizeof(value)) == ESP_OK) {
            left = atoi(value);
        }
        if (httpd_query_key_value(query, "r", value, sizeof(value)) == ESP_OK) {
            right = atoi(value);
        }
    }
    left = clamp_percent(left);
    right = clamp_percent(right);
    if (left != commanded_left || right != commanded_right) {
        ESP_LOGI(TAG, "WEB COMMAND: left=%d%% right=%d%%", left, right);
    }
    set_wheels(left, right);
    commanded_left = left;
    commanded_right = right;
    last_command_us = esp_timer_get_time();
    httpd_resp_set_type(req, "application/json");
    snprintf(response, sizeof(response),
             "{\"ok\":true,\"left\":%d,\"right\":%d}", left, right);
    return httpd_resp_sendstr(req, response);
}

static esp_err_t stop_handler(httpd_req_t *req)
{
    set_wheels(0, 0);
    commanded_left = 0;
    commanded_right = 0;
    last_command_us = esp_timer_get_time();
    return httpd_resp_sendstr(req, "OK");
}

static esp_err_t servo_handler(httpd_req_t *req)
{
    char query[80] = {0};
    char value[12];
    char response[96];
    int channel = -1;
    int pulse_us = SERVO_PULSE_US;

    if (swing_running) {
        httpd_resp_set_status(req, "409 Conflict");
        return httpd_resp_sendstr(req, "{\"ok\":false,\"error\":\"swing running\"}");
    }
    if (httpd_req_get_url_query_str(req, query, sizeof(query)) == ESP_OK) {
        if (httpd_query_key_value(query, "ch", value, sizeof(value)) == ESP_OK) {
            channel = atoi(value);
        }
        if (httpd_query_key_value(query, "us", value, sizeof(value)) == ESP_OK) {
            pulse_us = atoi(value);
        }
    }
    if (channel < 0 || channel >= SERVO_COUNT) {
        httpd_resp_set_status(req, "400 Bad Request");
        return httpd_resp_sendstr(req, "{\"ok\":false,\"error\":\"bad channel\"}");
    }
    set_servo_us(channel, pulse_us);
    pulse_us = servo_positions_us[channel];
    ESP_LOGI(TAG, "SERVO: channel=%d pulse=%d us", channel, pulse_us);
    httpd_resp_set_type(req, "application/json");
    snprintf(response, sizeof(response),
             "{\"ok\":true,\"channel\":%d,\"us\":%d}", channel, pulse_us);
    return httpd_resp_sendstr(req, response);
}

static esp_err_t swing_handler(httpd_req_t *req)
{
    char query[48] = {0};
    char type[12] = {0};
    if (httpd_req_get_url_query_str(req, query, sizeof(query)) == ESP_OK) {
        httpd_query_key_value(query, "type", type, sizeof(type));
    }

    if (strcmp(type, "center") == 0) {
        swing_abort = true;
        center_all_servos();
        ESP_LOGI(TAG, "CENTER ALL: four servos holding 1500 us");
        return httpd_resp_sendstr(req, "{\"ok\":true,\"action\":\"center\"}");
    }

    const int swing_type = strcmp(type, "main") == 0 ? 2 : 1;
    if (!start_swing(swing_type)) {
        httpd_resp_set_status(req, "409 Conflict");
        return httpd_resp_sendstr(req, "{\"ok\":false,\"error\":\"swing running\"}");
    }
    ESP_LOGI(TAG, "Starting %s swing", swing_type == 2 ? "coordinated" : "small");
    return httpd_resp_sendstr(req, "{\"ok\":true,\"action\":\"swing\"}");
}

static void start_web_server(void)
{
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    config.lru_purge_enable = true;
    httpd_handle_t server = NULL;
    ESP_ERROR_CHECK(httpd_start(&server, &config));

    const httpd_uri_t index_uri = {
        .uri = "/", .method = HTTP_GET, .handler = index_handler
    };
    const httpd_uri_t drive_uri = {
        .uri = "/api/drive", .method = HTTP_GET, .handler = drive_handler
    };
    const httpd_uri_t stop_uri = {
        .uri = "/api/stop", .method = HTTP_POST, .handler = stop_handler
    };
    const httpd_uri_t servo_uri = {
        .uri = "/api/servo", .method = HTTP_GET, .handler = servo_handler
    };
    const httpd_uri_t swing_uri = {
        .uri = "/api/swing", .method = HTTP_GET, .handler = swing_handler
    };
    ESP_ERROR_CHECK(httpd_register_uri_handler(server, &index_uri));
    ESP_ERROR_CHECK(httpd_register_uri_handler(server, &drive_uri));
    ESP_ERROR_CHECK(httpd_register_uri_handler(server, &stop_uri));
    ESP_ERROR_CHECK(httpd_register_uri_handler(server, &servo_uri));
    ESP_ERROR_CHECK(httpd_register_uri_handler(server, &swing_uri));
}

static void start_wifi_access_point(void)
{
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    esp_netif_create_default_wifi_ap();

    wifi_init_config_t init = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&init));

    wifi_config_t config = {0};
    strlcpy((char *)config.ap.ssid, WIFI_SSID, sizeof(config.ap.ssid));
    strlcpy((char *)config.ap.password, WIFI_PASSWORD, sizeof(config.ap.password));
    config.ap.ssid_len = strlen(WIFI_SSID);
    config.ap.channel = 1;
    config.ap.max_connection = 4;
    config.ap.authmode = WIFI_AUTH_WPA2_PSK;

    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_AP));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_AP, &config));
    ESP_ERROR_CHECK(esp_wifi_start());
}

static void handle_usb_serial_command(char *line)
{
    int left;
    int right;
    int channel;
    int pulse_us;

    if (sscanf(line, "DRIVE,%d,%d", &left, &right) == 2) {
        left = clamp_percent(left);
        right = clamp_percent(right);
        set_wheels(left, right);
        commanded_left = left;
        commanded_right = right;
        last_command_us = esp_timer_get_time();
        ESP_LOGI(TAG, "USB DRIVE: left=%d%% right=%d%%", left, right);
    } else if (strcmp(line, "STOP") == 0) {
        set_wheels(0, 0);
        commanded_left = 0;
        commanded_right = 0;
        last_command_us = esp_timer_get_time();
        ESP_LOGI(TAG, "USB STOP");
    } else if (sscanf(line, "SERVO,%d,%d", &channel, &pulse_us) == 2) {
        if (!swing_running && channel >= 0 && channel < SERVO_COUNT) {
            set_servo_us(channel, pulse_us);
            ESP_LOGI(TAG, "USB SERVO: channel=%d pulse=%d us",
                     channel, servo_positions_us[channel]);
        }
    } else if (strcmp(line, "SWING,SMALL") == 0) {
        start_swing(1);
    } else if (strcmp(line, "SWING,MAIN") == 0) {
        start_swing(2);
    } else if (strcmp(line, "SWING,CENTER") == 0) {
        swing_abort = true;
        center_all_servos();
    } else if (strcmp(line, "PING") == 0) {
        ESP_LOGI(TAG, "PONG");
    } else if (line[0] != '\0') {
        ESP_LOGW(TAG, "Unknown USB command: %s", line);
    }
}

static void usb_serial_task(void *unused)
{
    (void)unused;
    char line[96];
    size_t used = 0;
    uint8_t byte;

    while (true) {
        if (uart_read_bytes(UART_NUM_0, &byte, 1, pdMS_TO_TICKS(50)) != 1) {
            continue;
        }
        if (byte == '\r' || byte == '\n') {
            if (used > 0) {
                line[used] = '\0';
                handle_usb_serial_command(line);
                used = 0;
            }
        } else if (byte >= 32 && byte <= 126) {
            if (used < sizeof(line) - 1) {
                line[used++] = (char)byte;
            } else {
                used = 0;
            }
        }
    }
}

static void start_usb_serial_control(void)
{
    esp_err_t result = uart_driver_install(UART_NUM_0, 1024, 0, 0, NULL, 0);
    if (result != ESP_OK && result != ESP_ERR_INVALID_STATE) {
        ESP_ERROR_CHECK(result);
    }
    ESP_ERROR_CHECK(uart_set_baudrate(UART_NUM_0, 115200));
    xTaskCreate(usb_serial_task, "usb_serial_control", 3072, NULL, 9, NULL);
    ESP_LOGI(TAG, "USB serial control ready at 115200 baud");
}

void app_main(void)
{
    esp_err_t nvs_result = nvs_flash_init();
    if (nvs_result == ESP_ERR_NVS_NO_FREE_PAGES ||
        nvs_result == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ESP_ERROR_CHECK(nvs_flash_init());
    } else {
        ESP_ERROR_CHECK(nvs_result);
    }

    init_motor_pwm();
    last_command_us = esp_timer_get_time();
    ESP_LOGW(TAG, "SAFE IDLE: wheel outputs are off");
    init_centered_servos();
    start_usb_serial_control();

    start_wifi_access_point();
    start_web_server();
    xTaskCreate(failsafe_task, "wheel_failsafe", 3072, NULL, 10, NULL);

    ESP_LOGI(TAG, "Connect phone to %s (password: %s)", WIFI_SSID, WIFI_PASSWORD);
    ESP_LOGI(TAG, "Open http://192.168.4.1");
}
