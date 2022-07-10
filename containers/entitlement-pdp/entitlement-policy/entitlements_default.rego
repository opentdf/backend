package opentdf.entitlement

import data.opentdf.entitlementsvc
import data.opentdf.entitlement_ersvc
import future.keywords.in
import input.entitlement_context

default get_entitlements_from_emails = []
default get_entitlements_from_usernames = []

custom_attribute_names := attribute_names {
	attribute_names := ["name", "preferredUsername", "email"]
}

generated_entitlements := newEntitlements {
	# Fetch entitlements from user ids
	ids_entitlements := entitlementsvc.entitlements_fetch_success

	# Fetch entitlements from email addresses
	email_entitlements := get_entitlements_from_emails

	# Fetch entitlements from usernames
	username_entitlements := get_entitlements_from_usernames

	# Combine Entitlements: ids + email + username
	core_entitlements := array.concat(ids_entitlements, array.concat(email_entitlements, username_entitlements))

	idp_attributes := construct_idp_attributes(custom_attribute_names)

	entitlements := merge_idp_attributes(core_entitlements, idp_attributes)

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

construct_idp_attributes(attribute_names) = idp_attributes {
	idp_attributes := [attribute |
		some attribute_name in attribute_names
		attribute := construct_idp_attribute(attribute_name)
	]
}

construct_idp_attribute(attribute_name) = idp_attribute {
	# if entitlement_context is provided in input return the idp attribute object
	input.entitlement_context
	input.entitlement_context[attribute_name]
	not is_null(input.entitlement_context[attribute_name])
	idp_attribute := {
		"attribute": concat("", ["https://example.org/attr/OPA/value/", attribute_name]),
		"displayName": input.entitlement_context[attribute_name],
	}
}

merge_idp_attributes(core_entitlements, idp_attributes) = merged_entitlements {
	# merge attributes fetched from backend with idp attributes
	merged_entitlements := [entityItem |
		some entitiy in core_entitlements

		entityItem := {
			"entity_identifier": entitiy.entity_identifier,
			"entity_attributes": array.concat(entitiy.entity_attributes, idp_attributes),
		}
	]
}

# Function to search through map for the specified OpenTDF ID (otdf_id), and return the original identifier (i.e. email/username)
# Format: map = = [ {"original_id": {identifier: "email@company.com", type:"email"}, "EntityRepresentations": [{"id": "XXX-YYY-ZZZ", ...}] }, ... ]
find_original_id_from_otdfid(otdf_id, map) := my_id {
	map[i].EntityRepresentations[_].id = otdf_id
	my_id := map[i].original_id.identifier
}

get_entitlements_from_emails = entitlements_from_emails {

	# basic checks that we need to check email addresses
	input.entitlement_context["entity_emails"]
	count(input.entitlement_context["entity_emails"]) != 0

	# Grab the entire email list
	email_addrs := input.entitlement_context["entity_emails"]

	# Send the list to Entity Resolution Service, get back OpenTDF IDs (may be multiple) for each email
	# Gets back: email_entity_ids = [ {"original_id": {identifier: "email@company.com", type:"email"}, "EntityRepresentations": [{"id": "XXX-YYY-ZZZ", ...}] }, ... ]
	email_entity_ids := entitlement_ersvc.entity_resolution_fetch_success("email", email_addrs)

	# Extract a list of only OpenTDF IDs from the ERS returned results
	# This will be used to query the entitlement service
	entity_ids := [ entityItem |
		some entities in email_entity_ids                    # look @ each entity
		some entity_rep in entities.EntityRepresentations    # look through array of Entity Representations
		entityItem := entity_rep.id                          # add the ID to the list
	]

    # Do the Entitlements lookup using the list of OpenTDF IDs as "Secondary Entities".
	# The Primary Entity remains the unchanged (i.e. the client which created this request).
	# Gets back: entitlements_from_IDs= [ {"entity_attributes": [{"attribute": "attr1", "displayName": "DN"}], "entity_identifier": "XXX-YYY-ZZZ"}, ... ]
	entitlements_from_IDs := entitlementsvc.entitlements_fetch_success
		with input.secondary_entities as entity_ids

	# Add email address to each entry
	entitlements_from_emails := [ entitlementItem |
		some entry in entitlements_from_IDs               # iterate through all the returned entitlement entries
		entity_id := entry.entity_identifier
		entity_attributes := entry.entity_attributes

		# create the email address attribute
		email_attribute := {
			"attribute": concat("", ["https://example.com/attr/entity_email/value/", find_original_id_from_otdfid(entity_id, email_entity_ids)]),
			"displayName": "Email"
		}

		# Add updated entry (+ email address attribute) for response
		entitlementItem := {
			"entity_identifier": entity_id,
			"entity_attributes": array.concat(entity_attributes, [email_attribute])
		}
	]
}

get_entitlements_from_usernames = entitlements_from_usernames {

	# basic checks that we need to check usernames
	input.entitlement_context["entity_usernames"]
	count(input.entitlement_context["entity_usernames"]) != 0

	# Grab the entire username list
	username_addrs := input.entitlement_context["entity_usernames"]

	# Send the list to Entity Resolution Service, get back OpenTDF IDs (may be multiple) for each username
	# Gets back: username_entity_ids = [ {"original_id": {identifier: "user1", type:"username"}, "EntityRepresentations": [{"id": "XXX-YYY-ZZZ", ...}] }, ... ]
	username_entity_ids := entitlement_ersvc.entity_resolution_fetch_success("username", username_addrs)

	# Extract a list of only OpenTDF IDs from the ERS returned results
	# This will be used to query the entitlement service
	entity_ids := [ entityItem |
		some entities in username_entity_ids                    # look @ each entity
		some entity_rep in entities.EntityRepresentations    # look through array of Entity Representations
		entityItem := entity_rep.id                          # add the ID to the list
	]

    # Do the Entitlements lookup using the list of OpenTDF IDs as "Secondary Entities".
	# The Primary Entity remains the unchanged (i.e. the client which created this request).
	# Gets back: entitlements_from_IDs= [ {"entity_attributes": [{"attribute": "attr1", "displayName": "DN"}], "entity_identifier": "XXX-YYY-ZZZ"}, ... ]
	entitlements_from_IDs := entitlementsvc.entitlements_fetch_success
		with input.secondary_entities as entity_ids

	# Add username to each entry
	entitlements_from_usernames := [ entitlementItem |
		some entry in entitlements_from_IDs               # iterate through all the returned entitlement entries
		entity_id := entry.entity_identifier
		entity_attributes := entry.entity_attributes

		# create the username attribute
		username_attribute := {
			"attribute": concat("", ["https://example.com/attr/entity_username/value/", find_original_id_from_otdfid(entity_id, username_entity_ids)]),
			"displayName": "Username"
		}

		# Add updated entry (+ username attribute) for response
		entitlementItem := {
			"entity_identifier": entity_id,
			"entity_attributes": array.concat(entity_attributes, [username_attribute])
		}
	]
}