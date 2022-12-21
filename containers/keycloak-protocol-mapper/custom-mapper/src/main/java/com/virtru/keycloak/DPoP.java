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

import javax.ws.rs.ClientErrorException;

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
  static long MOCK_TIME = 0;

  private static Map<String, Integer> EC_BYTE_COUNTS = Map.of(
      "ES256", 32,
      "ES384", 48,
      "ES512", 64);

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
      throw new ClientErrorException("Unsupported JWK", 401, e);
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

  static boolean rightAboutNow(long issuedAtTime) {
    long now = MOCK_TIME != 0 ? MOCK_TIME : (System.currentTimeMillis() / 1000);
    // Issued not too far in the future, or too long in the past.
    // NOTE: Should this be customizeable?
    long fiveMinutesAgo = now - 5 * 60;
    long thirtySecondsFromNow = now + 30;
    return fiveMinutesAgo <= issuedAtTime && issuedAtTime <= thirtySecondsFromNow;
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

  /**
   * Convert from JWT ECDSA signature to 'DER' format.
   * Code from https://github.com/auth0/java-jwt
   * Released under MIT License by auth0
   * As of keycloak 20, its packed-in jose subset does not support ECDSA
   * signatures, so this is required for now.
   */
  static byte[] JOSEToDER(byte[] joseSignature, int ecNumberSize) throws SignatureException {
    // Retrieve R and S number's length and padding.
    int rPadding = countPadding(joseSignature, 0, ecNumberSize);
    int sPadding = countPadding(joseSignature, ecNumberSize, joseSignature.length);
    int rLength = ecNumberSize - rPadding;
    int sLength = ecNumberSize - sPadding;

    int length = 2 + rLength + 2 + sLength;

    final byte[] derSignature;
    int offset;
    if (length > 0x7f) {
      derSignature = new byte[3 + length];
      derSignature[1] = (byte) 0x81;
      offset = 2;
    } else {
      derSignature = new byte[2 + length];
      offset = 1;
    }

    // DER Structure: http://crypto.stackexchange.com/a/1797
    // Header with signature length info
    derSignature[0] = (byte) 0x30;
    derSignature[offset++] = (byte) (length & 0xff);

    // Header with "min R" number length
    derSignature[offset++] = (byte) 0x02;
    derSignature[offset++] = (byte) rLength;

    // R number
    if (rPadding < 0) {
      // Sign
      derSignature[offset++] = (byte) 0x00;
      System.arraycopy(joseSignature, 0, derSignature, offset, ecNumberSize);
      offset += ecNumberSize;
    } else {
      int copyLength = Math.min(ecNumberSize, rLength);
      System.arraycopy(joseSignature, rPadding, derSignature, offset, copyLength);
      offset += copyLength;
    }

    // Header with "min S" number length
    derSignature[offset++] = (byte) 0x02;
    derSignature[offset++] = (byte) sLength;

    // S number
    if (sPadding < 0) {
      // Sign
      derSignature[offset++] = (byte) 0x00;
      System.arraycopy(joseSignature, ecNumberSize, derSignature, offset, ecNumberSize);
    } else {
      System.arraycopy(joseSignature, ecNumberSize + sPadding, derSignature, offset,
          Math.min(ecNumberSize, sLength));
    }

    return derSignature;
  }

  private static int countPadding(byte[] bytes, int fromIndex, int toIndex) {
    int padding = 0;
    while (fromIndex + padding < toIndex && bytes[fromIndex + padding] == 0) {
      padding++;
    }
    return (bytes[fromIndex + padding] & 0xff) > 0x7f ? padding - 1 : padding;
  }

  static Proof validate(String dpopWireFormat) {
    // The org.keycloak.jose library is very rigid. We need to parse things manually
    // to get extensions to header (JWK, new typ value)
    String[] parts = dpopWireFormat.split("\\.");
    if (parts.length != 3) {
      throw new ClientErrorException("Parse failure of dpop [" + dpopWireFormat + "]", 401);
    }
    // Decode things we want to decode to make sure they are valid
    byte[] headerBytes, payloadBytes, signatureBytes;
    try {
      headerBytes = B64_DECODER.decode(parts[0]);
      payloadBytes = B64_DECODER.decode(parts[1]);
      signatureBytes = B64_DECODER.decode(parts[2]);
    } catch (IllegalArgumentException e) {
      throw new ClientErrorException("Error in DPoP JWT encoding", 401, e);
    }
    DPoPHeader header;
    try {
      header = JsonSerialization.readValue(headerBytes, DPoPHeader.class);
    } catch (IOException e) {
      throw new ClientErrorException(401, e);
    }

    // Validate syntax as described in
    // https://datatracker.ietf.org/doc/html/draft-ietf-oauth-dpop#section-4.2
    if (!"dpop+jwt".equals(header.getType())) {
      throw new ClientErrorException("DPoP typ invalid", 401);
    }
    if (!ALLOWED_DPOP_ALGORITHMS.contains(header.getAlgorithm())) {
      throw new ClientErrorException("DPoP alg invalid", 401);
    }

    PublicKey pk = JWKParser.create(header.getJwk()).toPublicKey();
    // This is deprecated since Keycloak will always want to look up the key
    // by the header's `kid` - the key identifier for Keycloak's signing keypair.
    // However, for DPoP we want to use the *client's* JWK.
    Signature sig;
    try {
      sig = Signature.getInstance(SIG_JWT_TO_JAVA.get(header.getAlgorithm()));
      if (header.getAlgorithm().startsWith("ES")) {
        signatureBytes = JOSEToDER(signatureBytes, EC_BYTE_COUNTS.get(header.getAlgorithm()));
      }
    } catch (NoSuchAlgorithmException e1) {
      throw new RuntimeException("Java Security Library missing verifier of type " + header.getAlgorithm());
    } catch (SignatureException e) {
      throw new ClientErrorException(401, e);
    }
    try {
      sig.initVerify(pk);
      sig.update(parts[0].getBytes(StandardCharsets.UTF_8));
      sig.update((byte) '.');
      sig.update(parts[1].getBytes(StandardCharsets.UTF_8));
      sig.verify(signatureBytes);
    } catch (SignatureException e) {
      throw new ClientErrorException("Error in DPoP signature verification [" + dpopWireFormat + "]", 401, e);
    } catch (InvalidKeyException e) {
      throw new ClientErrorException("Error in DPoP JWK / Algorithm initialization", 401, e);
    }

    DPoPPayload payload;
    try {
      payload = JsonSerialization.readValue(payloadBytes, DPoPPayload.class);
    } catch (IOException e) {
      throw new ClientErrorException(401, e);
    }

    // TODO: JTI reuse check
    if (Strings.isNullOrEmpty(payload.getIdentifier())) {
      throw new ClientErrorException("Invalid `jti` claim", 401);
    }
    // TODO what should these be? Can we look them up?
    if (Strings.isNullOrEmpty(payload.getHttpMethod()) || Strings.isNullOrEmpty(payload.getHttpUri())) {
      throw new ClientErrorException("Invalid dpop", 401);
    }
    if (payload.getIssuedAt() == null || !rightAboutNow(payload.getIssuedAt())) {
      throw new ClientErrorException(
          "Invalid dpop issuedAt [" + payload.getIssuedAt() + "] !~ [" + System.currentTimeMillis() + "]", 401);
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
