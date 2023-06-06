# KeycloakCustomProtocolMapper

(Original code: https://github.com/pavithB/KeycloakCustomProtocolMapper)

implement a CustomProtocolMapper class based on AbstractOIDCProtocolMapper

META-INF/services File with the name org.keycloak.protocol.ProtocolMapper must be available and contains the name of mapper

jboss-deployment-structure.xml need to be available to use keycloak built in classes

Jar File is deployed in /opt/jboss/keycloak/standalone/deployments/

custom Mapper
use POM.xml and resolve dependencies
Extend AbstractOIDCProtocolMapper and need to implement all abstract methods. If want to have a SAML Protocol Mapper then it's another base class (AbstractSAMLProtocolMapper)
one relevant method is transformAccessToken -can implement logic here.

Services File
The services File is important for keycloak to find the custom-Implementation.
Place a file with the fileName org.keycloak.protocol.ProtocolMapper inside \src\main\resources\META-INF\services\

Inside this file write to Name of your custom Provider - then keycloak knows that this class is available as Protocol Mapper
can add multiple file names

com.virtru.keycloak.TdfClaimsMapper

Deployment Structure XML
In custom mapper use files from keycloak. In order to use them it's needed to inform jboss about this dependency. Therefore create a file jboss-deployment-structure.xml inside \src\main\resources\META-INF\ Content:

Build and deploy your Extension
Build a jar File of the Extension (mvn clean package) - and place the jar in /opt/jboss/keycloak/standalone/deployments/ and restart keycloak

create a Mapper in keycloak admin ui and select getDisplayType given in the code

## Test

Device Authorization Grant

see https://github.com/keycloak/keycloak-community/blob/main/design/oauth2-device-authorization-grant.md#how-to-try-it

```shell
curl -X POST \
    -d "client_id=foo" \
    "http://localhost:65432/auth/realms/tdf/protocol/openid-connect/auth/device"
```