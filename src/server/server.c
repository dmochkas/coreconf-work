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
  addr.sin6_port   = htons(COAP_PORT);
  addr.sin6_addr   = in6addr_loopback;

  // Bind socket
  if (bind(sockfd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
    perror("Bind error.");
    close(sockfd);
    return 1;
  }

  printf("UDP socket bound!\n");
  printf("Listening to datagrams on [::]:%d...\n", COAP_PORT);

  // Receive UDP datagram
  char buf[BUFFER_MAX];
  struct sockaddr_in6 sender;
  socklen_t sender_len = sizeof(sender);

  ssize_t n = recvfrom(sockfd, buf, sizeof(buf)-1, 0,
                        (struct sockaddr*)&sender, &sender_len);

  if (n > 0) {
    // Handle message
    buf[n] = '\0';

    char sender_ip[INET6_ADDRSTRLEN];
    inet_ntop(AF_INET6, &sender.sin6_addr, sender_ip, sizeof(sender_ip));
    printf("Received %zd bytes from [%s]: %s\n",
            n, sender_ip, buf);

    // Send response back
    const char *reply = "ACK";
    sendto(sockfd, reply, 3, 0, (struct sockaddr*)&sender, sender_len);
  }

  close(sockfd);
  return 0;
}