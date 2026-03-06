# Contributing to UrbanPulse

## Branch Strategy
```
main        → production-ready code
develop     → integration branch
feature/*   → new features
fix/*       → bug fixes
```

## Commit Convention
```
feat: add agent decision log to dashboard
fix:  resolve CORS issue in production
docs: update architecture diagram
test: add IncidentService unit tests
```

## Pull Request Checklist
- [ ] Frontend builds without errors (`npm run build:prod`)
- [ ] Backend compiles and tests pass (`mvn test`)
- [ ] No secrets committed
- [ ] README updated if API changed
