#include <time.h>
#include <stdio.h>
#include <ctype.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include "fungez.h"

static uint8_t *map;

static void display(size_t height, size_t width) {
    for (int i = 0; i < height; i++) {
        write(1, map + i * width, width);
        write(1, "\n", 1);
    }
}

static int load_map(const char *path, size_t width, size_t height)
{
    int fd = open(path, O_RDONLY);
    if (fd < 0) {
        return -1;
    }
    size_t line = width + 1;
    uint8_t *buf = malloc(line);
    for (int i = 0; i < height; i++) {
        ssize_t l = read(fd, buf, line);
        if (l < 0) {
            return -1;
        }
        if (l == line && buf[l - 1] != '\n') {
            // every row must end with '\n'
            return -1;
        }
        memcpy(map + i * width, buf, width);
        // puts(buf);
    }
    return width * height;
}

int main(int argc, char *argv[])
{
    if (argc != 4) {
        printf("usage: %s width height map\n", argv[0]);
        return -1;
    }

    size_t width = atoi(argv[1]);
    size_t height = atoi(argv[2]);

    int fd = open("/dev/fungez", O_RDWR);
    if (fd == -1) {
        perror("open");
        return -1;
    }

    size_t code_size = width * height;
    size_t input_offset = code_size;
    size_t output_offset = input_offset + 0x1000;
    size_t stack_offset = output_offset + 0x1000;
    size_t map_size = stack_offset + 0x1000;

    map = mmap(NULL, map_size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (map == MAP_FAILED) {
        perror("mmap");
        return -1;
    }

    if (load_map(argv[3], width, height) < 0) {
        perror("load");
        return -1;
    }

    struct fungez_ioctl_setup setup = {
        .config = {
            .height = height,
            .width = width,
            .X = 0,
            .Y = 0,
            .code = 0,
            .input = input_offset,
            .output = output_offset,
            .stack = stack_offset,
            .memsz = map_size,
            .steps = 1000000,
        },
    };

    if (ioctl(fd, FUNGEZ_IOCTL_SETUP, &setup)) {
        perror("ioctl/setup");
        return -1;
    }

    char flag[100];
    printf("tell me your secret: ");
    scanf("%100s", &flag[0]);

    // check flag
    size_t l = strlen(flag);
    if (l != 64) {
        fprintf(stderr, "invalid flag\n");
        return -1;
    }

    for (int i = 0; i < l; i++) {
        if (!isalnum(flag[i])) {
            fprintf(stderr, "invalid flag\n");
            return -1;
        }
    }

    memcpy(map + input_offset, flag, l);

    int run = 1;
    if (ioctl(fd, FUNGEZ_IOCTL_START, &run)) {
        perror("ioctl/start");
        return -1;
    }
    // display(height, width);

    int c = 10;
    while (c--) {
        struct fungez_ioctl_info info;
        if (ioctl(fd, FUNGEZ_IOCTL_QUERY, &info)) {
            perror("ioctl/query");
            return -1;
        }
        printf("step #%d at (%d, %d) state = %d\n", info.count, info.X, info.Y, info.state);
        if (info.state == FUNGEZ_STOP) {
            break;
        }
        // display(height, width);
        sleep(1);
    }

    char *output = (char *)(map + output_offset);
    if (!strncmp(output, "win", 3)) {
        printf("flag is OOO{%s}\n", flag);
    } else {
        puts(output);
    }

    return 0;
}
