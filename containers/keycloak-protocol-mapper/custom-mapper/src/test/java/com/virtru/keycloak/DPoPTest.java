package com.virtru.keycloak;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.keycloak.common.crypto.CryptoIntegration;
import org.keycloak.common.crypto.CryptoProvider;
import org.keycloak.jose.jwk.JWK;
import org.keycloak.jose.jwk.JWKParser;

import com.virtru.keycloak.DPoP.Proof;

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

  @Test
  public void validate() {
    DPoP.MOCK_TIME = 1670866831;
    try {
      String dpop = "eyJhbGciOiJSUzI1NiIsInR5cCI6ImRwb3Arand0IiwiandrIjp7Imt0eSI6IlJTQSIsImUiOiJBUUFCIiwibiI6ImpZWUdvcGxoT3ViWnBiQ1ZVa0RDMTJhVUU3MmJKYk9Oa3VoS1g1ZVBMcXhiYV9BYWN5NXpzei04Ykxab2ttY2lKOUtQc2dwMkl3Q050UDBDMTJrX25kRlBGYzhwQ3pjSWp5MUxRZ3JnMEtUdXhac1JLN0k1bnRBOTRVM3IxR0tMcTBjM1J3RGZ2dWZDLUtjb2g5aWNVM0xFOTZGZUlmTFozYzlnMmROai1MWXJ4eFBPSzFuY2dobmZMbHI5QXNiM3UweUt2eFZ6M1FUTVRoVUFmTVY0NmFVdXdKSi1RNXRYLUZKbXdqajZRNVQ0bzgyT2xLcjhzZDZoZGp6NkY2YUlrMDIzcmxXeFRfRmdPLU1MdS0tVkFBblpuXzBaSFhKSGRCUjA2NUpKVi1obE5YdmdtZnJqOTFmckY2djNabDY2QUtJQUZQd29GdHV3ZzR2S0pFaFUzdyJ9fQ.eyJpYXQiOjE2NzA4NjY4MzEsImp0aSI6InBkc2tsX0lKdHJtY2h3NlZ1UjQycEZFZDFoTWxzVmlMNnV4MUcxT0FzRHMiLCJodG0iOiJQT1NUIiwiaHR1IjoiaHR0cDovL2xvY2FsaG9zdDo2NTQzMi9hdXRoL3JlYWxtcy90ZGYvcHJvdG9jb2wvb3BlbmlkLWNvbm5lY3QvdG9rZW4ifQ.WB_43xmaKdr--j7rm4Z1O1OVUXroxA-Pyp2j1qHHz0pwRq4ejHG3ev83edjOQT-sXp5kyySw2o-d5cW33OkGy1ZP2kX_B4TILwvVCIEGtXoz_JfKWchCVdQ49AmaTekWTq66uE8SA-H8NIyTaKIouMmGF4_wRFFH8nv203NVd_V2tSxm7AlrwlD2WdvB6a81tfw2wFBnxivoup0SKdy1UbEZ0usn-IcoVlqI-cy7dw_rdnJ7Gm6AwbJiNgLbcdN_-nzOXmJro7Mn41PMQCT13IZiP17fs1j58dpE11xYyQWWEjgFZG19iflzloKkNeoXy8uPT-iRgnunr-8FUay0sA";
      Proof p = DPoP.validate(dpop);
      assertEquals("dpop+jwt", p.getHeader().getType());
    } finally {
      DPoP.MOCK_TIME = 0;
    }
  }
}
