from string import Template
import argparse

separator = "---"

namespace_t = """
apiVersion: v1
kind: Namespace
metadata:
  labels:
    cos: ${cos}
    kubernetes.io/metadata.name: ${cos}-${sanitized_name}
    project: ${sanitized_name}
  name: ${cos}-${sanitized_name}
"""

route_t = """
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: http-route
  namespace: ${cos}-${sanitized_name}
spec:
  parentRefs:
  - name: external-https
    namespace:  gateway-infra
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
  labels:
    app: default-app
  name: default-app
  namespace: ${cos}-${sanitized_name}
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
  annotations:
    deployment.kubernetes.io/revision: "1"
  generation: 1
  labels:
    app: default-app
  name: default-app
  namespace: prod-karagatan-com
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
"""

resource_map = {
    "namespace": namespace_t,
    "route": route_t,
    "service": service_t,
    "deployment": deployment_t
}


def format(tmpl, data):
    return Template(tmpl).safe_substitute(data).strip('\n')


def do_generate(resources, data):
    data["sanitized_name"] = data["domain"].replace(".", "-")

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
    data["domain"] = domain

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
    parser.add_argument("--resources", type=str, default='namespace,route,service,deployment', help='generate type of resource')
    parser.add_argument("--cos", type=str, default='dev', help='class of service')
    parser.add_argument("--replicas", type=int, default=1, help='number of replicas')
    parser.add_argument("-o", type=str, help='output file name')
    args = parser.parse_args()
    generate(args)