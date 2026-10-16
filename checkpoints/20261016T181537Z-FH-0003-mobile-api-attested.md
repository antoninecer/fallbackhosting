# FH-0003 external API root observation

- Recorded UTC 2026-10-16T18:15:37Z. Operator confirmed from phone over mobile data that exact https://quantum.api.ventureout.cz/ displays the expected JSON API-running message. OPERATOR_ATTESTED; actual test timestamp not supplied. Earlier quantum.ventureout.cz default Nginx page was a different hostname.
- This establishes operator-reported external root reachability only; it does not establish random-generation behavior, all assets, a visual UI or independent full acceptance. Agent web reader could not access this endpoint; local verified-TLS GET returned expected root JSON.
- No reference app/configuration changed. FH-0003 remains TESTING until dynamic-function evidence is obtained.

- Follow-up: public OpenAPI GET200 exposes POST /random; bounded single integer probe returned200 with empty result, so dynamic behavior is NOT confirmed by HTTP status. Operator also confirmed live cafe demo heading and order-demo/return navigation on phone; these are demo observations, not reference random-generation acceptance.
