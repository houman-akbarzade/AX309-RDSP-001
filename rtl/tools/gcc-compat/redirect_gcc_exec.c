#define _GNU_SOURCE
#include <dlfcn.h>
#include <unistd.h>
#include <string.h>
#include <stdlib.h>

/* ISE 14.7 Fuse invokes /usr/bin/gcc by absolute path. On this host GCC 15
 * is too new for the 2013 simulator-generated C. Redirect only that compiler
 * invocation to the bundled host GCC 6.2 and supply the current multiarch
 * glibc include/startup-file locations.
 */
int execve(const char *path, char *const argv[], char *const envp[]) {
    static int (*real_execve)(const char *, char *const [], char *const []) = 0;
    static const char *gcc_compat =
        "/opt/Xilinx/Vivado/2019.1/tps/lnx64/gcc-6.2.0/bin/gcc";
    static char *extra[] = {
        "-std=gnu89",
        "-I/usr/include/x86_64-linux-gnu",
        "-B/usr/lib/x86_64-linux-gnu/",
        0
    };
    char **new_argv;
    int argc, i;

    if (!real_execve)
        real_execve = dlsym(RTLD_NEXT, "execve");

    if (strcmp(path, "/usr/bin/gcc") != 0)
        return real_execve(path, argv, envp);

    for (argc = 0; argv[argc] != 0; ++argc) {}
    new_argv = calloc((size_t)argc + 4, sizeof(char *));
    if (!new_argv)
        return -1;

    new_argv[0] = (char *)gcc_compat;
    for (i = 0; i < 3; ++i)
        new_argv[i + 1] = extra[i];
    for (i = 1; i < argc; ++i)
        new_argv[i + 3] = argv[i];

    return real_execve(gcc_compat, new_argv, envp);
}
