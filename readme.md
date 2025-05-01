docker build -t sys_55010 .

docker run -d --restart always -v /root/dir_sys_55010:/_app_/utils/download --name sys_55010 -p 55010:55010 sys_55010

D:\Code\FASTAPI\API\Docker

docker run -d --restart always -v D:\Code\FASTAPI\API\Docker\utils:/_app_/utils/ --name sys_55010 -p 55010:55010 sys_55010

docker save -o sys_55010.tar sys_55010

docker load -i sys_55010.tar

docker exec -it sys_55010 bash

