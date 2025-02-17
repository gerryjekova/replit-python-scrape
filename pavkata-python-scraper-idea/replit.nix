{ pkgs }: {
    deps = [
        pkgs.python39
        pkgs.redis
        pkgs.python39Packages.pip
    ];
}