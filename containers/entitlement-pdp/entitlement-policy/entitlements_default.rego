package virtru.entitlement

import data.virtru.entitlementsvc
import future.keywords.in

generated_entitlements := newEntitlements {
	#Fetch entitlements from rule output
	entitlements := entitlementsvc.entitlements_fetch_success

	missingAttrs := [st | st = entitlements[_]; count(st.entity_attributes) == 0]
	rest := [st | st = entitlements[_]; count(st.entity_attributes) != 0]

	# NOTE - previously I had thought the only way to do this was with a semi-gnarly object
	# comprehension, but in fact the newly-introduced `in` keyword (imported above, as it's not core yet)
	# makes this pretty simple
	updatedEntities := [entityItem |
		some attr in missingAttrs
		entityItem := {
			"entity_identifier": attr.entity_identifier,
			"entity_attributes": [{
				"attribute": "https://example.org/attr/OPA/value/AddedByOPA",
				"displayName": "Added By OPA",
			}],
		}
	]

	newEntitlements := array.concat(updatedEntities, rest)
}
