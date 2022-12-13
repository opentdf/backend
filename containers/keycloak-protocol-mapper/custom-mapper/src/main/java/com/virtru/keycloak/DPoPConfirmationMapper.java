package com.virtru.keycloak;

import com.fasterxml.jackson.databind.JsonNode;

import org.keycloak.models.*;
import org.keycloak.protocol.oidc.mappers.*;
import org.keycloak.provider.ProviderConfigProperty;
import org.keycloak.representations.AccessToken;
import org.keycloak.representations.AccessTokenResponse;
import org.keycloak.representations.IDToken;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.*;

import javax.ws.rs.BadRequestException;
import javax.ws.rs.core.HttpHeaders;

/**
 * Validates the DPoP on an auth request and sets the `cnf` value to the JWK
 * thumbprint value of the DPoP key.
 */
public class DPoPConfirmationMapper extends AbstractOIDCProtocolMapper
        implements OIDCAccessTokenMapper, OIDCIDTokenMapper, UserInfoTokenMapper {
    private static final Logger logger = LoggerFactory.getLogger(DPoPConfirmationMapper.class);
    static {
        logger.info("Registered DPoPConfirmationMapper");
    }

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
            logger.info("No DPoP Header");
            return Optional.empty();
        }
        if (dpopValues.size() > 1) {
            throw new BadRequestException("Conflicting dpop headers");
        }
        try {
            return Optional.of(DPoP.validate(dpopValues.get(0)));
        } catch (RuntimeException ex) {
            logger.error("failure", ex);
            throw ex;
        }
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
        logger.info("DPoP confirmation IDToken mapper triggered");
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

    @Override
    protected void setClaim(AccessTokenResponse accessTokenResponse, ProtocolMapperModel mappingModel, UserSessionModel userSession, KeycloakSession keycloakSession,
                            ClientSessionContext clientSessionCtx) {
        logger.info("DPoP confirmation AccessToken mapper triggered");
        Optional<DPoP.Proof> dpop = DPoPConfirmationMapper.getProofHeader(keycloakSession.getContext().getRequestHeaders());

        // If no PK in request, don't bother asking for claims - no authorization.
        if (dpop.isEmpty()) {
            logger.info("No public key in auth request, skipping remote auth call and returning empty claims");
            return;
        }

        JsonNode cnf = DPoP.confirmation(dpop.get().getHeader().getJwk());
        logger.debug("Registering dpop cnf jkt [{}] for dpop with jti [{}]", cnf.get("jkt"), dpop.get().getPayload().getIdentifier());
        OIDCAttributeMapperHelper.mapClaim(accessTokenResponse, mappingModel, cnf);
    }




    @Override
    public AccessToken transformUserInfoToken(AccessToken token, ProtocolMapperModel mappingModel, KeycloakSession session,
                                              UserSessionModel userSession, ClientSessionContext clientSessionCtx) {
        logger.info("transformUserInfoToken [{}]", token);
        return super.transformUserInfoToken(token, mappingModel, session, userSession, clientSessionCtx);
    }

    @Override
    public AccessToken transformAccessToken(AccessToken token, ProtocolMapperModel mappingModel, KeycloakSession session,
                                            UserSessionModel userSession, ClientSessionContext clientSessionCtx) {
        logger.info("transformAccessToken [{}] [{}]", token, mappingModel.getConfig());
        return super.transformAccessToken(token, mappingModel, session, userSession, clientSessionCtx);
    }

    @Override
    public IDToken transformIDToken(IDToken token, ProtocolMapperModel mappingModel, KeycloakSession session,
                                    UserSessionModel userSession, ClientSessionContext clientSessionCtx) {
        logger.info("transformIDToken [{}]", token);
        return super.transformIDToken(token, mappingModel, session, userSession, clientSessionCtx);
    }

    @Override
    public AccessTokenResponse transformAccessTokenResponse(AccessTokenResponse accessTokenResponse, ProtocolMapperModel mappingModel,
                                                            KeycloakSession session, UserSessionModel userSession,
                                                            ClientSessionContext clientSessionCtx) {
        logger.info("transformAccessTokenResponse [{}]", accessTokenResponse);
        return super.transformAccessTokenResponse(accessTokenResponse, mappingModel, session, userSession, clientSessionCtx);
    }

}
