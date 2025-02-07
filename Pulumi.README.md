# 4ir-guestbook-assignment

## Instructions to deploy the application locally

## Assumptions:
Running a minikube cluster that is the kubernetes current cluster, as determined by kubectl get current-context.

Running without a load balancer locally.

Install pulumi if it is not installed.

Clone this repo to a local folder. 
Go into the newly created folder and run the following command to deploy the guestbook stack:
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
Use the username and password provided after running "pulumi up" or "pulumi output" commands.

