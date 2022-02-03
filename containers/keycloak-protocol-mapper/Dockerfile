# NOTE - This base image is used here, but it should also really be used in other places such as the e2e test
# NOTE - The version is also needed in the site-packages COPY command below and should be x.x not x.x.x
ARG MAVEN_VERSION=3.8.2
ARG JDK_VERSION=11
ARG KEYCLOAK_VERSION=15.0.2-debian-10-r66

FROM maven:${MAVEN_VERSION}-openjdk-${JDK_VERSION} as build

COPY custom-mapper /usr/src/custom-mapper
RUN mvn -f /usr/src/custom-mapper/pom.xml -U clean package

FROM bitnami/keycloak:${KEYCLOAK_VERSION}

COPY --from=build /usr/src/custom-mapper/target/*.jar /opt/bitnami/keycloak/standalone/deployments/
# Any overrides for the bitnami Keycloak setup/customization scripts (https://github.com/bitnami/bitnami-docker-keycloak/tree/master/15/debian-10/rootfs/opt/bitnami/scripts)
# can go here - note that we DO use at least one script override, as the default Bitnami setup scripts
# either let you supply a complete Keycloak config and ignore all chart config options OR supply no config
# and rely on (currently insufficient for our purposes, no SPI config etc) chart options -
# we want a combination, so an override is required.
COPY bitnami-overrides/opt/bitnami/scripts /opt/bitnami/scripts
ENV KEYCLOAK_EXTRA_ARGS="-Dkeycloak.profile=preview -Dkeycloak.profile.feature.token_exchange=enabled"
