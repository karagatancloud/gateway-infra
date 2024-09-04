from string import Template
import argparse

separator = "---"

gateway_t = """
apiVersion: v1
kind: Namespace
metadata:
  labels:
    kubernetes.io/metadata.name: gateway-infra
    project: gateway-infra
  name: gateway-infra
"""

secret_t = """
apiVersion: v1
kind: Secret
metadata:
  name: cloudflare-api-token
  namespace: gateway-infra
type: Opaque
stringData:
  api-token: ${api_token}
"""

issuer_t = """
apiVersion: cert-manager.io/v1
kind: Issuer
metadata:
  name: acme-cert-issuer
  namespace: gateway-infra
spec:
  acme:
    # The ACME server URL
    server: https://acme-v02.api.letsencrypt.org/directory
    # Email address used for ACME registration
    email: ${email}
    # Name of a secret used to store the ACME account private key
    privateKeySecretRef:
      name: acme-cert-issuer-pk
    solvers:
    - dns01:
        cloudflare:
          apiTokenSecretRef:
            name: cloudflare-api-token
            key: api-token
"""

certificate_t = """
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: ${domain}
  namespace: gateway-infra
spec:
  # Common name to be used on the Certificate.
  commonName: "*.${domain}"
  # List of DNS subjectAltNames to be set on the Certificate.
  dnsNames:
    - "${domain}"
    - "*.${domain}"
  secretName: ${domain}-tls
  issuerRef:
    name: acme-cert-issuer
"""

header_t = """
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: external-https
  namespace: gateway-infra
  labels:
    public-service: "true"
spec:
  gatewayClassName: cilium
  listeners:
"""

entry_t = """
  - name: https-w-${sanitized_name}
    protocol: HTTPS
    port: 443
    hostname: "*.${domain}"
    tls:
      certificateRefs:
      - kind: Secret
        name: ${domain}-tls
    allowedRoutes:
      kinds:
      - kind: HTTPRoute
      namespaces:
        from: Selector
        selector:
          matchLabels:
            project: ${sanitized_name}
  - name: https-${sanitized_name}
    protocol: HTTPS
    port: 443
    hostname: "${domain}"
    tls:
      certificateRefs:
      - kind: Secret
        name: ${domain}-tls
    allowedRoutes:
      kinds:
      - kind: HTTPRoute
      namespaces:
        from: Selector
        selector:
          matchLabels:
            project: ${sanitized_name}
"""

def format(tmpl, **kwargs):
    return Template(tmpl).safe_substitute(kwargs).strip('\n')


def gen_namespace(domain_list, data):
    yield gateway_t.strip('\n')


def get_secret(domain_list, data):
    yield format(secret_t, api_token=data["api_token"])


def gen_issuer(domain_list, data):
    yield format(issuer_t, email=data["email"])


def gen_certificates(domain_list, data):
    for domain in domain_list:
        if domain != "":
            yield format(certificate_t, domain=domain)


def gen_gateway(domain_list, data):
    yield header_t.strip('\n')
    for domain in domain_list:
        yield format(entry_t, domain=domain, sanitized_name=domain.replace(".", "-"))


def gen_gateway_collector(domain_list, data):
    lines = []
    for value in gen_gateway(domain_list, data):
        lines.append(value)
    yield "\n".join(lines)


resource_map = {
    "namespace": gen_namespace,
    "secret": get_secret,
    "issuer": gen_issuer,
    "certificates": gen_certificates,
    "gateway": gen_gateway_collector
}


def do_generate(resources, domain_list, data):
    first = True
    for resource in resources:

        if resource not in resource_map:
            raise Exception(f"unknown resource '{resource}'")

        generator = resource_map[resource]

        for value in generator(domain_list, data):
            if not first:
                print(separator)
            print(value)
            first = False


def parse_tokens(input_str):
    return [x.strip() for x in input_str.split(',')]


def generate(args):

    data = {}

    resources = parse_tokens(args.resources)

    if "secret" in resources:
        email = args.email
        if email == None:
            email = input("Enter email for ACME account: ")
        data["email"] = email

        api_token = args.api_token
        if api_token == None:
            api_token = input("Enter API-TOKEN of Cloudflare account: ")
        data["api_token"] = api_token


    domain_list = args.domains
    if domain_list == None:
        domain_list = input("Enter comma separated domain list: ")
    domain_list = parse_tokens(domain_list)

    outputFile = args.o
    if outputFile != None:
        import sys
        with open(outputFile, 'w') as sys.stdout:
            do_generate(resources, domain_list, data)
    else:
        do_generate(resources, domain_list, data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='Gateway',
                    description='Gateway-infra gateway generator',
                    epilog='Copyright (C) Karagatan, LLC.')
    parser.add_argument("--domains", type=str, help='comma separated domain list')
    parser.add_argument("--resources", type=str, default='namespace,secret,issuer,certificates,gateway', help='generate type of resource')
    parser.add_argument("--email", type=str, help='email for ACME account')
    parser.add_argument("--api_token", type=str, help='API-TOKEN from Cloudflare account')
    parser.add_argument("-o", type=str, help='output file name')
    args = parser.parse_args()
    generate(args)
