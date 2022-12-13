package com.virtru.keycloak;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.keycloak.jose.jwk.JWK;

import java.io.IOException;

@JsonIgnoreProperties(ignoreUnknown = true)
public class DPoPHeader {
  private static final ObjectMapper mapper = new ObjectMapper();

  @JsonProperty("alg")
  protected String algorithm;

  @JsonProperty("typ")
  protected String type;

  @JsonProperty("jwk")
  protected JWK jwk;


  public DPoPHeader() {
    this.algorithm = algorithm;
    this.type = "dpop+jwt";
    this.jwk = jwk;
  }

  public DPoPHeader(String algorithm, JWK jwk) {
    this.algorithm = algorithm;
    this.type = "dpop+jwt";
    this.jwk = jwk;
  }

  public String getAlgorithm() {
    return algorithm;
  }

  public void setAlgorithm(String algorithm) {
    this.algorithm = algorithm;
  }

  public String getType() {
    return type;
  }

  public void setType(String type) {
    this.type = type;
  }

  public JWK getJwk() {
    return this.jwk;
  }

  public void setJwk(JWK jwk) {
    this.jwk = jwk;
  }

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
}
