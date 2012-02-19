/*
  Interface to the Dreambox dm800/dm8000 proprietary accel interface.
*/

#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <linux/fb.h>
#include <sys/mman.h>
#include <sys/ioctl.h>

// Sigma BLIT struct
typedef struct {
	unsigned int p[20];
} BLITSCALE;

#define FBIO_BLIT_SCALE _IOW('F', 0x25, BLITSCALE)
#define FBIO_ACCEL  0x23

static int fb_fd;

int sigma_accel_init(void)
{
	fb_fd = open("/dev/fb/0", O_RDWR);
	if (fb_fd < 0)
	{
		perror("/dev/fb/0");
		return 1;
	}

	return 0;
}

void sigma_accel_close(void)
{
	if (fb_fd >= 0)
	{
		close(fb_fd);
		fb_fd = -1;
	}
}

int sigma_accel_blit(
		int src_addr, int src_width, int src_height, int src_stride, int src_format,
		int dst_addr, int dst_width, int dst_height, int dst_stride,
		int src_x, int src_y, int width, int height,
		int dst_x, int dst_y, int dwidth, int dheight,
		int pal_addr, int colornb, int flags)
{
	BLITSCALE blit;
	blit.p[0] = src_addr; blit.p[1] = src_width; blit.p[2] = src_height; blit.p[3] = src_stride;
	blit.p[4] = src_format; blit.p[5] = dst_addr; blit.p[6] = dst_width; blit.p[7] = dst_height;
	blit.p[8] = dst_stride; blit.p[9] = src_x; blit.p[10] = src_y; blit.p[11] = width;
	blit.p[12] = height; blit.p[13] = dst_x; blit.p[14] = dst_y; blit.p[15] = dwidth;
	blit.p[16] = dheight; blit.p[17] = pal_addr; blit.p[18] = colornb; blit.p[19] = flags;

	if (ioctl(fb_fd, FBIO_BLIT_SCALE,&blit) < 0)
		return -1;
	return 0;
}

int sigma_accel_fill(
		int dst_addr, int dst_width, int dst_height, int dst_stride,
		int x, int y, int width, int height,
		unsigned long color)
{
	return -1;
}
