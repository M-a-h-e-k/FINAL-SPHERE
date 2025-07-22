# SecureSphere - Security Assessment Platform

A comprehensive web application for conducting security assessments and reviews with role-based access control.

## 🚀 Features

### For Clients
- **Product Management**: Add and manage security products for assessment
- **Interactive Questionnaires**: Answer security questions across multiple dimensions
- **Progress Tracking**: Real-time progress indicators with new status flow:
  - Not Started → Filled Questions → In Review → Review → Completed
- **Evidence Upload**: Upload supporting documents with pin-icon interface
- **Review Status Tracking**: See review feedback with status-specific behaviors
- **Responsive Design**: Works on desktop, tablet, and mobile devices

### For Reviewers (Leads)
- **Organized Dashboard**: Questions grouped by sections with accordion interface
- **Review Management**: Review client responses with three status options:
  - **APPROVED**: Freezes client questions (no further edits allowed)
  - **NEEDS REVISION**: Enables comments and evidence upload for specific question
  - **REJECTED**: Requires complete re-submission with new evidence
- **Progress Tracking**: Section-wise review progress indicators
- **Comment System**: Provide detailed feedback to clients

### For Administrators
- **User Management**: Manage client and reviewer accounts
- **Analytics Dashboard**: View comprehensive assessment statistics
- **Product Oversight**: Monitor all products and assessments

## 🛠 Setup Instructions

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone/Download the project**
   ```bash
   # If you have the source code in a directory, navigate to it
   cd securesphere
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Access the application**
   - Open your web browser
   - Navigate to: `http://localhost:5000`
   - Register a new account or use existing credentials

## 🎯 Usage Guide

### Initial Setup
1. **Register**: Create your account with role selection
2. **Login**: Access your dashboard based on your role
3. **Add Product** (Clients): Create your first security assessment

### Assessment Process
1. **Fill Questionnaire**: Answer questions across security dimensions:
   - Build and Deployment
   - Culture and Organization
   - Implementation
   - Information Gathering
   - Test and Verification

2. **Submit for Review**: Questions are automatically sent for reviewer feedback

3. **Review Process**: Reviewers provide feedback with specific statuses:
   - Questions may be approved, need revision, or be rejected
   - Follow the feedback to complete your assessment

4. **View Results**: Access comprehensive scoring and analytics

### Key Features

#### New Status Flow
- **Not Started**: No questions answered yet
- **Filled Questions**: Some questions completed
- **In Review**: Assessment under reviewer evaluation  
- **Review**: Feedback provided, may need action
- **Completed**: Assessment finalized and approved

#### Review Status Behaviors
- **Approved Questions**: 
  - Questions are locked (cannot be modified)
  - Evidence upload disabled
  - Comments become read-only

- **Needs Revision**:
  - Comments required from client
  - Evidence upload recommended
  - Specific guidance provided

- **Rejected Questions**:
  - Complete re-submission required
  - New evidence upload mandatory
  - Must re-answer the entire question

#### File Upload System
- **Pin Icon Interface**: Clean, minimal file upload buttons
- **Supported Formats**: CSV, TXT, PDF, JPG, JPEG, PNG, DOC, DOCX
- **Evidence Tracking**: View existing evidence and upload new files

#### Scoring System
- **CSV-Based Scoring**: Scores pulled from assessment framework
- **Real-time Calculation**: Automatic score computation
- **Visual Indicators**: Color-coded scores (Green: 4-5, Blue: 3, Yellow: 2, Red: 0-1)

## 🏗 Architecture

### Backend (Flask)
- **app.py**: Main application with routes and database models
- **SQLite Database**: User data, products, responses, and comments
- **CSV Integration**: Assessment framework from devweb.csv

### Frontend
- **Bootstrap 5**: Responsive UI framework
- **Custom CSS**: Professional styling with animations
- **Vanilla JavaScript**: Interactive features and API integration
- **Chart.js**: Data visualization for results

### Database Models
- **User**: Account management with role-based access
- **Product**: Security assessment products
- **QuestionnaireResponse**: Client answers and evidence
- **LeadComment**: Reviewer feedback and status tracking

## 🎨 Design System

### Color Palette
- **Primary**: Professional blue gradient (#1e40af to #60a5fa)
- **Success**: Green (#10b981) for approved items
- **Warning**: Amber (#f59e0b) for items needing attention  
- **Danger**: Red (#ef4444) for rejected items
- **Secondary**: Slate grays for neutral elements

### Status Indicators
- **Filled Questions**: Blue badge
- **In Review**: Amber badge  
- **Review**: Purple badge
- **Completed**: Green badge

### Responsive Design
- **Mobile-first**: Optimized for small screens
- **Tablet-friendly**: Enhanced layouts for medium screens
- **Desktop-optimized**: Full feature experience on large screens

## 🔧 Technical Details

### Security Features
- **Password Hashing**: Secure password storage with Werkzeug
- **Session Management**: Secure user session handling
- **Role-based Access**: Different interfaces for different user types
- **File Upload Security**: Validated file types and secure storage

### Performance Optimizations
- **Lazy Loading**: Accordion-based question organization
- **Efficient Queries**: Optimized database interactions
- **Caching**: Static file caching for better performance
- **Responsive Images**: Optimized for different screen sizes

### Browser Compatibility
- **Modern Browsers**: Chrome, Firefox, Safari, Edge (latest versions)
- **Progressive Enhancement**: Basic functionality on older browsers
- **JavaScript Required**: Enhanced features require JavaScript

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Install missing dependencies
   pip install flask flask-sqlalchemy werkzeug
   ```

2. **Database Issues**
   ```bash
   # Delete existing database and restart
   rm securesphere.db
   python app.py
   ```

3. **File Upload Problems**
   - Ensure the `static/uploads` directory exists
   - Check file permissions
   - Verify supported file formats

4. **Styling Issues**
   - Clear browser cache
   - Ensure `static/style.css` is accessible
   - Check for JavaScript errors in browser console

### Development Mode
- Set `debug=True` in app.py for detailed error messages
- Use browser developer tools for frontend debugging
- Check terminal output for backend errors

## 📝 File Structure

```
securesphere/
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── devweb.csv                     # Assessment framework
├── static/
│   ├── style.css                  # Custom CSS styles
│   ├── devweb.csv                 # CSV for frontend access
│   └── uploads/                   # File upload storage
└── templates/
    ├── base.html                  # Base template
    ├── dashboard_client.html      # Client dashboard
    ├── dashboard_lead.html        # Reviewer dashboard  
    ├── fill_questionnaire_section.html # Question interface
    ├── review_questionnaire.html  # Review interface
    ├── product_results.html       # Results display
    └── client_comments.html       # Comments interface
```

## 🤝 Contributing

1. Follow the existing code style and structure
2. Test changes thoroughly before submitting
3. Update documentation for new features
4. Ensure responsive design principles are maintained

## 📄 License

This project is provided as-is for educational and assessment purposes.

---

**SecureSphere** - Professional Security Assessment Platform
Built with Flask, Bootstrap, and modern web standards.