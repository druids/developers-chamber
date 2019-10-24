FROM docker:stable-dind

RUN apk update && apk add git python3 python3-dev libffi-dev openssl-dev gcc libc-dev make gettext openssl-dev bash openssh 
RUN pip3 install --upgrade urllib3==1.24.3 awscli==1.16.241 requests==2.22.0 docker-compose developers-chamber==0.0.19

ENTRYPOINT ["bash", "-c"]

