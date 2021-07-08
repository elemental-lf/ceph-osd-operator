analytics_settings(enable=False)
version_settings(check_updates=False)
disable_snapshots()
docker_prune_settings(disable=False, num_builds=1, max_age_mins=1)

allow_k8s_contexts('kind-osdk-test')

docker_build('localhost:5000/testing-operator', '.',
             ignore=['*', '!Dockerfile', '!watches.yaml', '!requirements.yml', '!roles'])

k8s_kind('CephOSD')
k8s_resource('osdk-ceph-osds',
             extra_pod_selectors=[{'ceph.elemental.net/owner': 'CephOSD-osdk-ceph-osds'}],
             objects=['osdk-ceph-osd:PriorityClass'])


# listdir is used to trigger reevaluation of the Tiltfile and so an update of the manifests
_ = listdir('config', recursive=True)
k8s_yaml(local('kustomize build --load-restrictor LoadRestrictionsNone config/testing', quiet=True))
k8s_yaml(local('kustomize build --load-restrictor LoadRestrictionsNone config/samples', quiet=True))
