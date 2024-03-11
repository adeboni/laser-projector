#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "pico/float.h"
#include "pico/stdlib.h"
#include "pico/util/queue.h"
#include "pico/multicore.h"
#include "hardware/pwm.h"
#include "hardware/spi.h"
#include "hardware/clocks.h"
#include "wizchip_conf.h"
#include "w5x00_spi.h"
#include "socket.h"

#define DAC_PIN_SCK  10
#define DAC_PIN_MOSI 11
#define DAC_PIN_MISO 12
#define DAC_PIN_CS   13
#define DAC_SPI_PORT spi1
#define PLL_SYS_KHZ (133 * 1000)

#define RED_PIN 2
#define GRN_PIN 3
#define BLU_PIN 4

#define LASER_TIMEOUT     3000
#define LASER_WAIT_US     150
#define POINT_BUFFER_SIZE 1500

typedef struct {
    uint16_t x;
    uint16_t y;
    uint8_t r;
    uint8_t g;
    uint8_t b;
} laser_point_t;

queue_t data_buf;

static void set_clock_khz(void) {
	set_sys_clock_khz(PLL_SYS_KHZ, true);
	clock_configure(
        clk_peri,
        0,                                                // No glitchless mux
        CLOCKS_CLK_PERI_CTRL_AUXSRC_VALUE_CLKSRC_PLL_SYS, // System PLL on AUX mux
        PLL_SYS_KHZ * 1000,                               // Input frequency
        PLL_SYS_KHZ * 1000                                // Output (must be same as no divider)
	);
}

void set_laser(uint8_t r, uint8_t g, uint8_t b) {
    pwm_set_gpio_level(RED_PIN, r >> 1);
    pwm_set_gpio_level(GRN_PIN, g >> 1);
    pwm_set_gpio_level(BLU_PIN, b >> 1);
}

void mcp4922_write(uint16_t x, uint16_t y) {
    if (x > 4095) x = 4095;
    if (y > 4095) y = 4095;
    y = 4095 - y;

    uint8_t xbuf[] = {0x30 | ((x >> 8) & 0x0f), x & 0xff};
    uint8_t ybuf[] = {0xb0 | ((y >> 8) & 0x0f), y & 0xff};

    gpio_put(DAC_PIN_CS, 0);
    spi_write_blocking(DAC_SPI_PORT, xbuf, 2);
    gpio_put(DAC_PIN_CS, 1);

    gpio_put(DAC_PIN_CS, 0);
    spi_write_blocking(DAC_SPI_PORT, ybuf, 2);
    gpio_put(DAC_PIN_CS, 1);
}

void init_pin(uint8_t pin) {
    gpio_set_function(pin, GPIO_FUNC_PWM);
    uint slice_num = pwm_gpio_to_slice_num(pin);

    pwm_config config = pwm_get_default_config();
    pwm_config_set_wrap(&config, 127);
    pwm_init(slice_num, &config, true);
    pwm_set_gpio_level(pin, 0);
}

void init_spi() {
    spi_init(DAC_SPI_PORT, 200000000);
    gpio_set_function(DAC_PIN_MISO, GPIO_FUNC_SPI);
    gpio_set_function(DAC_PIN_SCK, GPIO_FUNC_SPI);
    gpio_set_function(DAC_PIN_MOSI, GPIO_FUNC_SPI);

    gpio_init(DAC_PIN_CS);
    gpio_set_dir(DAC_PIN_CS, GPIO_OUT);
    gpio_put(DAC_PIN_CS, 1);
}

uint8_t get_board_id() {
    gpio_init(6);
    gpio_set_dir(6, GPIO_IN);
    gpio_pull_up(6);
    gpio_init(7);
    gpio_set_dir(7, GPIO_IN);
    gpio_pull_up(7);
    gpio_init(8);
    gpio_set_dir(8, GPIO_IN);
    gpio_pull_up(8);
    uint8_t b0 = 1 - gpio_get(6);
    uint8_t b1 = 1 - gpio_get(7);
    uint8_t b2 = 1 - gpio_get(8);
    return b0 | (b1 << 1) | (b2 << 2);
}

void w5500_init(uint8_t board_id) {
    wizchip_spi_initialize();
	wizchip_cris_initialize();
	wizchip_reset();
	wizchip_initialize();
	wizchip_check();
    
    wiz_NetInfo g_net_info = {
        .mac = {0x00, 0x08, 0xDC, 0x12, 0x34, 0x10 + board_id}, // MAC address
        .ip = {10, 0, 0, 10 + board_id},                        // IP address
        .sn = {255, 255, 255, 0},                               // Subnet Mask
        .gw = {10, 0, 0, 1},                                    // Gateway
        .dns = {8, 8, 8, 8},                                    // DNS server
        .dhcp = NETINFO_STATIC                                  // DHCP enable/disable
    };

	network_initialize(g_net_info);
}

void bytes_to_point(uint8_t *buf, uint16_t i, laser_point_t *target) {
    target->x = buf[i] << 4 | buf[i + 1] >> 4;
    target->y = (buf[i + 1] & 0x0f) << 8 | buf[i + 2];
    target->r = buf[i + 3];
    target->g = buf[i + 4];
    target->b = buf[i + 5];
}

void core1_entry() {
    int sockfd;
    uint8_t dest_ip[4];
    uint16_t dest_port;
    uint8_t recv_buf[DATA_BUF_SIZE];
    uint8_t curr_seq = 0;
    uint8_t board_id = get_board_id();
    w5500_init(board_id);

    while (1) {
        int32_t sock_status = getSn_SR(0);
        if (sock_status == SOCK_CLOSED) {
            sockfd = socket(0, Sn_MR_UDP, 8090, SF_IO_NONBLOCK);
            continue;
        }

        if (sock_status != SOCK_UDP) continue;
        int32_t size = getSn_RX_RSR(sockfd);
        if (size == 0) continue;
        if (size > DATA_BUF_SIZE) size = DATA_BUF_SIZE;
        size = recvfrom(sockfd, recv_buf, size, dest_ip, (uint16_t*)&dest_port);
        if (size <= 0) continue;

        uint8_t new_seq = recv_buf[0];
        if (new_seq < curr_seq && new_seq != 0) {
            curr_seq = new_seq;
            continue;
        }
        curr_seq = new_seq;

        for (uint16_t i = 1; i < size; i += 6) {
            laser_point_t new_point;
            bytes_to_point(recv_buf, i, &new_point);
            queue_add_blocking(&data_buf, &new_point);
        }
    }
}

bool valid_point(laser_point_t *target) {
    return target->x != 0 ||
           target->y != 0 ||
           target->r != 0 ||
           target->g != 0 ||
           target->b != 0;
}

int main() {
    set_clock_khz();
    stdio_init_all();

    gpio_init(PICO_DEFAULT_LED_PIN);
    gpio_set_dir(PICO_DEFAULT_LED_PIN, GPIO_OUT);
    gpio_put(PICO_DEFAULT_LED_PIN, 0);

    init_spi();
    init_pin(RED_PIN);
    init_pin(GRN_PIN);
    init_pin(BLU_PIN);

    queue_init(&data_buf, sizeof(laser_point_t), POINT_BUFFER_SIZE);
    multicore_launch_core1(core1_entry);
    laser_point_t new_point;
    uint32_t last_update = to_ms_since_boot(get_absolute_time());

	while (1) {
        if (queue_try_remove(&data_buf, &new_point) && valid_point(&new_point)) {
            last_update = to_ms_since_boot(get_absolute_time());
            set_laser(new_point.r, new_point.g, new_point.b);
            mcp4922_write(new_point.x, new_point.y);
        }

        if (to_ms_since_boot(get_absolute_time()) - last_update > LASER_TIMEOUT)
            set_laser(0, 0, 0);

        sleep_us(LASER_WAIT_US);
	}
}
