package com.virtru.keycloak;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.keycloak.common.crypto.CryptoIntegration;
import org.keycloak.common.crypto.CryptoProvider;
import org.keycloak.jose.jwk.JWK;
import org.keycloak.jose.jwk.JWKParser;

public class DPoPTest {
  // private static final String REFERENCE_DPOP = String.join("", """
  // eyJ0eXAiOiJkcG9wK2p3dCIsImFsZyI6IkVTMjU2IiwiandrIjp7Imt0eSI6Ik
  // VDIiwieCI6Imw4dEZyaHgtMzR0VjNoUklDUkRZOXpDa0RscEJoRjQyVVFVZldWQVdCR
  // nMiLCJ5IjoiOVZFNGpmX09rX282NHpiVFRsY3VOSmFqSG10NnY5VERWclUwQ2R2R1JE
  // QSIsImNydiI6IlAtMjU2In19.eyJqdGkiOiItQndDM0VTYzZhY2MybFRjIiwiaHRtIj
  // oiUE9TVCIsImh0dSI6Imh0dHBzOi8vc2VydmVyLmV4YW1wbGUuY29tL3Rva2VuIiwia
  // WF0IjoxNTYyMjYyNjE2fQ.2-GxA6T8lP4vfrg8v-FdWP0A0zdrj8igiMLvqRMUvwnQg
  // 4PtFLbdLXiOSsX0x7NVY-FNyJK70nfbV37xRZT3Lg
  // """.trim().split("\\s*,\\s*"));

  @BeforeAll
  public static void initCrypto() {
    CryptoIntegration.init(CryptoProvider.class.getClassLoader());
  }

  @Test
  public void canonicalize_ec() {
    JWK pk = JWKParser.create().parse("{"
        + "\"kty\": \"EC\","
        + "\"x\": \"l8tFrhx-34tV3hRICRDY9zCkDlpBhF42UQUfWVAWBFs\","
        + "\"y\": \"9VE4jf_Ok_o64zbTTlcuNJajHmt6v9TDVrU0CdvGRDA\","
        + "\"crv\": \"P-256\""
        + "}").getJwk();
    assertEquals(
        "{\"crv\":\"P-256\",\"kty\":\"EC\",\"x\":\"l8tFrhx-34tV3hRICRDY9zCkDlpBhF42UQUfWVAWBFs\",\"y\":\"9VE4jf_Ok_o64zbTTlcuNJajHmt6v9TDVrU0CdvGRDA\"}",
        DPoP.canonicalize(pk));
  }

  @Test
  public void canonicalize_rsa() {
    JWK pk = JWKParser.create()
        .parse(
            "{\"kty\": \"RSA\",\"n\":\"0vx7agoebGcQSuuPiLJXZptN9nndrQmbXEps2aiAFbWhM78LhWx4cbbfAAtVT86zwu1RK7aPFFxuhDR1L6tSoc_BJECPebWKRXjBZCiFV4n3oknjhMstn64tZ_2W-5JsGY4Hc5n9yBXArwl93lqt7_RN5w6Cf0h4QyQ5v-65YGjQR0_FDW2QvzqY368QQMicAtaSqzs8KJZgnYb9c7d0zgdAZHzu6qMQvRL5hajrn1n91CbOpbISD08qNLyrdkt-bFTWhAI4vMQFh6WeZu0fM4lFd2NcRwr3XPksINHaQ-G_xBniIqbw0Ls1jF44-csFCur-kEgU8awapJzKnqDKgw\","
                + "\"e\": \"AQAB\", \"alg\": \"RS256\", \"kid\": \"2011-04-29\" }")
        .getJwk();
    assertEquals(
        "{\"e\":\"AQAB\",\"kty\":\"RSA\",\"n\":\"0vx7agoebGcQSuuPiLJXZptN9nndrQmbXEps2aiAFbWhM78LhWx4cbbfAAtVT86zwu1RK7aPFFxuhDR1L6tSoc_BJECPebWKRXjBZCiFV4n3oknjhMstn64tZ_2W-5JsGY4Hc5n9yBXArwl93lqt7_RN5w6Cf0h4QyQ5v-65YGjQR0_FDW2QvzqY368QQMicAtaSqzs8KJZgnYb9c7d0zgdAZHzu6qMQvRL5hajrn1n91CbOpbISD08qNLyrdkt-bFTWhAI4vMQFh6WeZu0fM4lFd2NcRwr3XPksINHaQ-G_xBniIqbw0Ls1jF44-csFCur-kEgU8awapJzKnqDKgw\"}",
        DPoP.canonicalize(pk));
  }

  @Test
  public void cnf_ec() {
    JWK pk = JWKParser.create().parse(
      "{"
      + "\"kty\": \"EC\","
      + "\"x\": \"l8tFrhx-34tV3hRICRDY9zCkDlpBhF42UQUfWVAWBFs\","
      + "\"y\": \"9VE4jf_Ok_o64zbTTlcuNJajHmt6v9TDVrU0CdvGRDA\","
      + "\"crv\": \"P-256\""
      + "}")
        .getJwk();
    assertEquals("0ZcOCORZNYy-DWpqq30jZyJGHTN0d2HglBV3uiguA4I", DPoP.cnfThumbprint(pk));
  }

  @Test
  public void toPem_rsa() {
    JWK pk = JWKParser.create()
        .parse(
            "{\"kty\": \"RSA\",\"n\":\"0vx7agoebGcQSuuPiLJXZptN9nndrQmbXEps2aiAFbWhM78LhWx4cbbfAAtVT86zwu1RK7aPFFxuhDR1L6tSoc_BJECPebWKRXjBZCiFV4n3oknjhMstn64tZ_2W-5JsGY4Hc5n9yBXArwl93lqt7_RN5w6Cf0h4QyQ5v-65YGjQR0_FDW2QvzqY368QQMicAtaSqzs8KJZgnYb9c7d0zgdAZHzu6qMQvRL5hajrn1n91CbOpbISD08qNLyrdkt-bFTWhAI4vMQFh6WeZu0fM4lFd2NcRwr3XPksINHaQ-G_xBniIqbw0Ls1jF44-csFCur-kEgU8awapJzKnqDKgw\","
                + "\"e\": \"AQAB\", \"alg\": \"RS256\", \"kid\": \"2011-04-29\" }")
        .getJwk();
    assertEquals(
      "-----BEGIN PUBLIC KEY-----\n"
      + "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA0vx7agoebGcQSuuPiLJX\n"
      + "ZptN9nndrQmbXEps2aiAFbWhM78LhWx4cbbfAAtVT86zwu1RK7aPFFxuhDR1L6tS\n"
      + "oc/BJECPebWKRXjBZCiFV4n3oknjhMstn64tZ/2W+5JsGY4Hc5n9yBXArwl93lqt\n"
      + "7/RN5w6Cf0h4QyQ5v+65YGjQR0/FDW2QvzqY368QQMicAtaSqzs8KJZgnYb9c7d0\n"
      + "zgdAZHzu6qMQvRL5hajrn1n91CbOpbISD08qNLyrdkt+bFTWhAI4vMQFh6WeZu0f\n"
      + "M4lFd2NcRwr3XPksINHaQ+G/xBniIqbw0Ls1jF44+csFCur+kEgU8awapJzKnqDK\n"
      + "gwIDAQAB\n"
      + "-----END PUBLIC KEY-----\n",
        DPoP.jwkToPem(pk));
  }

  @Test
  public void toPem_ec() {
    JWK pk = JWKParser.create().parse(
      "{"
      + "\"kty\": \"EC\","
      + "\"x\": \"l8tFrhx-34tV3hRICRDY9zCkDlpBhF42UQUfWVAWBFs\","
      + "\"y\": \"9VE4jf_Ok_o64zbTTlcuNJajHmt6v9TDVrU0CdvGRDA\","
      + "\"crv\": \"P-256\""
      + "}")
        .getJwk();
    assertEquals("-----BEGIN PUBLIC KEY-----\n"
    + "MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEl8tFrhx+34tV3hRICRDY9zCkDlpB\n"
    + "hF42UQUfWVAWBFv1UTiN/86T+jrjNtNOVy40lqMea3q/1MNWtTQJ28ZEMA==\n"
    + "-----END PUBLIC KEY-----\n"
    , DPoP.jwkToPem(pk));
  }
}
