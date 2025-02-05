# 4ir-guestbook-assignment

## Instructions to deploy the application

# Assumptions:
Running a minikube cluster that is the kubernetes current cluster, as determined by kubectl get current-context

Running without a load balancer locally


Run the following command to deploy the guestbook stack:
    pulumi up

# To access the Guestbook:
    kubectl port-forward svc/frontend 8080:80
    
Access Grafana via the browser at http://localhost:8080

# To access Prometheus:
    kubectl port-forward svc/grafana 9090:80
Access Grafana via the browser at http://localhost:9090    

# To access Grafana:
    kubectl port-forward svc/grafana 32000:80
Access Grafana via the browser at http://localhost:32000
Use the username and password provided after running pulumi up or pulumi output commands.

