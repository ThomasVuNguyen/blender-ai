# Blender MCP playbook

This is a record of the **October 24, 2026 sandwich study** in this workspace. It is a working example, not a promise that every future Blender or add-on version has the same API. The first packaged result is [`artifacts/001-sandwich/`](artifacts/001-sandwich/). `sandwich_scene.py` builds the scene. The result is **stylized**, visibly less realistic than the generated food photo.

## Fast path for an agent

1. Check the live scene before changing it: `uv run --with mcp-for-blender python blender_mcp_client.py scene`. On this Mac, Blender's add-on listens on `127.0.0.1:9876` when Blender is open. If the call fails, check that Blender is running and that the **MCP for Blender** add-on is enabled. `codex mcp get blender` shows the Codex registration; new Codex sessions load newly registered tools.
2. Save or duplicate any existing user scene before replacing objects. The sandwich began from Blender's unsaved default cube scene, so its builder cleared all objects. That clearing step is not safe to reuse in a scene containing user work.
3. Keep scene-building Python in a local `.py` file and call `uv run --with mcp-for-blender python blender_mcp_client.py exec path/to/script.py --prompt 'What this edit does'`. This sends it through the MCP `execute_blender_code` tool. The server logs the full script, so the helper captures that output in `blender-mcp-client.log` instead of spending tool-output tokens on it. The helper prints tool results and returns a failure status for textual execution errors.
4. Render a low-cost hero view, inspect the image, correct the largest visible mismatch, then render front, side, and top views. Confirm the `.blend` opens and the final camera and packed reference are present. Stop when the render matches the requested level of realism, not when the tool merely reports success.

## Client registrations on this Mac

- Codex: `codex mcp get blender` should show `uvx mcp-for-blender`.
- Antigravity: the `blender` entry is in both `~/.gemini/config/mcp_config.json` (current global config) and `~/.gemini/antigravity/mcp_config.json` (this installation's older app config). Refresh or restart Antigravity after edits.
- Claude Code: `claude mcp get blender` should report Connected. Claude Desktop uses `~/Library/Application Support/Claude/claude_desktop_config.json`; restart it after editing. Its running app rewrote that file once during setup, so check that the entry persisted before relying on it.
- All entries use the absolute command `/Users/thomasthemaker/.local/bin/uvx` and argument `mcp-for-blender`. This avoids GUI apps missing `uvx` on their PATH. The package includes both the MCP process and the Blender add-on; the Blender add-on must be enabled separately.

## Concrete mistakes from this run

| Symptom | Cause and fix |
| --- | --- |
| `BLENDER_EEVEE_NEXT` enum error | This installed Blender 5.2.2 reports `BLENDER_EEVEE`, `BLENDER_WORKBENCH`, and `CYCLES`. Query `bpy.context.scene.render.bl_rna.properties['engine'].enum_items` if a future version differs. |
| `Medium High Contrast` enum error | The look here is `AgX - Medium High Contrast`. Query the live enum rather than guessing display names. |
| MCP result said `isError=False` while Blender raised an exception | Read the returned text. It began `Error executing code: Communication error with Blender: ...`. A transport success is not a script success. The helper catches that case. |
| Reference photo looked edible, first 3D render looked like a layered diagram | Four image views helped plan the anatomy, but they did not automatically turn into geometry or texture. The first pass had pale toast, flat sheets, bead-like sauce, oversized lettuce, and visible air between layers. Render review exposed these immediately. |
| Long procedural code was hard to iterate | Put the code in `sandwich_scene.py`, make one visual change per pass, rerun through MCP, and keep the generated image separate. The `.blend` packs the image with `bpy.data.images.load(...); image.pack()`. |

## Quality recipe for food scenes

- Choose the target **before modeling**: a stylized study or a photoreal food render. For photorealism, budget for detailed mesh shaping, textures or scanned assets, subsurface scattering where appropriate, roughness variation, realistic food thickness, and close photographic lighting. Our procedural primitives were sufficient for an MCP test but did not reach the reference photo's realism.
- Build a tight silhouette from the hero camera first. Check the actual rendered overlap of bread, cheese, meat, greens, and sauce; numerical layer heights alone did not prevent apparent gaps. Inspect the side view as a structural check.
- Avoid repeating identical cylinders or spheres where food should be irregular. The first tomatoes read as discs and the aioli as pearls. The aioli improved when overlapping metaballs made one continuous ribbon; further mesh sculpting would help the tomatoes and turkey.
- Use the four-view reference to check consistent ingredient order and overhangs. Keep the reference as a viewport image object with `hide_render=True`, and pack it into the `.blend` for portability.
- Keep early renders cheap. This 1100 px EEVEE scene rendered in seconds in background mode; iterate before spending time on higher samples or Cycles.

## Working render command

Use the saved `.blend` to render a camera without disturbing the interactive Blender session:

```sh
/Applications/Blender.app/Contents/MacOS/Blender -b sandwich-study.blend --python-expr "import bpy; s=bpy.context.scene; s.camera=bpy.data.objects['Camera - hero']; s.render.filepath='sandwich-hero.png'; bpy.ops.render.render(write_still=True)"
```

The scene defines `Camera - hero`, `Camera - front`, `Camera - side`, and `Camera - top`. Inspect the resulting PNG rather than trusting a successful exit code alone.
