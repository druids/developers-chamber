FROM docker:stable-dind

RUN apk update && apk add git python3 python3-dev libffi-dev openssl-dev gcc libc-dev make gettext openssl-dev bash openssh 
RUN pip3 install --upgrade urllib3==1.24.3 awscli docker-compose developers-chamber==0.0.10

ENTRYPOINT ["bash", "-c"]

