# Tenant Schema

## Application
```json
{
    "application": {
        "name": "Document Generator System",
        "version": "1.1.0",
        "author": "Your Organization",
        "description": "Generates various types of documents from Excel records"
    },
```

## Documents Types
```json
    "documents_types": [
        {
            "payment_advice": {
                "name": "Payment Advice",
                "schema": "payment_advice_schema.json",
                "template_data": [
                    {
                        "CONTACT_NUMBER_1": "123123123"
                    },
                    {
                        "CONTACT_NUMBER_2": "123123123"
                    }
                ]
            }
        }
    ],
```

## HTML & PDF
```json
    "html": {
        "images": {
            "UseBase64": true,
            "CopyToOutput": false
        }
    },
    "pdf": {
        "generator": "wkhtmltopdf",
        "page_size": "A4",
        "orientation": "portrait",
        "margin": "2cm",
        "font_size": "12pt",
        "text_color": "#333333",
        "background_color": "#ffffff",
        "wkhtmltopdf": "/usr/bin/wkhtmltopdf"
    },
```

## Database & Storage
```json
    "database": {
        "driver": "sqlite",
        "path": "data.db"
    },
    "storage": {
        "type": "disk",
        "path": "output"
    },
```

## Tenant
```json
    "tenant": {
        "id": "414",
        "name": "jre",
        "connections": {
            "local_sqlite": {
                "path": "C:/xampp/htdocs/DocTypeGen/output/{hash}/data.db"
            },
            "local_mysql": {
                "driver": "mysql",
                "host": "localhost",
                "port": 3306,
                "username": "cp",
                "password": "4334.4334",
                "database": "dc_414"
            },
            "aws":{
                "river": "mysql",
                "host": "dc-414-instance.ckmzsqmzjz7m.us-east-1.rds.amazonaws.com",
                "port": 3306,
                "username": "cp",
                "password": "4334.4334",
                "database": "dc_414"
            }
        },
        "mappings": {
            "payment_advice": {
                "column_to_column": [
                    "local_sqlite:imported_ce65e00a45:'Shareholder ID Number' = local_mysql:users:email"
                ],
                "type_to_column": [
                    "local_sqlite:imported_ce65e00a45:SA_ID_NUMBER = local_mysql:users:email"
                ]
            }
        },
        "storage":{
            "type": "disk",
            "path": "C:\\dcfiles"
        }
    },
```

## API 
```json
    "api": {
        "auth_enabled": false,
        "auth_token": "4334.4334",
        "host": "0.0.0.0",
        "port": 8000,
        "static_mounts": {
            "dashboard": "/",
            "logs": "/logs",
            "session": "/static",
            "dashboard_dir": "public/dist",
            "logs_dir": "public/logs"
        },
        "base_url": "http://localhost:8000"
    },
```

## Logging
```json
    "logging": {
        "level": "DEBUG",
        "file": "logs/app.log",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    }
}
```