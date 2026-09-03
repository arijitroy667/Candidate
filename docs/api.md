# API

All backend endpoints are REST/JSON under `/api/v1`.

Assessment endpoints currently include:

- `POST /assessments`, `GET /assessments`, `GET /assessments/{id}`
- `POST /question-banks`
- `POST /assessments/{id}/questions`
- `POST /applications/{application_id}/assessment/{assessment_id}/start`
- `GET /assessment-attempts/{id}`
- `POST /assessment-attempts/{id}/submit`
- `GET /assessment-attempts/{id}/result`

MCQ and true/false answers are graded synchronously. Subjective and coding answers are persisted as `PENDING_REVIEW`; coding test cases are ready for a sandbox runner integration.
