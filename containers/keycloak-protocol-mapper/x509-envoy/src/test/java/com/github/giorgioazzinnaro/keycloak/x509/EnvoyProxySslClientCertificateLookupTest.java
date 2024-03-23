package com.github.giorgioazzinnaro.keycloak.x509;

import jakarta.ws.rs.core.HttpHeaders;
import jakarta.ws.rs.core.MultivaluedHashMap;
import jakarta.ws.rs.core.MultivaluedMap;
import org.apache.commons.io.IOUtils;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.keycloak.common.crypto.CryptoIntegration;
import org.keycloak.common.crypto.CryptoProvider;
import org.keycloak.http.HttpRequest;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.net.URLEncoder;
import java.nio.charset.Charset;
import java.security.cert.X509Certificate;
import java.util.Arrays;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.mockito.Mockito.when;

@ExtendWith({MockitoExtension.class})
class EnvoyProxySslClientCertificateLookupTest {

    @Mock
    HttpRequest mockRequest;
    @Mock
    HttpHeaders httpHeaders;

    @BeforeAll
    public static void initCrypto() {
        CryptoIntegration.init(CryptoProvider.class.getClassLoader());
    }


    @Test
    void getCertificateChain() throws Exception {

        when(mockRequest.getHttpHeaders()).thenReturn(httpHeaders);

        MultivaluedMap<String, String> reqHeaders = new MultivaluedHashMap<>();

        String forwardedHeader = "By=http://frontend.lyft.com;Hash=468ed33be74eee6556d90c0149c1309e9ba61d6425303443c0748a02dd8de688;" +
                "Subject=\"/C=US/ST=CA/L=San Francisco/OU=Lyft/CN=Test Client\";URI=http://testclient.lyft.com;" +
                "Chain=" + URLEncoder.encode(IOUtils.resourceToString("/pem1.pem", Charset.defaultCharset()),
                Charset.defaultCharset());

        reqHeaders.put("x-forwarded-client-cert", Arrays.asList(forwardedHeader));
        when(httpHeaders.getRequestHeaders()).thenReturn(reqHeaders);

        EnvoyProxySslClientCertificateLookup envoyProxySslClientCertificateLookup = new EnvoyProxySslClientCertificateLookup();
        X509Certificate[] certs = envoyProxySslClientCertificateLookup.getCertificateChain(mockRequest);

        assertNotNull(certs);
        assertEquals(1 , certs.length);
    }
}