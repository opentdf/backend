# Attribute-based Access Control (ABAC)
# -------------------------------------
package opentdf.entitlement

import data.opentdf.entitlementsvc
import future.keywords.if
import future.keywords.in

generated_entitlements := new_entitlements if {
	# Fetch entitlements from rule output
	core_entitlements := entitlementsvc.entitlements_fetch_success
	custom_attribute_names := ["name", "preferredUsername", "email"]
	idp_attributes := construct_idp_attributes(custom_attribute_names)

	entitlements := merge_idp_attributes(core_entitlements, idp_attributes)

	missing_attrs := [st | some st in entitlements; count(st.entity_attributes) == 0]
	rest := [st | some st in entitlements; count(st.entity_attributes) != 0]

	# NOTE - previously I had thought the only way to do this was with a semi-gnarly object
	# comprehension, but in fact the newly-introduced `in` keyword (imported above, as it's not core yet)
	# makes this pretty simple
	updated_entities := [entity_item |
		some attr in missing_attrs
		entity_item := {
			"entity_identifier": attr.entity_identifier,
			"entity_attributes": [{
				"attribute": "https://example.org/attr/OPA/value/AddedByOPA",
				"displayName": "Added By OPA",
			}],
		}
	]

	new_entitlements := array.concat(updated_entities, rest)
}

construct_idp_attributes(attribute_names) := idp_attributes if {
	some attribute_name in attribute_names
	idp_attributes := construct_idp_attribute(attribute_name)
}

construct_idp_attribute(attribute_name) := idp_attribute if {
	# if entitlement_context is provided in input return the idp attribute object
	input.entitlement_context
	input.entitlement_context[attribute_name]
	not is_null(input.entitlement_context[attribute_name])
	idp_attribute := {
		"attribute": concat("", ["https://example.org/attr/OPA/value/", attribute_name]),
		"displayName": input.entitlement_context[attribute_name],
	}
}

merge_idp_attributes(core_entitlements, idp_attributes) := merged_entitlements if {
	# merge attributes fetched from backend with idp attributes
	merged_entitlements := [entity_item |
		some entity in core_entitlements

		entity_item := {
			"entity_identifier": entity.entity_identifier,
			"entity_attributes": array.concat(entity.entity_attributes, idp_attributes),
		}
	]
}
