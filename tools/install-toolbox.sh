#!/usr/bin/env bash
# نصب جعبه‌ابزار گلیچ‌لب برای Claude Code روی لپ‌تاپ (ماژول ۲۷)
# اجرا از ریشهٔ مخزن برد:  bash tools/install-toolbox.sh   [--all برای ابزارهای سنگین‌تر]
# اگر Claude Code اسکیل‌ها را از پوشهٔ دیگری می‌خواند:  CLAUDE_SKILLS_DIR="/e/cluade/claude-code/skills" bash tools/install-toolbox.sh --all
set -e
SK="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
mkdir -p "$SK"
here="$(cd "$(dirname "$0")/.." && pwd)"
cp -r "$here/agent/skills/glitchlab-toolbox" "$SK/"
echo "✓ glitchlab-toolbox"

clone() { # repo  dest  [subdir]
  if [ -d "$SK/$2" ]; then git -C "$SK/$2" pull -q 2>/dev/null || true; echo "↻ $2"; return; fi
  if [ -n "$3" ]; then
    t=$(mktemp -d); git clone -q --depth 1 "https://github.com/$1" "$t"; cp -r "$t/$3" "$SK/$2"; rm -rf "$t"
  else git clone -q --depth 1 "https://github.com/$1" "$SK/$2"; fi
  echo "✓ $2"
}
clone wheresryan22/anatomy anatomy
clone MrBongoC/ai-iso-skill iso-figure skills/iso-figure
# اسکیل‌های Remotion داخل زیرپوشهٔ skills/ اند؛ هر کدام مستقیم در پوشهٔ اسکیل‌ها کپی می‌شود
t=$(mktemp -d); git clone -q --depth 1 https://github.com/remotion-dev/skills "$t" && cp -r "$t"/skills/* "$SK/" && echo "✓ remotion skills"; rm -rf "$t"
[ -d "$SK/remotion-skills" ] && rm -rf "$SK/remotion-skills" && echo "↻ remotion-skills قدیمی پاک شد"
if command -v npx >/dev/null; then
  npx -y skills add coreyhaines31/marketingskills -g -a claude-code -y || echo "! marketingskills: دستی نصب کن"
fi
if [ "$1" = "--all" ]; then
  t=$(mktemp -d); git clone -q --depth 1 https://github.com/charlie947/social-media-skills "$t" && cp -r "$t"/skills/* "$SK/" && echo "✓ social-media-skills"; rm -rf "$t"
  echo "SeeCode، EpicInfographics و Open Carrusel رو طبق README خودشون نصب کن (پلاگین یا clone در پوشهٔ کار)."
  pip install --user rembg instaloader >/dev/null 2>&1 && echo "✓ rembg, instaloader" || echo "! pip: دستی نصب کن"
fi
echo "تمام. Claude Code رو ری‌استارت کن یا /reload-skills بزن."
