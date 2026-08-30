# Graph Report - My-Blog  (2026-08-30)

## Corpus Check
- 108 files · ~96,630 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 609 nodes · 961 edges · 53 communities (37 shown, 16 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 7 edges (avg confidence: 0.92)
- Token cost: 1,250 input · 450 output

## Community Hubs (Navigation)
- Software Integrity & Posts Test Suite
- Terraform Infrastructure Core
- User Profile & Security Helpers Test Suite
- AWS CloudWatch, ECR & Container Infra
- User Data Model & Management
- Post & Comment Interactivity Controllers
- Post Model & Formatting Logic
- App Configuration & Background Scheduler
- Authentication & Security Integration Tests
- User Interactions & Bookmarks Model
- Admin Dashboard & Management Routes
- Post Creation & Image Utility Tests
- OWASP Access Control Security Tests
- OWASP Auth Security Tests
- Open Redirect Protection Tests
- Security Misconfiguration Tests
- Cryptographic Failures Tests
- Flask Application Initialization & Setup
- Comment Model & Data Handling
- Test Fixtures & AWS Mocks Setup
- XSS & Injection Protection Tests
- Category & Tag Taxonomy Model
- Notification Model & Management
- Report Model & Resolution Logic
- Audit Logging Model & Handler
- REST API Routes & Documentation
- Insecure Design Security Tests
- System Settings Model & Defaults
- SEO, RSS & Sitemap Controllers
- Category & Tag Routes
- Asynchronous Email Delivery Service
- WSGI Entry Point & Shims
- AWS Deployment & Architecture Documentation
- Terraform Provider Lock Configurations
- MCP Protocol Configuration
- Glassmorphism UI & Styling Assets
- Services Package Initialization
- AWS Setup Shell Automation Script
- Pre-Deployment & Offline AWS Verification Strategy
- Docker Deployment Containers (Nginx/Gunicorn)
- OWASP Security Matrix & Dependencies
- Deployment Shell Script
- DynamoDB Setup Documentation
- Software Lifecycle Documentation
- Boto3 Dependency
- Interface Preview Assets
- Markdown Editor Component

## God Nodes (most connected - your core abstractions)
1. `register_user()` - 32 edges
2. `login_user()` - 26 edges
3. `create_app()` - 19 edges
4. `login_required()` - 18 edges
5. `var.app_name` - 18 edges
6. `create_post()` - 17 edges
7. `PostModel` - 16 edges
8. `UserModel` - 16 edges
9. `aws_iam_policy.app_data_policy` - 15 edges
10. `get_post_id_from_redirect()` - 15 edges

## Surprising Connections (you probably didn't know these)
- `TestA05SecurityMisconfiguration` --uses--> `ProductionConfig`  [INFERRED]
  tests/test_owasp.py → app/config.py
- `UI Glassmorphism Showcase Screenshot` --references--> `Doodle-Glassmorphism UI Aesthetic`  [EXTRACTED]
  UI.png → README.md
- `app()` --calls--> `create_app()`  [EXTRACTED]
  tests/conftest.py → app/__init__.py
- `csrf_app()` --calls--> `create_app()`  [EXTRACTED]
  tests/conftest.py → app/__init__.py
- `rate_app()` --calls--> `create_app()`  [EXTRACTED]
  tests/conftest.py → app/__init__.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **AWS Infrastructure & Deployment Layer** — readme_cloud_native_aws_architecture, deploy_deploy_aws_deployment_guide, deploy_deploy_s3_presigned_url_strategy, deploy_deploy_dynamodb_schema_setup, requirements_boto3_aws_sdk [INFERRED 0.85]
- **Doodle Glassmorphism UI & Template System** — readme_doodle_glassmorphism_ui, templates_base_doodle_layout_template, templates_create_markdown_live_preview_editor, ui_doodle_glassmorphism_interface, static_ui_screenshot_blog_interface_preview [INFERRED 0.85]
- **AWS Infrastructure & Deployment Layer** — readme_cloud_native_aws_architecture, deploy_deploy_aws_deployment_guide, deploy_deploy_s3_presigned_url_strategy, deploy_deploy_dynamodb_schema_setup, requirements_boto3_aws_sdk [INFERRED 0.85]
- **Doodle Glassmorphism UI & Template System** — readme_doodle_glassmorphism_ui, templates_base_doodle_layout_template, templates_create_markdown_live_preview_editor, ui_doodle_glassmorphism_interface, static_ui_screenshot_blog_interface_preview [INFERRED 0.85]

## Communities (53 total, 16 thin omitted)

### Community 0 - "Software Integrity & Posts Test Suite"
Cohesion: 0.06
Nodes (42): _add_image_urls(), create(), delete_post(), edit_post(), _handle_image_upload(), index(), preview_markdown(), route (+34 more)

### Community 1 - "Terraform Infrastructure Core"
Cohesion: 0.08
Nodes (41): aws_dynamodb_table.audit, aws_dynamodb_table.comments, aws_dynamodb_table.interactions, aws_dynamodb_table.notifications, aws_dynamodb_table.posts, aws_dynamodb_table.reports, aws_dynamodb_table.settings, aws_dynamodb_table.taxonomy (+33 more)

### Community 2 - "User Profile & Security Helpers Test Suite"
Cohesion: 0.08
Nodes (26): Flask extension singletons — initialized in create_app()., author_profile(), change_password(), delete_account(), edit_profile(), login(), logout(), route (+18 more)

### Community 3 - "AWS CloudWatch, ECR & Container Infra"
Cohesion: 0.13
Nodes (25): aws_cloudwatch_log_group.ecs, aws_cloudwatch_metric_alarm.alb_5xx, aws_cloudwatch_metric_alarm.unhealthy_hosts, aws_ecr_lifecycle_policy.app, aws_ecr_repository.app, aws_ecs_cluster.main, aws_ecs_service.main, aws_ecs_task_definition.app (+17 more)

### Community 4 - "User Data Model & Management"
Cohesion: 0.08
Nodes (13): UserModel — DynamoDB data access for users with Argon2id hashing. Security…, Fetch user profile by username., Check if a username exists (case-insensitive)., Update user profile attributes., Update user RBAC role (user, author, moderator, admin)., Bump session_version to invalidate all existing sessions for this user., Update account status (active, suspended, banned) and invalidate sessions., Change user password and invalidate all active sessions. (+5 more)

### Community 5 - "Post & Comment Interactivity Controllers"
Cohesion: 0.13
Nodes (24): dashboard(), route, add_comment(), delete_comment(), route, Comments routes: Post comments, nested replies, moderation, reports., report_comment(), bookmarks() (+16 more)

### Community 6 - "Post Model & Formatting Logic"
Cohesion: 0.10
Nodes (12): PostModel, PostModel — DynamoDB data access for blog posts. DynamoDB Table: myblog-posts…, Fetch a post WITHOUT incrementing view counter., Fetch a post by slug., Return all drafts for an author., Insert a new post. Returns post_id., Update a post and store a revision in version history., Soft-delete a post by setting status='deleted'. (+4 more)

### Community 7 - "App Configuration & Background Scheduler"
Cohesion: 0.12
Nodes (14): BaseConfig, DevelopmentConfig, ProductionConfig, Configuration classes for different environments., BackgroundScheduler, Distributed BackgroundScheduler — Multi-instance safe background task runner.…, Acquire a distributed lock using DynamoDB settings table., Tests for production deployment configuration, Free-Tier environment… (+6 more)

### Community 8 - "Authentication & Security Integration Tests"
Cohesion: 0.15
Nodes (15): login_user(), Register a test user and return the response., Log in a test user and return the response., register_user(), Tests for Production Readiness Audit: - Session invalidation upon status update…, test_account_deletion_flow(), test_session_invalidation_on_password_change(), test_session_invalidation_on_suspension() (+7 more)

### Community 9 - "User Interactions & Bookmarks Model"
Cohesion: 0.09
Nodes (11): InteractionModel, InteractionModel — DynamoDB data access for likes, bookmarks, and author…, Check if follower follows author., List usernames following an author., List authors followed by follower., Toggle post like atomically. Returns True if liked, False if unliked., Check if user has liked a post., Toggle post bookmark atomically. Returns True if bookmarked, False if removed. (+3 more)

### Community 10 - "Admin Dashboard & Management Routes"
Cohesion: 0.21
Nodes (18): audit_logs(), dashboard(), manage_posts(), manage_reports(), manage_settings(), manage_users(), route, Admin routes: Complete Admin & Moderation Dashboard. (+10 more)

### Community 11 - "Post Creation & Image Utility Tests"
Cohesion: 0.17
Nodes (17): create_post(), get_post_id_from_redirect(), make_fake_jpeg_bytes(), make_jpeg_bytes(), make_png_bytes(), pytest fixtures for OWASP security test suite. All AWS services (DynamoDB + S3)…, Create a post and return the response., Extract post_id from a redirect Location header like /post/<id>. (+9 more)

### Community 12 - "OWASP Access Control Security Tests"
Cohesion: 0.10
Nodes (11): User B cannot delete User A's post., Admin user can edit any user's post., Accessing a non-existent post ID returns 404 (not 500)., Verifies that protected routes enforce authentication and ownership. An…, GET /create without login → redirect to /login., POST /create without login → redirect to /login., GET /edit/<id> without login → redirect to /login., POST /delete/<id> without login → redirect to /login. (+3 more)

### Community 13 - "OWASP Auth Security Tests"
Cohesion: 0.10
Nodes (11): Verifies rate limiting, session security, and auth validation., CRITICAL: Brute-force protection. After 5 failed login attempts from same IP,…, Login with empty username must be rejected with 400., Login with empty password must be rejected., Usernames shorter than 3 chars must be rejected., Usernames with special characters must be rejected., Password without numbers rejected ('onlyletters' has no digit)., Password shorter than 8 chars must be rejected. (+3 more)

### Community 14 - "Open Redirect Protection Tests"
Cohesion: 0.15
Nodes (10): is_safe_redirect_url(), Validate that a redirect URL is safe (relative path, same host). Prevents open…, Verifies the ?next= redirect parameter cannot be used to redirect users to…, Relative paths must be allowed as safe redirects., CRITICAL: External URLs in ?next= must be blocked. Allows phishing: user clicks…, Protocol-relative URLs (//evil.com) must be blocked., javascript: URI scheme must be blocked., After login, ?next=http://evil.com must NOT redirect externally. Must redirect… (+2 more)

### Community 15 - "Security Misconfiguration Tests"
Cohesion: 0.12
Nodes (9): Verifies that the production configuration has all security-sensitive flags set…, ProductionConfig must have DEBUG=False., ProductionConfig must not propagate exceptions (hides stack traces)., SESSION_COOKIE_HTTPONLY must be True in production config., SESSION_COOKIE_SAMESITE must be Lax or Strict in production., SECRET_KEY must be read from env, not a literal string in source., 404 error page must not contain Python traceback information., 404 should render a custom page, not Flask's default. (+1 more)

### Community 16 - "Cryptographic Failures Tests"
Cohesion: 0.14
Nodes (8): Verifies passwords are stored with strong hashing and session cookies have…, Password in DynamoDB must NOT equal the original plaintext., Password hash must start with Argon2id signature ($argon2id$)., Session cookie must have HttpOnly flag set (prevents JS access)., Session cookie must have SameSite=Lax (CSRF mitigation)., Session lifetime must be configured (not unlimited)., SECRET_KEY must be set and at least 32 characters long., TestA02CryptographicFailures

### Community 17 - "Flask Application Initialization & Setup"
Cohesion: 0.24
Nodes (10): create_app(), Application factory — My Blog. Usage: from app import create_app app =…, Create and configure the Flask application., _register_error_handlers(), _setup_logging(), Analytics routes: Author dashboard analytics., route, Search & Discovery routes: Full-text search, filtering, and recommendations. (+2 more)

### Community 18 - "Comment Model & Data Handling"
Cohesion: 0.15
Nodes (6): CommentModel, CommentModel — DynamoDB data access for comments and nested replies., Create a new comment or nested reply (max depth 3)., Fetch all approved comments for a post, structured for nested rendering., Soft-delete a comment., Scan all comments for admin/moderator dashboard.

### Community 19 - "Test Fixtures & AWS Mocks Setup"
Cohesion: 0.20
Nodes (12): fixture, app(), client(), _create_aws_resources(), csrf_app(), csrf_client(), rate_app(), Flask app with CSRF ENABLED. Used specifically to verify CSRF protection works. (+4 more)

### Community 20 - "XSS & Injection Protection Tests"
Cohesion: 0.17
Nodes (7): Verifies that HTML/JS injection in post titles and content is stripped before…, <script> tags in the title must be stripped before DB storage., <img onerror=...> in title must be stripped., XSS payload must not appear unescaped in any HTTP response., XSS in ?q= search param must not be reflected unescaped., Markdown content with <script> must be sanitized in the rendered view., TestA03Injection

### Community 22 - "Notification Model & Management"
Cohesion: 0.22
Nodes (5): NotificationModel, NotificationModel — DynamoDB data access for user notifications., Create a new notification for a recipient user., Fetch notifications for a recipient, sorted newest-first., Mark all unread notifications as read.

### Community 23 - "Report Model & Resolution Logic"
Cohesion: 0.20
Nodes (5): ReportModel — Data access for user reports and moderation workflow., Create a new moderation report., Fetch reports for moderation queue., Update report status (resolved/dismissed) with moderator action notes., ReportModel

### Community 24 - "Audit Logging Model & Handler"
Cohesion: 0.25
Nodes (4): AuditModel, AuditModel — Security audit trail logging for administrative and security…, Record an immutable audit log entry., Fetch audit log history, newest-first.

### Community 25 - "REST API Routes & Documentation"
Cohesion: 0.36
Nodes (7): api_docs(), api_get_post(), api_list_posts(), health(), route, Health check and API utilities., Liveness + readiness probe for Docker healthcheck and AWS load balancer.…

### Community 26 - "Insecure Design Security Tests"
Cohesion: 0.25
Nodes (5): Verifies the auth system doesn't leak whether a username exists. Both 'wrong…, Login with a username that doesn't exist → generic error message., Login with valid username but wrong password → SAME generic error., Registering a taken username must say 'already taken', NOT expose the full user…, TestA04InsecureDesign

### Community 28 - "SEO, RSS & Sitemap Controllers"
Cohesion: 0.47
Nodes (5): route, SEO and RSS routes: sitemap.xml, robots.txt, and RSS/Atom feeds., robots(), rss_feed(), sitemap()

### Community 29 - "Category & Tag Routes"
Cohesion: 0.47
Nodes (5): category_view(), list_categories(), route, Taxonomy routes: Categories and Tags browsing., tag_view()

### Community 30 - "Asynchronous Email Delivery Service"
Cohesion: 0.50
Nodes (4): EmailService — Asynchronous email delivery service for verification, password…, Queue an email for background delivery without blocking HTTP request execution., send_email_async(), _send_email_task()

### Community 32 - "AWS Deployment & Architecture Documentation"
Cohesion: 0.67
Nodes (3): AWS Deployment Guide, S3 Private Bucket Presigned URL Strategy, Cloud-Native AWS Architecture

### Community 35 - "Glassmorphism UI & Styling Assets"
Cohesion: 0.67
Nodes (3): Doodle-Glassmorphism UI Aesthetic, Base Doodle Layout Template, UI Glassmorphism Showcase Screenshot

## Knowledge Gaps
- **22 isolated node(s):** `uvx`, `aws-setup.sh script`, `provider.registry.terraform.io/hashicorp/aws`, `provider.registry.terraform.io/hashicorp/random`, `var.admin_username` (+17 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **16 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `create_app()` connect `Flask Application Initialization & Setup` to `User Data Model & Management`, `Post Model & Formatting Logic`, `User Interactions & Bookmarks Model`, `Post Creation & Image Utility Tests`, `Comment Model & Data Handling`, `Test Fixtures & AWS Mocks Setup`, `Category & Tag Taxonomy Model`, `Notification Model & Management`, `Report Model & Resolution Logic`, `Audit Logging Model & Handler`, `System Settings Model & Defaults`, `WSGI Entry Point & Shims`?**
  _High betweenness centrality (0.133) - this node is a cross-community bridge._
- **Why does `UserModel` connect `User Data Model & Management` to `Flask Application Initialization & Setup`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
- **Why does `PostModel` connect `Post Model & Formatting Logic` to `Flask Application Initialization & Setup`?**
  _High betweenness centrality (0.059) - this node is a cross-community bridge._
- **What connects `uvx`, `aws-setup.sh script`, `provider.registry.terraform.io/hashicorp/aws` to the rest of the system?**
  _22 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Software Integrity & Posts Test Suite` be split into smaller, more focused modules?**
  _Cohesion score 0.0602322206095791 - nodes in this community are weakly interconnected._
- **Should `Terraform Infrastructure Core` be split into smaller, more focused modules?**
  _Cohesion score 0.08244897959183674 - nodes in this community are weakly interconnected._
- **Should `User Profile & Security Helpers Test Suite` be split into smaller, more focused modules?**
  _Cohesion score 0.08199643493761141 - nodes in this community are weakly interconnected._