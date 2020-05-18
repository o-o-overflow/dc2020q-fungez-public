obj-m := ooo.o
ooo-objs := fungez.o befunge.o

CROSS_COMPILE := aarch64-linux-gnu-
LINUX_KERNEL_PATH := ../../linux-5.6.8

all: test ooo.ko ooo rootfs.img test_rootfs.img skip_mbind.so

ooo.ko: fungez.c fungez.h befunge.c befunge.h
	$(MAKE) -C $(LINUX_KERNEL_PATH) M=$(shell pwd) ARCH=arm64 CROSS_COMPILE=$(CROSS_COMPILE) modules

ooo: ooo.c
	$(CROSS_COMPILE)gcc -static -o $@ $^
	$(CROSS_COMPILE)strip $@

rootfs.img: base.img ooo ooo.ko map init
	cp base.img $@
	echo './init\n./ooo\nooo.ko\nmap\n' | cpio -o -A --format=newc -F $@

map: map_static draw.py
	python draw.py

map_static: gen.py
	python gen.py

skip_mbind.so: skip_mbind.c
	gcc -shared -o $@ $^

clean:
	rm -f *.ko *.o ooo rootfs.img map*
