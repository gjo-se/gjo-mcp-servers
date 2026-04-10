# Repo-Cleanup Runbook

> Generisches Runbook für den sauberen Abschluss einer Arbeitsphase in einem Repo.
> Wird am Ende jedes größeren Feature-Blocks oder Epics ausgeführt.
> Für jedes Projekt anwendbar – Pfade und Branch-Namen anpassen.

---

## Wann ausführen

- Nach Abschluss eines Epics oder Feature-Blocks
- Bevor ein neuer Arbeitsbereich (z. B. Client-Seite) beginnt
- Vor einem größeren Release oder Merge-Freeze

---

## 1. Offene PRs / Branches klären

Alle Feature-Branches müssen entweder einen offenen PR haben oder gelöscht sein.

```zsh
# Offene Branches auf GitHub prüfen
gh pr list --state open

# Branches ohne PR identifizieren
git branch -r | grep "feature/" | while read branch; do
  name=$(echo $branch | sed 's/origin\///')
  gh pr list --head "$name" --json number --jq '.[].number' 2>/dev/null | grep -q . \
    || echo "KEIN PR: $name"
done
```

→ Für jeden Branch ohne PR: entweder PR öffnen oder Branch löschen.

---

## 2. Stashes auflösen

```zsh
git stash list
```

Für jeden Stash entscheiden:

| Zustand | Aktion |
|---|---|
| Inhalt relevant, noch nicht committed | `git stash pop` → committen |
| Inhalt überholt / bereits in Branch enthalten | `git stash drop stash@{N}` |

Kein Stash darf unkommentiert zurückbleiben.

---

## 3. Lokale Branches bereinigen (`gf_cleanup`)

```zsh
git checkout develop && git pull
gf_cleanup
```

`gf_cleanup` löscht alle lokalen Branches die bereits in `develop` enthalten sind
und führt `git remote prune origin` aus.

Manuell (falls `gf_cleanup` nicht verfügbar):

```zsh
git branch --merged develop | grep -v "develop\|main" | xargs git branch -d
git remote prune origin
```

---

## 4. Alte Remote-Branches auf GitHub löschen

`git remote prune origin` löscht nur dead tracking refs lokal – die Branches
auf GitHub bleiben bestehen. Gemergte Remote-Branches manuell entfernen:

```zsh
# Gemergte Remote-Branches anzeigen
git branch -r --merged origin/develop \
  | grep "origin/feature/" \
  | sed 's/origin\///' \
  | grep -v "develop\|main"

# Löschen (einzeln oder in Schleife)
git push origin --delete feature/ISSUE-XX
```

Oder via GitHub CLI:

```zsh
gh api repos/{owner}/{repo}/branches \
  --jq '.[].name' | grep "feature/" \
  | while read b; do
      gh api -X DELETE "repos/{owner}/{repo}/git/refs/heads/$b"
    done
```

---

## 5. TODOs auf Ticket-Referenzen prüfen

Kein `TODO` ohne Issue-Referenz im finalen Code:

```zsh
grep -rn "TODO" servers/ shared/ tests/ src/ app/ | grep -v "# TODO #"
```

→ Jeden Treffer entweder mit `# TODO #<nr>:` ergänzen oder entfernen.

---

## 6. Auskommentierten Code entfernen

```zsh
grep -rn "^# .*def \|^# .*class \|^#.*import " servers/ shared/ src/ app/
```

→ Nur als Kommentar getarnte Code-Blöcke (keine erklärenden Kommentare) entfernen.

---

## 7. Dependency-Audit

```zsh
# Dependency-Baum prüfen
uv tree

# Konflikte und veraltete Packages
uv sync

# Nach Entfernen ungenutzter Packages: Lock-Datei aktualisieren
uv lock
```

**Nicht verwenden:** `uv run pip check` – liefert in uv-Projekten irreführende Ergebnisse.

---

## 8. Docs-Konsistenz prüfen

Runbooks und README müssen den aktuellen Stand widerspiegeln:

```zsh
# Schnellcheck: Default-Services, Ports, Variablen
grep -n "8001\|8002\|8003\|8004\|8005\|8006" docs/runbooks/**/*.md README.md
```

→ Veraltete Port-Einträge, veraltete Servicelisten oder falsche Default-Markierungen korrigieren.

---

## 9. Abschluss-Verifikation

```zsh
uv run ruff check .
uv run black --check .
uv run pytest --tb=short -q
```

Alle drei müssen grün sein. Wenn nicht → Fehler beheben bevor PR geöffnet wird.

---

## Definition of Done

```zsh
git stash list                         # → leer
git branch --merged develop            # → nur develop / main
git branch -r | grep "feature/"        # → nur aktive Branches
uv run ruff check . && uv run black --check . && uv run pytest --tb=short -q
```

Erwartung: Repo ist in einem sauberen, reviewbaren Zustand.

---

## Checkliste

```
[ ] Alle offenen Branches haben einen PR oder sind gelöscht
[ ] Keine Stashes ohne Begründung
[ ] Keine gemergten lokalen Branches
[ ] Keine gemergten Remote-Feature-Branches auf GitHub
[ ] Alle TODO-Kommentare haben Ticket-Referenzen
[ ] Keine auskommentierten Code-Blöcke
[ ] uv tree / uv sync ohne Konflikte
[ ] uv.lock aktuell (nach Dependency-Änderungen: uv lock committen)
[ ] README und Runbooks spiegeln aktuellen Stand wider
[ ] ruff check + black --check + pytest grün
```

