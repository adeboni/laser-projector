#ifndef _W5500_H_
#define _W5500_H_

#include <stdint.h>
#include "wizchip_conf.h"

#define _W5500_SPI_READ_ (0x00 << 2)                  //< SPI interface Read operation in Control Phase
#define _W5500_SPI_WRITE_ (0x01 << 2)                 //< SPI interface Write operation in Control Phase
#define WIZCHIP_CREG_BLOCK 0x00                       //< Common register block
#define WIZCHIP_SREG_BLOCK(N) (1 + 4 * N)             //< Socket N register block
#define WIZCHIP_TXBUF_BLOCK(N) (2 + 4 * N)            //< Socket N Tx buffer address block
#define WIZCHIP_RXBUF_BLOCK(N) (3 + 4 * N)            //< Socket N Rx buffer address block
#define WIZCHIP_OFFSET_INC(ADDR, N) (ADDR + (N << 8)) //< Increase offset address

#define MR ((0x0000 << 8) + (WIZCHIP_CREG_BLOCK << 3))
#define GAR ((0x0001 << 8) + (WIZCHIP_CREG_BLOCK << 3))
#define SUBR ((0x0005 << 8) + (WIZCHIP_CREG_BLOCK << 3))
#define SHAR ((0x0009 << 8) + (WIZCHIP_CREG_BLOCK << 3))
#define SIPR ((0x000F << 8) + (WIZCHIP_CREG_BLOCK << 3))
#define INTLEVEL ((0x0013 << 8) + (WIZCHIP_CREG_BLOCK << 3))
#define IR ((0x0015 << 8) + (WIZCHIP_CREG_BLOCK << 3))
#define _IMR_ ((0x0016 << 8) + (WIZCHIP_CREG_BLOCK << 3))
#define SIR ((0x0017 << 8) + (WIZCHIP_CREG_BLOCK << 3))
#define SIMR ((0x0018 << 8) + (WIZCHIP_CREG_BLOCK << 3))
#define _RTR_ ((0x0019 << 8) + (WIZCHIP_CREG_BLOCK << 3))
#define _RCR_ ((0x001B << 8) + (WIZCHIP_CREG_BLOCK << 3))
#define PTIMER ((0x001C << 8) + (WIZCHIP_CREG_BLOCK << 3))
#define PMAGIC ((0x001D << 8) + (WIZCHIP_CREG_BLOCK << 3))
#define PHAR ((0x001E << 8) + (WIZCHIP_CREG_BLOCK << 3))
#define PSID ((0x0024 << 8) + (WIZCHIP_CREG_BLOCK << 3))
#define PMRU ((0x0026 << 8) + (WIZCHIP_CREG_BLOCK << 3))
#define UIPR ((0x0028 << 8) + (WIZCHIP_CREG_BLOCK << 3))
#define UPORTR ((0x002C << 8) + (WIZCHIP_CREG_BLOCK << 3))
#define PHYCFGR ((0x002E << 8) + (WIZCHIP_CREG_BLOCK << 3))
#define VERSIONR ((0x0039 << 8) + (WIZCHIP_CREG_BLOCK << 3))
#define Sn_MR(N) ((0x0000 << 8) + (WIZCHIP_SREG_BLOCK(N) << 3))
#define Sn_CR(N) ((0x0001 << 8) + (WIZCHIP_SREG_BLOCK(N) << 3))
#define Sn_IR(N) ((0x0002 << 8) + (WIZCHIP_SREG_BLOCK(N) << 3))
#define Sn_SR(N) ((0x0003 << 8) + (WIZCHIP_SREG_BLOCK(N) << 3))
#define Sn_PORT(N) ((0x0004 << 8) + (WIZCHIP_SREG_BLOCK(N) << 3))
#define Sn_DHAR(N) ((0x0006 << 8) + (WIZCHIP_SREG_BLOCK(N) << 3))
#define Sn_DIPR(N) ((0x000C << 8) + (WIZCHIP_SREG_BLOCK(N) << 3))
#define Sn_DPORT(N) ((0x0010 << 8) + (WIZCHIP_SREG_BLOCK(N) << 3))
#define Sn_MSSR(N) ((0x0012 << 8) + (WIZCHIP_SREG_BLOCK(N) << 3))
#define Sn_TOS(N) ((0x0015 << 8) + (WIZCHIP_SREG_BLOCK(N) << 3))
#define Sn_TTL(N) ((0x0016 << 8) + (WIZCHIP_SREG_BLOCK(N) << 3))
#define Sn_RXBUF_SIZE(N) ((0x001E << 8) + (WIZCHIP_SREG_BLOCK(N) << 3))
#define Sn_TXBUF_SIZE(N) ((0x001F << 8) + (WIZCHIP_SREG_BLOCK(N) << 3))
#define Sn_TX_FSR(N) ((0x0020 << 8) + (WIZCHIP_SREG_BLOCK(N) << 3))
#define Sn_TX_RD(N) ((0x0022 << 8) + (WIZCHIP_SREG_BLOCK(N) << 3))
#define Sn_TX_WR(N) ((0x0024 << 8) + (WIZCHIP_SREG_BLOCK(N) << 3))
#define Sn_RX_RSR(N) ((0x0026 << 8) + (WIZCHIP_SREG_BLOCK(N) << 3))
#define Sn_RX_RD(N) ((0x0028 << 8) + (WIZCHIP_SREG_BLOCK(N) << 3))
#define Sn_RX_WR(N) ((0x002A << 8) + (WIZCHIP_SREG_BLOCK(N) << 3))
#define Sn_IMR(N) ((0x002C << 8) + (WIZCHIP_SREG_BLOCK(N) << 3))
#define Sn_FRAG(N) ((0x002D << 8) + (WIZCHIP_SREG_BLOCK(N) << 3))
#define Sn_KPALVTR(N) ((0x002F << 8) + (WIZCHIP_SREG_BLOCK(N) << 3))
#define MR_RST 0x80
#define MR_WOL 0x20
#define MR_PB 0x10
#define MR_PPPOE 0x08
#define MR_FARP 0x02
#define IR_CONFLICT 0x80
#define IR_UNREACH 0x40
#define IR_PPPoE 0x20
#define IR_MP 0x10
#define PHYCFGR_RST ~(1 << 7)
#define PHYCFGR_OPMD (1 << 6)
#define PHYCFGR_OPMDC_ALLA (7 << 3)
#define PHYCFGR_OPMDC_PDOWN (6 << 3)
#define PHYCFGR_OPMDC_NA (5 << 3)
#define PHYCFGR_OPMDC_100FA (4 << 3)
#define PHYCFGR_OPMDC_100F (3 << 3)
#define PHYCFGR_OPMDC_100H (2 << 3)
#define PHYCFGR_OPMDC_10F (1 << 3)
#define PHYCFGR_OPMDC_10H (0 << 3)
#define PHYCFGR_DPX_FULL (1 << 2)
#define PHYCFGR_DPX_HALF (0 << 2)
#define PHYCFGR_SPD_100 (1 << 1)
#define PHYCFGR_SPD_10 (0 << 1)
#define PHYCFGR_LNK_ON (1 << 0)
#define PHYCFGR_LNK_OFF (0 << 0)
#define IM_IR7 0x80
#define IM_IR6 0x40
#define IM_IR5 0x20
#define IM_IR4 0x10
#define Sn_MR_MULTI 0x80
#define Sn_MR_BCASTB 0x40
#define Sn_MR_ND 0x20
#define Sn_MR_UCASTB 0x10
#define Sn_MR_MACRAW 0x04
#define Sn_MR_IPRAW 0x03
#define Sn_MR_UDP 0x02
#define Sn_MR_TCP 0x01
#define Sn_MR_CLOSE 0x00
#define Sn_MR_MFEN Sn_MR_MULTI
#define Sn_MR_MMB Sn_MR_ND
#define Sn_MR_MIP6B Sn_MR_UCASTB
#define Sn_MR_MC Sn_MR_ND
#define SOCK_STREAM Sn_MR_TCP
#define SOCK_DGRAM Sn_MR_UDP
#define Sn_CR_OPEN 0x01
#define Sn_CR_LISTEN 0x02
#define Sn_CR_CONNECT 0x04
#define Sn_CR_DISCON 0x08
#define Sn_CR_CLOSE 0x10
#define Sn_CR_SEND 0x20
#define Sn_CR_SEND_MAC 0x21
#define Sn_CR_SEND_KEEP 0x22
#define Sn_CR_RECV 0x40
#define Sn_IR_SENDOK 0x10
#define Sn_IR_TIMEOUT 0x08
#define Sn_IR_RECV 0x04
#define Sn_IR_DISCON 0x02
#define Sn_IR_CON 0x01
#define SOCK_CLOSED 0x00
#define SOCK_INIT 0x13
#define SOCK_LISTEN 0x14
#define SOCK_SYNSENT 0x15
#define SOCK_SYNRECV 0x16
#define SOCK_ESTABLISHED 0x17
#define SOCK_FIN_WAIT 0x18
#define SOCK_CLOSING 0x1A
#define SOCK_TIME_WAIT 0x1B
#define SOCK_CLOSE_WAIT 0x1C
#define SOCK_LAST_ACK 0x1D
#define SOCK_UDP 0x22
#define SOCK_IPRAW 0x32
#define SOCK_MACRAW 0x42
#define IPPROTO_IP 0
#define IPPROTO_ICMP 1
#define IPPROTO_IGMP 2
#define IPPROTO_GGP 3
#define IPPROTO_TCP 6
#define IPPROTO_PUP 12
#define IPPROTO_UDP 17
#define IPPROTO_IDP 22
#define IPPROTO_ND 77
#define IPPROTO_RAW 255

#define WIZCHIP_CRITICAL_ENTER() WIZCHIP.CRIS._enter()

#ifdef _exit
#undef _exit
#endif

#define WIZCHIP_CRITICAL_EXIT() WIZCHIP.CRIS._exit()

uint8_t WIZCHIP_READ(uint32_t AddrSel);
void WIZCHIP_WRITE(uint32_t AddrSel, uint8_t wb);
void WIZCHIP_READ_BUF(uint32_t AddrSel, uint8_t *pBuf, uint16_t len);
void WIZCHIP_WRITE_BUF(uint32_t AddrSel, uint8_t *pBuf, uint16_t len);

#define setMR(mr) WIZCHIP_WRITE(MR, mr)
#define getMR() WIZCHIP_READ(MR)
#define setGAR(gar) WIZCHIP_WRITE_BUF(GAR, gar, 4)
#define getGAR(gar) WIZCHIP_READ_BUF(GAR, gar, 4)
#define setSUBR(subr) WIZCHIP_WRITE_BUF(SUBR, subr, 4)
#define getSUBR(subr) WIZCHIP_READ_BUF(SUBR, subr, 4)
#define setSHAR(shar) WIZCHIP_WRITE_BUF(SHAR, shar, 6)
#define getSHAR(shar) WIZCHIP_READ_BUF(SHAR, shar, 6)
#define setSIPR(sipr) WIZCHIP_WRITE_BUF(SIPR, sipr, 4)
#define getSIPR(sipr) WIZCHIP_READ_BUF(SIPR, sipr, 4)
#define getPHYCFGR() WIZCHIP_READ(PHYCFGR)
#define getVERSIONR() WIZCHIP_READ(VERSIONR)
#define setSn_MR(sn, mr) WIZCHIP_WRITE(Sn_MR(sn), mr)
#define getSn_MR(sn) WIZCHIP_READ(Sn_MR(sn))
#define setSn_CR(sn, cr) WIZCHIP_WRITE(Sn_CR(sn), cr)
#define getSn_CR(sn) WIZCHIP_READ(Sn_CR(sn))
#define setSn_IR(sn, ir) WIZCHIP_WRITE(Sn_IR(sn), (ir & 0x1F))
#define getSn_IR(sn) (WIZCHIP_READ(Sn_IR(sn)) & 0x1F)
#define setSn_IMR(sn, imr) WIZCHIP_WRITE(Sn_IMR(sn), (imr & 0x1F))
#define getSn_IMR(sn) (WIZCHIP_READ(Sn_IMR(sn)) & 0x1F)
#define getSn_SR(sn) WIZCHIP_READ(Sn_SR(sn))
#define setSn_PORT(sn, port)                                              \
    {                                                                     \
        WIZCHIP_WRITE(Sn_PORT(sn), (uint8_t)(port >> 8));                 \
        WIZCHIP_WRITE(WIZCHIP_OFFSET_INC(Sn_PORT(sn), 1), (uint8_t)port); \
    }
#define setSn_DIPR(sn, dipr) WIZCHIP_WRITE_BUF(Sn_DIPR(sn), dipr, 4)
#define getSn_DIPR(sn, dipr) WIZCHIP_READ_BUF(Sn_DIPR(sn), dipr, 4)
#define setSn_DPORT(sn, dport)                                              \
    {                                                                       \
        WIZCHIP_WRITE(Sn_DPORT(sn), (uint8_t)(dport >> 8));                 \
        WIZCHIP_WRITE(WIZCHIP_OFFSET_INC(Sn_DPORT(sn), 1), (uint8_t)dport); \
    }
#define getSn_DPORT(sn) (((uint16_t)WIZCHIP_READ(Sn_DPORT(sn)) << 8) + WIZCHIP_READ(WIZCHIP_OFFSET_INC(Sn_DPORT(sn), 1)))
#define setSn_MSSR(sn, mss)                                              \
    {                                                                    \
        WIZCHIP_WRITE(Sn_MSSR(sn), (uint8_t)(mss >> 8));                 \
        WIZCHIP_WRITE(WIZCHIP_OFFSET_INC(Sn_MSSR(sn), 1), (uint8_t)mss); \
    }
#define getSn_MSSR(sn) (((uint16_t)WIZCHIP_READ(Sn_MSSR(sn)) << 8) + WIZCHIP_READ(WIZCHIP_OFFSET_INC(Sn_MSSR(sn), 1)))
#define setSn_TOS(sn, tos) WIZCHIP_WRITE(Sn_TOS(sn), tos)
#define getSn_TOS(sn) WIZCHIP_READ(Sn_TOS(sn))
#define setSn_TTL(sn, ttl) WIZCHIP_WRITE(Sn_TTL(sn), ttl)
#define getSn_TTL(sn) WIZCHIP_READ(Sn_TTL(sn))
#define setSn_RXBUF_SIZE(sn, rxbufsize) WIZCHIP_WRITE(Sn_RXBUF_SIZE(sn), rxbufsize)
#define getSn_RXBUF_SIZE(sn) WIZCHIP_READ(Sn_RXBUF_SIZE(sn))
#define setSn_TXBUF_SIZE(sn, txbufsize) WIZCHIP_WRITE(Sn_TXBUF_SIZE(sn), txbufsize)
#define getSn_TXBUF_SIZE(sn) WIZCHIP_READ(Sn_TXBUF_SIZE(sn))

uint16_t getSn_TX_FSR(uint8_t sn);

#define setSn_TX_WR(sn, txwr)                                              \
    {                                                                      \
        WIZCHIP_WRITE(Sn_TX_WR(sn), (uint8_t)(txwr >> 8));                 \
        WIZCHIP_WRITE(WIZCHIP_OFFSET_INC(Sn_TX_WR(sn), 1), (uint8_t)txwr); \
    }
#define getSn_TX_WR(sn) (((uint16_t)WIZCHIP_READ(Sn_TX_WR(sn)) << 8) + WIZCHIP_READ(WIZCHIP_OFFSET_INC(Sn_TX_WR(sn), 1)))

uint16_t getSn_RX_RSR(uint8_t sn);

#define setSn_RX_RD(sn, rxrd)                                              \
    {                                                                      \
        WIZCHIP_WRITE(Sn_RX_RD(sn), (uint8_t)(rxrd >> 8));                 \
        WIZCHIP_WRITE(WIZCHIP_OFFSET_INC(Sn_RX_RD(sn), 1), (uint8_t)rxrd); \
    }
#define getSn_RX_RD(sn) (((uint16_t)WIZCHIP_READ(Sn_RX_RD(sn)) << 8) + WIZCHIP_READ(WIZCHIP_OFFSET_INC(Sn_RX_RD(sn), 1)))
#define getSn_RX_WR(sn) (((uint16_t)WIZCHIP_READ(Sn_RX_WR(sn)) << 8) + WIZCHIP_READ(WIZCHIP_OFFSET_INC(Sn_RX_WR(sn), 1)))
#define setSn_KPALVTR(sn, kpalvt) WIZCHIP_WRITE(Sn_KPALVTR(sn), kpalvt)
#define getSn_KPALVTR(sn) WIZCHIP_READ(Sn_KPALVTR(sn))
#define getSn_RxMAX(sn) (((uint16_t)getSn_RXBUF_SIZE(sn)) << 10)
#define getSn_TxMAX(sn) (((uint16_t)getSn_TXBUF_SIZE(sn)) << 10)

void wiz_send_data(uint8_t sn, uint8_t *wizdata, uint16_t len);
void wiz_recv_data(uint8_t sn, uint8_t *wizdata, uint16_t len);
void wiz_recv_ignore(uint8_t sn, uint16_t len);

#endif // _W5500_H_
