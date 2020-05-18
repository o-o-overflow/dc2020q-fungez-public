#ifndef _FUNGEZ_H
#define _FUNGEZ_H

#include <linux/ioctl.h>
#include "befunge.h"

#define DEAD_CELL '.'
#define LIVE_CELL '#'

enum fungez_state {
    FUNGEZ_IDLE,
    FUNGEZ_READY,
    FUNGEZ_RUNNING,
    FUNGEZ_STOP,
    FUNGEZ_ERROR,
};

struct fungez_ioctl_setup {
    struct befunge_config config;
};

struct fungez_ioctl_info {
    uint16_t X, Y;
    enum fungez_state state;
    uint32_t count;
};

#define FUNGEZ_IOCTL_SETUP _IOW('O', 0x1, struct fungez_ioctl_setup)
#define FUNGEZ_IOCTL_START _IOW('O', 0x2, int)
#define FUNGEZ_IOCTL_QUERY _IOR('O', 0x3, struct fungez_ioctl_info)

#endif
