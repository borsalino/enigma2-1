#include <sys/socket.h>
#include <fcntl.h>
#include <stdbool.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <sys/un.h>
#include <unistd.h>
#include <openssl/bn.h>
#include <openssl/sha.h>
#include <lib/base/eerror.h>

#include "etpm.h"

eTPM::eTPM()
{

}

eTPM::~eTPM()
{

}

bool eTPM::send_cmd(enum tpmd_cmd cmd, const void *data, size_t len)
{
	return true;
}

void* eTPM::recv_cmd(unsigned int *tag, size_t *len)
{
	return NULL;
}

void eTPM::parse_data(const unsigned char *data, size_t datalen)
{
}

std::string eTPM::getCert(cert_type type)
{
	return "";
}

std::string eTPM::challenge(std::string rnd)
{
	return "";
}
