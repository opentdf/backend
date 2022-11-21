package com.virtru.keycloak;

import com.fasterxml.jackson.databind.node.JsonNodeCreator;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.ValueNode;
import com.google.common.base.Strings;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.http.client.methods.CloseableHttpResponse;
import org.apache.http.client.methods.HttpPost;
import org.apache.http.client.utils.URIBuilder;
import org.apache.http.entity.StringEntity;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.impl.client.HttpClientBuilder;
import org.apache.http.util.EntityUtils;
import org.jboss.resteasy.plugins.providers.RegisterBuiltin;
import org.jboss.resteasy.plugins.providers.jackson.ResteasyJackson2Provider;

import com.fasterxml.jackson.core.JsonProcessingException;
import org.jboss.resteasy.spi.ResteasyProviderFactory;
import org.keycloak.common.util.Base64Url;
import org.keycloak.jose.JOSEParser;
import org.keycloak.jose.jwk.JWK;
import org.keycloak.jose.jwk.JWKUtil;
import org.keycloak.jose.jws.JWSInput;
import org.keycloak.models.*;
import org.keycloak.protocol.oidc.mappers.*;
import org.keycloak.provider.ProviderConfigProperty;
import org.keycloak.representations.IDToken;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.*;
import java.util.stream.Collectors;

import javax.ws.rs.BadRequestException;
import javax.ws.rs.NotAuthorizedException;
import javax.ws.rs.core.HttpHeaders;

import java.util.Map;

/**
 * Validates the DPoP on an auth request and sets the `cnf` value to the JWK
 * thumbprint value of the DPoP key.
 */
public class DPoPConfirmationMapper extends AbstractOIDCProtocolMapper
        implements OIDCAccessTokenMapper, OIDCIDTokenMapper, UserInfoTokenMapper {
    private static final Logger logger = LoggerFactory.getLogger(DPoPConfirmationMapper.class);

    public static final String PROVIDER_ID = "dpop-cnf-mapper";

    private static final List<ProviderConfigProperty> configProperties = new ArrayList<ProviderConfigProperty>();

    final static String DPOP_HEADER = "client.dpop";

    static {
        OIDCAttributeMapperHelper.addIncludeInTokensConfig(configProperties, DPoPConfirmationMapper.class);
        OIDCAttributeMapperHelper.addTokenClaimNameConfig(configProperties);
        configProperties.get(configProperties.size() - 1).setDefaultValue("cnf");

        configProperties.add(new ProviderConfigProperty(DPOP_HEADER, "DPoP Header Name",
                "Header containing `DPoP`",
                ProviderConfigProperty.STRING_TYPE, "DPoP"));
    }

    static Optional<DPoP.Proof> getProofHeader(HttpHeaders headers) {
        List<String> dpopValues = new ArrayList<>(new HashSet<>(headers.getRequestHeader("dpop")));
        if (dpopValues.isEmpty()) {
            return Optional.empty();
        }
        if (dpopValues.size() > 1) {
            throw new BadRequestException("Conflicting dpop headers");
        }
        return Optional.of(DPoP.validate(dpopValues.get(0)));
    }

    @Override
    public List<ProviderConfigProperty> getConfigProperties() {
        return configProperties;
    }

    @Override
    public String getDisplayCategory() {
        return TOKEN_MAPPER_CATEGORY;
    }

    @Override
    public String getDisplayType() {
        return "DPoP Confirmation Claim (cnf) Mapper";
    }

    @Override
    public String getId() {
        return PROVIDER_ID;
    }

    @Override
    public String getHelpText() {
        return "Generates a DPoP Binding claim, cnf.jkt, to indicate requiring proofs of possession with this access token";
    }

    @Override
    protected void setClaim(IDToken token, ProtocolMapperModel mappingModel, UserSessionModel userSession,
            KeycloakSession keycloakSession,
            ClientSessionContext clientSessionCtx) {
        logger.info("DPoP confirmation mapper triggered");
        Optional<DPoP.Proof> dpop = DPoPConfirmationMapper.getProofHeader(keycloakSession.getContext().getRequestHeaders());

        // If no PK in request, don't bother asking for claims - no authorization.
        if (dpop.isEmpty()) {
            logger.info("No public key in auth request, skipping remote auth call and returning empty claims");
            return;
        }

        JsonNode cnf = DPoP.confirmation(dpop.get().getHeader().getJwk());
        logger.debug("Registering dpop cnf jkt [{}] for dpop with jti [{}]", cnf.get("jkt"), dpop.get().getPayload().getIdentifier());
        OIDCAttributeMapperHelper.mapClaim(token, mappingModel, cnf);
    }
}
