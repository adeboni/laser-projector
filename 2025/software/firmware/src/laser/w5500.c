#include "w5500.h"

uint8_t WIZCHIP_READ(uint32_t AddrSel)
{
   WIZCHIP_CRITICAL_ENTER();
   WIZCHIP.CS._select();

   AddrSel |= _W5500_SPI_READ_;

   WIZCHIP.SPI._write_byte((AddrSel & 0x00FF0000) >> 16);
   WIZCHIP.SPI._write_byte((AddrSel & 0x0000FF00) >> 8);
   WIZCHIP.SPI._write_byte((AddrSel & 0x000000FF) >> 0);
   uint8_t ret = WIZCHIP.SPI._read_byte();

   WIZCHIP.CS._deselect();
   WIZCHIP_CRITICAL_EXIT();
   return ret;
}

void WIZCHIP_WRITE(uint32_t AddrSel, uint8_t wb)
{
   WIZCHIP_CRITICAL_ENTER();
   WIZCHIP.CS._select();

   AddrSel |= _W5500_SPI_WRITE_;

   WIZCHIP.SPI._write_byte((AddrSel & 0x00FF0000) >> 16);
   WIZCHIP.SPI._write_byte((AddrSel & 0x0000FF00) >> 8);
   WIZCHIP.SPI._write_byte((AddrSel & 0x000000FF) >> 0);
   WIZCHIP.SPI._write_byte(wb);

   WIZCHIP.CS._deselect();
   WIZCHIP_CRITICAL_EXIT();
}

void WIZCHIP_READ_BUF(uint32_t AddrSel, uint8_t *pBuf, uint16_t len)
{
   WIZCHIP_CRITICAL_ENTER();
   WIZCHIP.CS._select();

   AddrSel |= _W5500_SPI_READ_;

   WIZCHIP.SPI._write_byte((AddrSel & 0x00FF0000) >> 16);
   WIZCHIP.SPI._write_byte((AddrSel & 0x0000FF00) >> 8);
   WIZCHIP.SPI._write_byte((AddrSel & 0x000000FF) >> 0);
   for (uint16_t i = 0; i < len; i++)
      pBuf[i] = WIZCHIP.SPI._read_byte();

   WIZCHIP.CS._deselect();
   WIZCHIP_CRITICAL_EXIT();
}

void WIZCHIP_WRITE_BUF(uint32_t AddrSel, uint8_t *pBuf, uint16_t len)
{
   WIZCHIP_CRITICAL_ENTER();
   WIZCHIP.CS._select();

   AddrSel |= _W5500_SPI_WRITE_;

   WIZCHIP.SPI._write_byte((AddrSel & 0x00FF0000) >> 16);
   WIZCHIP.SPI._write_byte((AddrSel & 0x0000FF00) >> 8);
   WIZCHIP.SPI._write_byte((AddrSel & 0x000000FF) >> 0);
   for (uint16_t i = 0; i < len; i++)
      WIZCHIP.SPI._write_byte(pBuf[i]);

   WIZCHIP.CS._deselect();
   WIZCHIP_CRITICAL_EXIT();
}

uint16_t getSn_TX_FSR(uint8_t sn)
{
   uint16_t val = 0;
   uint16_t val1 = 0;

   do
   {
      val1 = WIZCHIP_READ(Sn_TX_FSR(sn));
      val1 = (val1 << 8) + WIZCHIP_READ(WIZCHIP_OFFSET_INC(Sn_TX_FSR(sn), 1));
      if (val1 != 0)
      {
         val = WIZCHIP_READ(Sn_TX_FSR(sn));
         val = (val << 8) + WIZCHIP_READ(WIZCHIP_OFFSET_INC(Sn_TX_FSR(sn), 1));
      }
   } while (val != val1);
   return val;
}

uint16_t getSn_RX_RSR(uint8_t sn)
{
   uint16_t val = 0;
   uint16_t val1 = 0;

   do
   {
      val1 = WIZCHIP_READ(Sn_RX_RSR(sn));
      val1 = (val1 << 8) + WIZCHIP_READ(WIZCHIP_OFFSET_INC(Sn_RX_RSR(sn), 1));
      if (val1 != 0)
      {
         val = WIZCHIP_READ(Sn_RX_RSR(sn));
         val = (val << 8) + WIZCHIP_READ(WIZCHIP_OFFSET_INC(Sn_RX_RSR(sn), 1));
      }
   } while (val != val1);
   return val;
}

void wiz_send_data(uint8_t sn, uint8_t *wizdata, uint16_t len)
{
   if (len == 0)
      return;
   uint16_t ptr = getSn_TX_WR(sn);
   uint32_t addrsel = ((uint32_t)ptr << 8) + (WIZCHIP_TXBUF_BLOCK(sn) << 3);
   WIZCHIP_WRITE_BUF(addrsel, wizdata, len);
   ptr += len;
   setSn_TX_WR(sn, ptr);
}

void wiz_recv_data(uint8_t sn, uint8_t *wizdata, uint16_t len)
{
   if (len == 0)
      return;
   uint16_t ptr = getSn_RX_RD(sn);
   uint16_t addrsel = ((uint32_t)ptr << 8) + (WIZCHIP_RXBUF_BLOCK(sn) << 3);
   WIZCHIP_READ_BUF(addrsel, wizdata, len);
   ptr += len;
   setSn_RX_RD(sn, ptr);
}

void wiz_recv_ignore(uint8_t sn, uint16_t len)
{
   uint16_t ptr = getSn_RX_RD(sn);
   ptr += len;
   setSn_RX_RD(sn, ptr);
}
