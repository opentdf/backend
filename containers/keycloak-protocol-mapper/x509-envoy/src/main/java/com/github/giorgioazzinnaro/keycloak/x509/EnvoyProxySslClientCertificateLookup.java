/*
 * Copyright 2020 Giorgio Azzinnaro
 * and other contributors as indicated by the @author tags.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 */
package com.github.giorgioazzinnaro.keycloak.x509;

import com.google.common.base.Charsets;
import org.jboss.logging.Logger;
import org.keycloak.common.util.PemUtils;
import org.keycloak.services.x509.X509ClientCertificateLookup;

import java.net.URLDecoder;
import java.security.cert.X509Certificate;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;

/**
 * EnvoyProxySslClientCertificateLookup is based on this documentation from Envoy:
 * https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_conn_man/headers#x-forwarded-client-cert
 *
 * @author <a href="mailto:giorgio.azzinnaro@gmail.com">Giorgio Azzinnaro</a>
 * @since 2020-01-18
 */
public class EnvoyProxySslClientCertificateLookup implements X509ClientCertificateLookup {

    protected Logger logger = Logger.getLogger(getClass());

    private String HEADER = "x-forwarded-client-cert";

    @Override
    public void close() {
    }

    /**
     * Here we can get the header `x-forwarded-client-cert` which has a `;` separated list of values,
     * of these values we want to extract that with key "Chain", separated by an `=` from the URL-encoded PEM-encoded
     * client certificate chain.
     * <p>
     * Decoding of the PEM chain happens elsewhere.
     */
    @Override
    public X509Certificate[] getCertificateChain(org.keycloak.http.HttpRequest httpRequest) {
        String header = getHeaderFromRequest(httpRequest);
        if (header.isEmpty()) {
            logger.warnf("HTTP header `%s` is empty", HEADER);
        }

        String rawChain = getRawChainFromHeader(header);
        if (rawChain == null || rawChain.isEmpty()) {
            logger.warnf("Chain could not be extracted from `%s`", HEADER);
        }
        String decodedChain = decodeRawChain(rawChain == null ? "" : rawChain);
        List<String> certChainPemBlocks = stringChainToPemBlocks(decodedChain);
        return decodePemBlocks(certChainPemBlocks).toArray(new X509Certificate[0]);
    }

    /**
     * Get the semicolon-delimited header "x-forwarded-client-cert"
     */
    private String getHeaderFromRequest(org.keycloak.http.HttpRequest httpRequest) {
        return httpRequest.getHttpHeaders().getRequestHeaders().getFirst(HEADER);
    }

    /**
     * From the semicolon-delimited header "x-forwarded-client-cert",
     * create a map with each key-value pair,
     * and retrieve the string with key "Chain"
     */
    private String getRawChainFromHeader(String header) {
        return Arrays.stream(header.split(";")).
                collect(Collectors.toMap(value -> value.split("=")[0],
                        value -> value.split("=")[1])).get("Chain");
    }

    /**
     * Here we sanitize the input,
     * removing possible double quotes around the input and URL-decoding
     */
    private String decodeRawChain(String rawChain) {
        String value = rawChain.replaceAll("^\"|\"$", "");
        return URLDecoder.decode(value, Charsets.UTF_8);
    }

    /**
     * We take a string which represents a chain of certificates and return a list of strings
     * where each string is a single certificate
     */
    private List<String> stringChainToPemBlocks(String chain) {
        List<String> pemBlocks = new ArrayList<>();
        if (!chain.isEmpty()) {
            List<Integer> indexes = new ArrayList<>();
            int lastIndex = 0;
            while (lastIndex != -1) {
                indexes.add(lastIndex);
                lastIndex = chain.indexOf("-----BEGIN CERTIFICATE-----", lastIndex + 1);
            }
            for (int i = 0; i < indexes.size(); i++) {
                pemBlocks.add(chain.substring(indexes.get(i), i == indexes.size() - 1 ? chain.length() : indexes.get(i + 1)));
            }
        }
        return pemBlocks;
    }

    private List<X509Certificate> decodePemBlocks(List<String> blocks) {
        return blocks.stream().map(s -> PemUtils.decodeCertificate(s)).collect(Collectors.toList());
    }

}
