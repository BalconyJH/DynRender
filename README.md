# DynRender-skia
使用skia渲染BiliBili动态

# 注意

Linux用户可能会出现以下报错
```bash
libGL.so.1: cannot open shared object file: No such file or directory
```
## 解决方法

> ubuntu用户

```bash

apt install libgl1-mesa-glx

```
> ArchLinux用户

```bash
pacman -S libgl
```