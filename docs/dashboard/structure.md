# Project Structure

```sh
/src
  /components        # Reusable UI components
    /ui              # ShadCN UI components
    /layouts         # Layout components (Sidebar, Header)
    /auth            # Authentication components
    /dashboard       # Dashboard-specific components
    /sessions        # Session management components
    /workflow        # Process workflow components
    /logs            # Log viewer components
    /users           # User management components
  /hooks             # Custom React hooks
  /lib               # Utility functions and constants
  /types             # TypeScript type definitions
  /contexts          # React contexts (auth, theme)
  /pages             # Page components
  /api               # API integration layer
  /assets            # Static assets
  App.tsx            # Main application component
  main.tsx           # Entry point
  index.css          # Global styles
```





```sh
public 
  |    .env.development
  |    .env.production
  |    components.json
  |    favicon.ico
  |    favicon.png
  |    index.html
  |    package-lock.json
  |    Package.json
  |    postcss.config.js
  |    README.md
  |    tailwind.config.js
  |    tsconfig.json
  |    tsconfig.node.json
  |    tsconfig.node.tsbuildinfo
  |    vite-env.d.ts
  |    vite.config.d.ts
  |    vite.config.d.ts.map
  |    vite.config.js
  |    vite.config.ts
  ├───src
    │   App.tsx
    │   index.css
    │   main.tsx
    │
    ├───api
    │       client.ts
    │       services.ts
    │
    ├───components
    │   ├───auth
    │   │       ProtectedRoute.tsx
    │   │
    │   ├───layouts
    │   │       DashboardLayout.tsx
    │   │       Header.tsx
    │   │       Sidebar.tsx
    │   │
    │   ├───ui
    │   │       alert-dialog.tsx
    │   │       alert.tsx
    │   │       avatar.tsx
    │   │       badge.tsx
    │   │       button.tsx
    │   │       card.tsx
    │   │       dialog.tsx
    │   │       dropdown-menu.tsx
    │   │       form.tsx
    │   │       input.tsx
    │   │       label.tsx
    │   │       progress.tsx
    │   │       scroll-area.tsx
    │   │       select.tsx
    │   │       separator.tsx
    │   │       spinner.tsx
    │   │       switch.tsx
    │   │       table.tsx
    │   │       tabs.tsx
    │   │
    │   ├───upload
    │   │       FileUpload.tsx
    │   │
    │   └───workflow
    │           HtmlGenerationStep.tsx
    │           MappingStep.tsx
    │           PdfGenerationStep.tsx
    │           ValidateStep.tsx
    │           WorkflowStepper.tsx
    │
    ├───config
    │       index.ts
    │
    ├───contexts
    │       AuthContext.tsx
    │       ThemeContext.tsx
    │
    ├───lib
    │       utils.ts
    │
    ├───pages
    │       DashboardPage.tsx
    │       LoginPage.tsx
    │       LogsPage.tsx
    │       SessionsPage.tsx
    │       SettingsPage.tsx
    │       UsersPage.tsx
    │       WorkflowPage.tsx
    │
    └───types
            index.ts
```