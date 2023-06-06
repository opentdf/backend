package com.virtru.keycloak;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Stream;
import javax.ws.rs.ApplicationPath;
import javax.ws.rs.Consumes;
import javax.ws.rs.POST;
import javax.ws.rs.Path;
import javax.ws.rs.Produces;
import javax.ws.rs.core.Application;
import javax.ws.rs.core.HttpHeaders;
import javax.ws.rs.core.MediaType;
import org.jboss.resteasy.plugins.server.undertow.UndertowJaxrsServer;
import org.jboss.resteasy.test.TestPortProvider;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfSystemProperty;
import org.junit.jupiter.api.extension.ExtendWith;
import org.keycloak.common.enums.SslRequired;
import org.keycloak.component.ComponentModel;
import org.keycloak.models.AuthenticatedClientSessionModel;
import org.keycloak.models.AuthenticationExecutionModel;
import org.keycloak.models.AuthenticationFlowModel;
import org.keycloak.models.AuthenticatorConfigModel;
import org.keycloak.models.CibaConfig;
import org.keycloak.models.ClientInitialAccessModel;
import org.keycloak.models.ClientModel;
import org.keycloak.models.ClientScopeModel;
import org.keycloak.models.ClientSessionContext;
import org.keycloak.models.GroupModel;
import org.keycloak.models.IdentityProviderMapperModel;
import org.keycloak.models.IdentityProviderModel;
import org.keycloak.models.KeycloakContext;
import org.keycloak.models.KeycloakSession;
import org.keycloak.models.OAuth2DeviceConfig;
import org.keycloak.models.OTPPolicy;
import org.keycloak.models.ParConfig;
import org.keycloak.models.PasswordPolicy;
import org.keycloak.models.ProtocolMapperModel;
import org.keycloak.models.RealmModel;
import org.keycloak.models.RequiredActionProviderModel;
import org.keycloak.models.RequiredCredentialModel;
import org.keycloak.models.RoleModel;
import org.keycloak.models.UserModel;
import org.keycloak.models.UserSessionModel;
import org.keycloak.models.WebAuthnPolicy;
import org.keycloak.models.session.PersistentAuthenticatedClientSessionAdapter;
import org.keycloak.models.session.PersistentClientSessionModel;
import org.keycloak.protocol.oidc.mappers.OIDCAttributeMapperHelper;
import org.keycloak.representations.AccessToken;
import org.keycloak.storage.adapter.InMemoryUserAdapter;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mockito.junit.jupiter.MockitoSettings;
import org.mockito.quality.Strictness;

import static com.virtru.keycloak.TdfClaimsMapper.CLAIM_NAME;
import static com.virtru.keycloak.TdfClaimsMapper.DPOP_ENABLED;
import static com.virtru.keycloak.TdfClaimsMapper.PUBLIC_KEY_HEADER;
import static com.virtru.keycloak.TdfClaimsMapper.REMOTE_PARAMETERS_CLIENTID;
import static com.virtru.keycloak.TdfClaimsMapper.REMOTE_PARAMETERS_USERNAME;
import static com.virtru.keycloak.TdfClaimsMapper.REMOTE_URL;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.Mockito.when;

@ExtendWith({ MockitoExtension.class })
@MockitoSettings(strictness = Strictness.LENIENT)
public class TdfClaimsMapperTest {
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

    TdfClaimsMapper attributeOIDCProtocolMapper;

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
        Assertions.assertThrows(JsonRemoteClaimException.class, () -> assertTransformAccessToken_WithPKHeader(),
                " Error when accessing remote claim - Configured URL: "
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
        // claim is an object node. keycloak jackson serialization happens upstream so
        // we have the object node
        assertTrue(customClaims instanceof ObjectNode);
        ObjectNode objectNode = (ObjectNode) customClaims;
        Map responseClaimAsMap = new ObjectMapper().readValue(objectNode.toPrettyString(), Map.class);
        assertNotNull(responseClaimAsMap, "Echoed claim present");
        assertEquals(2, responseClaimAsMap.keySet().size(), "2 entries");
        assertEquals("12345", responseClaimAsMap.get("client_public_signing_key"));
        ArrayList entitlements = (ArrayList) responseClaimAsMap.get("entitlements");
        Map ent = (Map) entitlements.get(0);
        assertEquals("1234-4567-8901", ent.get("primary_entity_id"));
    }

    // If user ID is a service account, that means we are doing direct-grant auth
    // against a client (not a user+client),
    // and we only want entitlements for the client, not the internal service
    // account user Keycloak attaches
    // to the client session. So we should make the client ID the primary entity ID,
    // and remove the clientID from the
    // secondary clientId list
    private void assertTransformAccessToken_WithPKHeader_DirectGrantSvcAccount() throws Exception {
        AccessToken accessToken = new AccessToken();
        attributeOIDCProtocolMapper.transformAccessToken(accessToken, protocolMapperModel,
                keycloakSession, userSessionModel, clientSessionContext);
        Object customClaims = accessToken.getOtherClaims().get("customAttrs");
        assertNotNull(customClaims, "Custom claim present");
        // claim is an object node. keycloak jackson serialization happens upstream so
        // we have the object node
        assertTrue(customClaims instanceof ObjectNode);
        ObjectNode objectNode = (ObjectNode) customClaims;
        Map responseClaimAsMap = new ObjectMapper().readValue(objectNode.toPrettyString(), Map.class);
        assertNotNull(responseClaimAsMap, "Echoed claim present");
        assertEquals(2, responseClaimAsMap.keySet().size(), "2 entries");
        assertEquals("12345", responseClaimAsMap.get("client_public_signing_key"));
        ArrayList entitlements = (ArrayList) responseClaimAsMap.get("entitlements");
        Map ent = (Map) entitlements.get(0);
        assertEquals("1234599998888", ent.get("primary_entity_id"));
        assertEquals(0, ((List) ent.get("secondary_entity_ids")).size(), "0 entries");
    }

    private void assertTransformUserInfo_WithPKHeader() throws Exception {
        AccessToken accessToken = new AccessToken();
        attributeOIDCProtocolMapper.transformUserInfoToken(accessToken, protocolMapperModel,
                keycloakSession, userSessionModel, clientSessionContext);
        Object customClaims = accessToken.getOtherClaims().get("customAttrs");
        assertNotNull(customClaims, "Custom claim present");
        // claim is an object node. keycloak jackson serialization happens upstream so
        // we have the object node
        assertTrue(customClaims instanceof ObjectNode);
        ObjectNode objectNode = (ObjectNode) customClaims;
        Map responseClaimAsMap = new ObjectMapper().readValue(objectNode.toPrettyString(), Map.class);
        assertNotNull(responseClaimAsMap, "Echoed claim present");
        assertEquals(2, responseClaimAsMap.keySet().size(), "2 entries");
        assertEquals("12345", responseClaimAsMap.get("client_public_signing_key"));
        ArrayList entitlements = (ArrayList) responseClaimAsMap.get("entitlements");
        Map ent = (Map) entitlements.get(0);
        assertEquals("1234-4567-8901", ent.get("primary_entity_id"));
    }

    @EnabledIfSystemProperty(named = "attributemapperTestMode", matches = "config")
    @Test
    public void testNoRemoteUrl() {
        commonSetup("12345", false, false, false);
        AccessToken accessToken = new AccessToken();
        Assertions.assertThrows(JsonRemoteClaimException.class,
                () -> attributeOIDCProtocolMapper.transformAccessToken(accessToken, protocolMapperModel,
                        keycloakSession, userSessionModel, clientSessionContext),
                "");

    }

//    @EnabledIfSystemProperty(named = "attributemapperTestMode", matches = "config")
//    @Test
//    public void testDeviceGrant() throws JsonProcessingException {
//        commonSetup("12345", true, true, false);
//        Map<String, String> notes = new HashMap<>(1);
//        notes.put("KC_DEVICE_NOTE", "eyJpcEFkZHJlc3MiOiIxNzIuMjQuMC4xIiwib3MiOiJXaW5kb3dzIiwib3NWZXJzaW9uIjoiMTAiLCJicm93c2VyIjoiQ2hyb21lLzExMS4wLjAiLCJkZXZpY2UiOiJPdGhlciIsImxhc3RBY2Nlc3MiOjAsIm1vYmlsZSI6ZmFsc2V9");
//        when(userSessionModel.getNotes()).thenReturn(notes);
//        UserModel user = new InMemoryUserAdapter(keycloakSession, realmModel, "test-user");
//        user.setEmail("test@test.net");
//        when(userSessionModel.getUser()).thenReturn(user);
//        AccessToken accessToken = new AccessToken();
//        Map<String, Object> formattedParameters = attributeOIDCProtocolMapper.getRequestParameters(protocolMapperModel,
//                        userSessionModel, accessToken);
//        assertTrue(formattedParameters.get("entitlement_context_obj").toString().contains("test@test.net"));
//    }

    void commonSetup(String pkHeader, boolean setConfig, boolean userInfo, boolean userIsSvcAcct) {
        server.deployOldStyle(TestApp.class);
        String url = TestPortProvider.generateURL("/base/endpoint");
        String clientId = "1234599998888";

        Map<String, String> config = new HashMap<>();
        if (setConfig) {
            config.put(REMOTE_URL, url);
        }
        config.put(CLAIM_NAME, "customAttrs");
        config.put(DPOP_ENABLED, "true");
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
            // For ref, see:
            // https://github.com/keycloak/keycloak/blob/99c06d11023689875b48ef56442c90bdb744c869/services/src/main/java/org/keycloak/exportimport/util/ExportUtils.java#L519
            when(userModel.getServiceAccountClientLink()).thenReturn(clientId);
        }
        when(userSessionModel.getUser()).thenReturn(userModel);

        if (pkHeader != null) {
            List<String> pkHeaders = pkHeader == null ? Collections.emptyList() : Collections.singletonList(pkHeader);
            when(httpHeaders.getRequestHeader("dpop")).thenReturn(Collections.emptyList());
            when(httpHeaders.getRequestHeader("testPK")).thenReturn(pkHeaders);

            when(clientSessionContext.getAttribute("remote-authorizations", JsonNode.class)).thenReturn(null);
            AuthenticatedClientSessionModel authenticatedClientSessionModel = new PersistentAuthenticatedClientSessionAdapter(
                    keycloakSession, persistentClientSessionModel, realmModel, clientModel, userSessionModel);
            if (userIsSvcAcct) {
                when(clientModel.getId()).thenReturn(clientId);
                Map<String, AuthenticatedClientSessionModel> clients = new HashMap<String, AuthenticatedClientSessionModel>();
                clients.put("x", authenticatedClientSessionModel);
                clients.put("y", authenticatedClientSessionModel);
                when(userSessionModel.getAuthenticatedClientSessions()).thenReturn(clients);
            }
        }
    }

    @BeforeEach
    public void setup() throws Exception {
        server = new UndertowJaxrsServer().start();
        attributeOIDCProtocolMapper = new TdfClaimsMapper();
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
        public Map[] createMyModel(Map payload) {
            Map[] response = { payload };
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
