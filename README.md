# Ceph OSD Operator

This repository includes a Ceph OSD operator based on the Ansible variant of the
[Red Hat (formerly CoreOS) Operator SDK](https://github.com/operator-framework/operator-sdk).

In contrast to [Rook](https://github.com/rook/rook) it is not a one-stop solution for deploying Ceph but only deals
with the orchestration of the Ceph OSDs. To be a complete solution it needs further support. Currently 
`ceph-osd-operator` is used in [ceph-with-helm](https://github.com/elemental-lf/ceph-with-helm) to form a complete
container based installation of Ceph.

## Version Information

This is the second major version based on version 0.10.0 of the Operator SDK. Its predecessor worked like 
a charm for over six months.

* Functionality is the same as in previous versions.

* A test suite based on the framework provided by the SDK has been added. It uses
  [Molecule](https://molecule.readthedocs.io/en/stable/). Two test scenarios are provided: `default` and `test-local`.
  Both create a three node Kubernetes cluster based on [Kind](https://github.com/kubernetes-sigs/kind). `test-local`
  is the more useful of the two scenarios. Requirements: Docker, Ansible, Python packages `molecule`, `openshift`,
  `jmespath`. (NB: Kind does not work when `/var/lib/docker` is on a `btrfs` filesystem. The main problem seems
  to be with `kubelet`.)

* The naming of the CRD was erroneous as it used the singular instead of the plural, this has been corrected. The CRD
  and all custom resources need to be recreated which will disrupt the Ceph cluster. **Action required.**

* Any Helm charts including operator will also need updating as the manifests have changed.
  See `deploy/operator.yaml` and `deploy/role.yaml`. **Action required.**

* The problem where logging artifacts would accumulate in the operator pod has been solved through the Operator SDK
  update. Only the log files of the last twenty runs are kept now.

* The helper scripts have been updated to reflect the new pod structure of the Operator SDK. **Action required.**

## Details

This operator only supports Bluestore based deployments with `ceph-volume`. Separate devices for the RocksDB and 
the WAL can be specified. Support for passing the WAL is untested as `ceph-with-helm` currently doesn't support it.
The operator creates one pod per OSD. The `restartPolicy` on these pods should normally by `Always` to ensure that
they are restarted automatically when they terminate unexpectedly. Missing pods will automatically be recreated by 
the operator. During deployment of the pods `nodeAffinity` rules are injected into the pod definition to bind the pod
to a specific node.

Rolling updates of the pod configuration (including container images) can either be performed one OSD at a time or 
on a host by host basis. At the moment there is no direct interaction between the operator and Ceph and the operator
only watches the `Ready` condition of newly created pods. But if the readiness check is implemented correctly
this should go a long way in making sure that the OSD is okay. If an updated OSD pod doesn't become ready the update
process is halted and no further OSDs are updated without manual intervention.

### Structure of the CephOSD custom resource

```yaml
apiVersion: ceph.elemental.net/v1alpha1
kind: CephOSD
metadata:
  name: ceph-osds
spec:
  storage:
    - hosts:
      - worker041.example.com
      - worker042.example.com
      osds:
      - data: '/dev/disk/by-slot/pci-0000:5c:00.0-encl-0:7:0-slot-1'
        db: '/dev/disk/by-slot/pci-0000:5c:00.0-encl-0:7:0-slot-10-part1'
      - data: '/dev/disk/by-slot/pci-0000:5c:00.0-encl-0:7:0-slot-2'
        db: '/dev/disk/by-slot/pci-0000:5c:00.0-encl-0:7:0-slot-10-part2'
  updateDomain: "Host"
  podTemplate:
# [...]
```

* `storage` is a list of `hosts`/`osds` pairs. The cartesian product of each element of the `hosts` list and each
  element of the `osds` is formed and an OSD pod is created for each resulting host/osd pair. This is repeated for
  each element of the `storage` list.
* The hostnames of a `hosts` list must match your Kubernetes node names as they are used for constructing the 
  `nodeAffinity` rules.
* Each element of an `osds` list consists of a dictionary with up to three keys: `data`, `db` and `wal`. Only the `data`
  key is mandatory and its value represent the primary OSD data device. A separate RocksDB or WAL location can be
  specified by setting the `db` or `wal` keys respectively.
* `updateDomain` can either be set to `OSD` to perform rolling updates one OSD at a time. Or it can be set to `Host`
  to update all pods on a host at the same time before proceeding to the next host.
* The `podTemplate` should contain a complete pod definition. It is instantiated for each OSD by replacing some values
  like `metadata.name` or `metadata.namespace` and adding other values (`labels`, `annotations`, and `nodeAffinity` 
  rules). See `ansible/roles/CephOSD/templates/pod-definition-additions.yaml.j2` for a complete list of changes.
  
The whole custom resource is checked against an OpenAPIv3 schema provided in the included custom resource definition.
This includes the `podTemplate`. Changes to the `Pod` specification by the Kubernetes team might require updates
to the schema in the future.

### Pod states and rolling update state machine

Each pod has an annotation named `ceph.elemental.net/pod-state` tracking its state. These states are:

* `up-to-date`: The pod looks fine and its configuration is up-to-date.
* `out-of-date` The pod looks fine but its configuration is out-of-date and it will be updated by recreating it.
* `ready`: The pod is up-to-date, it is waiting to get ready and its actual state is ready. This state is only
  used internally and is not reflected in the annotation.
* `unready`: The pod is up-to-date and it is waiting to get ready but it is not ready (yet). Internal state only.
* `invalid`: The pod is missing some mandatory annotations, i.e. it is a duplicate or has an invalid name. 
  It will be deleted. Internal state only.

The state of a pod is determined by this logic:

* If the pod is terminating:
    * The pod is ignored altogether.
* Else if the mandatory pod annotations are present:
    * If the pod is a duplicate of another pod:
        * The pod is invalid.
    * Else if the pod name doesn't conform to our scheme:
        * The pod is invalid.
    * Else if the pod's template hash equals the current template hash from the CR:
        * If the pod is waiting to get ready and its actual state is ready:
            * The pod is ready.
        * Else if the pod is waiting to get ready and it's not ready:
            * The pod is unready.
        * Else:
            * The pod is up-to-date.
    * Else:
        * The pod is out-of-date.
* Else:
    * The pod is invalid.

When the `podTemplate` is changed all pods are marked as `out-of-date`. Depending on the `updateDomain` one pod 
or all pods of one host from the `out-of-date` list are recreated with the new configuration. After that the
operator waits for the new pod or for the group of new pods to become ready. When all new pods have become ready the
operator proceeds to the next `out-of-date` pod or group of pods. If not all pods become ready the update process
halts and it requires manual intervention by an administrator. Options for the administrator include:

* If the `podTemplate` is faulty, the administrator can fix the `podTemplate` and the update process will 
  automatically restart from the beginning.
* If there are other reasons preventing a pod from becoming ready the administrator can fix them. After that the pod 
  should become ready after some time and the update process continues automatically.
* The administrator can delete the `ceph.elemental.net/pod-state` annotation or set it to `up-to-date` overriding the
  operator. The update process will continue without waiting for this pod to become ready. 
 
### Recommendations for the pod template

The `restartPolicy` in the pod template should be `Always`. In addition the following tolerations should be included
to prevent eviction under these conditions:

```yaml
      tolerations:
        - key: node.kubernetes.io/unschedulable
          operator: Exists
          effect: NoSchedule
        - key: node.kubernetes.io/not-ready
          operator: Exists
        - key: node.kubernetes.io/unreachable
          operator: Exists
```

It is also a good idea to set a `priorityClass` in the template:
  
```yaml
apiVersion: scheduling.k8s.io/v1beta1
kind: PriorityClass
metadata:
  name: ceph-osd
value: 1000000000

```
  
## Container Images

Container images for the operator are available on [Docker Hub](https://hub.docker.com/r/elementalnet/ceph-osd-operator/).
Images are build automatically from the Git repository by Travis CI.

## Future Ideas

* Setting `noout` for OSDs during update
* Watch OSD status directly via Ceph during update
