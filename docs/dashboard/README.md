# DocTypeGen Web UI Documentation

## Overview

The DocTypeGen Web UI provides a comprehensive dashboard for managing the document processing workflow. It is built using React and Tailwind CSS and provides a modern, responsive interface for all document processing operations.

## Accessing the Web UI

The Web UI is available at:

```
http://localhost:8000/app/
```

## Authentication

The Web UI requires authentication. You can log in using the credentials created through the CLI or API:

```bash
# Create a user via CLI
python cli.py user add username password --role admin
```

## Dashboard Layout

The Web UI consists of the following main sections:

### Navigation

The main navigation menu provides access to:

- **Dashboard**: Overview of recent sessions and system status
- **Sessions**: List of all processing sessions
- **Workflow**: Step-by-step document processing workflow
- **Logs**: System logs and audit trails
- **Users**: User management (admin only)
- **Settings**: System configuration (admin only)

### Dashboard

The dashboard provides an overview of:

- Recent sessions
- System status
- Quick access to common actions

### Sessions

The sessions page lists all processing sessions with:

- Session hash
- Document type
- Creation date
- Last operation
- Status
- Actions (continue processing, view details, delete)

### Workflow

The workflow section guides you through the document processing steps:

1. **Upload**: Upload and import a spreadsheet file
2. **Validate & Map**: Validate data and map columns to field types
3. **HTML Generation**: Generate HTML documents from templates
4. **PDF Generation**: Convert HTML documents to PDF
5. **Lookup Resolution**: Match records to external data sources
6. **Entity Creation**: Create new entities based on document data
7. **Data Sync**: Sync data to tenant databases
8. **Storage**: Transfer files to S3 storage

Each step provides:
- Clear instructions
- Progress indicators
- Error handling
- Navigation to previous/next steps

### Logs

The logs section provides access to:

- System logs
- Session-specific logs
- Audit trails
- Error reports

### Users

The users section (admin only) allows:

- Creating new users
- Editing existing users
- Changing user roles
- Deactivating users
- Deleting users

### Settings

The settings section (admin only) allows configuration of:

- System settings
- API keys
- Database connections
- S3 storage settings
- PDF generation options

## Workflow Steps in Detail

### Step 1: Upload

The upload page allows you to:

- Drag and drop a file or click to browse
- View file details before upload
- Start the import process
- View import progress and results

### Step 2: Validate & Map

The validation page provides:

- Document type detection results
- Validation statistics (valid/invalid rows, success rate)
- Field mapping editor
- Validation error details
- Options to reset or adjust mappings

### Step 3: HTML Generation

The HTML generation page allows you to:

- View the template that will be used
- Start the HTML generation process
- View generation progress and results
- Preview and download generated HTML files

### Step 4: PDF Generation

The PDF generation page allows you to:

- Start the PDF generation process
- View generation progress and results
- Preview and download generated PDF files

### Step 5: Lookup Resolution

The lookup resolution page provides:

- Lookup statistics (matched/unmatched records)
- Exception handling interface
- Manual matching options
- Lookup error details

### Step 6: Entity Creation

The entity creation page allows you to:

- Review entities to be created
- Start the entity creation process
- View creation progress and results
- Handle creation errors

### Step 7: Data Sync

The data sync page allows you to:

- Start the data sync process
- View sync progress and results
- Handle sync errors

### Step 8: Storage

The storage page allows you to:

- Start the file transfer process
- View transfer progress and results
- Handle transfer errors

## Session Details

The session details page provides comprehensive information about a specific session:

- Session metadata (hash, document type, creation date)
- Processing status and history
- Generated files (HTML, PDF)
- Logs and reports
- Actions (continue processing, delete)

## Dark Mode

The Web UI supports dark mode, which can be toggled via:

- The theme toggle button in the navigation bar
- System preferences (if enabled)

Dark mode settings are stored in localStorage and persist between sessions.

## Responsive Design

The Web UI is fully responsive and works on:

- Desktop computers
- Tablets
- Mobile devices

The layout adapts automatically to different screen sizes.

## Keyboard Shortcuts

The Web UI supports the following keyboard shortcuts:

- `Ctrl+/`: Open help menu
- `Ctrl+D`: Toggle dark mode
- `Ctrl+S`: Save current form (where applicable)
- `Esc`: Close modal dialogs

## Troubleshooting

### Common Issues

1. **"Cannot connect to server" error**
   - Ensure the API server is running (`uvicorn api:app --reload`)
   - Check network connectivity

2. **Authentication failures**
   - Verify username and password
   - Check if the user account is active
   - Clear browser cookies and try again

3. **File upload issues**
   - Check file size (max 10MB by default)
   - Ensure file format is supported (CSV, XLSX, XLS)
   - Try a different browser

4. **Workflow navigation issues**
   - Check session status in the API
   - Try activating the session explicitly
   - Clear browser cache and reload

### Browser Compatibility

The Web UI is compatible with:

- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

For the best experience, use the latest version of Chrome or Firefox.
