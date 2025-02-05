# __main__.py

import pulumi
from pulumi_kubernetes.apps.v1 import Deployment
from pulumi_kubernetes.core.v1 import Service, Namespace

from pulumi_kubernetes.helm.v3 import Chart, ChartOpts
from pulumi_kubernetes.helm.v3 import FetchOpts
from pulumi_kubernetes import Provider
from pulumi_kubernetes.core.v1 import ConfigMap


with open('./Pulumi.README.md') as f:
    pulumi.export('readme',f.read())

# Create only services of type `ClusterIP`
# for clusters that don't support `LoadBalancer` services
config = pulumi.Config()
useLoadBalancer = config.get_bool("useLoadBalancer")

# Kubernetes provider
provider = Provider("k8s-provider")

redis_leader_labels = {
    "app": "redis-leader",
}

redis_leader_deployment = Deployment(
    "redis-leader",
    spec={
        "selector": {
            "match_labels": redis_leader_labels,
        },
        "replicas": 3,
        "template": {
            "metadata": {
                "labels": redis_leader_labels,
            },
            "spec": {
                "containers": [{
                    "name": "redis-leader",
                    "image": "redis",
                    "resources": {
                        "requests": {
                            "cpu": "100m",
                            "memory": "100Mi",
                        },
                    },
                    "ports": [{
                        "container_port": 6379,
                    }],
                }],
            },
        },
    })

redis_leader_service = Service(
    "redis-leader",
    metadata={
        "name": "redis-leader",
        "labels": redis_leader_labels
    },
    spec={
        "ports": [{
            "port": 6379,
            "target_port": 6379,
        }],
        "selector": redis_leader_labels
    })

redis_replica_labels = {
    "app": "redis-replica",
}

redis_replica_deployment = Deployment(
    "redis-replica",
    spec={
        "selector": {
            "match_labels": redis_replica_labels
        },
        "replicas": 3,
        "template": {
            "metadata": {
                "labels": redis_replica_labels,
            },
            "spec": {
                "containers": [{
                    "name": "redis-replica",
                    "image": "pulumi/guestbook-redis-replica",
                    "resources": {
                        "requests": {
                            "cpu": "100m",
                            "memory": "100Mi",
                        },
                    },
                    "env": [{
                        "name": "GET_HOSTS_FROM",
                        "value": "dns",
                        # If your cluster config does not include a dns service, then to instead access an environment
                        # variable to find the leader's host, comment out the 'value: dns' line above, and
                        # uncomment the line below:
                        # value: "env"
                    }],
                    "ports": [{
                        "container_port": 6379,
                    }],
                }],
            },
        },
    })

redis_replica_service = Service(
    "redis-replica",
    metadata={
        "name": "redis-replica",
        "labels": redis_replica_labels
    },
    spec={
        "ports": [{
            "port": 6379,
            "target_port": 6379,
        }],
        "selector": redis_replica_labels
    })

# Frontend
frontend_labels = {
    "app": "frontend",
}


frontend_deployment = Deployment(
    "frontend",
    spec={
        "selector": {
            "match_labels": frontend_labels,
        },
        "replicas": 3,
        "template": {
            "metadata": {
                "labels": frontend_labels,
            },
            "spec": {
                "containers": [{
                    "name": "php-redis",
                    "image": "pulumi/guestbook-php-redis",
                    "resources": {
                        "requests": {
                            "cpu": "100m",
                            "memory": "100Mi",
                        },
                    },
                    "env": [{
                        "name": "GET_HOSTS_FROM",
                        "value": "dns",
                        # If your cluster config does not include a dns service, then to instead access an environment
                        # variable to find the leader's host, comment out the 'value: dns' line above, and
                        # uncomment the line below:
                        # "value": "env"
                    }],
                    "ports": [{
                        "container_port": 80,
                    }],
                }],
            },
        },
    })

frontend_service = Service(
    "frontend",
    metadata={
        "name": "frontend",
        "labels": frontend_labels
    },
    spec={
        "type": "LoadBalancer" if useLoadBalancer else "ClusterIP",
        "ports": [{
            "port": 80
        }],
        "selector": frontend_labels,
    })

frontend_ip = ""
if useLoadBalancer:
    ingress = frontend_service.status.apply(lambda status: status["load_balancer"]["ingress"][0])
    frontend_ip = ingress.apply(lambda ingress: ingress.get("ip", ingress.get("hostname", "")))
else:
    frontend_ip = frontend_service.spec.apply(lambda spec: spec.get("cluster_ip", ""))



###################################################
#  Additions added to pulumi Guestbook example
###################################################

# Create a namespace for monitoring tools
monitoring_ns = Namespace("monitoring", metadata={"name": "monitoring"})




extra_scrape_config = ConfigMap(
    "extra-scrape-config",
    metadata={
        "name": "extra-scrape-config",
        "namespace": monitoring_ns.metadata["name"],
    },
    data={
        "additional-scrape-configs.yaml": """
scrape_configs:
  - job_name: "redis-exporter"
    static_configs:
      - targets: ["redis-exporter.default.svc.cluster.local:9121"]
"""
    }
)


# Deploy Prometheus using Helm chart
prometheus_chart = Chart(
    "prometheus",
    ChartOpts(
        chart="prometheus",
        version="25.10.0",  # Check the latest stable version
        fetch_opts=FetchOpts(
            repo="https://prometheus-community.github.io/helm-charts"
        ),
        namespace=monitoring_ns.metadata["name"],
        values={
            "server": {
                "enabled": True,
                "global": {
                    "scrape_interval": "15s"
                },
                "extraScrapeConfigs": [
                    {
                        "job_name": "redis-exporter",
                        "static_configs": [
                            {"targets": ["redis-exporter.default.svc.cluster.local:9121"]}
                        ]
                    }
                ]
            },
            "prometheus": {
                "prometheusSpec": {
                    "additionalScrapeConfigsSecret": "extra-scrape-config",
                }
            }  
        }    
    ),
    opts=pulumi.ResourceOptions(provider=provider),
)

# Deploy Grafana using Helm chart
grafana_chart = Chart(
    "grafana",
    ChartOpts(
        chart="grafana",
        version="7.0.8",  # Check the latest stable version
        fetch_opts=FetchOpts(
            repo="https://grafana.github.io/helm-charts"
        ),
        namespace=monitoring_ns.metadata["name"],
        values={
            "service": {
                "type": "NodePort",
                "nodePort": 32000,  # Expose Grafana on NodePort 32000
            },
            "adminUser": "admin",
            "adminPassword": "admin",  # Change this in production
        },
    ),
    opts=pulumi.ResourceOptions(provider=provider),
)

# Expose Grafana URL
grafana_service = grafana_chart.get_resource("v1/Service", "monitoring/grafana")
grafana_node_port = grafana_service.spec.apply(lambda spec: spec.ports[0].node_port)

grafana_url = grafana_service.spec.apply(lambda spec: (
    f"http://localhost:{spec.ports[0].node_port}" if spec and spec.type == "NodePort"
    else "Grafana service type not found or incorrect"
))


# Added redis_exporter for additional metrics

redis_exporter_deployment = Deployment(
    "redis-exporter",
    spec={
        "selector": {
            "match_labels": {"app": "redis-exporter"},
        },
        "replicas": 1,
        "template": {
            "metadata": {
                "labels": {"app": "redis-exporter"},
            },
            "spec": {
                "containers": [{
                    "name": "redis-exporter",
                    "image": "oliver006/redis_exporter:latest",
                    "ports": [{
                        "container_port": 9121,
                    }],
                    "env": [
                        {"name": "REDIS_ADDR", "value": "redis-leader:6379"},
                        {"name": "REDIS_ADDR_R", "value": "redis-replica:6379"},
                    ],
                }],
            },
        },
    })

redis_exporter_service = Service(
    "redis-exporter",
    metadata={
        "name": "redis-exporter",
        "labels": {"app": "redis-exporter"},
    },
    spec={
        "ports": [{
            "port": 9121,
            "target_port": 9121,
        }],
        "selector": {"app": "redis-exporter"},
    })


pulumi.export("frontend_ip", frontend_ip)
pulumi.export("command to expose frontend locally on port 8080","kubectl port-forward svc/frontend 8080:80")
pulumi.export("frontend_url","http://localhost:8080")

pulumi.export("grafana_url", grafana_url)
# kubectl port-forward -n monitoring svc/grafana 32000:80
pulumi.export("grafana_node_port", grafana_node_port)

# hard coded the grafana user/password. TODO - pull these programattically...
pulumi.export("grafana_admin_user", "admin")
pulumi.export("grafana_admin_password", "admin")  # Consider using Kubernetes Secrets in production


# Cluster Recommendation
recommended_cluster = "minikube"  # Recommended for NodePort support, running locally for ease of use.
pulumi.export("recommended_cluster", recommended_cluster)
