package com.virtru.keycloak;

import java.io.IOException;
import java.io.StringWriter;
import java.nio.charset.StandardCharsets;
import java.security.InvalidKeyException;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.security.PublicKey;
import java.security.Signature;
import java.security.SignatureException;
import java.util.Base64;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;

import javax.ws.rs.NotAuthorizedException;

import org.bouncycastle.openssl.jcajce.JcaPEMWriter;
import org.keycloak.jose.jwk.ECPublicJWK;
import org.keycloak.jose.jwk.JWK;
import org.keycloak.jose.jwk.JWKParser;
import org.keycloak.jose.jwk.RSAPublicJWK;
import org.keycloak.util.JsonSerialization;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.google.common.base.Strings;

/**
 * Utilities for parsing and validating DPoP headers.
 */
class DPoP {
  private static final ObjectMapper mapper = new ObjectMapper();
  private static final Base64.Decoder B64_DECODER = Base64.getUrlDecoder();
  private static final Base64.Encoder B64_ENCODER = Base64.getUrlEncoder().withoutPadding();

  private static Map<String, String> SIG_JWT_TO_JAVA = Map.of(
      "RS256", "SHA256withRSA",
      "RS384", "SHA384withRSA",
      "RS512", "SHA512withRSA",
      "ES256", "SHA256withECDSA",
      "ES384", "SHA384withECDSA",
      "ES512", "SHA512withECDSA");
  private static Set<String> ALLOWED_DPOP_ALGORITHMS = SIG_JWT_TO_JAVA.keySet();

  static Map<String, String> canonicalMap(JWK jwk) {
    Map<String, String> ans = new LinkedHashMap<>(4);
    if (jwk instanceof ECPublicJWK) {
      ECPublicJWK ec = (ECPublicJWK) jwk;
      ans.put("crv", ec.getCrv());
      ans.put("kty", "EC");
      ans.put("x", ec.getX());
      ans.put("y", ec.getY());
      return ans;
    }
    if (jwk instanceof RSAPublicJWK) {
      RSAPublicJWK rsa = (RSAPublicJWK) jwk;
      ans.put("e", rsa.getPublicExponent());
      ans.put("kty", "RSA");
      ans.put("n", rsa.getModulus());
      return ans;
    }
    switch (jwk.getKeyType()) {
      case "EC":
        ans.put("crv", (String) jwk.getOtherClaims().get("crv"));
        ans.put("kty", "EC");
        ans.put("x", (String) jwk.getOtherClaims().get("x"));
        ans.put("y", (String) jwk.getOtherClaims().get("y"));
        return ans;
      case "RSA":
        ans.put("e", (String) jwk.getOtherClaims().get("e"));
        ans.put("kty", "RSA");
        ans.put("n", (String) jwk.getOtherClaims().get("n"));
        return ans;
    }
    throw new UnsupportedOperationException("Unsupported jwk.kty: " + jwk.getKeyType());
  }

  static String canonicalize(JWK jwk) {
    try {
      return mapper.writeValueAsString(canonicalMap(jwk));
    } catch (JsonProcessingException e) {
      throw new NotAuthorizedException(e, "Unsupported JWK");
    }
  }

  static JsonNode confirmation(JWK jwk) {
    ObjectNode root = mapper.createObjectNode();
    root.put("jkt", cnfThumbprint(jwk));
    return root;
  }

  /**
   * Get the thumbprint from the public key for use in the cnf.jkt field.
   * See https://datatracker.ietf.org/doc/html/draft-ietf-oauth-dpop#section-6.1
   * 
   * @return base64 encoded sha-256 of keyData
   */
  static String cnfThumbprint(JWK keyData) {
    MessageDigest digest;
    try {
      digest = MessageDigest.getInstance("SHA-256");
    } catch (NoSuchAlgorithmException e) {
      // This is a pretty standard algorithm. Let's return a 500
      throw new RuntimeException(e);
    }
    byte[] canonicalData = canonicalize(keyData).getBytes(StandardCharsets.UTF_8);
    byte[] hash = digest.digest(canonicalData);
    return B64_ENCODER.encodeToString(hash);
  }

  static boolean righttAboutNow(long nowishIGuess) {
    long timeOff = System.currentTimeMillis() - nowishIGuess;
    if (-5 * 60 * 1000 < timeOff) {
      // We don't let things in from more than five minutes ago.
      return false;
    }
    // But also not more than 30 seconds from now
    return timeOff < 30 * 1000;
  }

  static String jwkToPem(JWK jwk) {
    PublicKey publicKey = JWKParser.create(jwk).toPublicKey();
    StringWriter sw = new StringWriter();
    try (JcaPEMWriter writer = new JcaPEMWriter(sw)) {
      writer.writeObject(publicKey);
      writer.flush();
    } catch (IOException e) {
      throw new RuntimeException(e);
    }
    return sw.toString();
  }

  static Proof validate(String dpopWireFormat) {
    // The org.keycloak.jose library is very rigid. We need to parse things manually
    // to get extensions to header (JWK, new typ value)
    String[] parts = dpopWireFormat.split("\\.");
    if (parts.length != 3) {
      throw new NotAuthorizedException("Parse failure of dpop [" + dpopWireFormat + "]");
    }
    // Decode things we want to decode to make sure they are valid
    byte[] headerBytes, payloadBytes, signatureBytes;
    try {
      headerBytes = B64_DECODER.decode(parts[0]);
      payloadBytes = B64_DECODER.decode(parts[1]);
      signatureBytes = B64_DECODER.decode(parts[2]);
    } catch (IllegalArgumentException e) {
      throw new NotAuthorizedException(e, "Error in DPoP JWT encoding");
    }
    DPoPHeader header;
    try {
      header = JsonSerialization.readValue(headerBytes, DPoPHeader.class);
    } catch (IOException e) {
      throw new NotAuthorizedException(e);
    }

    // Validate syntax as described in
    // https://datatracker.ietf.org/doc/html/draft-ietf-oauth-dpop#section-4.2
    if (!"dpop+jwt".equals(header.getType())) {
      throw new NotAuthorizedException("DPoP typ invalid");
    }
    if (!ALLOWED_DPOP_ALGORITHMS.contains(header.getAlgorithm())) {
      throw new NotAuthorizedException("DPoP alg invalid");
    }

    PublicKey pk = JWKParser.create(header.getJwk()).toPublicKey();
    // This is deprecated since Keycloak will always want to look up the key
    // by the header's `kid` - the key identifier for Keycloak's signing keypair.
    // However, for DPoP we want to use the *client's* JWK.
    Signature sig;
    try {
      sig = Signature.getInstance(SIG_JWT_TO_JAVA.get(header.getAlgorithm()));
    } catch (NoSuchAlgorithmException e1) {
      throw new RuntimeException("Java Security Library missing verifier of type " + header.getAlgorithm());
    }
    try {
      sig.initVerify(pk);
      byte[] encodedSignatureInput = (parts[0] + '.' + parts[1]).getBytes(StandardCharsets.UTF_8);
      sig.update(encodedSignatureInput);
      sig.verify(signatureBytes);
    } catch (SignatureException e) {
      throw new NotAuthorizedException(e, "Error in DPoP signature verification");
    } catch (InvalidKeyException e) {
      throw new NotAuthorizedException(e, "Error in DPoP JWK / Algorithm initialization");
    }

    DPoPPayload payload;
    try {
      payload = JsonSerialization.readValue(payloadBytes, DPoPPayload.class);
    } catch (IOException e) {
      throw new NotAuthorizedException(e);
    }

    // TODO: JTI reuse check
    if (Strings.isNullOrEmpty(payload.getIdentifier())) {
      throw new NotAuthorizedException("Invalid `jti` claim");
    }
    // TODO what should these be? Can we look them up?
    if (Strings.isNullOrEmpty(payload.getHttpMethod()) || Strings.isNullOrEmpty(payload.getHttpUri())) {
      throw new NotAuthorizedException("Invalid dpop");
    }
    if (payload.getIssuedAt() == null || !righttAboutNow(payload.getIssuedAt())) {
      throw new NotAuthorizedException("Invalid dpop");
    }
    // TODO support DPoP-Nonce flow
    // TODO Fail on `ath` claims, right?
    return new Proof(header, payload);
  }

  public static class Proof {
    private DPoPHeader header;
    private DPoPPayload payload;

    public Proof() {
      super();
    }

    public Proof(DPoPHeader header, DPoPPayload payload) {
      this();
      this.header = header;
      this.payload = payload;
    }

    public DPoPHeader getHeader() {
      return header;
    }

    public void setHeader(DPoPHeader header) {
      this.header = header;
    }

    public DPoPPayload getPayload() {
      return payload;
    }

    public void setPayload(DPoPPayload payload) {
      this.payload = payload;
    }
  }
}
