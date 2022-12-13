package com.virtru.keycloak;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.keycloak.jose.jwk.JWK;

import java.io.IOException;

@JsonIgnoreProperties(ignoreUnknown = true)
public class DPoPPayload {
  private static final ObjectMapper mapper = new ObjectMapper();

  @JsonProperty("jti")
  protected String identifier;

  @JsonProperty("htm")
  protected String httpMethod;

  @JsonProperty("htu")
  protected String httpUri;

  @JsonProperty("iat")
  protected Long issuedAt;

  @JsonProperty("ath")
  protected String accessTokenHash;

  protected String nonce;

  static {
    mapper.setSerializationInclusion(JsonInclude.Include.NON_NULL);
  }

  public String toString() {
    try {
      return mapper.writeValueAsString(this);
    } catch (IOException e) {
      throw new RuntimeException(e);
    }
  }

  public String getAccessTokenHash() {
    return accessTokenHash;
  }

  public String getHttpMethod() {
    return httpMethod;
  }

  public String getHttpUri() {
    return httpUri;
  }
  public String getIdentifier() {
    return identifier;
  }
  public Long getIssuedAt() {
    return issuedAt;
  }
  public String getNonce() {
    return nonce;
  }

  public void setAccessTokenHash(String accessTokenHash) {
    this.accessTokenHash = accessTokenHash;
  }

  public void setHttpMethod(String httpMethod) {
    this.httpMethod = httpMethod;
  }

  public void setHttpUri(String httpUri) {
    this.httpUri = httpUri;
  }

  public void setIdentifier(String identifier) {
    this.identifier = identifier;
  }

  public void setIssuedAt(Long issuedAt) {
    this.issuedAt = issuedAt;
  }

  public void setNonce(String nonce) {
    this.nonce = nonce;
  }
}
