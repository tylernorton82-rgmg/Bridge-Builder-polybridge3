# Bridge Trimmer for Poly Bridge 3

Free Windows viewer for Poly Bridge 3 saves that colours every piece by estimated stress. Pair the project with Claude Code to make cheaper bridges one tested change at a time.

Fan-made. Not affiliated with Dry Cactus.

**Read this first**

- Edited saves can trigger the game's cheat or illegal-bridge flags. Use this at your own risk.
- Bridges made or changed with these tools aren't clean leaderboard scores. Don't present them as your own unassisted results.
- All cost and stress numbers are estimates. The stress model has been wrong in real tests, so only the game decides whether a bridge holds.
- There's no in-game automation. You run and test every bridge yourself.
- Every write first backs up that level's saves to `Documents\Bridge Trimmer Backups`.

## Install

1. Download `BridgeTrimmer.exe` from the Releases page.
2. Double-click it. There's nothing to install.
3. Windows may show "Windows protected your PC" because the app isn't code-signed. Click **More info**, then **Run anyway**.

## Use

1. Solve a level in the game so it has a saved bridge.
2. Pick the level and save in the app, or use **Open save**.
3. Optional: type the max stress the game showed to scale the colours.

The app only reads saves. It doesn't change them.

## What it doesn't do

- It doesn't trim or build bridges by itself. Early automatic versions failed in the game, so they were removed from the app.
- The EXE doesn't need Claude. New slots come from the Claude Code route below.
- Stress is a simple estimate. Moving parts aren't simulated.
- A screenshot can be shown next to the bridge for reference. The app doesn't read it.

## Use it with Claude Code (optional)

The viewer works without this. Claude Code lets you ask Claude to design bridges, read your saves or change the app. It needs a paid Claude account, and it uses the project's source code rather than the EXE.

1. Install [Git](https://git-scm.com/downloads).
2. Open PowerShell and install Claude Code:

   ```powershell
   irm https://claude.ai/install.ps1 | iex
   ```

3. Download this project and open it:

   ```powershell
   git clone https://github.com/tylernorton82-rgmg/Bridge-Builder-polybridge3.git
   cd Bridge-Builder-polybridge3
   ```

4. Start Claude Code and sign in when it asks:

   ```powershell
   claude
   ```

5. Ask for what you want, for example: `Read my saves for level 181 and make the bridge cheaper as a new slot.`
6. Test each new slot in the game and tell Claude pass or fail, the max stress and where it broke. Claude logs it and makes the next try.

Claude reads `CLAUDE.md` in this folder, so it already knows the project and its rules, such as never overwriting your saves. Check what it plans to do before you approve it, and test every bridge in the game.

## Build from source

```bash
py -3.11 -m venv .venv
.venv\Scripts\pip install -r requirements.txt pyinstaller
.venv\Scripts\pyinstaller --onefile --windowed --name BridgeTrimmer app.py
```

MIT License.
