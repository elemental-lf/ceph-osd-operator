FROM elementalnet/ansible-operator:af4fa0b
USER root
RUN echo 'jinja2_extensions = jinja2.ext.do,jinja2.ext.loopcontrols' >> /etc/ansible/ansible.cfg && \
	HOME=/tmp pip install --upgrade jinja2 && \
	rm -rf /tmp/.cache/pip && \
	useradd -u ${USER_UID} ${USER_NAME}

USER ${USER_NAME}

ENV RESYNC_PERIOD=8
COPY ansible/playbook.yaml ${HOME}/playbook.yaml
COPY ansible/roles/ ${HOME}/roles/
COPY watches.yaml ${HOME}/watches.yaml
