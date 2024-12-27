from string import Template
import argparse
import pyunycode

separator = "---"

namespace_t = """
apiVersion: v1
kind: Namespace
metadata:
  labels:
    cos: ${cos}
    kubernetes.io/metadata.name: ${cos}-${sanitized_domain}
    project: ${sanitized_domain}
  name: ${cos}-${sanitized_domain}
"""

route_t = """
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: http-route
  namespace: ${cos}-${sanitized_domain}
  labels:
    cos: ${cos}
    kubernetes.io/metadata.name: ${cos}-${sanitized_domain}
    project: ${sanitized_domain}
spec:
  parentRefs:
  - name: external-https
    namespace:  gateway-infra
  hostnames:
  - ${subdomain}.${domain}
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /
    backendRefs:
    - name: default-app
      port: 80
"""

service_t = """
apiVersion: v1
kind: Service
metadata:
  name: default-app
  namespace: ${cos}-${sanitized_domain}
  labels:
    app: default-app
    cos: ${cos}
    kubernetes.io/metadata.name: ${cos}-${sanitized_domain}
    project: ${sanitized_domain}
spec:
  ports:
  - port: 80
    protocol: TCP
    targetPort: 80
  selector:
    app: default-app
"""

deployment_t = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: default-app
  namespace: ${cos}-${sanitized_domain}
  labels:
    app: default-app
    cos: ${cos}
    kubernetes.io/metadata.name: ${cos}-${sanitized_domain}
    project: ${sanitized_domain}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: default-app
  template:
    metadata:
      labels:
        app: default-app
    spec:
      containers:
      - image: nginx
        name: nginx
        ports:
        - containerPort: 80
          protocol: TCP
        volumeMounts:
        - mountPath: /usr/share/nginx/html
          name: html
      volumes:
      - name: html
        persistentVolumeClaim:
          claimName: ${cos}-${sanitized_domain}-pvc
"""

pvc_t = """
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ${cos}-${sanitized_domain}-pvc
  namespace: ${cos}-${sanitized_domain}
  labels:
    app: default-app
    cos: ${cos}
    kubernetes.io/metadata.name: ${cos}-${sanitized_domain}
    project: ${sanitized_domain}
spec:
  storageClassName: local-hostpath
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 4Gi
"""

resource_map = {
    "namespace": namespace_t,
    "route": route_t,
    "service": service_t,
    "deployment": deployment_t,
    "pvc": pvc_t
}


def format(tmpl, data):
    return Template(tmpl).safe_substitute(data).strip('\n')


def do_generate(resources, data):

    first = True
    for resource in resources:
        if not first:
            print(separator)

        if resource not in resource_map:
            raise Exception(f"unknown resource '{resource}'")

        print(format(resource_map[resource], data))
        first = False


def parse_tokens(input_str):
    return [x.strip() for x in input_str.split(',')]


def generate(args):

    resources = parse_tokens(args.resources)

    data = {
        "cos": args.cos,
        "replicas": args.replicas
    }

    domain = args.domain
    if domain == None:
        domain = input("Enter domain name: ")

    domain = pyunycode.convert(domain)
    data["domain"] = domain
    data["subdomain"] = "www" if args.cos == "prod" else args.cos
    data["sanitized_domain"] = domain.replace(".", args.dot)

    outputFile = args.o
    if outputFile != None:
        import sys
        with open(outputFile, 'w') as sys.stdout:
            do_generate(resources, data)
    else:
        do_generate(resources, data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='Project',
                    description='Gateway-infra project generator',
                    epilog='Copyright (C) Karagatan, LLC.')
    parser.add_argument("--domain", type=str, help='domain name')
    parser.add_argument("--resources", type=str, default='namespace,route,service,deployment,pvc', help='generate type of resource')
    parser.add_argument("--cos", type=str, default='prod', help='class of service')
    parser.add_argument("--replicas", type=int, default=1, help='number of replicas')
    parser.add_argument("--dot", type=str, default='-dot-', help='replace dot to this')
    parser.add_argument("-o", type=str, help='output file name')
    args = parser.parse_args()
    generate(args)
