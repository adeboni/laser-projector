#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "wizchip_conf.h"
#include "socket.h"
#include "httpClient.h"

HttpRequest request = HttpRequest_get_initializer;

static int8_t httpsock = 0;
static uint8_t dest_ip[4] = {0, };
static uint16_t dest_port = 0;
static uint16_t httpc_any_port = 0;

uint8_t httpc_isSockOpen = HTTPC_FALSE;
uint8_t httpc_isConnected = HTTPC_FALSE;
uint16_t httpc_isReceived = HTTPC_FALSE;

uint8_t httpc_init(uint8_t sock, uint8_t * ip, uint16_t port) {
	if (sock <= _WIZCHIP_SOCK_NUM_)
	{
		httpsock = sock;
		dest_ip[0] = ip[0];
		dest_ip[1] = ip[1];
		dest_ip[2] = ip[2];
		dest_ip[3] = ip[3];
		dest_port = port;
		return HTTPC_TRUE;
	}

	return HTTPC_FALSE;
}

// return: source port number for tcp client
uint16_t get_httpc_any_port(void) {
	if (httpc_any_port)
	{
		if ((httpc_any_port >= HTTP_CLIENT_PORT_MIN) && (httpc_any_port < HTTP_CLIENT_PORT_MAX))
			httpc_any_port++;
		else 
			httpc_any_port = 0;
	}

	if (httpc_any_port < HTTP_CLIENT_PORT_MIN)
		httpc_any_port = (rand() % 10000) + 46000; // 46000 ~ 55999

	return httpc_any_port;
}

// return: true / false
uint8_t httpc_connection_handler() {
	uint8_t ret = HTTPC_FALSE;

	switch (getSn_SR(httpsock))
	{
		case SOCK_INIT:
			// state: connect
			ret = HTTPC_TRUE;
			break;

		case SOCK_ESTABLISHED:
			if (getSn_IR(httpsock) & Sn_IR_CON)
			{
#ifdef _HTTPCLIENT_DEBUG_
				// Serial debug message printout
				uint8_t destip[4] = {0, };
				uint16_t destport = 0;
				getsockopt(httpsock, SO_DESTIP, &destip);
				getsockopt(httpsock, SO_DESTPORT, &destport);
				printf(" > HTTP CLIENT: CONNECTED TO - %d.%d.%d.%d : %d\r\n",destip[0], destip[1], destip[2], destip[3], destport);
#endif
				httpc_isConnected = HTTPC_TRUE;
				setSn_IR(httpsock, Sn_IR_CON);
			}

			httpc_isReceived = getSn_RX_RSR(httpsock);
			ret = HTTPC_CONNECTED;
			break;

		case SOCK_CLOSE_WAIT:
			disconnect(httpsock);
			break;

		case SOCK_FIN_WAIT:
		case SOCK_CLOSED:
			httpc_isSockOpen = HTTPC_FALSE;
			httpc_isConnected = HTTPC_FALSE;

			uint16_t source_port = get_httpc_any_port();
#ifdef _HTTPCLIENT_DEBUG_
			printf(" > HTTP CLIENT: source_port = %d\r\n", source_port);
#endif

			if (socket(httpsock, Sn_MR_TCP, source_port, Sn_MR_ND) == httpsock)
			{
				if (httpc_isSockOpen == HTTPC_FALSE)
				{
#ifdef _HTTPCLIENT_DEBUG_
					printf(" > HTTP CLIENT: SOCKOPEN\r\n");
#endif
					httpc_isSockOpen = HTTPC_TRUE;
				}
			}

			break;

		default:
			break;
	}

	return ret;
}


// return: socket status
uint8_t httpc_connect() {
	uint8_t ret = HTTPC_FALSE;

	if (httpsock >= 0)
	{
		if (httpc_isSockOpen == HTTPC_TRUE)
		{
			// TCP connect
			ret = connect(httpsock, dest_ip, dest_port);
			if (ret == SOCK_OK) ret = HTTPC_TRUE;
		}
	}

	return ret;
}

// return: sent data length
uint16_t httpc_send(HttpRequest * req, uint8_t * buf, uint16_t content_len) {
	uint16_t len;
	uint8_t http_header_generated = HTTPC_FAILED;

	if (httpc_isConnected == HTTPC_TRUE) {
		do {
			memset(buf, 0x00, DATA_BUF_SIZE);

			len = sprintf((char *)buf, "%s %s HTTP/1.1\r\n", req->method, req->uri);
			len += sprintf((char *)buf+len, "Host: %s\r\n", req->host);
			len += sprintf((char *)buf+len, "Connection: %s\r\n", req->connection);

			if (content_len > 0)
			{
				len += sprintf((char *)buf+len, "Content-Length: %d\r\n", content_len);
				len += sprintf((char *)buf+len, "Content-Type: %s\r\n", req->content_type);
			}

			len += sprintf((char *)buf+len, "\r\n");

			// Avoiding buffer overflow
			if ((len + content_len) > DATA_BUF_SIZE)
				content_len = DATA_BUF_SIZE - len;
			else 
				http_header_generated = HTTPC_SUCCESS;
		} while (http_header_generated != HTTPC_SUCCESS);

#ifdef _HTTPCLIENT_DEBUG_
		printf(" >> HTTP Request - Method: %s, URI: %s, Content-Length: %d\r\n", req->method, req->uri, content_len);
		for(uint16_t i = 0; i < len; i++) printf("%c", buf[i]);
		printf("\r\n");
#endif
		send(httpsock, buf, len);
	}
	else
	{
		len = HTTPC_FAILED;
	}

	return len;
}


// return: received data length
uint16_t httpc_recv(uint8_t * buf, uint16_t len) {
	uint16_t recvlen;

	if (httpc_isConnected == HTTPC_TRUE) {
		if (len > DATA_BUF_SIZE) len = DATA_BUF_SIZE;
		recvlen = recv(httpsock, buf, len);
	} else {
		recvlen = HTTPC_FAILED;
	}

	return recvlen;
}


// return: true / false
uint8_t httpc_disconnect(void) {
	uint8_t ret = HTTPC_FALSE;

	if (httpc_isConnected == HTTPC_TRUE) {
#ifdef _HTTPCLIENT_DEBUG_
		printf(" > HTTP CLIENT: Try to disconnect\r\n");
#endif
		ret = disconnect(httpsock);
		if (ret == SOCK_OK) {
			ret = HTTPC_TRUE;
#ifdef _HTTPCLIENT_DEBUG_
			printf(" > HTTP CLIENT: Disconnected\r\n");
#endif
		}
	}

	return ret;
}
