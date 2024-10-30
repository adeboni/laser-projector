#include <stdio.h>

#include "pico/stdlib.h"
#include "pico/critical_section.h"
#include "hardware/spi.h"
#include "hardware/clocks.h"
#include "hardware/gpio.h"

#include "wizchip_conf.h"
#include "w5x00_spi.h"
#include "socket.h"

static critical_section_t g_wizchip_cri_sec;

static inline void wizchip_select(void)
{
    gpio_put(PIN_CS, 0);
}

static inline void wizchip_deselect(void)
{
    gpio_put(PIN_CS, 1);
}

void wizchip_reset()
{
    gpio_set_dir(PIN_RST, GPIO_OUT);
    gpio_put(PIN_RST, 0);
    sleep_ms(100);
    gpio_put(PIN_RST, 1);
    sleep_ms(100);
}

static uint8_t wizchip_read(void)
{
    uint8_t rx_data = 0;
    uint8_t tx_data = 0xFF;
    spi_read_blocking(SPI_PORT, tx_data, &rx_data, 1);
    return rx_data;
}

static void wizchip_write(uint8_t tx_data)
{
    spi_write_blocking(SPI_PORT, &tx_data, 1);
}

static void wizchip_critical_section_lock(void)
{
    critical_section_enter_blocking(&g_wizchip_cri_sec);
}

static void wizchip_critical_section_unlock(void)
{
    critical_section_exit(&g_wizchip_cri_sec);
}

void wizchip_spi_initialize(void)
{
    // this example will use SPI0 at 5MHz
    spi_init(SPI_PORT, 5000 * 1000);

    gpio_set_function(PIN_SCK, GPIO_FUNC_SPI);
    gpio_set_function(PIN_MOSI, GPIO_FUNC_SPI);
    gpio_set_function(PIN_MISO, GPIO_FUNC_SPI);

    // chip select is active-low, so we'll initialise it to a driven-high state
    gpio_init(PIN_CS);
    gpio_set_dir(PIN_CS, GPIO_OUT);
    gpio_put(PIN_CS, 1);
}

void wizchip_cris_initialize(void)
{
    critical_section_init(&g_wizchip_cri_sec);
    reg_wizchip_cris_cbfunc(wizchip_critical_section_lock, wizchip_critical_section_unlock);
}

void wizchip_initialize(void)
{
    wizchip_deselect();
    reg_wizchip_cs_cbfunc(wizchip_select, wizchip_deselect);
    reg_wizchip_spi_cbfunc(wizchip_read, wizchip_write);

    uint8_t temp;
    uint8_t memsize[2][8] = {{2, 2, 2, 2, 2, 2, 2, 2}, {2, 2, 2, 2, 2, 2, 2, 2}};

    if (ctlwizchip(CW_INIT_WIZCHIP, (void *)memsize) == -1)
    {
        printf(" W5500 initialized fail\n");
        return;
    }

    do
    {
        if (ctlwizchip(CW_GET_PHYLINK, (void *)&temp) == -1)
        {
            printf(" Unknown PHY link status\n");
            return;
        }
    } while (temp == PHY_LINK_OFF);
}

void wizchip_check(void)
{
    if (getVERSIONR() != 0x04)
    {
        printf(" ACCESS ERR : VERSION != 0x04, read value = 0x%02x\n", getVERSIONR());
        while (1)
            ;
    }
}

void network_initialize(wiz_NetInfo net_info)
{
    ctlnetwork(CN_SET_NETINFO, (void *)&net_info);
}

void print_network_information(wiz_NetInfo net_info)
{
    ctlnetwork(CN_GET_NETINFO, (void *)&net_info);

    printf("====================================================================================================\n");

    if (net_info.dhcp == NETINFO_DHCP)
        printf(" Network configuration : DHCP\n\n");
    else
        printf(" Network configuration : Static\n\n");
    
    printf(" MAC         : %02X:%02X:%02X:%02X:%02X:%02X\n", net_info.mac[0], net_info.mac[1], net_info.mac[2], net_info.mac[3], net_info.mac[4], net_info.mac[5]);
    printf(" IP          : %d.%d.%d.%d\n", net_info.ip[0], net_info.ip[1], net_info.ip[2], net_info.ip[3]);
    printf(" Subnet Mask : %d.%d.%d.%d\n", net_info.sn[0], net_info.sn[1], net_info.sn[2], net_info.sn[3]);
    printf(" Gateway     : %d.%d.%d.%d\n", net_info.gw[0], net_info.gw[1], net_info.gw[2], net_info.gw[3]);
    printf(" DNS         : %d.%d.%d.%d\n", net_info.dns[0], net_info.dns[1], net_info.dns[2], net_info.dns[3]);
    printf("====================================================================================================\n\n");
}
