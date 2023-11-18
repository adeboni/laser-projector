#ifndef HTTPCLIENT_H_
#define HTTPCLIENT_H_

#include <stdint.h>

// HTTP client debug message enable
//#define _HTTPCLIENT_DEBUG_

#define DATA_BUF_SIZE 2048

#define HTTP_CLIENT_PORT_MIN   0xB000 // 45056
#define HTTP_CLIENT_PORT_MAX   0xFFFF // 65535

/*********************************************
* HTTP Simple Return 
*********************************************/
// Return value
#define HTTPC_FAILED                0
#define HTTPC_SUCCESS               1
#define HTTPC_CONNECTED             2
// Return value: boolean type
#define HTTPC_FALSE                 0
#define HTTPC_TRUE                  1


/*********************************************
* HTTP Requset Structure Initializer
*********************************************/
#define HttpRequest_get_initializer            {(uint8_t *)"GET", NULL, NULL, NULL, (uint8_t *)"keep-alive", 0}


// HTTP client structure
typedef struct __HttpRequest {
	uint8_t * method;
	uint8_t * uri;
	uint8_t * host;
	uint8_t * content_type;
	uint8_t * connection;
	uint32_t content_length;
} __attribute__((packed)) HttpRequest;

// HTTP client status flags
extern uint8_t  httpc_isSockOpen;
extern uint8_t  httpc_isConnected;
extern uint16_t httpc_isReceived;

// extern: HTTP request structure
extern HttpRequest request;

/*********************************************
* HTTP Client Functions
*********************************************/
uint8_t  httpc_connection_handler(); // HTTP client socket handler - for main loop, implemented in polling

uint8_t  httpc_init(uint8_t sock, uint8_t * ip, uint16_t port); // HTTP client initialize
uint8_t  httpc_connect(); // HTTP client connect (after HTTP socket opened)
uint8_t  httpc_disconnect(void);

uint16_t httpc_send(HttpRequest * req, uint8_t * buf, uint16_t content_len); // Send the HTTP header and body
uint16_t httpc_recv(uint8_t * buf, uint16_t len); // Receive the HTTP response header and body, User have to parse the received messages depending on needs


#endif /* HTTPCLIENT_H_ */