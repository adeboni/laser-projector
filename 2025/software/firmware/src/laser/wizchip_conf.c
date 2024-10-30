#include <stddef.h>
#include "wizchip_conf.h"

void wizchip_cris_enter(void) {}
void wizchip_cris_exit(void) {}
void wizchip_cs_select(void) {}
void wizchip_cs_deselect(void) {}
uint8_t wizchip_spi_readbyte(void) { return 0; }
void wizchip_spi_writebyte(uint8_t wb) {}

_WIZCHIP WIZCHIP =
{
   { wizchip_cris_enter, wizchip_cris_exit },
   { wizchip_cs_select, wizchip_cs_deselect },
   { wizchip_spi_readbyte, wizchip_spi_writebyte }
};

static uint8_t _DNS_[4];
static dhcp_mode _DHCP_;

void reg_wizchip_cris_cbfunc(void (*cris_en)(void), void (*cris_ex)(void))
{
   if (!cris_en || !cris_ex)
   {
      WIZCHIP.CRIS._enter = wizchip_cris_enter;
      WIZCHIP.CRIS._exit = wizchip_cris_exit;
   }
   else
   {
      WIZCHIP.CRIS._enter = cris_en;
      WIZCHIP.CRIS._exit = cris_ex;
   }
}

void reg_wizchip_cs_cbfunc(void (*cs_sel)(void), void (*cs_desel)(void))
{
   if (!cs_sel || !cs_desel)
   {
      WIZCHIP.CS._select = wizchip_cs_select;
      WIZCHIP.CS._deselect = wizchip_cs_deselect;
   }
   else
   {
      WIZCHIP.CS._select = cs_sel;
      WIZCHIP.CS._deselect = cs_desel;
   }
}

void reg_wizchip_spi_cbfunc(uint8_t (*spi_rb)(void), void (*spi_wb)(uint8_t wb))
{
   if (!spi_rb || !spi_wb)
   {
      WIZCHIP.SPI._read_byte = wizchip_spi_readbyte;
      WIZCHIP.SPI._write_byte = wizchip_spi_writebyte;
   }
   else
   {
      WIZCHIP.SPI._read_byte = spi_rb;
      WIZCHIP.SPI._write_byte = spi_wb;
   }
}

int8_t ctlwizchip(ctlwizchip_type cwtype, void *arg)
{
   uint8_t tmp = 0;
   uint8_t *ptmp[2] = {0, 0};
   switch (cwtype)
   {
   case CW_INIT_WIZCHIP:
      if (arg != 0)
      {
         ptmp[0] = (uint8_t *)arg;
         ptmp[1] = ptmp[0] + _WIZCHIP_SOCK_NUM_;
      }
      return wizchip_init(ptmp[0], ptmp[1]);
   case CW_GET_PHYLINK:
      tmp = wizphy_getphylink();
      if ((int8_t)tmp == -1)
         return -1;
      *(uint8_t *)arg = tmp;
      break;
   default:
      return -1;
   }
   return 0;
}

int8_t ctlnetwork(ctlnetwork_type cntype, void *arg)
{
   switch (cntype)
   {
   case CN_SET_NETINFO:
      wizchip_setnetinfo((wiz_NetInfo *)arg);
      break;
   case CN_GET_NETINFO:
      wizchip_getnetinfo((wiz_NetInfo *)arg);
      break;
   default:
      return -1;
   }
   return 0;
}

void wizchip_sw_reset(void)
{
   uint8_t gw[4], sn[4], sip[4];
   uint8_t mac[6];
   getSHAR(mac);
   getGAR(gw);
   getSUBR(sn);
   getSIPR(sip);
   setMR(MR_RST);
   getMR();
   setSHAR(mac);
   setGAR(gw);
   setSUBR(sn);
   setSIPR(sip);
}

int8_t wizchip_init(uint8_t *txsize, uint8_t *rxsize)
{
   int8_t tmp = 0;
   wizchip_sw_reset();
   if (txsize)
   {
      tmp = 0;
      for (int8_t i = 0; i < _WIZCHIP_SOCK_NUM_; i++)
      {
         tmp += txsize[i];
         if (tmp > 16)
            return -1;
      }
      for (int8_t i = 0; i < _WIZCHIP_SOCK_NUM_; i++)
         setSn_TXBUF_SIZE(i, txsize[i]);
   }

   if (rxsize)
   {
      tmp = 0;
      for (int8_t i = 0; i < _WIZCHIP_SOCK_NUM_; i++)
      {
         tmp += rxsize[i];
         if (tmp > 16)
            return -1;
      }

      for (int8_t i = 0; i < _WIZCHIP_SOCK_NUM_; i++)
         setSn_RXBUF_SIZE(i, rxsize[i]);
   }
   return 0;
}

int8_t wizphy_getphylink(void)
{
   if (getPHYCFGR() & PHYCFGR_LNK_ON)
      return PHY_LINK_ON;
   else
      return PHY_LINK_OFF;
}

void wizchip_setnetinfo(wiz_NetInfo *pnetinfo)
{
   setSHAR(pnetinfo->mac);
   setGAR(pnetinfo->gw);
   setSUBR(pnetinfo->sn);
   setSIPR(pnetinfo->ip);
   _DNS_[0] = pnetinfo->dns[0];
   _DNS_[1] = pnetinfo->dns[1];
   _DNS_[2] = pnetinfo->dns[2];
   _DNS_[3] = pnetinfo->dns[3];
   _DHCP_ = pnetinfo->dhcp;
}

void wizchip_getnetinfo(wiz_NetInfo *pnetinfo)
{
   getSHAR(pnetinfo->mac);
   getGAR(pnetinfo->gw);
   getSUBR(pnetinfo->sn);
   getSIPR(pnetinfo->ip);
   pnetinfo->dns[0] = _DNS_[0];
   pnetinfo->dns[1] = _DNS_[1];
   pnetinfo->dns[2] = _DNS_[2];
   pnetinfo->dns[3] = _DNS_[3];
   pnetinfo->dhcp = _DHCP_;
}
