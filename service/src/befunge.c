#include "befunge.h"

#ifdef DEBUG
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#else
#include <linux/errno.h>
#include <linux/random.h>
#endif

int befunge_check(struct befunge_config *C)
{
    if (C->steps == 0 || C->height == 0 || C->width == 0) {
        return -EINVAL;
    }

    if (C->height <= C->Y || C->width <= C->X) {
        return -EINVAL;
    }

    if (C->code >= C->memsz || C->input >= C->memsz || C->output >= C->memsz || C->stack >= C->memsz) {
        return -EINVAL;
    }

    // check overflow
    if ((C->memsz - C->code) / C->height < C->width) {
        return -EINVAL;
    }

    // off-by-one trap!
    // if (C->stack % 2 == 1) {
    //     return -EINVAL;
    // }

    return 0;
}

int befunge_run(struct befunge_machine *M, struct befunge_config *C, uint32_t steps)
{
    uint16_t X = M->X, Y = M->Y;
    int dx = M->dx, dy = M->dy;
    uint32_t step = 0;
    int stop = 0;
    int string = 0;
    uint32_t o;

#define V(o) (o < C->memsz ? M->membase[o] : 0)

#define POP() (o = C->stack - M->sp * 2 + 2, (o < C->memsz && M->sp > 0) ? (M->sp--, *(uint16_t *)&M->membase[o]) : 0)

#define PUSH(v) (o = C->stack - M->sp * 2, o < C->memsz ? (*(uint16_t *)&M->membase[o] = v, M->sp++) : 0)

    while (step < steps && !stop) {
        uint8_t c = V(C->code + Y * C->width + X);
        step += 1;
#ifdef DEBUG
        if (c != '#') {
            printf("%d: %d, %d => '%c'\t%d:|", step, X, Y, c, M->sp);
            for (int i = 1; i <= M->sp; i++) {
                o = C->stack - i * 2;
                printf("%04x|", *(uint16_t *)&M->membase[o]);
            }
            puts("");
        }
#elif 0
        if (c != '#') {
            printk(KERN_WARNING"%d: %d, %d => '%c'\t%d:|", step, X, Y, c, M->sp);
        }
#endif
        if (string) {
            if (c != '"') {
                PUSH(c);
            } else {
                string = 0;
            }
        } else {
            switch (c) {
                case '0' ... '9':
                    PUSH(c - '0');
                    break;
                case 'a' ... 'f':
                    PUSH(c - 'a' + 10); // custom extension
                    break;
                case '+':
                    {
                        uint16_t a = POP();
                        uint16_t b = POP();
                        PUSH(a + b);
                        break;
                    }
                case '-':
                    {
                        uint16_t a = POP();
                        uint16_t b = POP();
                        PUSH(b - a);
                        break;
                    }
                case '*':
                    {
                        uint16_t a = POP();
                        uint16_t b = POP();
                        PUSH(a * b);
                        break;
                    }
                case '/':
                    {
                        uint16_t a = POP();
                        uint16_t b = POP();
                        if (a == 0) {
                            PUSH(0);
                        } else {
                            PUSH(b / a);
                        }
                        break;
                    }
                case '%':
                    {
                        uint16_t a = POP();
                        uint16_t b = POP();
                        if (a == 0) {
                            PUSH(0);
                        } else {
                            PUSH(b % a);
                        }
                        break;
                    }
                case '!':
                    {
                        uint16_t a = POP();
                        PUSH(a == 0);
                        break;
                    }
                case '`':
                    {
                        uint16_t a = POP();
                        uint16_t b = POP();
                        PUSH(b > a);
                        break;
                    }
                case '>':
                    dx = 1;
                    dy = 0;
                    break;
                case '<':
                    dx = -1;
                    dy = 0;
                    break;
                case '^':
                    dx = 0;
                    dy = -1;
                    break;
                case 'v':
                    dx = 0;
                    dy = 1;
                    break;
                case '?':
                    {
                        // random redirect
#ifdef DEBUG
                        uint8_t k = rand() & 3;
#else
                        uint8_t k = get_random_int() & 3;
#endif
                        static int DX[] = {-1, 0, 0, 1};
                        static int DY[] = {0, -1, 1, 0};
                        dx = DX[k];
                        dy = DY[k];
                        break;
                    }
                case '_':
                    dy = 0;
                    dx = POP() ? -1 : 1;
                    break;
                case '|':
                    dx = 0;
                    dy = POP() ? -1 : 1;
                    break;
                case '"':
                    string = 1;
                    break;
                case ':':
                    {
                        uint16_t a = POP();
                        PUSH(a);
                        PUSH(a);
                        break;
                    }
                case '\\':
                    {
                        uint16_t a = POP();
                        uint16_t b = POP();
                        PUSH(a);
                        PUSH(b);
                        break;
                    }
                case '$':
                    POP();
                    break;
                case '#':
                    // NOP BRIDGE
                    /*
                    X += dx;
                    Y += dy;
                    */
                    break;
                case 'p':
                    {
                        uint16_t y = POP(), x = POP(), v = POP();
                        if (y < C->height && x < C->width) {
                            M->membase[C->code + y * C->width + x] = v;
                        }
                        break;
                    }
                case 'g':
                    {
                        uint16_t y = POP(), x = POP();
                        if (y < C->height && x < C->width) {
                            PUSH(V(C->code + y * C->width + x));
                        }
                        break;
                    }
                case ',':
                    {
                        uint16_t a = POP();
#ifdef DEBUG
                        printf("%c\n", a);
#elif 0
                        printk(KERN_WARNING"%c", a);
#endif
                        if (M->O < C->memsz) {
                            M->membase[M->O++] = a;
                        }
                        break;
                    }
                case '~':
                    {
                        if (M->I < C->memsz) {
#ifdef DEBUG
                            printf("read %d = '%c'\n", M->I, M->membase[M->I]);
#endif
                            PUSH(M->membase[M->I++]);
                        }
                        break;
                    }
                case '.':
                    {
                        // FIXME output integer
#ifdef DEBUG
                        uint16_t a = POP();
                        printf("%d\n", a);
#else
                        // ignore
#endif
                        break;
                    }
                case '&':
                    // FIXME input integer
                    // ignore
                    break;
                case ' ':
#ifdef DEBUG
                    printf("halt!\n");
                    // fallthrough
#endif
                case '@':
                    stop = 1;
                    break;
                default:
                    {
                        // skip any other character
                        break;
                    }
            }
        }
        X = (X + dx + C->width) % C->width;
        Y = (Y + dy + C->height) % C->height;
    }

    M->X = X;
    M->Y = Y;
    M->dx = dx;
    M->dy = dy;
    M->count += step;

#ifdef DEBUG
    printf("%d: %d, %d => \t%d:|", step, X, Y, M->sp);
    for (int i = 1; i <= M->sp; i++) {
        o = C->stack - i * 2;
        printf("%04x|", *(uint16_t *)&M->membase[o]);
    }
#endif

    return stop;
}
