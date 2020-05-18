#ifndef _BEFUNGE_H
#define _BEFUNGE_H

#ifdef DEBUG
#include <stdint.h>
#else
typedef unsigned char uint8_t;
typedef unsigned short uint16_t;
typedef unsigned int uint32_t;
#endif

struct befunge_config {
    uint16_t height;
    uint16_t width;
    uint16_t X;
    uint16_t Y;
    uint32_t code;
    uint32_t input;
    uint32_t output;
    uint32_t stack;
    uint32_t memsz;
    uint32_t steps;
};

struct befunge_machine {
    uint8_t *membase;
    uint32_t sp;
    uint16_t X, Y;
    uint32_t I, O;
    uint32_t count;
    int dx, dy;
};

int befunge_check(struct befunge_config *C);

int befunge_run(struct befunge_machine *M, struct befunge_config *C, uint32_t steps);

#endif
