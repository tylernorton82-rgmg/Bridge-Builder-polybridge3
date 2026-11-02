# Bridge Trimmer for Poly Bridge 3

Free Windows app that reads your Poly Bridge 3 saves, colours every piece by estimated stress, and writes a cheaper copy of your bridge as a new save slot.

Fan-made. Not affiliated with Dry Cactus.

## Install

1. Download `BridgeTrimmer.exe` from the Releases page.
2. Double-click it. There's nothing to install.
3. Windows may show "Windows protected your PC" because the app isn't code-signed. Click **More info**, then **Run anyway**.

## Use

1. Solve a level in the game so it has a passing bridge saved.
2. Pick the level and save in the app, or use **Open save**.
3. Type the max stress the game showed. This calibrates the estimate.
4. Click **Trim this bridge**.
5. Name it and click **Save as new slot**, then load that slot in the game and test it.

## New level

1. In the game, place one road piece and save, so the level has a save file.
2. Pick that save in the app and click **Build a new bridge**.
3. Click **Save as new slot**, load it in the game and test it. Then run a trim on it once it passes.

The builder replaces your one piece. It runs a straight road between the outermost anchors with a truss above it. It can't see terrain or no-build zones, and it won't suit levels that need boats, ramps or islands.

## What it does and doesn't do

- It never changes or overwrites an existing save.
- It only removes pieces or swaps steel for wood. It never adds joints, so it can't put one in an illegal spot.
- Road, hydraulics, rope, cable and the most loaded steel pieces are left alone.
- Stress numbers are estimates from a simple truss model. Moving parts aren't simulated, so the game has the final say.
- A screenshot can be shown next to the bridge for reference. The app doesn't read it automatically.

## Use it with Claude Code (optional)

The app works without this. Claude Code lets you ask Claude to design bridges, read your saves or change the app. It needs a paid Claude account, and it uses the project's source code rather than the EXE.

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

Claude reads `CLAUDE.md` in this folder, so it already knows the project and its rules, such as never overwriting your saves. Check what it plans to do before you approve it, and test every bridge in the game.

## Build from source

```bash
py -3.11 -m venv .venv
.venv\Scripts\pip install -r requirements.txt pyinstaller
.venv\Scripts\pyinstaller --onefile --windowed --name BridgeTrimmer app.py
```

MIT License.
