#!/bin/bash
export PASSPHRASE=123456
CERTS_DIR="certs"
mkdir -p $CERTS_DIR

if kubectl get secret x509-secret; then
  echo "X509 secret already exists"
else
#Generate CA and Server Certificates

  openssl genrsa -aes256 -out $CERTS_DIR/rootca_kc.key -passout env:PASSPHRASE 2048

  openssl req -x509 -new -nodes -key $CERTS_DIR/rootca_kc.key -sha256 -days 1024 -out $CERTS_DIR/rootca_kc.crt -subj "/C=US/ST=Home/L=Home/O=mycorp/OU=myorg/CN=caroot.keycloak-http" -passin env:PASSPHRASE

  openssl genrsa -out  $CERTS_DIR/tls.key 2048

  openssl req -new -key  $CERTS_DIR/tls.key -out  $CERTS_DIR/keycloak-http.csr -subj "/C=UA/ST=Home/L=Home/O=mycorp/OU=myorg/CN=keycloak-http"

  openssl x509 -req -extfile <(printf "subjectAltName=DNS:keycloak-http") -in $CERTS_DIR/keycloak-http.csr -CA $CERTS_DIR/rootca_kc.crt -CAkey $CERTS_DIR/rootca_kc.key -CAcreateserial -out $CERTS_DIR/tls.crt -days 500 -sha256 -passin env:PASSPHRASE


#Generate Client certificate

  openssl genrsa -out $CERTS_DIR/john.doe.key 2048

  openssl req -new -sha256 -key $CERTS_DIR/john.doe.key -out $CERTS_DIR/john.doe.req -subj "/CN=john"

  openssl x509 -req -sha256 -in $CERTS_DIR/john.doe.req -CA $CERTS_DIR/rootca_kc.crt -CAkey $CERTS_DIR/rootca_kc.key -extensions client -days 365 -outform PEM -out $CERTS_DIR/john.doe.cer -passin env:PASSPHRASE


# Create Kubernetes Secret for Keycloak

  kubectl create secret generic x509-secret --from-file=ca.crt=$CERTS_DIR/rootca_kc.crt --from-file=tls.crt=$CERTS_DIR/tls.crt --from-file=tls.key=$CERTS_DIR/tls.key
fi
