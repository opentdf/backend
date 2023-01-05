## Generate CA and Server Certificates

```console
openssl genrsa -aes256 -out ca.key 2048

openssl req -x509 -new -nodes -key ca.key -sha256 -days 1024 -out ca.crt -subj "/C=US/ST=Home/L=Home/O=mycorp/OU=myorg/CN=caroot.keycloak-http"

openssl genrsa -out  tls.key 2048

openssl req -new -key  tls.key -out  keycloak-http.csr -subj "/C=UA/ST=Home/L=Home/O=mycorp/OU=myorg/CN=keycloak-http"

openssl x509 -req -extfile <(printf "subjectAltName=DNS:keycloak-http") -in keycloak-http.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out tls.crt -days 500 -sha256
```

## Generate Client certificate

```console
openssl genrsa -out john.doe.key 2048

openssl req -new -sha256 -key john.doe.key -out john.doe.req -subj "/CN=john"

openssl x509 -req -in john.doe.req -CA ca.crt -CAkey ca.key -set_serial 101 -extensions client -days 365 -outform PEM -out john.doe.cer

openssl pkcs12 -export -inkey john.doe.key -in john.doe.cer -out john.doe.p12
```

## Register a secret to be deploy for Wildfly and the Ingress

```
 kubectl create secret generic x509-secret --from-file=ca.crt=ca.crt --from-file=tls.crt=tls.crt --from-file=tls.key=tls.key
```
