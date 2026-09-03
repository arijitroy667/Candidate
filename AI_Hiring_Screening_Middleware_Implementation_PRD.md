# AI Hiring & Screening Middleware
## Implementation-Grade Phase-Wise PRD

> **Document purpose:** This document converts the uploaded product requirements into an implementation-ready specification for a 2-person team over an 8-week MVP build.
>
> **Source basis:** Uploaded `AI Hiring & Screening Middleware.pdf` plus the previously agreed 8-week execution plan.
>
> **Important reading convention**
>
> - **PRD Requirement** = directly grounded in the uploaded product requirements.
> - **Implementation Decision** = an engineering choice added to make the PRD executable. These are recommendations, not claims that the source document mandated them.
>
> The MVP centers on company/job setup, configurable hiring pipelines, candidate application, resume/JD analysis, assessments, AI text interviews, evaluation, ranking, explainability, recruiter review, and human-controlled shortlisting.
>
> The 8-week plan intentionally excludes voice/video interviews, Kubernetes, custom LLM training, mobile apps, full ATS replacement, payroll/HRMS functionality, and other post-MVP scope.

---

# 1. Product Definition

## 1.1 Product

AI Hiring & Screening Middleware is a multi-tenant recruitment platform that orchestrates structured hiring workflows and AI-assisted screening.

The product should help recruiters:

1. Define a job and hiring requirements.
2. Configure a hiring pipeline.
3. Publish the role.
4. Receive candidate applications.
5. Parse and structure candidate resumes.
6. Apply hard eligibility gates.
7. Compute resume/JD fit.
8. Run assessments.
9. Conduct adaptive text-based AI interviews.
10. Evaluate candidates across configurable dimensions.
11. Produce normalized weighted scores.
12. Rank candidates with evidence.
13. Compare candidates side-by-side.
14. Route low-confidence or exceptional cases to humans.
15. Let recruiters make the final hiring decision.

## 1.2 Product Principle

The system is **decision support**, not autonomous hiring authority.

The final decision must remain with a human recruiter/hiring manager. AI outputs are recommendations with evidence and confidence, not irreversible hiring actions.

---

# 2. Goals and Success Criteria

## 2.1 MVP Goals

### Recruiter goals

- Create and publish jobs quickly.
- Convert natural-language JDs into structured requirements.
- Configure hiring pipelines without engineering support.
- See candidates ranked by configurable criteria.
- Understand *why* a candidate received a score.
- Identify uncertainty and route candidates for review.
- Compare multiple candidates using consistent metrics.

### Candidate goals

- Create a profile once.
- Upload a resume.
- Discover jobs.
- Apply with minimal repeated data entry.
- Complete assessments.
- Complete a text AI interview.
- Track application progress.

### Platform goals

- Multi-tenant isolation.
- Auditable scoring and evaluation.
- Structured AI outputs.
- Explainable recommendations.
- Asynchronous processing for expensive work.
- Reliable end-to-end pipeline execution.

## 2.2 MVP Success Metrics

The source PRD emphasizes candidate throughput, ranking quality, recruiter agreement, explainability, and end-to-end workflow reliability.

Recommended measurable implementation targets:

| Metric | MVP Target |
|---|---:|
| Resume parsing success on supported files | >= 95% |
| Job requirement extraction success | >= 90% usable fields |
| Structured scoring jobs completed successfully | >= 98% |
| Assessment auto-grading correctness | >= 99% for deterministic questions |
| AI output schema-validity after retries | >= 99% |
| Ranking reproducibility | 100% for identical inputs/config |
| Human-AI ranking agreement | Measure during evaluation; establish baseline before launch |
| Critical API 5xx rate | < 1% |
| End-to-end demo success | 100% for golden path |

---

# 3. Scope

## 3.1 In Scope

### Company / Recruiter

- Authentication
- Company account
- Recruiter/member roles
- Company dashboard
- Job creation
- JD analysis
- Requirement editing
- Pipeline builder
- Pipeline stage configuration
- Scoring configuration
- Job publishing
- Candidate list
- Candidate detail
- Candidate comparison
- Recruiter notes/feedback
- Shortlisting
- Auditability

### Candidate

- Registration/login
- Candidate profile
- Resume upload
- Resume parsing
- Job discovery
- Job detail
- Application
- Application status tracking
- Assessment
- AI text interview
- Interview completion
- Candidate-side status view

### AI

- JD analysis
- Resume parsing/normalization
- Hard eligibility evaluation
- Skill matching
- Semantic resume/JD matching
- LLM contextual validation
- Subjective assessment evaluation
- Adaptive text interview
- Interview response evaluation
- Candidate scoring
- Ranking
- Explainability
- Confidence estimation

### Infrastructure

- PostgreSQL
- pgvector
- Redis
- Celery
- S3
- Docker
- GitHub Actions
- Cloud deployment
- Logging/monitoring/error reporting

## 3.2 Explicitly Out of Scope

Do not let these consume MVP time:

- Voice interviews
- Video interviews
- Mobile applications
- Kubernetes
- Custom foundation-model training
- Full ATS replacement
- Payroll
- HRMS
- Large enterprise integrations
- Complex marketplace mechanics
- Autonomous hiring decisions

---

# 4. User Roles

| Role | Main Responsibilities |
|---|---|
| `COMPANY_ADMIN` | Company settings, members, jobs, pipelines, scoring |
| `RECRUITER` | Jobs, candidates, reviews, interviews, shortlists |
| `HIRING_MANAGER` | Candidate review, comparison, feedback, shortlist recommendations |
| `CANDIDATE` | Profile, applications, assessments, interviews |

## 4.1 Permission Model

Use RBAC with tenant boundaries.

### Company Admin

- Manage company
- Manage members
- CRUD jobs
- Configure pipeline
- Configure scoring
- View all company candidates
- Review audit logs

### Recruiter

- Create/edit jobs if permitted
- Publish jobs
- View candidates
- Review evaluations
- Add feedback
- Shortlist/reject

### Hiring Manager

- Read assigned jobs
- View candidate details
- Compare candidates
- Add feedback
- Participate in human review

### Candidate

- Own profile only
- Own resumes only
- Read published jobs
- Own applications only
- Complete assigned assessments/interviews
- Read allowed candidate-facing status

---

# 5. High-Level Architecture

```text
                           ┌───────────────────────┐
                           │       Browser         │
                           │   Recruiter /         │
                           │   Candidate UI        │
                           └──────────┬────────────┘
                                      │
                                      │ HTTPS
                                      ▼
                           ┌───────────────────────┐
                           │      Next.js App      │
                           │ UI + route guards     │
                           └──────────┬────────────┘
                                      │ REST/JSON
                                      ▼
                           ┌───────────────────────┐
                           │       FastAPI         │
                           │ API + Auth + RBAC     │
                           └──────┬───────┬────────┘
                                  │       │
                   ┌──────────────┘       └──────────────┐
                   ▼                                     ▼
          ┌──────────────────┐                  ┌─────────────────┐
          │   PostgreSQL     │                  │     Redis       │
          │   + pgvector     │                  │ Cache / Queue   │
          └───────┬──────────┘                  └────────┬────────┘
                  │                                      │
                  │                                      ▼
                  │                              ┌───────────────┐
                  │                              │ Celery Workers │
                  │                              └───────┬───────┘
                  │                                      │
                  │                        ┌─────────────┼─────────────┐
                  │                        ▼             ▼             ▼
                  │                  Resume Engine   Matching      AI Interview
                  │                  JD Analyzer     Engine         / Evaluation
                  │
                  ▼
          ┌──────────────────┐
          │       S3         │
          │ Resume / objects │
          └──────────────────┘

External AI Providers
       │
       ├── LLM API
       └── Embedding API
```

## 5.1 Architectural Principles

1. **Synchronous APIs should be fast.**
2. **Long-running AI/file work must be asynchronous.**
3. **PostgreSQL is the system of record.**
4. **pgvector stores semantic vectors alongside relational data.**
5. **Redis is not a source of truth.**
6. **S3 stores binary resumes and artifacts.**
7. **All AI outputs are schema-validated.**
8. **Candidate content is untrusted input.**
9. **AI actions are auditable.**
10. **Company boundaries are enforced at the service/query layer.**

---

# 6. Technology Stack

## 6.1 Frontend

| Area | Technology | Purpose |
|---|---|---|
| Framework | Next.js | Web application |
| Language | TypeScript | Type-safe frontend |
| Styling | Tailwind CSS | UI styling |
| Components | Reusable component library | Form/table/dialog primitives |
| Data fetching | TanStack Query | Server state |
| Forms | React Hook Form | Complex forms |
| Validation | Zod | Client/schema validation |
| Charts | Recharts | MVP analytics/score visuals |

## 6.2 Backend

| Area | Technology |
|---|---|
| API | FastAPI |
| Language | Python |
| ORM | SQLAlchemy |
| Validation | Pydantic |
| Migrations | Alembic |
| Auth | JWT/secure session architecture |
| API docs | OpenAPI generated by FastAPI |
| Background jobs | Celery |
| Broker/cache | Redis |
| File storage | AWS S3 |
| Database | PostgreSQL |
| Vector search | pgvector |

## 6.3 AI Layer

| Capability | Implementation |
|---|---|
| JD analysis | LLM with structured JSON output |
| Resume extraction | Parser + LLM normalization |
| Embeddings | Embedding model/API |
| Semantic matching | pgvector cosine similarity |
| Contextual reasoning | LLM |
| Subjective grading | LLM rubric evaluation |
| Interview | LLM with structured state |
| Ranking | Deterministic scoring service |
| Explainability | Evidence extraction + structured summaries |

## 6.4 DevOps

| Area | Technology |
|---|---|
| Packaging | Docker |
| CI/CD | GitHub Actions |
| Cloud | AWS |
| Compute | Container-capable service |
| DB | Managed PostgreSQL |
| Cache | Managed Redis where practical |
| Object storage | S3 |
| Logging | Cloud logging |
| Error monitoring | Sentry or equivalent |
| Secrets | Cloud secret manager / environment secrets |

> **Implementation decision:** Do not introduce Kubernetes for this 8-week MVP.

---

# 7. Repository Structure

```text
ai-hiring-middleware/
│
├── apps/
│   ├── web/
│   │   ├── app/
│   │   ├── components/
│   │   ├── features/
│   │   ├── lib/
│   │   ├── hooks/
│   │   └── types/
│   │
│   └── api/
│       ├── app/
│       │   ├── api/
│       │   ├── core/
│       │   ├── db/
│       │   ├── models/
│       │   ├── schemas/
│       │   ├── repositories/
│       │   ├── services/
│       │   ├── ai/
│       │   ├── workers/
│       │   └── utils/
│       └── tests/
│
├── packages/
│   ├── api-contracts/
│   └── config/
│
├── infra/
│   ├── docker/
│   ├── github/
│   └── aws/
│
├── docs/
│   ├── architecture.md
│   ├── api.md
│   ├── ai.md
│   ├── database.md
│   └── security.md
│
└── README.md
```

---

# 8. Environment Strategy

## 8.1 Environments

- `local`
- `staging`
- `production`

## 8.2 Required Environment Variables

```env
APP_ENV=
DATABASE_URL=
REDIS_URL=
S3_BUCKET=
AWS_REGION=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=

JWT_SECRET=
JWT_EXPIRY_MINUTES=

LLM_PROVIDER=
LLM_API_KEY=
LLM_MODEL=

EMBEDDING_PROVIDER=
EMBEDDING_API_KEY=
EMBEDDING_MODEL=

SENTRY_DSN=
```

Never commit secrets.

---

# 9. Core Domain Model

```text
Company
 ├── CompanyMember
 ├── Job
 │    ├── JobRequirement
 │    ├── HiringPipeline
 │    │    └── PipelineStage
 │    ├── Assessment
 │    └── Application
 │          ├── Resume
 │          ├── AssessmentAttempt
 │          ├── InterviewSession
 │          ├── Evaluation
 │          ├── Ranking
 │          └── RecruiterFeedback
 │
Candidate
 ├── CandidateProfile
 └── Resume
```

---

# 10. Database Schema

> The source PRD identifies the major entities. The fields below are an implementation-ready expansion.

## 10.1 `users`

```text
id UUID PK
email VARCHAR UNIQUE NOT NULL
password_hash TEXT NOT NULL
full_name VARCHAR
role ENUM NOT NULL
is_active BOOLEAN DEFAULT TRUE
created_at TIMESTAMP
updated_at TIMESTAMP
last_login_at TIMESTAMP NULL
```

Indexes:

- unique(email)
- role
- is_active

## 10.2 `companies`

```text
id UUID PK
name VARCHAR NOT NULL
slug VARCHAR UNIQUE NOT NULL
website VARCHAR NULL
industry VARCHAR NULL
size VARCHAR NULL
created_at TIMESTAMP
updated_at TIMESTAMP
```

## 10.3 `company_members`

```text
id UUID PK
company_id UUID FK companies.id
user_id UUID FK users.id
role ENUM
created_at TIMESTAMP
```

Unique:

```text
(company_id, user_id)
```

## 10.4 `candidate_profiles`

```text
id UUID PK
user_id UUID FK users.id
phone VARCHAR NULL
location VARCHAR NULL
headline VARCHAR NULL
summary TEXT NULL
experience_years NUMERIC NULL
education JSONB
skills JSONB
projects JSONB
links JSONB
created_at TIMESTAMP
updated_at TIMESTAMP
```

## 10.5 `resumes`

```text
id UUID PK
candidate_id UUID FK candidate_profiles.id
file_name VARCHAR
storage_key TEXT
mime_type VARCHAR
file_size BIGINT
file_hash VARCHAR
parse_status ENUM
parsed_text TEXT NULL
structured_data JSONB NULL
parser_version VARCHAR NULL
created_at TIMESTAMP
updated_at TIMESTAMP
```

`parse_status`:

```text
UPLOADED
PROCESSING
COMPLETED
FAILED
```

## 10.6 `jobs`

```text
id UUID PK
company_id UUID FK companies.id
created_by UUID FK users.id
title VARCHAR
department VARCHAR NULL
location VARCHAR NULL
employment_type VARCHAR NULL
experience_level VARCHAR NULL
salary_min NUMERIC NULL
salary_max NUMERIC NULL
currency VARCHAR NULL
description TEXT
status ENUM
published_at TIMESTAMP NULL
closing_at TIMESTAMP NULL
version INTEGER DEFAULT 1
created_at TIMESTAMP
updated_at TIMESTAMP
```

`status`:

```text
DRAFT
PUBLISHED
PAUSED
CLOSED
ARCHIVED
```

## 10.7 `job_requirements`

```text
id UUID PK
job_id UUID FK jobs.id
required_skills JSONB
preferred_skills JSONB
minimum_experience NUMERIC
education_requirements JSONB
certifications JSONB
seniority VARCHAR
responsibilities JSONB
normalized_requirements JSONB
ai_analysis_version VARCHAR
created_at TIMESTAMP
updated_at TIMESTAMP
```

## 10.8 `hiring_pipelines`

```text
id UUID PK
job_id UUID FK jobs.id
name VARCHAR
description TEXT NULL
is_active BOOLEAN
created_at TIMESTAMP
updated_at TIMESTAMP
```

## 10.9 `pipeline_stages`

```text
id UUID PK
pipeline_id UUID FK hiring_pipelines.id
name VARCHAR
stage_type ENUM
position INTEGER
is_required BOOLEAN
passing_score NUMERIC NULL
weight NUMERIC NULL
time_limit_seconds INTEGER NULL
max_attempts INTEGER NULL
configuration JSONB
created_at TIMESTAMP
updated_at TIMESTAMP
```

`stage_type`:

```text
APPLICATION
ELIGIBILITY
RESUME_SCREENING
ASSESSMENT
AI_INTERVIEW
HUMAN_REVIEW
SHORTLIST
FINAL_INTERVIEW
OFFER
HIRED
```

## 10.10 `applications`

```text
id UUID PK
job_id UUID FK jobs.id
candidate_id UUID FK candidate_profiles.id
pipeline_id UUID FK hiring_pipelines.id
current_stage_id UUID NULL
status ENUM
submitted_at TIMESTAMP
withdrawn_at TIMESTAMP NULL
rejected_at TIMESTAMP NULL
created_at TIMESTAMP
updated_at TIMESTAMP
```

Application states:

```text
APPLIED
ELIGIBILITY_CHECK
RESUME_SCREENING
ASSESSMENT
AI_INTERVIEW
HUMAN_REVIEW
SHORTLISTED
FINAL_INTERVIEW
OFFER
HIRED
REJECTED
WITHDRAWN
EXPIRED
ON_HOLD
```

Unique recommendation:

```text
(job_id, candidate_id)
```

unless the product later allows multiple applications to the same job.

## 10.11 `assessments`

```text
id UUID PK
job_id UUID FK jobs.id
pipeline_stage_id UUID FK pipeline_stages.id
name VARCHAR
description TEXT
duration_seconds INTEGER
passing_score NUMERIC
question_count INTEGER
configuration JSONB
created_at TIMESTAMP
updated_at TIMESTAMP
```

## 10.12 `questions`

```text
id UUID PK
assessment_id UUID FK assessments.id
question_text TEXT
question_type ENUM
skill_tag VARCHAR
difficulty ENUM
options JSONB NULL
correct_answer JSONB NULL
rubric JSONB NULL
explanation TEXT NULL
points NUMERIC
time_limit_seconds INTEGER NULL
position INTEGER
created_at TIMESTAMP
```

## 10.13 `assessment_attempts`

```text
id UUID PK
assessment_id UUID FK assessments.id
application_id UUID FK applications.id
attempt_number INTEGER
started_at TIMESTAMP
submitted_at TIMESTAMP NULL
status ENUM
raw_score NUMERIC NULL
normalized_score NUMERIC NULL
passed BOOLEAN NULL
created_at TIMESTAMP
```

## 10.14 `assessment_answers`

```text
id UUID PK
attempt_id UUID FK assessment_attempts.id
question_id UUID FK questions.id
answer JSONB
is_correct BOOLEAN NULL
auto_score NUMERIC NULL
ai_score NUMERIC NULL
feedback TEXT NULL
evaluation JSONB NULL
created_at TIMESTAMP
```

## 10.15 `interview_sessions`

```text
id UUID PK
application_id UUID FK applications.id
status ENUM
started_at TIMESTAMP
completed_at TIMESTAMP NULL
current_question_index INTEGER
max_questions INTEGER
context_snapshot JSONB
rubric JSONB
created_at TIMESTAMP
updated_at TIMESTAMP
```

## 10.16 `interview_messages`

```text
id UUID PK
session_id UUID FK interview_sessions.id
role ENUM
content TEXT
sequence_number INTEGER
question_metadata JSONB NULL
evaluation JSONB NULL
created_at TIMESTAMP
```

Roles:

```text
AI
CANDIDATE
SYSTEM
```

## 10.17 `evaluation_results`

```text
id UUID PK
application_id UUID FK applications.id
evaluation_type ENUM
source_id UUID NULL
score NUMERIC
dimensions JSONB
strengths JSONB
gaps JSONB
evidence JSONB
confidence NUMERIC
model_name VARCHAR NULL
model_version VARCHAR NULL
prompt_version VARCHAR NULL
created_at TIMESTAMP
```

## 10.18 `candidate_scores`

```text
id UUID PK
application_id UUID FK applications.id
resume_score NUMERIC
assessment_score NUMERIC
interview_score NUMERIC
communication_score NUMERIC
experience_score NUMERIC
final_score NUMERIC
score_breakdown JSONB
scoring_config_snapshot JSONB
calculated_at TIMESTAMP
```

## 10.19 `candidate_rankings`

```text
id UUID PK
job_id UUID FK jobs.id
application_id UUID FK applications.id
rank INTEGER
final_score NUMERIC
confidence NUMERIC
eligibility_passed BOOLEAN
ranking_version VARCHAR
calculated_at TIMESTAMP
```

Recommended unique constraint:

```text
(job_id, application_id)
```

## 10.20 `recruiter_feedback`

```text
id UUID PK
application_id UUID FK applications.id
user_id UUID FK users.id
rating INTEGER NULL
decision ENUM NULL
comment TEXT NULL
reason_codes JSONB NULL
created_at TIMESTAMP
updated_at TIMESTAMP
```

`decision`:

```text
NONE
ADVANCE
SHORTLIST
REJECT
ON_HOLD
```

## 10.21 `notifications`

```text
id UUID PK
user_id UUID FK users.id
type VARCHAR
title VARCHAR
body TEXT
data JSONB
read_at TIMESTAMP NULL
created_at TIMESTAMP
```

## 10.22 `audit_logs`

```text
id UUID PK
company_id UUID NULL
user_id UUID NULL
entity_type VARCHAR
entity_id UUID NULL
action VARCHAR
old_value JSONB NULL
new_value JSONB NULL
metadata JSONB NULL
created_at TIMESTAMP
```

Audit:

- Job publication
- Pipeline changes
- Scoring changes
- Candidate status changes
- Recruiter decisions
- AI evaluation generation
- Manual overrides

---

# 11. Database Indexes

Minimum indexes:

```text
users(email)

company_members(company_id)
company_members(user_id)

jobs(company_id, status)
jobs(company_id, created_at)

applications(job_id, status)
applications(candidate_id)
applications(job_id, candidate_id)

resumes(candidate_id)
resumes(parse_status)

pipeline_stages(pipeline_id, position)

assessment_attempts(application_id)
interview_sessions(application_id)

candidate_scores(application_id)
candidate_rankings(job_id, rank)
candidate_rankings(job_id, final_score)

audit_logs(company_id, created_at)
```

Vector index recommendation:

- pgvector vector column for resume/job embeddings
- Use an approximate nearest-neighbor index when dataset size warrants it
- Start with exact similarity in development for correctness tests

---

# 12. API Standards

## 12.1 Base URL

```text
/api/v1
```

## 12.2 Response Shape

Success:

```json
{
  "data": {},
  "meta": {}
}
```

Error:

```json
{
  "error": {
    "code": "JOB_NOT_FOUND",
    "message": "Job not found",
    "details": {}
  }
}
```

## 12.3 Pagination

```text
?page=1&page_size=20
```

Return:

```json
{
  "data": [],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 100
  }
}
```

## 12.4 IDs

Use UUIDs externally.

## 12.5 Dates

Use ISO 8601 UTC timestamps.

---

# 13. Authentication Routes

```http
POST   /auth/register
POST   /auth/login
POST   /auth/logout
POST   /auth/refresh
GET    /auth/me
POST   /auth/password/forgot
POST   /auth/password/reset
```

---

# 14. Company Routes

```http
POST   /companies
GET    /companies/{company_id}
PATCH  /companies/{company_id}

GET    /companies/{company_id}/members
POST   /companies/{company_id}/members
PATCH  /companies/{company_id}/members/{member_id}
DELETE /companies/{company_id}/members/{member_id}
```

---

# 15. Job Routes

```http
POST   /jobs
GET    /jobs
GET    /jobs/{job_id}
PATCH  /jobs/{job_id}
DELETE /jobs/{job_id}

POST   /jobs/{job_id}/analyze-jd
GET    /jobs/{job_id}/requirements
PATCH  /jobs/{job_id}/requirements

POST   /jobs/{job_id}/publish
POST   /jobs/{job_id}/pause
POST   /jobs/{job_id}/close
```

Candidate-public routes:

```http
GET /public/jobs
GET /public/jobs/{job_id}
```

---

# 16. Pipeline Routes

```http
POST   /jobs/{job_id}/pipeline
GET    /jobs/{job_id}/pipeline
PATCH  /pipelines/{pipeline_id}
DELETE /pipelines/{pipeline_id}

POST   /pipelines/{pipeline_id}/stages
PATCH  /pipelines/{pipeline_id}/stages/{stage_id}
DELETE /pipelines/{pipeline_id}/stages/{stage_id}
POST   /pipelines/{pipeline_id}/reorder
```

---

# 17. Candidate Routes

```http
GET    /candidates/me
PATCH  /candidates/me

POST   /candidates/me/resumes
GET    /candidates/me/resumes
GET    /candidates/me/resumes/{resume_id}
DELETE /candidates/me/resumes/{resume_id}

GET    /candidates/me/applications
GET    /candidates/me/applications/{application_id}
```

Recruiter routes:

```http
GET    /jobs/{job_id}/candidates
GET    /applications/{application_id}
PATCH  /applications/{application_id}/status
POST   /applications/{application_id}/notes
POST   /applications/{application_id}/shortlist
POST   /applications/{application_id}/reject
POST   /applications/{application_id}/hold
```

---

# 18. Application Routes

```http
POST /jobs/{job_id}/apply
GET  /applications/{application_id}
GET  /applications/{application_id}/timeline
```

Application submission should validate:

- candidate authentication
- job is published
- candidate has required profile fields
- resume available if required
- candidate has not already applied

---

# 19. Resume Intelligence Routes

```http
POST /resumes/{resume_id}/parse
GET  /resumes/{resume_id}/status
GET  /resumes/{resume_id}/parsed-data

POST /applications/{application_id}/screen
GET  /applications/{application_id}/screening

POST /applications/{application_id}/match
GET  /applications/{application_id}/match
```

These actions should usually enqueue background jobs.

---

# 20. Assessment Routes

Recruiter:

```http
POST   /assessments
GET    /assessments/{assessment_id}
PATCH  /assessments/{assessment_id}
DELETE /assessments/{assessment_id}

POST   /assessments/{assessment_id}/questions
PATCH  /questions/{question_id}
DELETE /questions/{question_id}
```

Candidate:

```http
POST /applications/{application_id}/assessment/start
GET  /attempts/{attempt_id}
POST /attempts/{attempt_id}/answers
POST /attempts/{attempt_id}/submit
GET  /attempts/{attempt_id}/result
```

---

# 21. Interview Routes

```http
POST /applications/{application_id}/interview/start
GET  /interviews/{interview_id}
GET  /interviews/{interview_id}/messages
POST /interviews/{interview_id}/messages
POST /interviews/{interview_id}/complete
GET  /interviews/{interview_id}/result
```

The interview should store enough structured state to resume safely after network interruption.

---

# 22. Evaluation Routes

```http
GET /applications/{application_id}/evaluations
GET /applications/{application_id}/evaluations/{evaluation_id}

POST /applications/{application_id}/evaluate/resume
POST /applications/{application_id}/evaluate/assessment
POST /applications/{application_id}/evaluate/interview
POST /applications/{application_id}/score/recalculate
```

---

# 23. Ranking Routes

```http
POST /jobs/{job_id}/rankings/recalculate
GET  /jobs/{job_id}/rankings
GET  /jobs/{job_id}/rankings/{application_id}
GET  /jobs/{job_id}/compare?application_ids=a,b,c
```

---

# 24. Frontend Information Architecture

```text
/
├── login
├── register
│
├── candidate/
│   ├── dashboard
│   ├── profile
│   ├── resume
│   ├── jobs
│   ├── jobs/[jobId]
│   ├── applications
│   ├── applications/[applicationId]
│   ├── assessment/[attemptId]
│   └── interview/[interviewId]
│
└── company/
    ├── dashboard
    ├── jobs
    ├── jobs/new
    ├── jobs/[jobId]
    ├── jobs/[jobId]/edit
    ├── jobs/[jobId]/pipeline
    ├── jobs/[jobId]/candidates
    ├── jobs/[jobId]/rankings
    ├── jobs/[jobId]/compare
    ├── candidates/[applicationId]
    ├── assessments
    ├── assessments/[assessmentId]
    ├── settings
    └── audit
```

---

# 25. Frontend Global Elements

## 25.1 Common

- Responsive shell
- Header
- Sidebar
- Breadcrumbs
- Page title
- Toasts
- Modal/dialog
- Confirmation dialog
- Loading skeletons
- Empty states
- Error states
- Pagination
- Search
- Filters
- Sort controls
- Status badges

## 25.2 AI-specific UX

Never show AI output as if it were unquestionable truth.

Every major AI result should support:

- score
- confidence
- explanation
- evidence
- model/prompt version where appropriate
- last calculated time
- human review status

---

# 26. Recruiter Pages

## 26.1 Company Dashboard

Widgets:

- Active jobs
- Candidates in progress
- Assessment completions
- Interviews pending
- Candidates awaiting human review
- Recent activity

## 26.2 Job List

Columns:

```text
Job
Status
Applications
Shortlisted
Last Updated
Actions
```

## 26.3 Create Job

Sections:

### Basic information

- Job title
- Department
- Location
- Employment type
- Experience
- Compensation

### JD

- Text editor
- Paste/import JD
- Analyze button

### Requirements

- Required skills
- Preferred skills
- Education
- Experience
- Certifications
- Seniority

### Pipeline

- Stage editor
- Ordering
- Required/optional
- Pass scores
- Time limits

### Scoring

- Weight sliders/inputs
- Validation that weights sum to 100

## 26.4 Candidate Ranking Page

Main table:

```text
Rank
Candidate
Eligibility
Final Score
Confidence
Resume
Assessment
Interview
Status
Action
```

Filters:

- Score range
- Eligibility
- Pipeline stage
- Assessment passed
- Interview completed
- Confidence
- Status
- Skills

## 26.5 Candidate Detail

Sections:

1. Overview
2. Resume
3. Skill match
4. Resume score
5. Assessment
6. Interview
7. Final score
8. Strengths
9. Gaps
10. Evidence
11. AI confidence
12. Recruiter feedback
13. Application timeline
14. Actions

Actions:

```text
Shortlist
Advance
Reject
Hold
Request Human Review
```

## 26.6 Candidate Comparison

Show candidates as columns.

Rows:

- Eligibility
- Required skill match
- Preferred skill match
- Experience
- Resume fit
- Assessment
- Interview
- Communication
- Final score
- Confidence
- Strengths
- Gaps

---

# 27. Candidate Pages

## 27.1 Candidate Dashboard

Widgets:

- Profile completeness
- Recommended/open jobs
- Active applications
- Assessments pending
- Interviews pending
- Recent application updates

## 27.2 Profile

Sections:

- Personal
- Summary
- Skills
- Experience
- Education
- Projects
- Certifications
- GitHub/LinkedIn/portfolio

## 27.3 Resume

- Upload
- Replace
- View
- Parse status
- Parsed data preview
- Parsing error message
- Last updated time

## 27.4 Jobs

Filters:

- Keyword
- Location
- Experience
- Employment type

Job card:

- Title
- Company
- Location
- Experience
- Skills
- Apply CTA

## 27.5 Application Details

Show:

```text
Applied
  ↓
Screening
  ↓
Assessment
  ↓
Interview
  ↓
Human Review
  ↓
Decision
```

Candidate-facing status must not expose internal recruiter-only details.

---

# 28. Assessment UI

## Components

- Progress indicator
- Timer
- Question card
- Answer controls
- Next/previous
- Submit button
- Auto-save indicator
- Confirmation dialog
- Time-expired handler

Supported initial question types:

- MCQ
- Multiple choice
- True/false
- Numerical
- Subjective

---

# 29. Interview UI

## Candidate

```text
Interview header
Progress
Conversation panel
Candidate answer input
Send
Typing/loading state
End interview state
```

## Recruiter

Read-only transcript plus:

- per-answer evaluation
- dimension scores
- overall interview score
- strengths
- concerns
- confidence
- evidence

---

# 30. AI Engine Architecture

```text
                     AI Orchestrator
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
      JD Analyzer     Resume Engine    Interview Engine
          │                │                │
          ▼                ▼                ▼
     Requirement      Parser +           Question
     extraction       normalization      generation
                           │                │
                           ▼                ▼
                     Embeddings         Evaluation
                           │                │
                           └───────┬────────┘
                                   ▼
                              Scoring Engine
                                   │
                                   ▼
                              Ranking Engine
                                   │
                                   ▼
                            Explainability
```

---

# 31. AI Design Rules

## 31.1 Structured outputs only

LLM calls should use schemas.

Example:

```json
{
  "required_skills": [
    {
      "name": "Python",
      "importance": 1.0
    }
  ],
  "preferred_skills": [],
  "minimum_experience_years": 1,
  "seniority": "Junior"
}
```

Reject malformed results.

Retry with a constrained prompt.

Do not let free-form model text directly drive business logic.

---

# 32. JD Analyzer

## Input

- JD text
- Optional company/job metadata

## Output

- Role
- Responsibilities
- Required skills
- Preferred skills
- Experience
- Education
- Certifications
- Seniority
- Hard constraints
- Nice-to-have requirements

## Flow

```text
JD text
  ↓
clean/normalize
  ↓
LLM structured extraction
  ↓
schema validation
  ↓
persist draft requirements
  ↓
recruiter edits
  ↓
save final requirements
```

## Important rule

AI proposes requirements.

Recruiter confirms them.

The final saved requirement set becomes the authoritative hiring configuration.

---

# 33. Resume Engine

## Step 1: File validation

Supported initial formats:

- PDF
- DOCX

Validate:

- extension
- MIME type
- size
- file hash

## Step 2: Text extraction

```text
file
 ↓
extract text
 ↓
normalize whitespace
 ↓
remove irrelevant artifacts
```

## Step 3: Structured extraction

Output:

```json
{
  "candidate_name": "",
  "summary": "",
  "skills": [],
  "experience": [],
  "education": [],
  "projects": [],
  "certifications": [],
  "links": []
}
```

## Step 4: Persist

Store:

- raw text
- structured data
- parser version
- status

---

# 34. Hard Eligibility Engine

Hard constraints are evaluated before ranking.

Examples:

```text
minimum experience
mandatory skill
required certification
required degree
work authorization requirement if explicitly configured
```

Output:

```json
{
  "eligible": true,
  "checks": [
    {
      "requirement": "Python",
      "passed": true,
      "evidence": ["Resume skill section"]
    }
  ]
}
```

A failed hard constraint should prevent normal advancement unless the recruiter explicitly overrides it.

---

# 35. Semantic Matching Engine

Use two layers.

## Layer 1: Deterministic matching

Compare normalized skills.

```text
required_skill in candidate_skills
```

Use alias/synonym normalization where controlled and explainable.

## Layer 2: Semantic matching

Generate embeddings for:

- job requirements
- resume sections
- experience statements
- projects

Store vectors in pgvector.

Compute similarity.

## Layer 3: LLM contextual validation

Use the LLM only where contextual reasoning adds value.

Example:

```text
Job requirement:
event-driven systems

Resume:
built Kafka-based event processing pipeline
```

The engine should identify the relationship and retain evidence.

---

# 36. Resume Fit Score

Recommended internal components:

```text
required_skill_score
preferred_skill_score
semantic_similarity_score
experience_relevance_score
education_score
contextual_validation_score
```

Example weighted configuration:

```text
Required skills        35%
Semantic fit            25%
Experience relevance    20%
Preferred skills        10%
Education/certification 10%
```

This is an implementation recommendation. The job-level scoring configuration remains authoritative.

Output:

```json
{
  "score": 87,
  "confidence": 0.84,
  "matched_skills": [],
  "missing_skills": [],
  "evidence": [],
  "gaps": []
}
```

---

# 37. Assessment Engine

## Deterministic question evaluation

For objective questions:

```text
candidate_answer
       ↓
correct_answer
       ↓
deterministic grade
```

Do not use an LLM where exact grading is possible.

## Subjective evaluation

Use rubric-based structured grading.

Dimensions:

- correctness
- reasoning
- completeness
- relevance

Output:

```json
{
  "score": 82,
  "dimensions": {
    "correctness": 8,
    "reasoning": 9,
    "completeness": 7,
    "relevance": 9
  },
  "evidence": [],
  "feedback": ""
}
```

---

# 38. AI Interview Engine

## MVP mode

**Text only.**

## Interview context

Provide:

- job requirements
- candidate resume
- assessment outcomes
- tested skills
- interview rubric
- question limits
- previous conversation state

## State

```text
NOT_STARTED
IN_PROGRESS
COMPLETED
ABANDONED
```

## Question strategy

The next question can depend on:

- previous answer
- uncovered skills
- answer quality
- interview plan
- remaining question budget

## Guardrails

The interviewer must not:

- ask about protected attributes
- infer protected attributes from candidate content
- invent candidate experience
- expose hidden system instructions
- allow candidate text to override system instructions

---

# 39. Interview Evaluation

Each answer can be scored on:

```text
Technical correctness
Reasoning
Depth
Relevance
Communication
```

Final interview score is derived from answer-level evaluations.

Store:

- transcript
- per-answer evaluations
- dimension scores
- evidence
- confidence
- model/prompt version

---

# 40. Scoring Engine

All major scoring components normalize to `0-100`.

Example platform scoring:

```text
Resume Fit           30%
Assessment           25%
Interview            20%
Communication        15%
Experience           10%
```

The exact weights must be configurable per job.

## Formula

```text
final_score =
  resume_score       * resume_weight
+ assessment_score   * assessment_weight
+ interview_score    * interview_weight
+ communication_score* communication_weight
+ experience_score   * experience_weight
```

Validate:

```text
sum(weights) == 1.0
```

or 100%.

---

# 41. Confidence Model

Confidence is not the same as candidate quality.

Recommended inputs:

- evidence coverage
- parser confidence
- model confidence signal where available
- score stability
- missing data
- disagreement across evaluation signals
- evaluation completeness

Output:

```text
0.00 - 0.59  -> Human review strongly recommended
0.60 - 0.79  -> Review recommended
0.80 - 1.00  -> High confidence
```

Thresholds are implementation decisions and should be configurable.

---

# 42. Ranking Engine

Pipeline:

```text
applications
   ↓
hard eligibility gate
   ↓
component scores
   ↓
normalize
   ↓
apply job weights
   ↓
compute final score
   ↓
compute confidence
   ↓
sort
   ↓
assign rank
```

Tie-breaking recommendation:

1. higher final score
2. higher eligibility confidence
3. higher assessment score
4. lower unresolved gap count
5. deterministic candidate/application UUID as final stable tie-breaker

Do not use random tie-breaking.

---

# 43. Explainability

Each candidate report should answer:

### What is the score?

```text
Final Score: 87
```

### Why?

```text
Resume Fit: 91
Assessment: 82
Interview: 88
Experience: 85
Communication: 80
```

### What matched?

```text
Python
FastAPI
PostgreSQL
REST APIs
```

### What is missing?

```text
Kubernetes
Advanced distributed systems
```

### What evidence supports the score?

Reference the actual candidate/job material used for evaluation.

### How certain is the system?

```text
Confidence: 84%
```

### Does a human need to review?

```text
Human Review: Recommended
```

---

# 44. Prompt Architecture

Store prompt templates in versioned files.

```text
apps/api/app/ai/prompts/
├── jd_analyzer/
│   └── v1.txt
├── resume_extractor/
│   └── v1.txt
├── contextual_match/
│   └── v1.txt
├── subjective_grader/
│   └── v1.txt
├── interview_questioner/
│   └── v1.txt
├── interview_evaluator/
│   └── v1.txt
└── explainability/
    └── v1.txt
```

Never silently change prompts in production.

Every AI result should retain:

```text
model_name
model_version
prompt_version
generated_at
```

---

# 45. Prompt Injection Defense

Treat candidate content as data.

Unsafe:

```text
SYSTEM PROMPT + raw candidate text concatenated
```

Safer structure:

```text
System instructions
Developer/business rules
Structured job data
Structured candidate data
Explicitly marked untrusted candidate text
```

Candidate content must never be allowed to redefine:

- scoring rules
- role permissions
- system instructions
- output schema
- business policy

---

# 46. AI Data Flow

## Resume

```text
Candidate
 ↓
S3
 ↓
Async parse task
 ↓
Text extraction
 ↓
Structured extraction
 ↓
Embedding generation
 ↓
Persistence
```

## JD

```text
Recruiter
 ↓
JD text
 ↓
Analyze task
 ↓
Structured requirements
 ↓
Recruiter edits
 ↓
Persist
```

## Match

```text
Resume vectors + JD vectors
 ↓
Similarity
 ↓
Deterministic skill match
 ↓
LLM contextual validation
 ↓
Resume fit result
```

## Interview

```text
Candidate
 ↓
start session
 ↓
load context
 ↓
generate question
 ↓
candidate answer
 ↓
evaluate answer
 ↓
adapt next question
 ↓
complete
 ↓
aggregate interview score
```

---

# 47. Background Jobs

Minimum Celery tasks:

```text
parse_resume
analyze_job_description
generate_resume_embeddings
generate_job_embeddings
calculate_resume_match
evaluate_subjective_answer
generate_interview_question
evaluate_interview_answer
finalize_interview
calculate_application_score
recalculate_job_rankings
send_notification
```

## Job principles

- Idempotent where possible
- Retry transient provider errors
- Persist job status
- Record failure reason
- Avoid duplicate evaluation
- Make model calls traceable

---

# 48. Task Status Model

```text
PENDING
RUNNING
SUCCEEDED
FAILED
RETRYING
```

Store execution metadata:

```text
task_id
task_type
entity_id
attempt_count
started_at
completed_at
error_code
error_message
```

---

# 49. End-to-End Hiring Workflow

```text
Company registers
      ↓
Create job
      ↓
Analyze JD
      ↓
Recruiter confirms requirements
      ↓
Create pipeline
      ↓
Configure score weights
      ↓
Publish job
      ↓
Candidate registers
      ↓
Candidate profile/resume
      ↓
Candidate applies
      ↓
Eligibility check
      ↓
Resume screening
      ↓
Assessment
      ↓
AI interview
      ↓
Evaluation
      ↓
Weighted score
      ↓
Ranking
      ↓
Recruiter review
      ↓
Shortlist / Reject / Hold
```

---

# 50. Application State Machine

```text
APPLIED
  |
  v
ELIGIBILITY_CHECK
  |
  v
RESUME_SCREENING
  |
  v
ASSESSMENT
  |
  v
AI_INTERVIEW
  |
  v
HUMAN_REVIEW
  |        \
  |         \
  v          v
SHORTLISTED REJECTED
  |
  v
FINAL_INTERVIEW
  |
  v
OFFER
  |
  v
HIRED
```

Alternative exits:

```text
WITHDRAWN
ON_HOLD
EXPIRED
```

The backend must reject invalid state transitions.

---

# 51. Notifications

MVP notification events:

- Application received
- Assessment assigned
- Assessment reminder
- Assessment completed
- Interview available
- Interview completed
- Human review requested
- Application state updated

Start with in-app notifications.

Email can be added using the same event abstraction.

---

# 52. Security Requirements

## Authentication

- Secure password hashing
- Short-lived access token/session
- Refresh strategy
- Logout invalidation strategy
- Password reset flow

## Authorization

Every protected request must check:

1. authenticated user
2. role
3. company membership
4. resource ownership/tenant
5. action permission

## Multi-tenancy

Every company-scoped query must filter by:

```text
company_id
```

Do not trust frontend-provided company IDs.

Resolve tenant from the authenticated user's membership.

## Object storage

Use:

- private S3 bucket
- short-lived signed URLs
- server-side metadata
- no permanent public resume URLs

## Input security

Validate:

- file type
- file size
- JSON payloads
- query params
- route IDs

## AI security

Protect against:

- prompt injection
- output schema corruption
- fabricated evidence
- protected-attribute reasoning
- data leakage
- unauthorized tool usage

---

# 53. Privacy Requirements

Candidate data includes resumes, profiles, assessments, interview transcripts and evaluation results.

Minimum MVP requirements:

- strict tenant isolation
- least-privilege access
- private object storage
- audit logs
- configurable retention path
- deletion workflow
- no unnecessary PII in prompts
- logging that avoids raw sensitive payloads where possible

---

# 54. Observability

## Application metrics

- request count
- latency
- error rate
- authentication failures
- queue depth
- task duration

## AI metrics

- token usage
- cost per task if provider reports it
- invalid output rate
- retry rate
- model failure rate
- evaluation confidence
- latency

## Product metrics

- jobs published
- applications submitted
- screening completion
- assessment completion
- interview completion
- shortlist rate
- human-review rate

---

# 55. Logging

Use structured JSON logs.

Example:

```json
{
  "timestamp": "2026-09-02T12:00:00Z",
  "level": "INFO",
  "service": "matching",
  "request_id": "uuid",
  "company_id": "uuid",
  "application_id": "uuid",
  "event": "resume_match_completed",
  "score": 87,
  "confidence": 0.84
}
```

Never log:

- passwords
- access tokens
- secret keys
- unnecessary raw resumes
- complete sensitive candidate content

---

# 56. Error Handling

## API

Use typed error codes:

```text
AUTH_INVALID_CREDENTIALS
FORBIDDEN
RESOURCE_NOT_FOUND
VALIDATION_ERROR
JOB_NOT_PUBLISHED
ALREADY_APPLIED
ASSESSMENT_EXPIRED
INTERVIEW_COMPLETED
AI_PROVIDER_ERROR
AI_OUTPUT_INVALID
FILE_UNSUPPORTED
FILE_TOO_LARGE
```

## AI provider failures

Retry transient errors.

Do not indefinitely retry deterministic validation failures.

Fallback behavior:

```text
AI failure
 ↓
retry
 ↓
still fails
 ↓
mark task failed
 ↓
surface actionable error
 ↓
allow retry/manual review
```

---

# 57. Testing Strategy

## 57.1 Unit Tests

Test:

- scoring
- ranking
- normalization
- weight validation
- eligibility gates
- state transitions
- permission checks
- parser normalization
- deterministic grading

## 57.2 Integration Tests

Test:

- auth + DB
- job creation
- application creation
- S3 metadata flow
- background jobs
- assessment submission
- interview state persistence
- ranking recalculation

## 57.3 E2E Tests

Golden path:

```text
register company
→ create job
→ publish job
→ register candidate
→ upload resume
→ apply
→ screening
→ assessment
→ interview
→ ranking
→ recruiter review
→ shortlist
```

## 57.4 AI Evaluation Tests

Create a fixed dataset of:

- representative JDs
- representative resumes
- subjective answers
- interview responses

Compare:

- human labels
- AI results
- score consistency
- evidence quality
- ranking stability

---

# 58. Golden Demo Dataset

Prepare:

### Jobs

3 jobs:

- Backend Engineer
- Frontend Engineer
- ML Engineer

### Candidates

At least:

- 20 candidate profiles
- 20 resumes
- varied experience
- strong matches
- weak matches
- borderline cases
- incomplete profiles

### Assessment

- 10 questions
- mix of deterministic and subjective questions

### Interview

- 5-8 questions per candidate

This dataset should intentionally contain edge cases.

---

# 59. Edge Cases to Test

## Candidate

- duplicate application
- missing resume
- corrupted file
- empty profile
- unsupported file type
- extremely large resume
- duplicate resume
- withdraw during pipeline

## Assessment

- timeout
- browser refresh
- double submit
- multiple attempts
- incomplete answers
- network failure

## Interview

- refresh
- reconnect
- model timeout
- empty answer
- repeated answer
- candidate attempts prompt injection
- max question limit reached

## Ranking

- score ties
- missing component score
- failed eligibility
- changed scoring weights
- candidate added after ranking
- candidate withdrawn
- manual override

---

# 60. API Security Checklist

For every route verify:

```text
[ ] Authentication required
[ ] Correct role required
[ ] Tenant verified
[ ] Resource belongs to tenant
[ ] Input validated
[ ] Output filtered
[ ] Audit event where required
```

---

# 61. AI Output Contract Checklist

Every AI feature should define:

```text
[ ] Input schema
[ ] System instruction
[ ] Business rules
[ ] Output schema
[ ] Validation
[ ] Retry policy
[ ] Failure handling
[ ] Model name
[ ] Prompt version
[ ] Test cases
```

---

# 62. Phase-Wise Development Plan

# Phase 0 - Product and Architecture Freeze
### Week 1, Days 1-2

## Deliverables

- Scope frozen
- Roles defined
- Architecture finalized
- Database ERD
- API conventions
- AI boundaries
- UI information architecture
- threat model
- repository initialized

## Acceptance criteria

- Team can explain every core entity.
- Every MVP workflow has an owner.
- No unresolved architectural blockers remain.

---

# Phase 1 - Platform Foundation
### Week 1, Days 3-7

## Backend

- FastAPI project
- SQLAlchemy models
- Alembic
- PostgreSQL
- Redis
- Celery
- Auth
- RBAC
- company membership

## Frontend

- Next.js
- app shell
- login
- registration
- route protection
- candidate/company layouts

## Acceptance

```text
Company registration works
Candidate registration works
Login works
Role-specific navigation works
DB migrations work
Background worker runs
```

---

# Phase 2 - Company Hiring System
### Week 2

## Backend

- jobs CRUD
- requirements CRUD
- JD analysis task
- pipeline CRUD
- pipeline stage CRUD
- scoring config

## Frontend

- recruiter dashboard
- job list
- create job
- JD editor
- requirement editor
- pipeline builder
- scoring configuration
- publish action

## Acceptance

```text
Recruiter
→ creates job
→ analyzes JD
→ edits requirements
→ builds pipeline
→ configures weights
→ publishes
```

---

# Phase 3 - Candidate Platform
### Week 3

## Backend

- candidate profile
- resume metadata
- S3 upload
- applications
- application state machine
- public job routes

## Frontend

- candidate dashboard
- profile
- resume upload
- job search
- job detail
- apply flow
- application status

## Acceptance

```text
Candidate
→ finds published job
→ uploads resume
→ applies
→ sees application status
```

---

# Phase 4 - Resume Intelligence
### Week 4

## Backend/AI

- PDF/DOCX extraction
- structured resume extraction
- embeddings
- pgvector
- eligibility engine
- semantic matching
- contextual validation
- resume fit score
- evidence generation

## Frontend

- parse status
- resume preview
- matched/missing skill UI
- screening result
- score breakdown

## Acceptance

Given a candidate and job:

```text
resume
→ parsed profile
→ eligibility
→ fit score
→ evidence
```

---

# Phase 5 - Assessment Engine
### Week 5

## Backend

- question bank
- assessment CRUD
- attempts
- answer storage
- deterministic grading
- subjective evaluation
- timers
- attempt limits

## Frontend

- assessment builder
- candidate assessment runner
- results page
- recruiter assessment report

## Acceptance

Candidate can:

```text
start
→ answer
→ submit
→ receive/store score
```

Recruiter can inspect the result.

---

# Phase 6 - AI Text Interview
### Week 6

## Backend/AI

- interview sessions
- transcript persistence
- interview context
- question generator
- response evaluator
- interview aggregate score
- confidence

## Frontend

- interview screen
- transcript
- candidate answer UI
- completion state
- recruiter transcript/report

## Acceptance

```text
Start interview
→ AI question
→ candidate answer
→ evaluation
→ next question
→ complete
→ report
```

---

# Phase 7 - Ranking and Recruiter Intelligence
### Week 7

## Backend

- normalization
- weighted score
- ranking
- confidence
- explainability
- compare endpoint
- shortlist/hold/reject

## Frontend

- ranking table
- filters
- sorting
- candidate detail
- score breakdown
- evidence
- candidate comparison
- decision actions

## Acceptance

Recruiter sees:

```text
all candidates
→ eligibility
→ scores
→ ranking
→ evidence
→ confidence
→ comparison
→ shortlist
```

---

# Phase 8 - Hardening and Deployment
### Week 8

## Security

- tenant isolation tests
- RBAC tests
- prompt injection tests
- signed URLs
- secrets handling
- audit logs

## Testing

- unit tests
- integration tests
- E2E golden path
- AI evaluation dataset

## Infrastructure

- Docker
- staging
- production
- CI/CD
- monitoring
- error reporting

## Acceptance

The entire golden flow works in a deployed environment with:

- no critical security issue
- no unresolved P0/P1 defects
- reproducible ranking
- visible explanations
- recoverable AI failures

---

# 63. Developer 1 Ownership

Primary ownership:

- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Auth/RBAC
- company/job APIs
- application APIs
- assessment backend
- Redis
- Celery
- S3
- Docker
- AWS
- CI/CD
- security
- observability

Shared ownership:

- API contracts
- DB design
- integration
- testing

---

# 64. Developer 2 Ownership

Primary ownership:

- Next.js
- recruiter UI
- candidate UI
- JD analyzer
- resume parser
- embeddings
- semantic matching
- AI interview
- evaluation
- ranking
- explainability

Shared ownership:

- AI evaluation dataset
- integration
- architecture
- testing
- deployment

---

# 65. Definition of Done

A feature is not done when the code runs locally.

It is done when:

```text
[ ] backend implemented
[ ] DB migration exists
[ ] API documented
[ ] permission checks exist
[ ] frontend integrated
[ ] loading state exists
[ ] error state exists
[ ] audit event exists if required
[ ] tests exist
[ ] logs/metrics exist where relevant
[ ] deployed in staging
```

---

# 66. MVP Release Checklist

## Product

```text
[ ] Company registration
[ ] Candidate registration
[ ] Job creation
[ ] JD analysis
[ ] Pipeline builder
[ ] Scoring configuration
[ ] Job publish
[ ] Job search
[ ] Application
[ ] Resume parsing
[ ] Eligibility
[ ] Resume matching
[ ] Assessment
[ ] AI interview
[ ] Evaluation
[ ] Ranking
[ ] Explainability
[ ] Candidate comparison
[ ] Shortlist
```

## Security

```text
[ ] RBAC
[ ] Tenant isolation
[ ] Private S3
[ ] Signed URLs
[ ] Secrets protection
[ ] Audit logs
[ ] Prompt injection defenses
```

## Reliability

```text
[ ] retries
[ ] idempotency
[ ] task status
[ ] error reporting
[ ] monitoring
[ ] backup strategy
```

## Testing

```text
[ ] unit
[ ] integration
[ ] E2E
[ ] AI evaluation
[ ] security
```

---

# 67. Final MVP Golden Path

The finished system should demonstrate this exact scenario:

```text
                 COMPANY
                    |
              Create Job
                    |
             Analyze JD with AI
                    |
          Confirm Requirements
                    |
            Build Hiring Pipeline
                    |
            Configure Score Weights
                    |
               Publish Job
                    |
                    v
                 CANDIDATE
                    |
              Create Profile
                    |
               Upload Resume
                    |
                  Apply
                    |
                    v
              ELIGIBILITY GATE
                    |
                    +---- FAIL ----> Rejected / Review
                    |
                   PASS
                    |
                    v
             RESUME SCREENING
                    |
            Fit Score + Evidence
                    |
                    v
                ASSESSMENT
                    |
              Score + Feedback
                    |
                    v
               AI INTERVIEW
                    |
          Adaptive Questions + Eval
                    |
                    v
             SCORING ENGINE
                    |
           Weighted Final Score
                    |
                    v
             RANKING ENGINE
                    |
        Rank + Confidence + Evidence
                    |
                    v
            RECRUITER DASHBOARD
                    |
              Compare Candidates
                    |
          Human Decision / Shortlist
```

---

# 68. Engineering Decisions That Must Stay Explicit

These are not guaranteed by the source PRD; they are implementation decisions that the team should either adopt or revise before coding:

1. REST/JSON API rather than GraphQL.
2. Next.js + TypeScript + Tailwind.
3. FastAPI + SQLAlchemy + Alembic.
4. PostgreSQL + pgvector.
5. Redis + Celery.
6. S3 for resumes.
7. UUIDs for public IDs.
8. Asynchronous AI/file processing.
9. Versioned prompts.
10. Structured AI output validation.
11. Stable deterministic ranking tie-breaks.
12. Confidence thresholds configurable per deployment/job.
13. No Kubernetes for MVP.
14. Text-only AI interview for MVP.
15. Human final decision remains mandatory.
16. In-app notifications first.

---

# 69. Recommended Build Order Inside the Codebase

Do not build screens randomly.

Build in vertical slices:

### Slice 1

```text
Auth
→ Company/Candidate
→ Dashboard
```

### Slice 2

```text
Job
→ JD
→ Publish
```

### Slice 3

```text
Candidate
→ Resume
→ Application
```

### Slice 4

```text
Resume
→ Parse
→ Match
→ Score
```

### Slice 5

```text
Assessment
→ Attempt
→ Grade
```

### Slice 6

```text
Interview
→ Conversation
→ Evaluation
```

### Slice 7

```text
Score
→ Rank
→ Explain
→ Recruiter decision
```

### Slice 8

```text
Secure
→ Test
→ Observe
→ Deploy
```

This keeps the product continuously demoable instead of creating seven beautiful unfinished subsystems, humanity's favorite way to manufacture software disappointment.

---

# 70. Phase Completion Rule

A phase is complete only when its output is usable by the next phase.

For example:

### Resume phase is not complete when:

```text
"the parser returns JSON"
```

It is complete when:

```text
resume upload
→ background processing
→ structured candidate data
→ stored result
→ matching service consumes it
→ recruiter sees it
```

Apply the same rule to every phase.

---

# 71. MVP Release Outcome

At MVP completion, the project must demonstrate that it can take a published job and a set of applicants through:

```text
structured job requirements
→ candidate intake
→ resume intelligence
→ eligibility
→ assessment
→ AI interview
→ evaluation
→ configurable scoring
→ ranking
→ explainability
→ recruiter review
→ human shortlist
```

That end-to-end chain is the product.

