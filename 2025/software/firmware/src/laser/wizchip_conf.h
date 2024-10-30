#ifndef _WIZCHIP_CONF_H_
#define _WIZCHIP_CONF_H_

#include <stdint.h>

typedef uint8_t iodata_t;
#include "w5500.h"

#define _WIZCHIP_SOCK_NUM_ 8

typedef struct __WIZCHIP
{
   struct _CRIS
   {
      void (*_enter)(void); ///< crtical section enter
      void (*_exit)(void);  ///< critial section exit
   } CRIS;

   struct _CS
   {
      void (*_select)(void);   ///< @ref \_WIZCHIP_ selected
      void (*_deselect)(void); ///< @ref \_WIZCHIP_ deselected
   } CS;

   struct _SPI
   {
      uint8_t (*_read_byte)(void);
      void (*_write_byte)(uint8_t wb);
   } SPI;
} _WIZCHIP;

extern _WIZCHIP WIZCHIP;

typedef enum
{
   CW_INIT_WIZCHIP,
   CW_GET_PHYLINK
} ctlwizchip_type;

typedef enum
{
   CN_SET_NETINFO, ///< Set Network with @ref wiz_NetInfo
   CN_GET_NETINFO, ///< Get Network with @ref wiz_NetInfo
} ctlnetwork_type;

#define PHY_LINK_OFF 0      ///< Link Off
#define PHY_LINK_ON 1       ///< Link On

typedef enum
{
   NETINFO_STATIC = 1, ///< Static IP configuration by manually.
   NETINFO_DHCP        ///< Dynamic IP configruation from a DHCP sever
} dhcp_mode;

typedef struct wiz_NetInfo_t
{
   uint8_t mac[6]; ///< Source Mac Address
   uint8_t ip[4];  ///< Source IP Address
   uint8_t sn[4];  ///< Subnet Mask
   uint8_t gw[4];  ///< Gateway IP Address
   uint8_t dns[4]; ///< DNS server IP Address
   dhcp_mode dhcp; ///< 1 - Static, 2 - DHCP
} wiz_NetInfo;

void reg_wizchip_cris_cbfunc(void (*cris_en)(void), void (*cris_ex)(void));
void reg_wizchip_cs_cbfunc(void (*cs_sel)(void), void (*cs_desel)(void));
void reg_wizchip_spi_cbfunc(uint8_t (*spi_rb)(void), void (*spi_wb)(uint8_t wb));
int8_t ctlwizchip(ctlwizchip_type cwtype, void *arg);
int8_t ctlnetwork(ctlnetwork_type cntype, void *arg);
void wizchip_sw_reset(void);
int8_t wizchip_init(uint8_t *txsize, uint8_t *rxsize);
int8_t wizphy_getphylink(void);
void wizchip_setnetinfo(wiz_NetInfo *pnetinfo);
void wizchip_getnetinfo(wiz_NetInfo *pnetinfo);

#endif // _WIZCHIP_CONF_H_
