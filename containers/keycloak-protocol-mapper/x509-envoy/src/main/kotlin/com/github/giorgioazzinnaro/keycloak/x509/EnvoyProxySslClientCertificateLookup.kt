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
package com.github.giorgioazzinnaro.keycloak.x509

import org.jboss.logging.Logger
import org.jboss.resteasy.spi.HttpRequest
import org.keycloak.common.util.PemUtils
import org.keycloak.services.x509.X509ClientCertificateLookup
import java.lang.IllegalArgumentException
import java.net.URLDecoder
import java.security.cert.X509Certificate

/**
 * EnvoyProxySslClientCertificateLookup is based on this documentation from Envoy:
 * https://www.envoyproxy.io/docs/envoy/v1.12.2/configuration/http/http_conn_man/headers#x-forwarded-client-cert
 *
 * @author <a href="mailto:giorgio.azzinnaro@gmail.com">Giorgio Azzinnaro</a>
 * @since 2020-01-18
 */
open class EnvoyProxySslClientCertificateLookup : X509ClientCertificateLookup {

    protected val logger: Logger = Logger.getLogger(javaClass)

    private val HEADER = "x-forwarded-client-cert"

    override fun close() { }

    /**
     * Here we can get the header `x-forwarded-client-cert` which has a `;` separated list of values,
     * of these values we want to extract that with key "Chain", separated by an `=` from the URL-encoded PEM-encoded
     * client certificate chain.
     *
     * Decoding of the PEM chain happens elsewhere.
     */
    override fun getCertificateChain(httpRequest: org.keycloak.http.HttpRequest): Array<out X509Certificate>? {
        val header = getHeaderFromRequest(httpRequest)
        if (header.isEmpty()) {
            logger.warnf("HTTP header `%s` is empty", HEADER)
        }

        val rawChain = getRawChainFromHeader(header)
        if (rawChain.isNullOrEmpty()) {
            logger.warnf("Chain could not be extracted from `%s`", HEADER)
        }

        val decodedChain = decodeRawChain(rawChain.orEmpty())

        val certChainPemBlocks = stringChainToPemBlocks(decodedChain)

        return decodePemBlocks(certChainPemBlocks).toTypedArray()
    }

    /**
     * Get the semicolon-delimited header "x-forwarded-client-cert"
     */
    private fun getHeaderFromRequest(httpRequest: org.keycloak.http.HttpRequest): String {
        return httpRequest.httpHeaders.requestHeaders.getFirst(HEADER)
    }

    /**
     * From the semicolon-delimited header "x-forwarded-client-cert",
     * create a map with each key-value pair,
     * and retrieve the string with key "Chain"
     */
    private fun getRawChainFromHeader(header: String): String? {
        return header
                .splitToSequence(';')
                .map { it.split('=') }
                .map { it[0] to it[1] }
                .toMap()
                .get("Chain")
    }

    /**
     * Here we sanitize the input,
     * removing possible double quotes around the input and URL-decoding
     */
    private fun decodeRawChain(rawChain: String): String {
        return rawChain
                .trim('"')
                .let { URLDecoder.decode(it, Charsets.UTF_8) }
    }

    /**
     * We take a string which represents a chain of certificates and return a list of strings
     * where each string is a single certificate
     */
    private fun stringChainToPemBlocks(chain: String): List<String> {

        val indexes = mutableListOf<Int>()

        var lastIndex = 0
        while (lastIndex != -1) {
            indexes.add(lastIndex)
            lastIndex = chain.indexOf("-----BEGIN CERTIFICATE-----", lastIndex + 1)
        }
        indexes.add(chain.length)

        return indexes.zipWithNext { a, b -> chain.substring(a, b) }
    }

    private fun decodePemBlocks(blocks: List<String>): List<X509Certificate> {
        return blocks.map { PemUtils.decodeCertificate(it) }
    }

}
