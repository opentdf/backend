
import "core-js/stable";
import "regenerator-runtime/runtime";

import React from "react";
import ReactDOM from "react-dom";

//OIDC shenanigans
import { ReactKeycloakProvider } from "@react-keycloak/web";
import Keycloak from "keycloak-js";

import ABACShip from './abacship';

//Obviously these would not be hardcoded normally
const KEYCLOAK_HOST = "http://localhost:65432/keycloak/auth/"
const KEYCLOAK_CLIENT_ID = "browsertest"
const KEYCLOAK_REALM = "tdf"

const keycloak = new Keycloak({
  url: KEYCLOAK_HOST,
  clientId: KEYCLOAK_CLIENT_ID,
  realm: KEYCLOAK_REALM,
});

ReactDOM.render(
    <ReactKeycloakProvider
      authClient={keycloak}
      initOptions={{
        onLoad: 'login-required',
      }}
      onEvent={(event, error) => {
        console.log("onKeycloakEvent", event, error);
      }}
      onTokens={(tokens) => {
        sessionStorage.setItem("keycloak", tokens.token || "");
      }}
    >
        <ABACShip />
    </ReactKeycloakProvider>,
    document.getElementById("react-root"),
);
