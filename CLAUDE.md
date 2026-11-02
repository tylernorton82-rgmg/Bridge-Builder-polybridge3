# Bridge Trimmer

Poly Bridge 3 tools. The standalone app is a read-only stress viewer. `pb.py` lets Claude write one-change slots for the player to test.

- `app.py`: the window (tkinter)
- `pb.py`: show, edit, result, log
- `trimmer.py`: stress, cost, backup, save_new. `trim` and `auto_build` failed in game tests and aren't in the app
- `pbslot.py`: reads and writes `.slot` files
- `truss.py`: truss solver
- `tests/test_trim.py`: run on copies of real saves

## Rules

- Never overwrite or delete an existing save. Only write new slots.
- Test on copies of saves, not the real SaveSlots folder.
- Never create joints in terrain or no-build zones. The game disables achievements and leaderboards for that bridge.
- No in-game auto-clicking or game automation in this release. Hands-off runs are only a possible later experiment. Do not build them.
- Back up saves before any write. If the backup fails, don't write.
- Label cost and stress as estimates. Never present results as clean leaderboard scores.
- The app must keep running without Claude, an account or internet.
- Stress numbers are estimates. Say so, and treat the game's result as the truth.
- Publishing to GitHub or making a release needs Tyler's explicit go-ahead.

## Build

```bash
.venv\Scripts\pyinstaller --noconfirm --onefile --windowed --name BridgeTrimmer app.py
```

Pushing a tag like `v1.0.0` makes GitHub build the EXE and attach it to a release.

## Working on a bridge with the player

The truss model is wrong about what is safe: it once predicted lower stress after key steel legs were removed. Only the game decides. Don't rely on `trimmer.trim` to choose pieces.

1. `py pb.py log <level>` to see what already passed or failed.
2. `py pb.py show <level> "<save>"` and ask for a screenshot of the level.
3. Pick one small change. Keep load paths to anchors and foundations.
4. `py pb.py edit ...` to write it as a new slot.
5. The player tests it and reports pass or fail, max stress and where it broke.
6. `py pb.py result ...` to log it, then repeat from the last passing slot.
