package opentdf.entitlement_ersvc

import future.keywords.in
import data.opentdf.entity_resolution_service
import input.primary_entity
import input.secondary_entities
import input.entitlement_context

# NOTE this is a separate rule because ATM `http.send` calls cannot be mocked
# in rego tests the way everything else can - so we mock this rule entirely
entity_resolution_service_fetch(type, ids) = response {

	# Create the list of ids
	list_of_ids := [ idEntry |
		some id in ids
		idEntry := {
			"identifier": id,
			"type": type
		}
	]

	response := http.send({
		"method": "POST",
		"url": entity_resolution_service.url,
		"body": {
			"entity_identifiers": list_of_ids
		}
	})
}

# This rule checks that the response meets criteria for valid entitlements.
entity_resolution_fetch_success(type, ids) = entity_ids {
	response := entity_resolution_service_fetch(type, ids)

	# Following must be TRUE or rule will eval to empty array
	response.body != null
	response.status_code == 200

	# Returns array of entity resolutions
	entity_ids := response.body
}
