# Graph Report - .  (2026-08-30)

## Corpus Check
- 39 files · ~77,963 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 303 nodes · 443 edges · 31 communities (22 shown, 9 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 13 edges (avg confidence: 0.63)
- Token cost: 1,250 input · 450 output

## Community Hubs (Navigation)
- Blog Post Routes & Model (C0)
- Authentication & Session Management (C1)
- Mocked AWS Test Fixtures (C2)
- Mocked AWS Test Fixtures (C3)
- OWASP Security Validation Tests (C4)
- Blog Post Routes & Model (C5)
- OWASP Security Validation Tests (C6)
- OWASP Security Validation Tests (C7)
- OWASP Security Validation Tests (C8)
- OWASP Security Validation Tests (C9)
- OWASP Security Validation Tests (C10)
- OWASP Security Validation Tests (C11)
- OWASP Security Validation Tests (C12)
- OWASP Security Validation Tests (C13)
- Mocked AWS Test Fixtures (C14)
- OWASP Security Validation Tests (C15)
- Cloud Architecture & Deployment (C16)
- Cloud Architecture & Deployment (C17)
- aws-setup.sh (C18)
- Mocked AWS Test Fixtures (C19)
- Cloud Architecture & Deployment (C20)
- OWASP Security Validation Tests (C21)
- Cloud Architecture & Deployment (C25)
- Cloud Architecture & Deployment (C26)
- Boto3 AWS SDK Dependency (C27)
- Blog Interface Preview Image (C28)
- Doodle UI Frontend Templates (C29)

## God Nodes (most connected - your core abstractions)
1. `register_user()` - 19 edges
2. `TestA07AuthenticationFailures` - 15 edges
3. `login_user()` - 13 edges
4. `create_app()` - 12 edges
5. `ProductionConfig` - 12 edges
6. `TestA01BrokenAccessControl` - 12 edges
7. `TestA08SoftwareIntegrityFailures` - 12 edges
8. `PostModel` - 11 edges
9. `is_valid_image()` - 11 edges
10. `create_post()` - 10 edges

## Surprising Connections (you probably didn't know these)
- `TestA01BrokenAccessControl` --uses--> `ProductionConfig`  [INFERRED]
  tests/test_owasp.py → app/config.py
- `TestA02CryptographicFailures` --uses--> `ProductionConfig`  [INFERRED]
  tests/test_owasp.py → app/config.py
- `TestA03Injection` --uses--> `ProductionConfig`  [INFERRED]
  tests/test_owasp.py → app/config.py
- `TestA05SecurityMisconfiguration` --uses--> `ProductionConfig`  [INFERRED]
  tests/test_owasp.py → app/config.py
- `TestA07AuthenticationFailures` --uses--> `ProductionConfig`  [INFERRED]
  tests/test_owasp.py → app/config.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **AWS Infrastructure & Deployment Layer** — readme_cloud_native_aws_architecture, deploy_deploy_aws_deployment_guide, deploy_deploy_s3_presigned_url_strategy, deploy_deploy_dynamodb_schema_setup, requirements_boto3_aws_sdk [INFERRED 0.85]
- **Doodle Glassmorphism UI & Template System** — readme_doodle_glassmorphism_ui, templates_base_doodle_layout_template, templates_create_markdown_live_preview_editor, ui_doodle_glassmorphism_interface, static_ui_screenshot_blog_interface_preview [INFERRED 0.85]

## Communities (31 total, 9 thin omitted)

### Community 0 - "Blog Post Routes & Model (C0)"
Cohesion: 0.09
Nodes (36): _add_image_urls(), create(), delete_post(), edit_post(), _handle_image_upload(), index(), route, Posts Blueprint — /, /post/<id>, /create, /edit/<id>, /delete/<id> Security… (+28 more)

### Community 1 - "Authentication & Session Management (C1)"
Cohesion: 0.07
Nodes (27): Flask extension singletons — initialized in create_app()., create_app(), Application factory — My Blog. Usage: from app import create_app app =…, Create and configure the Flask application., _register_error_handlers(), _setup_logging(), UserModel — DynamoDB data access for users with Argon2id hashing. Security…, Create a new user. Username is always stored as lowercase. Returns False if the… (+19 more)

### Community 2 - "Mocked AWS Test Fixtures (C2)"
Cohesion: 0.10
Nodes (20): create_post(), get_post_id_from_redirect(), login_user(), Register a test user and return the response., Log in a test user and return the response., Create a post and return the response., Extract post_id from a redirect Location header like /post/<id>., register_user() (+12 more)

### Community 3 - "Mocked AWS Test Fixtures (C3)"
Cohesion: 0.13
Nodes (19): fixture, app(), client(), _create_aws_resources(), csrf_app(), csrf_client(), make_fake_jpeg_bytes(), make_png_bytes() (+11 more)

### Community 4 - "OWASP Security Validation Tests (C4)"
Cohesion: 0.10
Nodes (11): Verifies rate limiting, session security, and auth validation., CRITICAL: Brute-force protection. After 5 failed login attempts from same IP,…, Login with empty username must be rejected with 400., Login with empty password must be rejected., Usernames shorter than 3 chars must be rejected., Usernames with special characters must be rejected., Password without numbers rejected ('onlyletters' has no digit)., Password shorter than 8 chars must be rejected. (+3 more)

### Community 5 - "Blog Post Routes & Model (C5)"
Cohesion: 0.13
Nodes (8): PostModel, PostModel — DynamoDB data access for blog posts. DynamoDB Table: myblog-posts…, Insert a new post. Returns the new post_id., Update title, content, and optionally the image key., Estimate reading time based on ~200 words per minute., Return a page of posts, optionally filtered by search term. DynamoDB Scan is…, Fetch a post and atomically increment its view counter. Returns None if the…, Fetch a post WITHOUT incrementing view counter. Used for edit/delete operations.

### Community 6 - "OWASP Security Validation Tests (C6)"
Cohesion: 0.15
Nodes (10): is_safe_redirect_url(), Validate that a redirect URL is safe (relative path, same host). Prevents open…, Verifies the ?next= redirect parameter cannot be used to redirect users to…, Relative paths must be allowed as safe redirects., CRITICAL: External URLs in ?next= must be blocked. Allows phishing: user clicks…, Protocol-relative URLs (//evil.com) must be blocked., javascript: URI scheme must be blocked., After login, ?next=http://evil.com must NOT redirect externally. Must redirect… (+2 more)

### Community 7 - "OWASP Security Validation Tests (C7)"
Cohesion: 0.12
Nodes (9): Verifies that the production configuration has all security-sensitive flags set…, ProductionConfig must have DEBUG=False., ProductionConfig must not propagate exceptions (hides stack traces)., SESSION_COOKIE_HTTPONLY must be True in production config., SESSION_COOKIE_SAMESITE must be Lax or Strict in production., SECRET_KEY must be read from env, not a literal string in source., 404 error page must not contain Python traceback information., 404 should render a custom page, not Flask's default. (+1 more)

### Community 8 - "OWASP Security Validation Tests (C8)"
Cohesion: 0.14
Nodes (8): Accessing a non-existent post ID returns 404 (not 500)., Verifies that protected routes enforce authentication and ownership. An…, GET /create without login → redirect to /login., POST /create without login → redirect to /login., GET /edit/<id> without login → redirect to /login., POST /delete/<id> without login → redirect to /login., CRITICAL: DELETE must not be possible via GET request. GET /delete/<id> is how…, TestA01BrokenAccessControl

### Community 9 - "OWASP Security Validation Tests (C9)"
Cohesion: 0.14
Nodes (8): Verifies passwords are stored with strong hashing and session cookies have…, Password in DynamoDB must NOT equal the original plaintext., Password hash must start with Argon2id signature ($argon2id$)., Session cookie must have HttpOnly flag set (prevents JS access)., Session cookie must have SameSite=Lax (CSRF mitigation)., Session lifetime must be configured (not unlimited)., SECRET_KEY must be set and at least 32 characters long., TestA02CryptographicFailures

### Community 10 - "OWASP Security Validation Tests (C10)"
Cohesion: 0.18
Nodes (8): is_valid_password(), Return True if password meets minimum strength requirements: - 8–72 characters…, Unit tests for the security utility functions., sanitize_text() must strip ALL HTML tags., Nested HTML tags must all be stripped., Strong passwords (letter + digit, 8+ chars) accepted., Weak passwords rejected., TestSecurityHelpers

### Community 11 - "OWASP Security Validation Tests (C11)"
Cohesion: 0.17
Nodes (7): Tests CSRF protection and file upload magic byte validation., POST /create without CSRF token must be rejected (400)., POST /delete/<id> without CSRF token must be rejected., A PHP script renamed to .jpg must be rejected., An HTML file renamed to .jpg must be rejected., Extension validator must block disallowed extensions., TestA08SoftwareIntegrityFailures

### Community 12 - "OWASP Security Validation Tests (C12)"
Cohesion: 0.25
Nodes (8): BaseConfig, DevelopmentConfig, ProductionConfig, Configuration classes for different environments., OWASP Top 10 (2021) Security Test Suite — My Blog…, Verifies the auth system doesn't leak whether a username exists. Both 'wrong…, Login with a username that doesn't exist → generic error message., TestA04InsecureDesign

### Community 13 - "OWASP Security Validation Tests (C13)"
Cohesion: 0.33
Nodes (4): is_valid_username(), Return True if username matches the allowed pattern., Valid usernames (alphanumeric + underscore, 3–32 chars) accepted., Invalid usernames rejected.

### Community 14 - "Mocked AWS Test Fixtures (C14)"
Cohesion: 0.33
Nodes (4): make_jpeg_bytes(), Return minimal valid JPEG file bytes (magic bytes + EOF marker)., A valid JPEG file (correct magic bytes) must be accepted., The file stream must be reset to position 0 after magic byte check. Otherwise…

### Community 15 - "OWASP Security Validation Tests (C15)"
Cohesion: 0.50
Nodes (3): Verifies that HTML/JS injection in post titles and content is stripped before…, XSS in ?q= search param must not be reflected unescaped., TestA03Injection

### Community 16 - "Cloud Architecture & Deployment (C16)"
Cohesion: 0.67
Nodes (3): AWS Deployment Guide, S3 Private Bucket Presigned URL Strategy, Cloud-Native AWS Architecture

### Community 17 - "Cloud Architecture & Deployment (C17)"
Cohesion: 0.67
Nodes (3): Doodle-Glassmorphism UI Aesthetic, Base Doodle Layout Template, UI Glassmorphism Showcase Screenshot

## Knowledge Gaps
- **15 isolated node(s):** `aws-setup.sh script`, `OWASP Top 10 Security Matrix`, `Software Development Life Cycle Strategy`, `AWS Deployment Guide`, `DynamoDB Table Setup Guide` (+10 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `TestA07AuthenticationFailures` connect `OWASP Security Validation Tests (C4)` to `Mocked AWS Test Fixtures (C2)`, `OWASP Security Validation Tests (C12)`?**
  _High betweenness centrality (0.120) - this node is a cross-community bridge._
- **Why does `create_app()` connect `Authentication & Session Management (C1)` to `Mocked AWS Test Fixtures (C3)`, `Blog Post Routes & Model (C5)`?**
  _High betweenness centrality (0.104) - this node is a cross-community bridge._
- **Why does `ProductionConfig` connect `OWASP Security Validation Tests (C12)` to `OWASP Security Validation Tests (C4)`, `OWASP Security Validation Tests (C6)`, `OWASP Security Validation Tests (C7)`, `OWASP Security Validation Tests (C8)`, `OWASP Security Validation Tests (C9)`, `OWASP Security Validation Tests (C10)`, `OWASP Security Validation Tests (C11)`, `OWASP Security Validation Tests (C15)`?**
  _High betweenness centrality (0.091) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `ProductionConfig` (e.g. with `TestA01BrokenAccessControl` and `TestA02CryptographicFailures`) actually correct?**
  _`ProductionConfig` has 9 INFERRED edges - model-reasoned connections that need verification._
- **What connects `aws-setup.sh script`, `OWASP Top 10 Security Matrix`, `Software Development Life Cycle Strategy` to the rest of the system?**
  _15 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Blog Post Routes & Model (C0)` be split into smaller, more focused modules?**
  _Cohesion score 0.08974358974358974 - nodes in this community are weakly interconnected._
- **Should `Authentication & Session Management (C1)` be split into smaller, more focused modules?**
  _Cohesion score 0.07112375533428165 - nodes in this community are weakly interconnected._