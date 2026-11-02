# Bridge Trimmer

Standalone Windows app for Poly Bridge 3. It reads save slots, estimates stress, trims finished bridges and builds simple new ones.

- `app.py`: the window (tkinter)
- `trimmer.py`: stress, cost, trim, auto_build, save_new
- `pbslot.py`: reads and writes `.slot` files
- `truss.py`: truss solver
- `tests/test_trim.py`: run on copies of real saves

## Rules

- Never overwrite or delete an existing save. Only write new slots.
- Test on copies of saves, not the real SaveSlots folder.
- Never create joints in terrain or no-build zones. The game disables achievements and leaderboards for that bridge.
- No in-game auto-clicking.
- The app must keep running without Claude, an account or internet.
- Stress numbers are estimates. Say so, and treat the game's result as the truth.
- Publishing to GitHub or making a release needs Tyler's explicit go-ahead.

## Build

```bash
.venv\Scripts\pyinstaller --noconfirm --onefile --windowed --name BridgeTrimmer app.py
```

Pushing a tag like `v1.0.0` makes GitHub build the EXE and attach it to a release.
