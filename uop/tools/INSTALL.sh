#!/bin/bash

if [ "$UID" -ne 0 ]
then
    echo "Need root authority."
    exit 0
fi

# 添加epel源
yum install –y epel-release
yum clean all
yum update

# 安装工具包
yum install -y git screen tree psmisc curl wget multitail htop vim
yum install readline readline-devel readline-static
yum install openssl openssl-devel openssl-static
yum install sqlite-devel
yum install bzip2-devel bzip2-libs
yum install zlib-devel
yum install gcc libffi-devel python-devel
yum install openldap-devel -y
yum install ipvsadm kernel-devel popt-devel libnl-devel -y
yum install nmap -y
yum install openssh-server openssh-clients -y
yum install keepalived nginx ansible nodejs -y

