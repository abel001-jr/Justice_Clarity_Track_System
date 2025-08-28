# Justice Clarity - Court Case Management System

A comprehensive Django-based court case management system designed to streamline judicial processes and improve efficiency in court administration. The system provides specialized dashboards for different user roles: Clerks, Judges, and Prison Officers.

## Project Overview

Justice Clarity is a modern web application built with Django that facilitates effective management of court cases, inmates, and judicial processes. The system features role-based access control, intuitive dashboards, and comprehensive reporting capabilities.

### Key Features

- **Role-Based Dashboards**: Specialized interfaces for Clerks, Judges, and Prison Officers
- **Case Management**: Complete lifecycle management of court cases
- **Inmate Management**: Comprehensive tracking of inmates and their records
- **Report Generation**: Automated reporting and documentation
- **User Authentication**: Secure login system with role-based permissions
- **Responsive Design**: Mobile-friendly interface using Bootstrap 5
- **Real-time Updates**: Dynamic content updates and notifications

## System Architecture

### Applications Structure

The project is organized into three main Django applications:

1. **Core App** (`core/`)
   - User authentication and authorization
   - User profiles and role management
   - Dashboard routing and notifications
   - Audit logging

2. **Court App** (`court/`)
   - Case management and tracking
   - Evidence handling
   - Hearing scheduling
   - Judge assignments
   - Case reporting

3. **Prison App** (`prison/`)
   - Inmate records management
   - Behavioral reports
   - Visitor logs
   - Program tracking
   - Release management

### Technology Stack

- **Backend Framework**: Django 5.2.5
- **Database**: SQLite (development) / PostgreSQL (production ready)
- **Frontend**: Bootstrap 5.3, HTML5, CSS3, JavaScript
- **Authentication**: Django's built-in authentication system
- **API**: Django REST Framework 3.16.1
- **Forms**: Django Crispy Forms with Bootstrap 5
- **CORS**: Django CORS Headers for API access

### Dependencies

```python
# Core Dependencies
Django==5.2.5
djangorestframework==3.16.1
django-crispy-forms==2.3
crispy-bootstrap5==2024.10
django-cors-headers==4.6.0

# Additional Utilities
Pillow==11.0.0  # Image handling
python-decouple==3.8  # Environment configuration
whitenoise==6.8.2  # Static file serving
```

## Installation and Setup

### Prerequisites

- Python 3.11 or higher
- pip (Python package installer)
- Virtual environment (recommended)

### Step-by-Step Installation

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd Justice_Clarity
   ```

2. **Create Virtual Environment**
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Database Setup**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create Superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Collect Static Files**
   ```bash
   python manage.py collectstatic
   ```

7. **Run Development Server**
   ```bash
   python manage.py runserver
   ```

The application will be available at `http://localhost:8000`

## User Roles and Permissions

### Clerk Dashboard
- **Primary Functions**: Case creation, judge assignment, administrative tasks
- **Access Level**: Full case management, user administration
- **Key Features**:
  - Create and manage court cases
  - Assign judges to cases
  - Schedule hearings
  - Generate administrative reports
  - Monitor case progress

### Judge Dashboard
- **Primary Functions**: Case review, decision making, report submission
- **Access Level**: Assigned cases, sentencing, final reports
- **Key Features**:
  - Review assigned cases
  - Pass sentences and verdicts
  - Submit final case reports
  - View case evidence
  - Schedule hearings

### Prison Officer Dashboard
- **Primary Functions**: Inmate management, behavioral reporting
- **Access Level**: Assigned inmates, report submission
- **Key Features**:
  - Monitor assigned inmates
  - Submit behavioral reports
  - Log visitor information
  - Track inmate programs
  - Manage release preparations

## Database Schema

### Core Models

#### UserProfile
- Extends Django's User model
- Stores role information (clerk, judge, prison_officer)
- Employee ID and department tracking
- Contact information

#### Notification
- System-wide notification management
- User-specific messaging
- Priority levels and read status

#### AuditLog
- Comprehensive activity logging
- User action tracking
- System security monitoring

### Court Models

#### Case
- Complete case information
- Case number, title, type, status
- Plaintiff and defendant details
- Lawyer information
- Priority and filing dates

#### Evidence
- Evidence item management
- File attachments and descriptions
- Chain of custody tracking
- Evidence type classification

#### Hearing
- Hearing scheduling and management
- Location and participant tracking
- Hearing type and status
- Notes and outcomes

#### CaseReport
- Final case reports and decisions
- Judge submissions and approvals
- Verdict and sentence documentation

### Prison Models

#### Inmate
- Comprehensive inmate records
- Personal information and case details
- Sentence information and release dates
- Behavioral ratings and status

#### InmateReport
- Behavioral and incident reports
- Officer submissions and reviews
- Priority levels and recommendations
- Incident date and time tracking

#### VisitorLog
- Visitor information and logs
- Visit scheduling and duration
- Relationship tracking
- Security clearance status

#### InmateProgram
- Rehabilitation program tracking
- Progress monitoring
- Completion status and outcomes

## API Endpoints

The system provides RESTful API endpoints for integration:

### Authentication
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout
- `GET /api/auth/user/` - Current user information

### Cases
- `GET /api/cases/` - List all cases
- `POST /api/cases/` - Create new case
- `GET /api/cases/{id}/` - Case details
- `PUT /api/cases/{id}/` - Update case
- `DELETE /api/cases/{id}/` - Delete case

### Inmates
- `GET /api/inmates/` - List all inmates
- `POST /api/inmates/` - Create inmate record
- `GET /api/inmates/{id}/` - Inmate details
- `PUT /api/inmates/{id}/` - Update inmate
- `GET /api/inmates/{id}/reports/` - Inmate reports

### Reports
- `GET /api/reports/` - List all reports
- `POST /api/reports/` - Submit new report
- `GET /api/reports/{id}/` - Report details
- `PUT /api/reports/{id}/review/` - Review report

## Security Features

### Authentication and Authorization
- Django's built-in authentication system
- Role-based access control (RBAC)
- Session management and CSRF protection
- Password hashing and validation

### Data Protection
- SQL injection prevention through ORM
- XSS protection via template escaping
- CORS configuration for API security
- Secure file upload handling

### Audit Trail
- Comprehensive activity logging
- User action tracking
- System access monitoring
- Data modification history

## Deployment

### Production Considerations

1. **Environment Configuration**
   - Use environment variables for sensitive settings
   - Configure production database (PostgreSQL recommended)
   - Set up proper static file serving
   - Configure email backend for notifications

2. **Security Settings**
   ```python
   DEBUG = False
   ALLOWED_HOSTS = ['your-domain.com']
   SECURE_SSL_REDIRECT = True
   SECURE_BROWSER_XSS_FILTER = True
   SECURE_CONTENT_TYPE_NOSNIFF = True
   ```

3. **Database Migration**
   ```bash
   python manage.py migrate --settings=Justice_Clarity.settings.production
   ```

4. **Static Files**
   ```bash
   python manage.py collectstatic --settings=Justice_Clarity.settings.production
   ```

### Docker Deployment (Optional)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "Justice_Clarity.wsgi:application", "--bind", "0.0.0.0:8000"]
```

## Testing

### Running Tests
```bash
python manage.py test
```

### Test Coverage
```bash
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

## Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make changes and add tests
4. Run test suite
5. Submit pull request

### Code Standards
- Follow PEP 8 style guidelines
- Write comprehensive docstrings
- Add unit tests for new features
- Update documentation as needed

## Troubleshooting

### Common Issues

1. **Database Migration Errors**
   ```bash
   python manage.py makemigrations --empty appname
   python manage.py migrate --fake-initial
   ```

2. **Static Files Not Loading**
   ```bash
   python manage.py collectstatic --clear
   ```

3. **Permission Denied Errors**
   - Check file permissions
   - Verify user role assignments
   - Review authentication settings

### Support

For technical support or questions:
- Check the documentation
- Review error logs
- Contact system administrator

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Changelog

### Version 1.0.0 (Initial Release)
- Complete court case management system
- Three specialized user dashboards
- Role-based access control
- Comprehensive reporting features
- Modern responsive design
- RESTful API endpoints
- Security features and audit logging

---

**Justice Clarity** - Streamlining judicial processes through technology.

