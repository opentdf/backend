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

import org.jboss.logging.Logger;
import org.keycloak.Config;
import org.keycloak.models.KeycloakSession;
import org.keycloak.models.KeycloakSessionFactory;
import org.keycloak.services.x509.X509ClientCertificateLookup;
import org.keycloak.services.x509.X509ClientCertificateLookupFactory;

/**
 * @author <a href="mailto:giorgio.azzinnaro@gmail.com">Giorgio Azzinnaro</a>
 * @since 2020-01-18
 */
public class EnvoyProxySslClientCertificateLookupFactory implements X509ClientCertificateLookupFactory {

    protected Logger logger = Logger.getLogger(getClass());

    @Override
    public String getId() {
        return "envoy";
    }

    @Override
    public X509ClientCertificateLookup create(KeycloakSession session) {
        return new EnvoyProxySslClientCertificateLookup();
    }

    @Override
    public void init(Config.Scope config) {
    }

    @Override
    public void postInit(KeycloakSessionFactory factory) {
    }

    @Override
    public void close() {
    }

}