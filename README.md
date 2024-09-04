# gateway-infra
gateway-infra creation scripts

## Gateway

Interactive mode to generate all resources for gateway-infra (default)
```
user@Mac-mini gateway-infra % python3 gateway.py                                   
Enter email for ACME account: alex@example.com
Enter API-TOKEN of Cloudflare account: <your secret token>
Enter comma separated domain list: example.com,experiment.com
```

Command line to generate only gateway
```
python3 gateway.py --domains=example.com,experiment.com --resources=gateway
```

Command line to generate only certificates
```
python3 gateway.py --domains=example.com,experiment.com --resources=certificates
```

Command line to generate only issuer
```
python3 gateway.py --email=alex@example.com --resources=issuer 
```

Command line to generate only secret
```
python3 gateway.py --api_token=<your_token> --resources=secret 
```

Command line to generate only namespace
```
python3 gateway.py --resources=namespace
```

## Project

Interactive mode to generate all resources (default)
```
user@Mac-mini gateway-infra % python3 project.py 
Enter domain name: example.com
```

Generate all resources
```
python3 project.py --domain=example.com  
```

Generate namespace
```
python3 project.py --domain=example.com --resources=namespace
```

Generate route
```
python3 project.py --domain=example.com --resources=route
```

Generate service
```
python3 project.py --domain=example.com --resources=service
```

Generate deployment
```
python3 project.py --domain=example.com --resources=deployment
```
