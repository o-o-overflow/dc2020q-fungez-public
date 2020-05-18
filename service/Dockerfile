FROM debian:bullseye

RUN apt-get -qq update && apt-get install -qq -y xinetd rsyslog qemu-system-aarch64 cpio procps

COPY src/skip_mbind.so /skip_mbind.so
COPY Image /
COPY run.sh /
COPY src/rootfs.img /

# the deployment tester will pass in the flag from the yaml
ARG THE_FLAG="OOO{this is a test flag}"
RUN touch /flag && chmod 000 /flag && echo $THE_FLAG > /flag && echo "flag" | cpio -o -A --format=newc -F rootfs.img

COPY service.conf /service.conf
COPY banner_fail /banner_fail

expose 10101
cmd ["/usr/sbin/xinetd", "-syslog", "local0", "-dontfork", "-f", "/service.conf"]
# ^^ If ps would be too revealing, replace with the line below.
#    AFAIK, this also disables the built-in printf(%n) protection, so YMMV.
#cmd chmod go-rwx /proc && /usr/sbin/xinetd -syslog local0 -dontfork -f /service.conf
