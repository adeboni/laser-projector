#ifndef _SOCKET_H_
#define _SOCKET_H_

#include "wizchip_conf.h"

#define SOCKET uint8_t   ///< SOCKET type define for legacy driver
#define SOCK_OK 1        ///< Result is OK about socket process.
#define SOCK_BUSY 0      ///< Socket is busy on processing the operation. Valid only Non-block IO Mode.
#define SOCK_FATAL -1000 ///< Result is fatal error about socket process.
#define SOCK_IO_BLOCK 0
#define SOCK_IO_NONBLOCK 1
#define SOCK_ERROR 0
#define SOCKERR_SOCKNUM (SOCK_ERROR - 1)    ///< Invalid socket number
#define SOCKERR_SOCKOPT (SOCK_ERROR - 2)    ///< Invalid socket option
#define SOCKERR_SOCKINIT (SOCK_ERROR - 3)   ///< Socket is not initialized or SIPR is Zero IP address when Sn_MR_TCP
#define SOCKERR_SOCKCLOSED (SOCK_ERROR - 4) ///< Socket unexpectedly closed.
#define SOCKERR_SOCKMODE (SOCK_ERROR - 5)   ///< Invalid socket mode for socket operation.
#define SOCKERR_SOCKFLAG (SOCK_ERROR - 6)   ///< Invalid socket flag
#define SOCKERR_SOCKSTATUS (SOCK_ERROR - 7) ///< Invalid socket status for socket operation.
#define SOCKERR_ARG (SOCK_ERROR - 10)       ///< Invalid argument.
#define SOCKERR_PORTZERO (SOCK_ERROR - 11)  ///< Port number is zero
#define SOCKERR_IPINVALID (SOCK_ERROR - 12) ///< Invalid IP address
#define SOCKERR_TIMEOUT (SOCK_ERROR - 13)   ///< Timeout occurred
#define SOCKERR_DATALEN (SOCK_ERROR - 14)   ///< Data length is zero or greater than buffer max size.
#define SOCKERR_BUFFER (SOCK_ERROR - 15)    ///< Socket buffer is not enough for data communication.
#define SOCKFATAL_PACKLEN (SOCK_FATAL - 1)  ///< Invalid packet length. Fatal Error.
#define SF_ETHER_OWN (Sn_MR_MFEN)           ///< In @ref Sn_MR_MACRAW, Receive only the packet as broadcast, multicast and own packet
#define SF_IGMP_VER2 (Sn_MR_MC)             ///< In @ref Sn_MR_UDP with \ref SF_MULTI_ENABLE, Select IGMP version 2.
#define SF_TCP_NODELAY (Sn_MR_ND)           ///< In @ref Sn_MR_TCP, Use to nodelayed ack.
#define SF_MULTI_ENABLE (Sn_MR_MULTI)       ///< In @ref Sn_MR_UDP, Enable multicast mode.
#define SF_BROAD_BLOCK (Sn_MR_BCASTB)       ///< In @ref Sn_MR_UDP or @ref Sn_MR_MACRAW, Block broadcast packet. Valid only in W5500
#define SF_MULTI_BLOCK (Sn_MR_MMB)          ///< In @ref Sn_MR_MACRAW, Block multicast packet. Valid only in W5500
#define SF_IPv6_BLOCK (Sn_MR_MIP6B)         ///< In @ref Sn_MR_MACRAW, Block IPv6 packet. Valid only in W5500
#define SF_UNI_BLOCK (Sn_MR_UCASTB)         ///< In @ref Sn_MR_UDP with \ref SF_MULTI_ENABLE. Valid only in W5500
#define SF_IO_NONBLOCK 0x01                 ///< Socket nonblock io mode. It used parameter in \ref socket().
#define PACK_FIRST 0x80                     ///< In Non-TCP packet, It indicates to start receiving a packet. (When W5300, This flag can be applied)
#define PACK_REMAINED 0x01                  ///< In Non-TCP packet, It indicates to remain a packet to be received. (When W5300, This flag can be applied)
#define PACK_COMPLETED 0x00                 ///< In Non-TCP packet, It indicates to complete to receive a packet. (When W5300, This flag can be applied)
#define PACK_FIFOBYTE 0x02                  ///< Valid only W5300, It indicate to have read already the Sn_RX_FIFOR.

int8_t socket(uint8_t sn, uint8_t protocol, uint16_t port, uint8_t flag);
int8_t close(uint8_t sn);
int8_t listen(uint8_t sn);
int8_t connect(uint8_t sn, uint8_t *addr, uint16_t port);
int8_t disconnect(uint8_t sn);
int32_t send(uint8_t sn, uint8_t *buf, uint16_t len);
int32_t recv(uint8_t sn, uint8_t *buf, uint16_t len);
int32_t sendto(uint8_t sn, uint8_t *buf, uint16_t len, uint8_t *addr, uint16_t port);
int32_t recvfrom(uint8_t sn, uint8_t *buf, uint16_t len, uint8_t *addr, uint16_t *port);

typedef enum
{
   SIK_CONNECTED = (1 << 0),
   SIK_DISCONNECTED = (1 << 1),
   SIK_RECEIVED = (1 << 2),
   SIK_TIMEOUT = (1 << 3),
   SIK_SENT = (1 << 4),
   SIK_ALL = 0x1F
} sockint_kind;

typedef enum
{
   CS_SET_IOMODE,
   CS_GET_IOMODE,
   CS_GET_MAXTXBUF,
   CS_GET_MAXRXBUF,
   CS_CLR_INTERRUPT,
   CS_GET_INTERRUPT,
   CS_SET_INTMASK,
   CS_GET_INTMASK
} ctlsock_type;

typedef enum
{
   SO_FLAG,
   SO_TTL,
   SO_TOS,
   SO_MSS,
   SO_DESTIP,
   SO_DESTPORT,
   SO_KEEPALIVESEND,
   SO_KEEPALIVEAUTO,
   SO_SENDBUF,
   SO_RECVBUF,
   SO_STATUS,
   SO_REMAINSIZE,
   SO_PACKINFO
} sockopt_type;

int8_t ctlsocket(uint8_t sn, ctlsock_type cstype, void *arg);
int8_t setsockopt(uint8_t sn, sockopt_type sotype, void *arg);
int8_t getsockopt(uint8_t sn, sockopt_type sotype, void *arg);

#endif // _SOCKET_H_
