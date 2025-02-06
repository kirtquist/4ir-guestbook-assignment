# 4ir-guestbook-assignment
Extend the existing Pulumi Kubernetes Guestbook example (https://github.com/pulumi/examples/blob/master/kubernetes-ts-guestbook/README.md)
by integrating monitoring with Prometheus and Grafana to observe application performance.

## Instructions to deploy the application locally

## Assumptions:
Running a minikube cluster that is the kubernetes current cluster, as determined by kubectl get current-context.

Running without a load balancer locally.

Install pulumi if it is not installed.  
Instructions to install pulumi.  
    https://www.pulumi.com/docs/iac/get-started/kubernetes/begin/ 

Clone this repo to a local folder.  
Go into the newly created folder and deploy the guestbook stack.
### Deploy the application using the following command.
    pulumi up

### To access the Guestbook:
    kubectl port-forward svc/frontend 8080:80
    
Access Grafana via the browser at http://localhost:8080

### To access Prometheus:
    kubectl port-forward svc/prometheus-server -n monitoring 9090:80

Access Grafana via the browser at http://localhost:9090    

### To access Grafana:
    kubectl port-forward svc/grafana -n monitoring 32000:80  


Access Grafana via the browser at http://localhost:32000  
You may not need to use the port-forward if it isn't blocked by a local firewall, as it may be on MacOS.
Use the username and password provided after running "pulumi up" or "pulumi stack output" commands.

