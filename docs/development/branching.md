# Branching & Git Strategy

> Git branching workflow and version control policies for CivicConnect.

---

# Branch Hierarchy

```
main (Production)
  ▲
  │ (Release Pull Request)
develop (Staging / Integration)
  ▲
  │ (Feature Pull Request)
feature/<feature-name> / fix/<bug-name> / docs/<doc-name>
```

---

# Branch Naming Conventions

- `feature/report-audio-descriptions`
- `fix/jwt-expiration-handling`
- `docs/api-specification-update`
- `chore/upgrade-fastapi-deps`

---

# Commit Message Format (Conventional Commits)

```
<type>(<scope>): <short summary>

[optional body]
```

## Allowed Types
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation changes
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `test`: Adding missing tests
- `chore`: Infrastructure, config, or dependency changes
