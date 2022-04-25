package com.virtru.keycloak;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.jboss.resteasy.plugins.server.undertow.UndertowJaxrsServer;
import org.jboss.resteasy.test.TestPortProvider;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.DisabledIfEnvironmentVariable;
import org.junit.jupiter.api.condition.EnabledIf;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import org.junit.jupiter.api.condition.EnabledIfSystemProperty;
import org.junit.jupiter.api.extension.ExtendWith;
import org.keycloak.models.*;
import org.keycloak.models.session.PersistentAuthenticatedClientSessionAdapter;
import org.keycloak.models.session.PersistentClientSessionModel;
import org.keycloak.protocol.oidc.mappers.OIDCAttributeMapperHelper;
import org.keycloak.representations.AccessToken;
import org.keycloak.storage.openshift.OpenshiftSAClientAdapter;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import javax.ws.rs.*;
import javax.ws.rs.core.Application;
import javax.ws.rs.core.HttpHeaders;
import javax.ws.rs.core.MediaType;
import java.util.*;

import static com.virtru.keycloak.AttributeOIDCProtocolMapper.*;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.when;

@ExtendWith({MockitoExtension.class})
public class AttributeOIDCProtocolMapperTest {
    private UndertowJaxrsServer server;

    @Mock
    KeycloakSession keycloakSession;
    @Mock
    UserSessionModel userSessionModel;
    @Mock
    PersistentClientSessionModel persistentClientSessionModel;
    @Mock
    RealmModel realmModel;
    @Mock
    ClientSessionContext clientSessionContext;
    @Mock
    ProtocolMapperModel protocolMapperModel;
    @Mock
    KeycloakContext keycloakContext;
    @Mock
    HttpHeaders httpHeaders;
    @Mock
    ClientModel clientModel;
    @Mock
    UserModel userModel;

    AttributeOIDCProtocolMapper attributeOIDCProtocolMapper;

    @EnabledIfSystemProperty(named = "attributemapperTestMode", matches = "config")
    @Test
    public void testTransformAccessToken_NoPKHeader() throws Exception {
        commonSetup(null, true, false, false);
        AccessToken accessToken = new AccessToken();
        attributeOIDCProtocolMapper.transformAccessToken(accessToken, protocolMapperModel,
                keycloakSession, userSessionModel, clientSessionContext);
        Object customClaims = accessToken.getOtherClaims().get("customAttrs");
        assertNull(customClaims, "No custom claims present as a result of no client public key header");
    }

    @EnabledIfSystemProperty(named = "attributemapperTestMode", matches = "env")
    @Test
    public void testTransformAccessToken_WithPKHeader_EnvVar() throws Exception {
        commonSetup("12345", false, false, false);
        Assertions.assertThrows(JsonRemoteClaimException.class, () ->
                assertTransformAccessToken_WithPKHeader(), " Error when accessing remote claim - Configured URL: "
                + System.getenv("CLAIMS_URL"));
    }

    @EnabledIfSystemProperty(named = "attributemapperTestMode", matches = "env")
    @Test
    public void testTransformAccessToken_WithPKHeader_EnvVar_ConfigOverride() throws Exception {
        commonSetup("12345", true, false, false);
        assertTransformAccessToken_WithPKHeader();
    }

    @EnabledIfSystemProperty(named = "attributemapperTestMode", matches = "config")
    @Test
    public void testTransformAccessToken_WithPKHeader_EnvVar_DirectGrantSvcAcct() throws Exception {
        commonSetup("12345", true, false, true);
        assertTransformAccessToken_WithPKHeader_DirectGrantSvcAccount();
    }

    @EnabledIfSystemProperty(named = "attributemapperTestMode", matches = "config")
    @Test
    public void testTransformAccessToken_WithPKHeader_ConfigVar() throws Exception {
        commonSetup("12345", true, false, false);
        assertTransformAccessToken_WithPKHeader();
    }

    @EnabledIfSystemProperty(named = "attributemapperTestMode", matches = "config")
    @Test
    public void testTransformUserInfo_WithPKHeader_ConfigVar() throws Exception {
        commonSetup("12345", true, true, false);
        assertTransformUserInfo_WithPKHeader();
    }

    private void assertTransformAccessToken_WithPKHeader() throws Exception {
        AccessToken accessToken = new AccessToken();
        attributeOIDCProtocolMapper.transformAccessToken(accessToken, protocolMapperModel,
                keycloakSession, userSessionModel, clientSessionContext);
        Object customClaims = accessToken.getOtherClaims().get("customAttrs");
        assertNotNull(customClaims, "Custom claim present");
        //claim is an object node. keycloak jackson serialization happens upstream so we have the object node
        assertTrue(customClaims instanceof ObjectNode);
        ObjectNode objectNode = (ObjectNode) customClaims;
        Map responseClaimAsMap = new ObjectMapper().readValue(objectNode.toPrettyString(), Map.class);
        Map echoedClaimValue = (Map) responseClaimAsMap.get("echo");
        assertEquals(5, echoedClaimValue.keySet().size(), "5 entries");
        assertEquals("12345", echoedClaimValue.get("clientPublicSigningKey"));
        assertEquals("1234-4567-8901", echoedClaimValue.get("primaryEntityId"));
    }

    //If user ID is a service account, that means we are doing direct-grant auth against a client (not a user+client),
    //and we only want entitlements for the client, not the internal service account user Keycloak attaches
    //to the client session. So we should make the client ID the primary entity ID, and remove the clientID from the
    //secondary clientId list
    private void assertTransformAccessToken_WithPKHeader_DirectGrantSvcAccount() throws Exception {
        AccessToken accessToken = new AccessToken();
        attributeOIDCProtocolMapper.transformAccessToken(accessToken, protocolMapperModel,
                keycloakSession, userSessionModel, clientSessionContext);
        Object customClaims = accessToken.getOtherClaims().get("customAttrs");
        assertNotNull(customClaims, "Custom claim present");
        //claim is an object node. keycloak jackson serialization happens upstream so we have the object node
        assertTrue(customClaims instanceof ObjectNode);
        ObjectNode objectNode = (ObjectNode) customClaims;
        Map responseClaimAsMap = new ObjectMapper().readValue(objectNode.toPrettyString(), Map.class);
        Map echoedClaimValue = (Map) responseClaimAsMap.get("echo");


        assertEquals(5, echoedClaimValue.keySet().size(), "5 entries");
        assertEquals("12345", echoedClaimValue.get("clientPublicSigningKey"));
        assertEquals("1234599998888", echoedClaimValue.get("primaryEntityId"));
        assertEquals(0, ((ArrayList<String>) echoedClaimValue.get("secondaryEntityIds")).size(), "0 entries");
    }

    private void assertTransformUserInfo_WithPKHeader() throws Exception {
        AccessToken accessToken = new AccessToken();
        attributeOIDCProtocolMapper.transformUserInfoToken(accessToken, protocolMapperModel,
                keycloakSession, userSessionModel, clientSessionContext);
        Object customClaims = accessToken.getOtherClaims().get("customAttrs");
        assertNotNull(customClaims, "Custom claim present");
        //claim is an object node. keycloak jackson serialization happens upstream so we have the object node
        assertTrue(customClaims instanceof ObjectNode);
        ObjectNode objectNode = (ObjectNode) customClaims;
        Map responseClaimAsMap = new ObjectMapper().readValue(objectNode.toPrettyString(), Map.class);
        Map echoedClaimValue = (Map) responseClaimAsMap.get("echo");
        assertEquals(5, echoedClaimValue.keySet().size(), "5 entries");
        assertEquals("12345", echoedClaimValue.get("clientPublicSigningKey"));
        assertEquals("1234-4567-8901", echoedClaimValue.get("primaryEntityId"));
    }

    @EnabledIfSystemProperty(named = "attributemapperTestMode", matches = "config")
    @Test
    public void testNoRemoteUrl() {
        commonSetup("12345", false, false, false);
        AccessToken accessToken = new AccessToken();
        Assertions.assertThrows(JsonRemoteClaimException.class, () ->
                attributeOIDCProtocolMapper.transformAccessToken(accessToken, protocolMapperModel,
                        keycloakSession, userSessionModel, clientSessionContext), "");

    }

    void commonSetup(String pkHeader, boolean setConfig, boolean userInfo, boolean userIsSvcAcct) {
        server.deploy(TestApp.class);
        String url = TestPortProvider.generateURL("/base/endpoint");
        String clientId = "1234599998888";

        Map<String, String> config = new HashMap<>();
        if (setConfig) {
            config.put(REMOTE_URL, url);
        }
        config.put(CLAIM_NAME, "customAttrs");
        config.put(PUBLIC_KEY_HEADER, "testPK");
        config.put(REMOTE_PARAMETERS_USERNAME, "true");
        config.put(REMOTE_PARAMETERS_CLIENTID, "true");
        if (userInfo) {
            config.put(OIDCAttributeMapperHelper.INCLUDE_IN_USERINFO, "true");
            config.put(OIDCAttributeMapperHelper.INCLUDE_IN_ACCESS_TOKEN, "false");
            config.put(OIDCAttributeMapperHelper.INCLUDE_IN_ID_TOKEN, "false");
        } else {
            config.put(OIDCAttributeMapperHelper.INCLUDE_IN_USERINFO, "false");
            config.put(OIDCAttributeMapperHelper.INCLUDE_IN_ACCESS_TOKEN, "true");
            config.put(OIDCAttributeMapperHelper.INCLUDE_IN_ID_TOKEN, "true");
        }
        when(protocolMapperModel.getConfig()).thenReturn(config);

        when(keycloakSession.getContext()).thenReturn(keycloakContext);
        when(keycloakContext.getRequestHeaders()).thenReturn(httpHeaders);

        when(userModel.getId()).thenReturn("1234-4567-8901");
        if (userIsSvcAcct) {
            // For ref, see: https://github.com/keycloak/keycloak/blob/99c06d11023689875b48ef56442c90bdb744c869/services/src/main/java/org/keycloak/exportimport/util/ExportUtils.java#L519
            when(userModel.getServiceAccountClientLink()).thenReturn(clientId);
        }
        when(userSessionModel.getUser()).thenReturn(userModel);

        if (pkHeader != null) {
            List<String> pkHeaders = pkHeader == null ? Collections.emptyList() : Collections.singletonList(pkHeader);
            when(httpHeaders.getRequestHeader("testPK")).thenReturn(pkHeaders);

            when(clientSessionContext.getAttribute("remote-authorizations", JsonNode.class)).thenReturn(null);
//            when(clientSessionContext.getScopeString()).thenReturn("email");
            when(clientModel.getId()).thenReturn(clientId);
            AuthenticatedClientSessionModel authenticatedClientSessionModel =  new PersistentAuthenticatedClientSessionAdapter(keycloakSession, persistentClientSessionModel, realmModel, clientModel, userSessionModel);
            Map<String, AuthenticatedClientSessionModel> clients = new HashMap<String, AuthenticatedClientSessionModel>();
            clients.put("x", authenticatedClientSessionModel);
            clients.put("y", authenticatedClientSessionModel);

            when(userSessionModel.getAuthenticatedClientSessions()).thenReturn(clients);
        }
    }


    @BeforeEach
    public void setup() throws Exception {
        server = new UndertowJaxrsServer().start();
        attributeOIDCProtocolMapper = new AttributeOIDCProtocolMapper();
    }

    @AfterEach
    public void stop() {
        server.stop();
    }


    @Path("/endpoint")
    public static class MyResource {

        @POST
        @Produces(MediaType.APPLICATION_JSON)
        @Consumes(MediaType.APPLICATION_JSON)
        public Map createMyModel(Map payload) {
            Map response = new HashMap<>();
            response.put("echo", payload);
            return response;
        }

    }


    @ApplicationPath("/base")
    public static class TestApp extends Application {
        @Override
        public Set<Class<?>> getClasses() {
            Set<Class<?>> classes = new HashSet<Class<?>>();
            classes.add(MyResource.class);
            return classes;
        }
    }
}
