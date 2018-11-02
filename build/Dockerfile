FROM elementalnet/ansible-operator
USER root
RUN true

RUN useradd -u ${USER_UID} ${USER_NAME}
USER ${USER_NAME}

ENV RESYNC_PERIOD=8
COPY ansible/roles/ ${HOME}/roles/
COPY ansible/playbook.yaml ${HOME}/playbook.yaml
COPY watches.yaml ${HOME}/watches.yaml
