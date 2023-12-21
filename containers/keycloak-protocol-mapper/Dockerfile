# NOTE - This base image is used here, but it should also really be used in other places such as the e2e test
# NOTE - The version is also needed in the site-packages COPY command below and should be x.x not x.x.x
ARG MAVEN_VERSION=3.8.5
ARG JDK_VERSION=17
# get value from ./VERSION
ARG KEYCLOAK_BASE_VERSION
ARG KEYCLOAK_BASE_IMAGE=quay.io/keycloak/keycloak

FROM maven:${MAVEN_VERSION}-jdk-${JDK_VERSION} as claimsmapperbuild

COPY custom-mapper /usr/src/custom-mapper
RUN mvn -f  /usr/src/custom-mapper/pom.xml clean package

FROM gradle:7-jdk${JDK_VERSION} as envoyBuild

RUN mkdir /dist

COPY x509-envoy /x509-envoy

WORKDIR /x509-envoy

# This GRADLE_OPTS is apparently necessary with ARM64 crossbuilds - gradle/JDK bug
# https://github.com/keeganwitt/docker-gradle/issues/196
ENV GRADLE_OPTS="-Dorg.gradle.daemon=false -Djdk.lang.Process.launchMechanism=vfork"
RUN gradle --debug shadowJar && cp build/libs/keycloak-x509-envoy-all.jar /dist


FROM ${KEYCLOAK_BASE_IMAGE}:${KEYCLOAK_BASE_VERSION}

# Pack this Java mapper binary into the Keycloak container
COPY --from=claimsmapperbuild /usr/src/custom-mapper/target/*.jar /opt/keycloak/providers/
# Add Envoy X509 SPI
COPY --from=envoyBuild /dist/keycloak-x509-envoy-all.jar /opt/keycloak/providers/
