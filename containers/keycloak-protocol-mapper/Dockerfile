# NOTE - This base image is used here, but it should also really be used in other places such as the e2e test
# NOTE - The version is also needed in the site-packages COPY command below and should be x.x not x.x.x
ARG MAVEN_VERSION=3.8.2
ARG JDK_VERSION=17
# get value from ./VERSION
ARG KEYCLOAK_BASE_VERSION=24.0.1
ARG KEYCLOAK_BASE_IMAGE=quay.io/keycloak/keycloak

FROM maven:${MAVEN_VERSION}-openjdk-${JDK_VERSION} as claimsmapperbuild

COPY custom-mapper /usr/src/custom-mapper
COPY x509-envoy /usr/src/x509-envoy
COPY pom.xml /usr/src/pom.xml

RUN mvn -f  /usr/src/pom.xml clean --no-transfer-progress package

FROM ${KEYCLOAK_BASE_IMAGE}:${KEYCLOAK_BASE_VERSION}

# Pack this Java mapper binary into the Keycloak container
COPY --from=claimsmapperbuild /usr/src/custom-mapper/target/*.jar /opt/keycloak/providers/
# Add Envoy X509 SPI
COPY --from=claimsmapperbuild /usr/src/x509-envoy/target/*.jar /opt/keycloak/providers/
