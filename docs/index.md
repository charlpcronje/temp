# DocTypeGen Documentation

This directory contains comprehensive documentation for the DocTypeGen system.

## System Documentation

- [System Architecture](system_architecture.md) - Overview of the system components and data flow
- [Workflow Guide](workflow_guide.md) - Step-by-step guide to the document processing workflow
- [Features](features.md) - Detailed description of system features
- [Updates](updates.md) - Recent updates and changes to the system

## Interface Documentation

- [Web UI](dashboard/README.md) - Documentation for the web-based user interface
- [API](api/README.md) - Documentation for the REST API
- [CLI](cli/README.md) - Documentation for the command-line interface

## Component Documentation

- [Validation System](validation/README.md) - Documentation for the validation system
- [Lookup System](lookup/README.md) - Documentation for the lookup resolution system
- [Entity System](entity/README.md) - Documentation for the entity creation system
- [Sync System](sync/README.md) - Documentation for the tenant database sync system
- [Storage System](storage/README.md) - Documentation for the S3 storage system

## Developer Documentation

- [Development Guide](development.md) - Guide for developers working on the system
- [Integration Guide](integration_guide.md) - Guide for integrating with external systems
- [Customization Guide](customization.md) - Guide for customizing the system

## User Documentation

- [Onboarding Guide](onboarding.md) - Guide for new users
- [Troubleshooting](troubleshooting.md) - Common issues and solutions

## Quick Start

1. Install the system as described in the main README.md file
2. Start the API server: `uvicorn api:app --reload`
3. Build and serve the frontend: `cd public && npm run build`
4. Access the web UI at http://localhost:8000/app/
5. Follow the workflow steps as described in the [Workflow Guide](workflow_guide.md)
