#!/usr/bin/env python3
"""Patch pygbag's generated browser shell with local compatibility tweaks."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT_DIR / "ccf_pygame" / "build" / "web" / "index.html"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"Expected snippet for {label!r} was not found in {INDEX_PATH}")
    return text.replace(old, new, 1)


def main() -> int:
    if not INDEX_PATH.exists():
        print(f"Missing build artifact: {INDEX_PATH}", file=sys.stderr)
        return 1

    text = INDEX_PATH.read_text(encoding="utf-8")

    text, count = re.subn(r"fb_ar\s+:\s+1\.77", "fb_ar   :  1.33", text, count=1)
    if count == 0 and "fb_ar   :  1.33" not in text:
        raise RuntimeError(f"Unable to patch framebuffer aspect ratio in {INDEX_PATH}")

    if "def _ccf_loader_status(message):" not in text:
        text = replace_once(
            text,
            "import json\nfrom pathlib import Path\n\n# do not rename\nasync def custom_site():\n",
            """import json\nimport traceback\nfrom pathlib import Path\n\n\ndef _ccf_loader_status(message):\n    print(f"[ccf-loader] {message}")\n    try:\n        platform.window.ccfLoaderSet(message, False)\n        return\n    except Exception:\n        pass\n    try:\n        platform.window.infobox.innerText = message\n        platform.window.infobox.style.display = "block"\n    except Exception:\n        pass\n\n\ndef _ccf_loader_error(message):\n    print(message)\n    try:\n        platform.window.ccfLoaderSet(message, True)\n        return\n    except Exception:\n        pass\n    try:\n        platform.window.infobox.innerText = message\n        platform.window.infobox.style.display = "block"\n    except Exception:\n        pass\n\n\n# do not rename\nasync def custom_site():\n""",
            "loader helpers",
        )
        text = replace_once(
            text,
            '    import embed\n    platform.document.body.style.background = "#7f7f7f"\n',
            '    import embed\n    _ccf_loader_status("loader: bootstrap started")\n    platform.document.body.style.background = "#7f7f7f"\n',
            "loader bootstrap stage",
        )
        text = replace_once(
            text,
            '    appdir = Path(f"/data/data/{bundle}") # /data/data/ccf_pygame\n    appdir.mkdir()\n',
            '    appdir = Path(f"/data/data/{bundle}") # /data/data/ccf_pygame\n    _ccf_loader_status("loader: preparing filesystem")\n    appdir.mkdir()\n',
            "loader filesystem stage",
        )
        text = replace_once(
            text,
            """    # unpack filesystem from compressed archive into work dir\n    if platform.window.location.host.find('.itch.zone')>0:\n        import zipfile\n        async with platform.fopen("ccf_pygame.apk", "rb") as archive:\n            with zipfile.ZipFile(archive) as zip_ref:\n                zip_ref.extractall(appdir.as_posix())\n    else:\n        import tarfile\n        async with platform.fopen("ccf_pygame.tar.gz", "rb") as archive:\n            tar = tarfile.open(fileobj=archive, mode="r:gz")\n            tar.extractall(path=appdir.as_posix(), filter='tar')\n            tar.close()\n""",
            """    # unpack filesystem from compressed archive into work dir\n    if platform.window.location.host.find('.itch.zone')>0:\n        import zipfile\n        _ccf_loader_status("loader: fetching ccf_pygame.apk")\n        async with platform.fopen("ccf_pygame.apk", "rb") as archive:\n            _ccf_loader_status("loader: extracting ccf_pygame.apk")\n            with zipfile.ZipFile(archive) as zip_ref:\n                zip_ref.extractall(appdir.as_posix())\n    else:\n        import tarfile\n        _ccf_loader_status("loader: fetching ccf_pygame.tar.gz")\n        async with platform.fopen("ccf_pygame.tar.gz", "rb") as archive:\n            _ccf_loader_status("loader: extracting ccf_pygame.tar.gz")\n            tar = tarfile.open(fileobj=archive, mode="r:gz")\n            tar.extractall(path=appdir.as_posix(), filter='tar')\n            tar.close()\n""",
            "loader archive stages",
        )
        text = replace_once(
            text,
            """    # preloader will change to work dir and prepend it to sys.path\n    platform.run_main(PyConfig, loaderhome= appdir / "assets", loadermain=None)\n\n\n    # wait preloading complete : that includes images and wasm compilation of bundled modules\n    while embed.counter()<0:\n        await asyncio.sleep(.1)\n""",
            """    # preloader will change to work dir and prepend it to sys.path\n    _ccf_loader_status("loader: starting runtime")\n    platform.run_main(PyConfig, loaderhome= appdir / "assets", loadermain=None)\n\n\n    # wait preloading complete : that includes images and wasm compilation of bundled modules\n    _ccf_loader_status("loader: waiting for preload")\n    while embed.counter()<0:\n        await asyncio.sleep(.1)\n    _ccf_loader_status("loader: preload complete")\n""",
            "loader runtime stages",
        )
        text = replace_once(
            text,
            """        # now make a prompt\n        msg  = "Ready to start ! Please click/touch page"\n        platform.window.infobox.innerText = msg\n        print("\\n"*4, f"    * Waiting for media user engagement. {msg} *" , "\\n"*4)\n\n        while not platform.window.MM.UME:\n            await asyncio.sleep(.1)\n""",
            """        # now make a prompt\n        msg  = "loader: waiting for click/touch to start"\n        _ccf_loader_status(msg)\n        print("\\n"*4, f"    * Waiting for media user engagement. {msg} *" , "\\n"*4)\n\n        while not platform.window.MM.UME:\n            await asyncio.sleep(.1)\n\n        _ccf_loader_status("loader: user interaction received")\n""",
            "loader ume stage",
        )
        text = replace_once(
            text,
            "    await TopLevel_async_handler.start_toplevel(platform.shell, console=window.python.config.debug)\n",
            '    _ccf_loader_status("loader: starting top-level async handler")\n    await TopLevel_async_handler.start_toplevel(platform.shell, console=window.python.config.debug)\n',
            "loader toplevel stage",
        )
        text = replace_once(
            text,
            """    def ui_callback(pkg):\n        platform.window.infobox.innerText = f"installing {pkg}"\n\n    await shell.source(main, callback=ui_callback)\n\n    # if you don't reach that step\n    # your main.py has an infinite sync loop somewhere !\n\n    platform.window.infobox.style.display = "none"\n""",
            """    def ui_callback(pkg):\n        _ccf_loader_status(f"loader: installing {pkg}")\n\n    _ccf_loader_status("loader: loading main.py")\n    await shell.source(main, callback=ui_callback)\n    _ccf_loader_status("loader: main.py loaded")\n\n    # if you don't reach that step\n    # your main.py has an infinite sync loop somewhere !\n\n    try:\n        platform.window.ccfLoaderClear()\n    except Exception:\n        platform.window.infobox.style.display = "none"\n""",
            "loader main handoff stages",
        )
        text = replace_once(
            text,
            "asyncio.run( custom_site() )\n",
            """try:\n    asyncio.run( custom_site() )\nexcept Exception:\n    _ccf_loader_error("loader failed before main.py\\n" + traceback.format_exc()[-2500:])\n    raise\n""",
            "loader top-level error handler",
        )

    if "window.ccfLoaderSet = ccfLoaderSet;" not in text:
        text = replace_once(
            text,
            "function show_infobox() {\n",
            """function ccfLoaderSet(message, isError = false) {\n    const text = String(message);\n    const box = document.getElementById("infobox");\n    if (box) {\n        box.style.display = "block";\n        box.style.background = isError ? "#4a0014" : "#114400";\n        box.style.color = isError ? "#ffe8e8" : "#d7f7ff";\n        box.style.whiteSpace = "pre-wrap";\n        box.innerText = text;\n        show_infobox();\n    }\n\n    let badge = document.getElementById("ccf-loader-status");\n    if (!badge) {\n        badge = document.createElement("pre");\n        badge.id = "ccf-loader-status";\n        badge.style.position = "fixed";\n        badge.style.top = "8px";\n        badge.style.left = "8px";\n        badge.style.zIndex = "1000001";\n        badge.style.maxWidth = "90vw";\n        badge.style.padding = "8px 12px";\n        badge.style.background = "rgba(0, 0, 0, 0.82)";\n        badge.style.color = "#d7f7ff";\n        badge.style.font = "12px/1.35 monospace";\n        badge.style.whiteSpace = "pre-wrap";\n        document.body.appendChild(badge);\n    }\n    badge.style.color = isError ? "#ffe8e8" : "#d7f7ff";\n    badge.textContent = text;\n}\n\nfunction ccfLoaderClear() {\n    const box = document.getElementById("infobox");\n    if (box) {\n        box.style.display = "none";\n    }\n\n    const badge = document.getElementById("ccf-loader-status");\n    if (badge) {\n        badge.remove();\n    }\n}\n\nwindow.ccfLoaderSet = ccfLoaderSet;\nwindow.ccfLoaderClear = ccfLoaderClear;\n\nwindow.addEventListener("error", (event) => {\n    const details = event.error && event.error.stack ? event.error.stack : event.message;\n    ccfLoaderSet(`js error before startup\\n${String(details).slice(-2000)}`, true);\n});\n\nwindow.addEventListener("unhandledrejection", (event) => {\n    const reason = event.reason && event.reason.stack ? event.reason.stack : event.reason;\n    ccfLoaderSet(`js promise rejection\\n${String(reason).slice(-2000)}`, true);\n});\n\nfunction show_infobox() {\n""",
            "loader js helpers",
        )
        text = replace_once(
            text,
            """function show_infobox() {\n    infobox.style.display = "block";\n\n    // Measure box\n    const w = infobox.offsetWidth;\n    const h = infobox.offsetHeight;\n\n    // Center in viewport\n    const left = (window.innerWidth - w) / 2;\n    const top = (window.innerHeight - h) / 2;\n\n    infobox.style.left = left + "px";\n    infobox.style.top = top + "px";\n}\n""",
            """function show_infobox() {\n    const box = document.getElementById("infobox");\n    if (!box) {\n        return;\n    }\n\n    box.style.display = "block";\n\n    // Measure box\n    const w = box.offsetWidth;\n    const h = box.offsetHeight;\n\n    // Center in viewport\n    const left = (window.innerWidth - w) / 2;\n    const top = (window.innerHeight - h) / 2;\n\n    box.style.left = left + "px";\n    box.style.top = top + "px";\n}\n""",
            "loader infobox helper",
        )

    INDEX_PATH.write_text(text, encoding="utf-8")
    print(f"Patched {INDEX_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
