# Unified operation platform 后端项目

## 开发环境准备

### 安装Python
	# yum install -y gcc glibc make openssl-devel mariadb-devel
	# cd /usr/local/src
	# wget https://www.python.org/ftp/python/2.7.10/Python-2.7.10.tgz
	# tar zxf Python-2.7.10.tgz
	# cd Python-2.7.10
	# ./configure --prefix=/usr/local/python-2.7.10
	# make && make install

### 安装setuptools

	# wget https://pypi.python.org/packages/55/61/fdecfda95355db1c67daa6c8e6ee747f8a0bbc0a5e18f8bfd716bdffac3e/setuptools-35.0.1.zip#md5=88b03a5f88772f96a60236368a91d86e
	# tar zxf pypa-setuptools-a6daa77a00b2.tar.gz && cd pypa-setuptools-a6daa77a00b2
	# /usr/local/python-2.7.10/bin/python setup.py install
	
### 安装pip

	# wget http://pip-1.5.6.tar.gz
    # tar zxf pip-1.5.6.tar.gz && cd pip-1.5.6
	# /usr/local/python-2.7.10/bin/python setup.py install


## 项目运行

###使用虚拟环境
    # /usr/local/python-2.7.10/bin/pip install virtualenv
	
	# cd /opt/
	# /usr/local/python-2.7.10/bin/virtualenv uop-backend-runtime
	# git clone git@172.28.4.61:devops/uop-backend.git
	# source uop-backend-runtime/bin/activate
	# pip install -r /opt/uop-backend-runtime/uop-backend/requirements.txt

启动mongodb 并分别创建uop数据库
  创建mongodb数据库和用户
  
    #> use uop
	#	switched to db cmdb
	#> db.addUser("uop", "uop");