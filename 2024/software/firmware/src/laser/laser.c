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
#include "httpClient.h"

#define DAC_PIN_SCK  10
#define DAC_PIN_MOSI 11
#define DAC_PIN_MISO 12
#define DAC_PIN_CS   13
#define DAC_SPI_PORT spi1

#define RED_PIN 2
#define GRN_PIN 3
#define BLU_PIN 4

#define LASER_ID 1 //change this to read from the dip switches
#define POINT_BUFFER_LEN        2048
#define POINT_BUFFER_THRESHOLD  1024
#define PLL_SYS_KHZ (133 * 1000)

typedef struct {
    uint16_t x;
    uint16_t y;
    uint8_t r;
    uint8_t g;
    uint8_t b;
} laser_point_t;

queue_t data_buf;

static wiz_NetInfo g_net_info = {
	.mac = {0x00, 0x08, 0xDC, 0x12, 0x34, 0x11}, // MAC address
	.ip = {192, 168, 11, 11},                    // IP address
	.sn = {255, 255, 255, 0},                    // Subnet Mask
	.gw = {192, 168, 11, 1},                     // Gateway
	.dns = {8, 8, 8, 8},                         // DNS server
	.dhcp = NETINFO_STATIC                       // DHCP enable/disable
};

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

    sleep_us(150);
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

void init_w5500() {
    wizchip_spi_initialize();
	wizchip_cris_initialize();
	wizchip_reset();
	wizchip_initialize();
	wizchip_check();
	network_initialize(g_net_info);
	//print_network_information(g_net_info);
}

void core1_entry() {
    uint8_t ip_address[4]  = {0,};
    uint8_t domain_name[] = "192.168.11.10:8100";
    uint8_t uri[20];
    sprintf(uri, "/laser_data/%d/%d/", LASER_ID, POINT_BUFFER_LEN - POINT_BUFFER_THRESHOLD);
    uint8_t g_send_buf[(POINT_BUFFER_LEN - POINT_BUFFER_THRESHOLD) * 6 + 512];
    uint8_t g_recv_buf[(POINT_BUFFER_LEN - POINT_BUFFER_THRESHOLD) * 6 + 512];
    httpc_init(0, ip_address, 8101, g_send_buf, g_recv_buf);
    bool sent_request = false;

    while (1) {
        if (queue_get_level_unsafe(&data_buf) < POINT_BUFFER_THRESHOLD) {
            httpc_connection_handler();
            if (httpc_isSockOpen)
				httpc_connect();
			
            if (httpc_isConnected) {
                if (!sent_request) {
                    request.method = (uint8_t *)HTTP_GET;
                    request.uri = (uint8_t *)uri;
                    request.host = (uint8_t *)domain_name;
                    httpc_send(&request, g_recv_buf, g_send_buf, 0);
                    sent_request = true;
                }

                if (httpc_isReceived > 0) {
                    int len = httpc_recv(g_recv_buf, httpc_isReceived);
                    printf(" >> HTTP Response - Received len: %d\r\n", len);
                    printf("======================================================\r\n");
                    for (int i = 0; i < len; i++) printf("%c", g_recv_buf[i]);
                    printf("\r\n");
                    printf("======================================================\r\n");
                    sent_request = false;
                }
            }
            
            for (int i = 0; i <= 360; i += 8) {
                uint16_t x = (uint16_t)(1000 * sin(i * 3.14 / 180) + 2048);
                uint16_t y = (uint16_t)(1000 * cos(i * 3.14 / 180) + 2048);
                uint8_t r = i % 255;
                uint8_t g = (i + 60) % 255;
                uint8_t b = (i + 120) % 255;
                laser_point_t new_point = {x, y, r, g, b};
                queue_add_blocking(&data_buf, &new_point);
            }
        }
    }
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
    init_w5500();    

    queue_init(&data_buf, sizeof(laser_point_t), POINT_BUFFER_LEN);
    multicore_launch_core1(core1_entry);
    laser_point_t new_point;

	while (1)
	{
        queue_remove_blocking(&data_buf, &new_point);
        set_laser(new_point.r, new_point.g, new_point.b);
        mcp4922_write(new_point.x, new_point.y);
        sleep_us(150);
	}
}

void test_circle() {
    for (int i = 0; i <= 360; i += 8) {
        uint16_t x = (uint16_t)(1000 * sin(i * 3.14 / 180) + 2048);
        uint16_t y = (uint16_t)(1000 * cos(i * 3.14 / 180) + 2048);
        uint8_t r = i % 255;
        uint8_t g = (i + 60) % 255;
        uint8_t b = (i + 120) % 255;
        set_laser(r, g, b);
        mcp4922_write(x, y);
        sleep_us(150);
    }
}

/*
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
    
    wizchip_spi_initialize();
	wizchip_cris_initialize();
	wizchip_reset();
	wizchip_initialize();
	wizchip_check();
	network_initialize(g_net_info);
	//print_network_information(g_net_info);



	int sockfd;
	e131_packet_t packet;
	e131_error_t error;
    uint8_t last_seq = 0x00;

	if ((sockfd = e131_socket()) < 0) {
		printf("e131_socket error\n");
		while (1);
	}

	while (1)
	{
		if (e131_recv(sockfd, &packet) <= 0)
			continue;

		if ((error = e131_pkt_validate(&packet)) != E131_ERR_NONE) {
			//printf("e131_pkt_validate: %s\n", e131_strerror(error));
			continue;
		}
		
		if (e131_pkt_discard(&packet, last_seq)) {
			//printf("warning: packet out of order received\n");
			last_seq = packet.frame.seq_number;
			continue;
		}

		//e131_pkt_dump(&packet);
		last_seq = packet.frame.seq_number;

        test_circle();

        for (int i = 0; i < packet.dmp.prop_val_cnt; i += 6) {
            uint16_t b0 = packet.dmp.prop_val[i];
            uint16_t b1 = packet.dmp.prop_val[i + 1];
            uint16_t b2 = packet.dmp.prop_val[i + 2];
            uint16_t x = b0 << 4 | b1 >> 4;
            uint16_t y = (b1 & 0x0f) << 8 | b2;
            uint8_t r = packet.dmp.prop_val[i + 3];
            uint8_t g = packet.dmp.prop_val[i + 4];
            uint8_t b = packet.dmp.prop_val[i + 5];

            set_laser(r, g, b);

            if (x == 0 && y == 0)
                break;

            mcp4922_write(x, y);
            sleep_us(150);
        }

        gpio_put(PICO_DEFAULT_LED_PIN, 1);
        sleep_ms(100);
        gpio_put(PICO_DEFAULT_LED_PIN, 0);
        sleep_ms(100);
	}
}
*/