# Commit and push (run locally)

Run these in a terminal from the repo root (`d:\abs-ai-fabric`):

```powershell
cd d:\abs-ai-fabric

# Stage all changes
git add -A

# Commit (Conventional Commits style)
git commit -m "feat(admin,playground): model status sync, Unload for running, aligned buttons

- Gateway: GET /v1/admin/models/pull/status, load timeout 300s for 70B
- Gateway: GET /v1/admin/models/list returns running state (sync with Assets)
- Admin: show RUNNING vs INSTALLED; Unload when running, Load when installed
- Admin: aligned model card action buttons (flex, min-height, margin-top auto)
- Playground: requestModel returns status; show timeout vs not-installed message
- Playground: poll pull/status, show Pulling... when Admin is pulling
- Docs: model status verification and pull flow in Adding_New_Models_Guide
- Core/assets: .env.example, audit docs, aliases, setup scripts fixes"

# Push
git push
```

If you prefer a shorter message:

```powershell
git add -A
git commit -m "feat(admin,playground): model status sync, Unload for running models, aligned grid buttons"
git push
```
