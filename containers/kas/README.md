# Key Access Service

KAS is an ABAC PEP (policy enforcement point) - specifically, a PEP specialized for encryption key release.

An ABAC PEP requests a decision from an ABAC PDP (policy decision point), and is responsible for "doing something" with that decision.

As a PEP, KAS is responsible for

- Collecting all entity attributes.
- Collecting all data attributes.
- Collecting attribute definitions for every data attribute.
- Presenting those 3 things to a PDP for a Yes/No decision.
- Deciding what to with that Yes/No decision - in KAS's case, either releasing an encryption key, or not.

KAS relies on https://github.com/virtru/access-pdp as its generic open-source ABAC PDP engine, and currently starts that PDP as a local gRPC server within its own container and invokes it directly.

KAS supports a plugin model for customizing PEP functionality.
