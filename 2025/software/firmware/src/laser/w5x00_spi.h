#ifndef _W5X00_SPI_H_
#define _W5X00_SPI_H_

#define SPI_PORT spi0
#define PIN_SCK 18
#define PIN_MOSI 19
#define PIN_MISO 16
#define PIN_CS 17
#define PIN_RST 20

static inline void wizchip_select(void);
static inline void wizchip_deselect(void);
static uint8_t wizchip_read(void);
static void wizchip_write(uint8_t tx_data);
static void wizchip_critical_section_lock(void);
static void wizchip_critical_section_unlock(void);
void wizchip_spi_initialize(void);
void wizchip_cris_initialize(void);
void wizchip_reset(void);
void wizchip_initialize(void);
void wizchip_check(void);
void network_initialize(wiz_NetInfo net_info);
void print_network_information(wiz_NetInfo net_info);

#endif /* _W5X00_SPI_H_ */
