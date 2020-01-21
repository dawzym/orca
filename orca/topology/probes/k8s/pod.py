from orca.common import logger, str_utils
from orca.k8s import client as k8s_client
from orca.topology.probes import fetcher
from orca.topology.probes.k8s import extractor, linker, probe

log = logger.get_logger(__name__)


class PodProbe(probe.Probe):

    def run(self):
        log.info("Starting K8S watch on resource: pod")
        extractor = PodExtractor()
        handler = probe.KubeHandler(self._graph, extractor)
        watch = k8s_client.ResourceWatch(self._client.CoreV1Api(), 'pod')
        watch.add_handler(handler)
        watch.run()


class PodExtractor(extractor.Extractor):

    def extract_properties(self, entity):
        properties = {}
        properties['name'] = entity.metadata.name
        properties['namespace'] = entity.metadata.namespace
        properties['labels'] = entity.metadata.labels.copy()
        properties['ip'] = entity.status.pod_ip
        properties['node'] = entity.spec.node_name
        properties['containers'] = self._extract_containers(entity)
        properties['volumes'] = self._extract_volumes(entity)
        return properties

    def _extract_containers(self, entity):
        containers = []
        for container in entity.spec.containers:
            properties = {}
            properties['name'] = container.name
            properties['image'] = container.image
            properties['command'] = None
            if container.command:
                properties['command'] = str_utils.escape(" ".join(container.command))
            properties['env'] = self._extract_env(container)
            properties['env_from'] = None
            if container.env_from:
                properties['env_from'] = [env.to_dict() for env in container.env_from]
            containers.append(properties)
        return containers

    def _extract_env(self, container):
        if not container.env:
            return None
        env_vars = []
        for env in container.env:
            properties = {}
            properties['value_from'] = None
            if env.value_from:
                properties['value_from'] = env.value_from.to_dict()
            env_vars.append(properties)
        return env_vars

    def _extract_volumes(self, entity):
        volumes = []
        for volume in entity.spec.volumes:
            properties = {}
            properties['name'] = volume.name
            properties['secret'] = None
            if volume.secret:
                properties['secret'] = volume.secret.to_dict()
            properties['config_map'] = None
            if volume.config_map:
                properties['config_map'] = volume.config_map.to_dict()
            volumes.append(properties)
        return volumes


class PodToServiceLinker(linker.Linker):

    @staticmethod
    def create(graph, client):
        fetcher_a = fetcher.GraphFetcher(graph, 'pod')
        fetcher_b = fetcher.GraphFetcher(graph, 'service')
        matcher = PodToServiceMatcher()
        return PodToServiceLinker(graph, 'pod', fetcher_a, 'service', fetcher_b, matcher)


class PodToServiceMatcher(linker.Matcher):

    def are_linked(self, pod, service):
        match_namespace = self._match_namespace(pod, service)
        match_selector = self._match_selector(pod, service.properties.selector)
        return match_namespace and match_selector


class PodToReplicaSetLinker(linker.Linker):

    @staticmethod
    def create(graph, client):
        fetcher_a = fetcher.GraphFetcher(graph, 'pod')
        fetcher_b = fetcher.GraphFetcher(graph, 'replicaset')
        matcher = PodToReplicaSetMatcher()
        return PodToReplicaSetLinker(
            graph, 'pod', fetcher_a, 'replicaset', fetcher_b, matcher)


class PodToReplicaSetMatcher(linker.Matcher):

    def are_linked(self, pod, replica_set):
        match_namespace = self._match_namespace(pod, replica_set)
        match_selector = self._match_selector(pod, replica_set.properties.selector)
        return match_namespace and match_selector


class PodToNodeLinker(linker.Linker):

    @staticmethod
    def create(graph, client):
        fetcher_a = fetcher.GraphFetcher(graph, 'pod')
        fetcher_b = fetcher.GraphFetcher(graph, 'node')
        matcher = PodToNodeMatcher()
        return PodToNodeLinker(graph, 'pod', fetcher_a, 'node', fetcher_b, matcher)


class PodToNodeMatcher(linker.Matcher):

    def are_linked(self, pod, node):
        return pod.properties.node == node.properties.name
