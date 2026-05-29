#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>

#include "definitions.h"

static int sockfd;
static struct sockaddr_in6 addr;

int main() {

  // Open socket
  sockfd = socket(AF_INET6, SOCK_DGRAM, 0);
  if (sockfd < 0) {
    perror("Failed to get socket. (sockfd < 0)");
    return 1;
  }

  // Setup address
  memset(&addr, 0, sizeof(addr));
  addr.sin6_family = AF_INET6;
  addr.sin6_port   = htons(CLIENT_PORT);
  addr.sin6_addr   = in6addr_loopback;

  // Bind socket
  if (bind(sockfd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
    perror("Bind error.");
    close(sockfd);
    return 1;
  }
  printf("UDP socket bound! [::1]:%d\n", CLIENT_PORT);

  // Assemble server address
  struct sockaddr_in6 server;
  memset(&server, 0, sizeof(server));
  server.sin6_family = AF_INET6;
  server.sin6_port   = htons(CLIENT_PORT);
  server.sin6_addr   = in6addr_loopback;
  socklen_t server_len = sizeof(server);

  printf("Sending to [::1]:%d...\n", COAP_PORT);

  // Send request
  char buf[BUFFER_MAX] = "FETCH";
  sendto(sockfd, buf, 5, 0, (struct sockaddr*)&server, server_len);

  // Receive response
  printf("Waiting for response from [::1]:%d...\n", COAP_PORT);
  ssize_t n = recvfrom(sockfd, buf, sizeof(buf)-1, 0,
                        (struct sockaddr*)&server, &server_len);

  if (n > 0) {
    // Handle message
    buf[n] = '\0';

    char server_ip[INET6_ADDRSTRLEN];
    inet_ntop(AF_INET6, &server.sin6_addr, server_ip, sizeof(server_ip));
    printf("Received %zd bytes from [%s]: %s\n",
            n, server_ip, buf);
  }

  close(sockfd);
  return 0;
}