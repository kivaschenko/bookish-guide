# Multi-User MVP Architecture Design

## Overview
Transforming StoryForge from single-user to multi-user system with Vue.js frontend, JWT authentication, and SQLAlchemy/SQLite backend.

## Architecture Components

### 1. Database Schema (SQLAlchemy + SQLite)

#### User Model
- id (Primary Key)
- username (Unique)
- email (Unique)
- password_hash
- created_at
- updated_at
- is_active
- role (user/admin)

#### Project Model
- id (Primary Key)
- name
- description
- user_id (Foreign Key → User)
- status (draft/processing/completed/error)
- input_text
- language
- created_at
- updated_at
- project_path (file system location)

#### VideoGeneration Model
- id (Primary Key)
- project_id (Foreign Key → Project)
- stage (script/voice/broll/assembly/complete)
- progress_percentage
- status (pending/processing/completed/error)
- error_message
- timeline_data (JSON)
- output_files (JSON)
- created_at
- updated_at

#### UserSession Model
- id (Primary Key)
- user_id (Foreign Key → User)
- token_jti (JWT ID)
- expires_at
- created_at

### 2. Authentication System

#### JWT Token Structure
```json
{
  "sub": "user_id",
  "username": "john_doe",
  "exp": 1640995200,
  "iat": 1640908800,
  "jti": "unique_token_id"
}
```

#### Authentication Flow
1. User registers/logs in with credentials
2. Server validates and returns JWT access token
3. Frontend stores token in httpOnly cookie or localStorage
4. All API requests include Bearer token
5. Server validates token and extracts user context

### 3. File Organization

#### User-Isolated Directory Structure
```
projects/
├── user_1/
│   ├── project_a/
│   │   ├── english/
│   │   │   ├── audio/
│   │   │   ├── outline.json
│   │   │   └── full_script.json
│   │   └── metadata_english.json
│   └── project_b/
└── user_2/
    └── project_c/

temp/
├── user_1/
│   ├── project_a/
│   │   ├── broll_timing.json
│   │   └── processing_files/
│   └── project_b/
└── user_2/
    └── project_c/
```

### 4. API Endpoints Design

#### Authentication Endpoints
- POST /api/auth/register
- POST /api/auth/login
- POST /api/auth/logout
- GET /api/auth/me
- POST /api/auth/refresh

#### Project Management
- GET /api/projects (list user's projects)
- POST /api/projects (create new project)
- GET /api/projects/{project_id}
- PUT /api/projects/{project_id}
- DELETE /api/projects/{project_id}

#### Video Generation
- POST /api/projects/{project_id}/generate
- GET /api/projects/{project_id}/status
- GET /api/projects/{project_id}/timeline
- PUT /api/projects/{project_id}/timeline
- GET /api/projects/{project_id}/files/{file_path}

#### B-roll Management
- GET /api/projects/{project_id}/broll
- POST /api/projects/{project_id}/broll/upload
- DELETE /api/projects/{project_id}/broll/{file_id}

### 5. Frontend Architecture (Vue.js + Bootstrap 5)

#### Main Components
1. **AuthPage.vue** - Login/Register forms
2. **Dashboard.vue** - Project overview and management
3. **ProjectEditor.vue** - Project creation and editing
4. **TimelineEditor.vue** - B-roll timeline editing
5. **ProgressTracker.vue** - Real-time generation progress
6. **FileManager.vue** - Project file management

#### State Management (Pinia)
- **authStore** - User authentication state
- **projectStore** - Project management state
- **timelineStore** - Timeline editing state
- **notificationStore** - Error/success messages

#### Routing Structure
```
/login
/register
/dashboard
/projects/:id/edit
/projects/:id/timeline
/projects/:id/files
```

### 6. Security Considerations

#### Backend Security
- JWT token validation on all protected routes
- User isolation enforced at database level
- File access restricted to project owners
- Input validation and sanitization
- Rate limiting on authentication endpoints

#### Frontend Security
- Secure token storage (httpOnly cookies preferred)
- Route guards for authentication
- CSRF protection
- XSS prevention via Vue.js built-in escaping

### 7. Development vs Production

#### Development Mode (SQLite)
- Single file database (storyforge.db)
- File-based storage for media
- Simplified deployment

#### Production Considerations
- PostgreSQL for better concurrent access
- Cloud storage for media files (S3, etc.)
- Redis for session management
- Docker containerization

## Implementation Phases

### Phase 1: Database & Authentication
1. Add SQLAlchemy models and database initialization
2. Implement JWT authentication system
3. Update backend routes for user context
4. Add user registration/login endpoints

### Phase 2: User Isolation
1. Modify file handling for user-specific directories
2. Update project creation/management for multi-user
3. Ensure all operations respect user ownership
4. Add proper error handling and validation

### Phase 3: Frontend Development
1. Create Vue.js application with routing
2. Implement authentication pages and flows
3. Build project dashboard and management UI
4. Integrate timeline editor with Bootstrap styling

### Phase 4: Integration & Testing
1. Connect frontend to backend APIs
2. Test user isolation and security
3. Verify complete video generation pipeline
4. Performance testing and optimization

## Technical Stack

### Backend
- FastAPI (existing)
- SQLAlchemy 2.0+ with SQLite (dev) / PostgreSQL (prod)
- Alembic for database migrations
- python-jose for JWT handling
- bcrypt for password hashing

### Frontend
- Vue 3 with Composition API
- Vue Router for navigation
- Pinia for state management
- Bootstrap 5 for styling
- Axios for HTTP requests
- WebSocket client for real-time updates

### Development Tools
- Vite for frontend build
- pytest for backend testing
- Vitest for frontend testing
- ESLint + Prettier for code quality