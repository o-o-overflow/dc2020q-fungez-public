#include<linux/module.h>
#include<linux/init.h>
#include <linux/kernel.h>
#include <linux/slab.h>
#include <linux/fs.h>
#include <linux/mm.h>
#include <linux/mman.h>
#include <linux/cdev.h>
#include <linux/uaccess.h>
#include <linux/workqueue.h>
#include <linux/dma-mapping.h>

#include "fungez.h"
#include "befunge.h"

struct fungez_device {
    size_t max_size;
    struct cdev dev;
    struct workqueue_struct *wq;
    struct befunge_machine machine;
};

struct fungez_context {
    enum fungez_state state;
    struct befunge_config config;
    struct fungez_device *dev;
    size_t mem_size;
    void *start_addr;
    struct mutex lock;
    struct work_struct flush;
    struct work_struct destroy;
};

static int fungez_run_locked(struct fungez_context *ctx)
{
    uint64_t steps = 10000;

    // early check
    if (ctx->dev->machine.count >= ctx->config.steps) {
        ctx->state = FUNGEZ_STOP;
        return 1;
    }

    if (ctx->state != FUNGEZ_RUNNING) {
        return 1;
    }

    if (steps > ctx->config.steps - ctx->dev->machine.count) {
        steps = ctx->config.steps - ctx->dev->machine.count;
    }

    return befunge_run(&ctx->dev->machine, &ctx->config, steps);
}

static void fungez_worker(struct work_struct *work)
{
    int stop = 0;
    struct fungez_context *ctx = container_of(work, struct fungez_context, flush);

    mutex_lock(&ctx->lock);
    if (ctx->state == FUNGEZ_READY) {
        ctx->state = FUNGEZ_RUNNING;
    }
    mutex_unlock(&ctx->lock);

    stop = 0;

    while (!stop) {
        mutex_lock(&ctx->lock);
        stop = fungez_run_locked(ctx);
        mutex_unlock(&ctx->lock);
    }

    ctx->state = FUNGEZ_STOP;
}

static void fungez_destroy(struct work_struct *work)
{
    struct fungez_context *ctx = container_of(work, struct fungez_context, destroy);

    BUG_ON(ctx->state == FUNGEZ_RUNNING);
    // TODO free resources

    if (ctx->start_addr != NULL) {
        kfree(ctx->start_addr);
    }

    kfree(ctx);
}


static int fungez_open(struct inode* inode, struct file* file)
{
    struct fungez_device *dev = NULL;
    struct fungez_context *ctx = NULL;
    dev = container_of(inode->i_cdev, struct fungez_device, dev);
    if (dev == NULL) {
        return -EINVAL;
    }
    ctx = kzalloc(sizeof(struct fungez_context), GFP_KERNEL);
    if (ctx == NULL) {
        return -ENOMEM;
    }
    ctx->dev = dev;
    ctx->state = FUNGEZ_IDLE;
    mutex_init(&ctx->lock);
    INIT_WORK(&ctx->flush, fungez_worker);
    INIT_WORK(&ctx->destroy, fungez_destroy);

    file->private_data = ctx;
    return 0;
}

static int fungez_release(struct inode* inode, struct file* file)
{
    struct fungez_context *ctx = (struct fungez_context *)file->private_data;
    if (ctx != NULL) {
        mutex_lock(&ctx->lock);
        if (ctx->state == FUNGEZ_RUNNING) {
            // stop the worker
            ctx->state = FUNGEZ_STOP;
        }
        mutex_unlock(&ctx->lock);
        queue_work(ctx->dev->wq, &ctx->destroy);
    }
    return 0;
}

static int fungez_mmap(struct file *file, struct vm_area_struct *vma)
{
    struct fungez_device *dev = NULL;
    unsigned long size = 0;
    unsigned long start = 0;
    int ret = 0;

    struct fungez_context *ctx = (struct fungez_context *)file->private_data;

    if (ctx == NULL) {
        return -EINVAL;
    }

    dev = ctx->dev;

    size = vma->vm_end - vma->vm_start;
    start = vma->vm_start;

#if 0
    printk(KERN_WARNING"[%#lx, %#lx] %#lx %#lx", vma->vm_start, vma->vm_end, size, vma->vm_pgoff);
#endif

    if(size > dev->max_size || size <= 0) {
        return -EINVAL;
    }

    // not sure if it's possible
    if (size & 0xfff) {
        return -EINVAL;
    }

    if (vma->vm_pgoff != 0) {
        return -EINVAL;
    }

    mutex_lock(&ctx->lock);
    if (ctx->state != FUNGEZ_IDLE || ctx->start_addr != NULL || ctx->mem_size != 0) {
        ret = -EBUSY;
    } else {
        ctx->start_addr = kzalloc(size, GFP_KERNEL);
        if (ctx->start_addr == NULL) {
            ret = -ENOMEM;
        } else {
            ctx->mem_size = size;
        }
    }
    mutex_unlock(&ctx->lock);

    if (ret != 0) {
        return ret;
    }

    vma->vm_page_prot = pgprot_writecombine(vma->vm_page_prot);

    ret = vm_iomap_memory(vma, virt_to_phys(ctx->start_addr), ctx->mem_size);

    return ret;
}

static long fungez_ioctl(struct file *file, unsigned int cmd, unsigned long __user arg)
{
    int ret = -EINVAL;
    struct fungez_context *ctx = (struct fungez_context *)file->private_data;

    if (ctx == NULL) {
        return -EINVAL;
    }
    switch (cmd) {
        case FUNGEZ_IOCTL_SETUP:
        {
            struct fungez_ioctl_setup setup;
            if (copy_from_user(&setup, (void *)arg, sizeof(setup))) {
                return -EFAULT;
            }

            ret = befunge_check(&setup.config);

            if (ret) {
                return ret;
            }

            mutex_lock(&ctx->lock);
            if (ctx->start_addr == NULL || ctx->mem_size != setup.config.memsz) {
                ret = -EINVAL;
            } else if (ctx->state == FUNGEZ_IDLE) {
                ctx->config = setup.config;
                ctx->state = FUNGEZ_READY;
                ret = 0;
            } else {
                ret = -EBUSY;
            }
            mutex_unlock(&ctx->lock);
            break;
        }
        case FUNGEZ_IOCTL_START:
        {
            int run;
            if (copy_from_user(&run, (void *)arg, sizeof(run))) {
                return -EFAULT;
            }

            mutex_lock(&ctx->lock);
            if (run) {
                if (ctx->state == FUNGEZ_READY || ctx->state == FUNGEZ_STOP) {
                    struct befunge_machine *M = &ctx->dev->machine;
                    M->membase = ctx->start_addr;
                    M->X = ctx->config.X;
                    M->Y = ctx->config.Y;
                    M->I = ctx->config.input;
                    M->O = ctx->config.output;
                    M->sp = M->count = 0;
                    M->dx = M->dy = 0;
                    ctx->state = FUNGEZ_READY;
                    if (queue_work(ctx->dev->wq, &ctx->flush)) {
                        ret = 0;
                    } else {
                        ret = -EBUSY;
                    }
                }
            } else if (ctx->state == FUNGEZ_RUNNING) {
                ctx->state = FUNGEZ_STOP;
                ret = 0;
            }
            mutex_unlock(&ctx->lock);
            break;
        }
        case FUNGEZ_IOCTL_QUERY:
        {
            struct befunge_machine *M = &ctx->dev->machine;
            struct fungez_ioctl_info info = {0};
            mutex_lock(&ctx->lock);
            info.state = ctx->state;
            info.count = M->count;
            info.X = M->X;
            info.Y = M->Y;
            mutex_unlock(&ctx->lock);

            if (copy_to_user((void *)arg, &info, sizeof(info))) {
                ret = -EFAULT;
            } else {
                ret = 0;
            }
            break;
        }
        default:
            ret = -EINVAL;
    }
    return ret;
}


static struct file_operations fungez_fops = {
    .owner = THIS_MODULE,
    .open = fungez_open,
    .release = fungez_release,
    .mmap = fungez_mmap,
    .unlocked_ioctl = fungez_ioctl
};

static int __init fungez_init(void)
{
    int ret = 0;
    struct fungez_device *dev = NULL;

    printk(KERN_WARNING"fungez init...\n");

    dev = kzalloc(sizeof(struct fungez_device), GFP_KERNEL);
    if (dev == NULL) {
        goto err;
    }

    cdev_init(&dev->dev, &fungez_fops);
    dev->dev.owner = THIS_MODULE;

    dev->max_size = 0x40000;

    ret = cdev_add(&dev->dev, MKDEV(13, 37), 1);
    if (ret) {
        printk(KERN_ALERT"fungez failed to add device...\n");
        goto err;
    }

    dev->wq = create_singlethread_workqueue("fungez workqueue");
    if (dev->wq == NULL) {
        ret = -ENOMEM;
        goto err;
    }

    return 0;

err:
    if (dev != NULL) {
        kfree(dev);
    }

    return ret;
}

static void __exit fungez_exit(void)
{
    printk(KERN_WARNING"fungez exit...\n");
}

module_init(fungez_init);
module_exit(fungez_exit);

MODULE_DESCRIPTION("FUNGEZ");
MODULE_ALIAS("fungez");
MODULE_AUTHOR("slipper");
MODULE_LICENSE("GPL");
