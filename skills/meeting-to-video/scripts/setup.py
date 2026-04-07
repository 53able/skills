#!/usr/bin/env python3
# Usage: python setup.py <output-dir>
#
# テンプレートを <output-dir> にコピーし、npm ci を実行する。
# remotion-best-practices が未検出なら npx skills add remotion-dev/skills --yes を実行する。

import shutil
import subprocess
import sys
from pathlib import Path

REMOTION_SKILL_MARK = ".agents/skills/remotion-best-practices/SKILL.md"


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("Usage: python setup.py <output-dir>")

    script_dir = Path(__file__).parent.resolve()
    skill_dir = script_dir.parent
    output_dir = Path(sys.argv[1]).resolve()
    template_dir = skill_dir / "template"

    print(f"→ Copying template to {output_dir}")
    if output_dir.exists():
        shutil.rmtree(output_dir)
    shutil.copytree(template_dir, output_dir)

    # node_modules は常に新規インストール
    # cp -r / shutil.copytree はシンボリックリンクを実体コピーするため
    # .bin/ エントリが壊れる場合がある
    node_modules = output_dir / "node_modules"
    if node_modules.exists():
        shutil.rmtree(node_modules)

    print("→ Installing dependencies (npm ci from lockfile)")
    subprocess.run(["npm", "ci"], cwd=output_dir, check=True)

    remotion_mark = output_dir / REMOTION_SKILL_MARK
    if not remotion_mark.exists():
        print(
            f"→ Installing remotion-dev/skills (remotion-best-practices)"
            f" — {REMOTION_SKILL_MARK} not found"
        )
        subprocess.run(
            ["npx", "skills", "add", "remotion-dev/skills", "--yes"],
            cwd=output_dir,
            check=True,
        )
    else:
        print(
            f"→ remotion-best-practices already present"
            f" ({REMOTION_SKILL_MARK}), skipping npx skills add"
        )

    print()
    print("✓ Setup complete.")
    print(f"  Next: write content.json, then run: cd {output_dir} && npx remotion preview")


if __name__ == "__main__":
    main()
