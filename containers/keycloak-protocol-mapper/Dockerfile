# NOTE - This base image is used here, but it should also really be used in other places such as the e2e test
# NOTE - The version is also needed in the site-packages COPY command below and should be x.x not x.x.x
ARG MAVEN_VERSION=3.8.2
ARG JDK_VERSION=11
ARG KEYCLOAK_BASE_VERSION=18.0.2
ARG CONTAINER_REGISTRY=ghcr.io
ARG KEYCLOAK_BASE_IMAGE=${CONTAINER_REGISTRY}/opentdf/keycloak-multiarch-base
    #to `ghcr.io/opentdf` but that is not publicly accessible yet.

FROM maven:${MAVEN_VERSION}-jdk-${JDK_VERSION} as claimsmapperbuild

COPY custom-mapper /usr/src/custom-mapper
RUN mvn -f  /usr/src/custom-mapper/pom.xml clean package

COPY blockchain-connector /usr/src/blockchain-connector
RUN mvn -f  /usr/src/blockchain-connector/pom.xml clean install

COPY custom-extension /usr/src/custom-extension
RUN mvn -f  /usr/src/custom-extension/pom.xml clean package

FROM ghcr.io/opentdf/keycloak-multiarch-base:sha-90096f5 as production

# Pack this Java mapper binary into the Keycloak container
COPY --from=claimsmapperbuild /usr/src/custom-mapper/target/*.jar /opt/jboss/keycloak/standalone/deployments/
COPY --from=claimsmapperbuild /usr/src/blockchain-connector/target/*.jar /opt/jboss/keycloak/standalone/deployments/
COPY --from=claimsmapperbuild /usr/src/custom-extension/target/*.jar /opt/jboss/keycloak/standalone/deployments/
