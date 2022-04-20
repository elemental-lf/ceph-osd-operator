FROM quay.io/operator-framework/ansible-operator:v1.19.1

USER 0
RUN echo 'jinja2_extensions = jinja2.ext.do,jinja2.ext.loopcontrols' >> /etc/ansible/ansible.cfg
USER ${USER_UID}

COPY requirements.yml ${HOME}/requirements.yml
RUN ansible-galaxy collection install -r ${HOME}/requirements.yml \
 && chmod -R ug+rwx ${HOME}/.ansible

COPY watches.yaml ${HOME}/watches.yaml

COPY roles/ ${HOME}/roles/
