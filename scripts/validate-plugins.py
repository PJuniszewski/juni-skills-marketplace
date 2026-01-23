#!/usr/bin/env python3
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set

ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE_FILE = ROOT / ".claude-plugin" / "marketplace.json"
TMP_DIR = ROOT / ".tmp_plugin_validation"

# =========================
# TUNABLE POLICY SETTINGS
# =========================

MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024      # 2MB per file hard fail
MAX_REPO_SIZE_BYTES = 20 * 1024 * 1024     # 20MB total repo hard fail (excluding .git)
MAX_FILES_COUNT = 2500                     # avoid huge repos
MAX_READ_BYTES_FOR_BINARY_CHECK = 4096

ALLOWED_CATEGORIES = {"official", "community"}
ALLOWED_SOURCE_TYPES = {"url"}

REQUIRED_FILES = ["README.md", "LICENSE"]
POSSIBLE_PLUGIN_MANIFESTS = ["plugin.json", ".claude-plugin/plugin.json"]
POSSIBLE_CONTENT_DIRS = ["commands", "agents", "hooks", "skills"]

# Disallowed binary-ish extensions often abused / bloating marketplace
DISALLOWED_EXTENSIONS = {
    ".exe", ".dll", ".so", ".dylib",
    ".bin", ".dat",
    ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz",
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".mp4", ".mov", ".avi", ".mkv",
    ".pdf",
    ".wasm",
}

# Allowed large-ish text formats (still size-limited above)
TEXT_EXTENSIONS = {
    ".md", ".txt", ".json", ".yml", ".yaml", ".toml",
    ".py", ".js", ".ts", ".sh", ".zsh", ".bash",
    ".rb", ".go", ".rs", ".java", ".kt", ".swift",
}

# Skip noise dirs during scan
SKIP_DIRS = {
    ".git", ".idea", ".vscode", "__pycache__", ".gradle", "build",
    "dist", "node_modules", ".tmp", ".cache"
}

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(-[0-9A-Za-z\.-]+)?(\+[0-9A-Za-z\.-]+)?$")

GITHUB_REPO_RE = re.compile(r"^https://github\.com/[^/]+/[^/]+(\.git)?$")

# =========================
# SECURITY PATTERNS
# =========================

# Secrets detection patterns (hardcoded credentials)
SECRET_PATTERNS = [
    # AWS
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
    (r"(?i)aws[_-]?secret[_-]?access[_-]?key\s*[=:]\s*['\"][^'\"]+['\"]", "AWS Secret Key assignment"),
    # Generic API keys
    (r"(?i)api[_-]?key\s*[=:]\s*['\"][a-zA-Z0-9_\-]{20,}['\"]", "API key assignment"),
    (r"(?i)api[_-]?secret\s*[=:]\s*['\"][^'\"]+['\"]", "API secret assignment"),
    # Tokens
    (r"(?i)bearer\s+[a-zA-Z0-9_\-\.]+", "Bearer token"),
    (r"(?i)token\s*[=:]\s*['\"][a-zA-Z0-9_\-]{20,}['\"]", "Token assignment"),
    (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token"),
    (r"gho_[a-zA-Z0-9]{36}", "GitHub OAuth Token"),
    (r"github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}", "GitHub Fine-grained PAT"),
    # Private keys
    (r"-----BEGIN (?:RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----", "Private key"),
    # Passwords
    (r"(?i)password\s*[=:]\s*['\"][^'\"]{8,}['\"]", "Password assignment"),
    (r"(?i)passwd\s*[=:]\s*['\"][^'\"]+['\"]", "Password assignment"),
    # Slack/Discord
    (r"xox[baprs]-[0-9a-zA-Z-]+", "Slack token"),
    (r"(?i)discord[_-]?(?:token|webhook)\s*[=:]\s*['\"][^'\"]+['\"]", "Discord token/webhook"),
    # Generic secrets
    (r"(?i)secret\s*[=:]\s*['\"][a-zA-Z0-9_\-]{16,}['\"]", "Secret assignment"),
]

# Network/telemetry patterns (BANNED - no phoning home)
NETWORK_PATTERNS = [
    # Python
    (r"^\s*import\s+requests\b", "requests import"),
    (r"^\s*from\s+requests\s+import", "requests import"),
    (r"^\s*import\s+urllib\.request", "urllib.request import"),
    (r"^\s*from\s+urllib\.request\s+import", "urllib.request import"),
    (r"^\s*import\s+http\.client", "http.client import"),
    (r"^\s*import\s+aiohttp", "aiohttp import"),
    (r"^\s*import\s+httpx", "httpx import"),
    (r"requests\.(get|post|put|delete|patch)\s*\(", "requests HTTP call"),
    (r"urllib\.request\.(urlopen|Request)", "urllib HTTP call"),
    # JavaScript/TypeScript
    (r"\bfetch\s*\(", "fetch() call"),
    (r"\baxios\s*[\.\(]", "axios call"),
    (r"new\s+XMLHttpRequest", "XMLHttpRequest"),
    (r"\.ajax\s*\(", "jQuery ajax call"),
    # URLs that look like telemetry/analytics
    (r"https?://[^'\"\s]*(?:analytics|telemetry|tracking|metrics|beacon)[^'\"\s]*", "Analytics/telemetry URL"),
    # WebSocket (could be used for data exfiltration)
    (r"\bWebSocket\s*\(", "WebSocket connection"),
    (r"^\s*import\s+websocket", "websocket import"),
]

# Files to scan for security issues
SCANNABLE_EXTENSIONS = {".py", ".js", ".ts", ".sh", ".bash", ".zsh", ".rb", ".go", ".rs"}


@dataclass
class PluginResult:
    name: str
    category: str
    url: str
    errors: List[str]
    warnings: List[str]


def run(cmd: List[str], cwd: Optional[Path] = None) -> Tuple[int, str]:
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    out = (p.stdout or "") + (p.stderr or "")
    return p.returncode, out.strip()


def fail(msg: str) -> None:
    print(f"❌ {msg}")
    sys.exit(1)


def load_marketplace() -> dict:
    if not MARKETPLACE_FILE.exists():
        fail(f"Marketplace index not found: {MARKETPLACE_FILE}")
    with MARKETPLACE_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def ensure_tmp() -> None:
    if TMP_DIR.exists():
        shutil.rmtree(TMP_DIR)
    TMP_DIR.mkdir(parents=True, exist_ok=True)


def cleanup_tmp() -> None:
    if TMP_DIR.exists():
        shutil.rmtree(TMP_DIR)


def clone_repo(url: str, dest: Path) -> Tuple[bool, str]:
    code, out = run(["git", "clone", "--depth", "1", url, str(dest)])
    if code != 0:
        return False, f"Could not clone {url}: {out}"
    return True, ""


def exists_any(repo_path: Path, paths: List[str]) -> Optional[str]:
    for p in paths:
        if (repo_path / p).exists():
            return p
    return None


def is_probably_binary(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            chunk = f.read(MAX_READ_BYTES_FOR_BINARY_CHECK)
        if b"\x00" in chunk:
            return True
        # heuristic: if many bytes are non-printable
        # allow newlines/tabs/carriage returns
        printable = set(range(32, 127)) | {9, 10, 13}
        if not chunk:
            return False
        non_printable = sum(1 for b in chunk if b not in printable)
        ratio = non_printable / max(1, len(chunk))
        return ratio > 0.35
    except Exception:
        # if can't read, treat as suspicious
        return True


def walk_repo_files(repo_path: Path) -> List[Path]:
    files: List[Path] = []
    for root, dirs, filenames in os.walk(repo_path):
        # prune dirs
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fn in filenames:
            files.append(Path(root) / fn)
    return files


def get_repo_size_bytes(files: List[Path]) -> int:
    total = 0
    for f in files:
        try:
            total += f.stat().st_size
        except Exception:
            continue
    return total


def validate_marketplace_schema(marketplace: dict) -> List[str]:
    errors = []
    name = marketplace.get("name")
    if not name or not isinstance(name, str):
        errors.append("marketplace.name missing or invalid")

    version = marketplace.get("version")
    if not version or not isinstance(version, str) or not SEMVER_RE.match(version):
        errors.append("marketplace.version missing or not semver (e.g. 1.0.0)")

    owner = marketplace.get("owner", {})
    if not isinstance(owner, dict) or not owner.get("name"):
        errors.append("marketplace.owner.name missing")

    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list) or len(plugins) == 0:
        errors.append("marketplace.plugins must be a non-empty array")

    # ensure plugin names unique
    seen: Set[str] = set()
    if isinstance(plugins, list):
        for p in plugins:
            n = p.get("name")
            if not n:
                continue
            if n in seen:
                errors.append(f"duplicate plugin.name detected: '{n}'")
            seen.add(n)

    return errors


def parse_plugin_entry(plugin: dict) -> Tuple[Optional[str], Optional[str], Optional[str], List[str]]:
    errors = []
    name = plugin.get("name")
    if not name or not isinstance(name, str):
        errors.append("plugin.name missing or invalid")

    category = plugin.get("category")
    if category not in ALLOWED_CATEGORIES:
        errors.append(f"plugin.category must be one of: {sorted(ALLOWED_CATEGORIES)}")

    tags = plugin.get("tags", [])
    if tags is None:
        tags = []
    if not isinstance(tags, list) or any(not isinstance(t, str) for t in tags):
        errors.append("plugin.tags must be a list of strings")

    src = plugin.get("source", {})
    url = None
    if isinstance(src, dict):
        source_type = src.get("source")
        if source_type not in ALLOWED_SOURCE_TYPES:
            errors.append(f"plugin.source.source must be one of: {sorted(ALLOWED_SOURCE_TYPES)}")
        url = src.get("url")

    if not url or not isinstance(url, str) or not url.startswith("http"):
        errors.append("plugin.source.url missing or invalid")

    # URL quality check
    if url and isinstance(url, str):
        if url.endswith(".git"):
            pass
        elif GITHUB_REPO_RE.match(url):
            pass
        else:
            # allow other git hosts too, but warn
            errors.append("plugin.source.url must be a valid GitHub repo URL or end with .git")

    return name, category, url, errors


def extract_command_names(repo_path: Path) -> Set[str]:
    """
    Best-effort command name extraction for future-proofing.
    We assume commands live in commands/*.md and command name equals filename stem.
    """
    cmds: Set[str] = set()
    cmd_dir = repo_path / "commands"
    if not cmd_dir.exists() or not cmd_dir.is_dir():
        return cmds

    for f in cmd_dir.rglob("*"):
        if f.is_file() and f.suffix.lower() in {".md", ".txt"}:
            cmds.add(f.stem.strip())
    return cmds


def scan_file_for_secrets(file_path: Path, content: str) -> List[Tuple[int, str, str]]:
    """
    Scan file content for hardcoded secrets.
    Returns list of (line_number, pattern_name, matched_text).
    """
    findings: List[Tuple[int, str, str]] = []
    lines = content.split("\n")

    for line_num, line in enumerate(lines, 1):
        # Skip comments (basic heuristic)
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("*"):
            continue

        for pattern, name in SECRET_PATTERNS:
            if re.search(pattern, line):
                # Truncate match for display
                match = re.search(pattern, line)
                if match:
                    matched = match.group(0)
                    # Redact middle of secrets for safety
                    if len(matched) > 20:
                        matched = matched[:8] + "..." + matched[-4:]
                    findings.append((line_num, name, matched))

    return findings


def scan_file_for_network(file_path: Path, content: str) -> List[Tuple[int, str, str]]:
    """
    Scan file content for network/telemetry code.
    Returns list of (line_number, pattern_name, matched_text).
    """
    findings: List[Tuple[int, str, str]] = []
    lines = content.split("\n")

    for line_num, line in enumerate(lines, 1):
        # Skip comments
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("*"):
            continue

        for pattern, name in NETWORK_PATTERNS:
            if re.search(pattern, line):
                match = re.search(pattern, line)
                if match:
                    matched = match.group(0)[:50]  # Truncate long matches
                    findings.append((line_num, name, matched))

    return findings


def security_scan_repo(repo_path: Path, files: List[Path]) -> Tuple[List[str], List[str]]:
    """
    Scan repository for security issues: secrets and network/telemetry code.
    Only scans plugin content directories (commands/, hooks/, agents/, skills/).
    Development scripts and other files are not scanned.
    Returns (errors, warnings).
    """
    errors: List[str] = []
    warnings: List[str] = []

    # Only scan files in plugin content directories
    content_dirs = {"commands", "hooks", "agents", "skills"}

    for f in files:
        if f.suffix.lower() not in SCANNABLE_EXTENSIONS:
            continue

        # Check if file is in a content directory
        try:
            rel_parts = f.relative_to(repo_path).parts
            if not rel_parts or rel_parts[0] not in content_dirs:
                continue  # Skip files outside content directories
        except ValueError:
            continue

        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
            rel = f.relative_to(repo_path)

            # Check for secrets (HARD FAIL)
            secret_findings = scan_file_for_secrets(f, content)
            for line_num, name, matched in secret_findings:
                errors.append(f"SECURITY: Hardcoded secret in {rel}:{line_num} - {name}")

            # Check for network/telemetry (HARD FAIL - telemetry banned)
            network_findings = scan_file_for_network(f, content)
            for line_num, name, matched in network_findings:
                errors.append(f"SECURITY: Network/telemetry code in {rel}:{line_num} - {name}")

        except Exception as e:
            warnings.append(f"Could not security scan {f.relative_to(repo_path)}: {e}")

    return errors, warnings


def validate_plugin_repo(repo_path: Path) -> Tuple[List[str], List[str], Set[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    # Required: manifest exists
    manifest = exists_any(repo_path, POSSIBLE_PLUGIN_MANIFESTS)
    if not manifest:
        errors.append(f"Missing plugin manifest (expected one of: {POSSIBLE_PLUGIN_MANIFESTS})")

    # Required: README + LICENSE
    for f in REQUIRED_FILES:
        if not (repo_path / f).exists():
            errors.append(f"Missing required file: {f}")

    # Required: content dirs
    has_content = any((repo_path / d).exists() for d in POSSIBLE_CONTENT_DIRS)
    if not has_content:
        errors.append(f"No content dirs found (expected one of: {POSSIBLE_CONTENT_DIRS})")

    # Validate plugin.json minimal fields (if present)
    if manifest:
        try:
            data = json.loads((repo_path / manifest).read_text(encoding="utf-8"))
            if "name" not in data:
                errors.append(f"{manifest} missing required field: name")
            if "description" not in data:
                warnings.append(f"{manifest} missing recommended field: description")
            if "version" not in data:
                warnings.append(f"{manifest} missing recommended field: version")
        except Exception as e:
            errors.append(f"Invalid JSON in {manifest}: {e}")

    # Deep scan: file sizes, binaries, repo size
    files = walk_repo_files(repo_path)

    if len(files) > MAX_FILES_COUNT:
        errors.append(f"Repo contains too many files: {len(files)} > {MAX_FILES_COUNT}")

    repo_size = get_repo_size_bytes(files)
    if repo_size > MAX_REPO_SIZE_BYTES:
        errors.append(
            f"Repo too large: {repo_size/1024/1024:.2f}MB > {MAX_REPO_SIZE_BYTES/1024/1024:.2f}MB"
        )

    for f in files:
        # ignore symlinks
        try:
            if f.is_symlink():
                warnings.append(f"Symlink detected: {f.relative_to(repo_path)} (review manually)")
                continue

            size = f.stat().st_size
            rel = f.relative_to(repo_path)

            if size > MAX_FILE_SIZE_BYTES:
                errors.append(
                    f"File too large: {rel} ({size/1024/1024:.2f}MB) > {MAX_FILE_SIZE_BYTES/1024/1024:.2f}MB"
                )

            ext = f.suffix.lower()

            # strongly disallow heavy/binary blobs
            if ext in DISALLOWED_EXTENSIONS:
                errors.append(f"Disallowed file type in repo: {rel} ({ext})")

            # binary detection (for unknown or suspicious ext)
            if ext not in TEXT_EXTENSIONS and size > 0:
                if is_probably_binary(f):
                    errors.append(f"Binary/suspicious file detected: {rel}")

        except Exception as e:
            warnings.append(f"Could not inspect file: {f} ({e})")

    commands = extract_command_names(repo_path)
    if len(commands) == 0:
        warnings.append("No commands detected under commands/ (ok if plugin uses hooks/agents only)")

    # Security scan: secrets and network/telemetry
    sec_errors, sec_warnings = security_scan_repo(repo_path, files)
    errors.extend(sec_errors)
    warnings.extend(sec_warnings)

    return errors, warnings, commands


def main() -> int:
    marketplace = load_marketplace()

    schema_errors = validate_marketplace_schema(marketplace)
    if schema_errors:
        print("❌ Marketplace schema invalid:")
        for e in schema_errors:
            print(f"  - {e}")
        return 1

    plugins = marketplace.get("plugins", [])
    ensure_tmp()

    results: List[PluginResult] = []
    all_command_index: Dict[str, List[str]] = {}  # command -> [plugin names] (warning only)

    for idx, plugin in enumerate(plugins):
        name, category, url, entry_errors = parse_plugin_entry(plugin)

        # Guard if entry invalid
        if entry_errors or not name or not category or not url:
            results.append(
                PluginResult(
                    name=name or f"plugin_{idx}",
                    category=category or "unknown",
                    url=url or "missing",
                    errors=entry_errors or ["Invalid marketplace entry"],
                    warnings=[],
                )
            )
            continue

        safe_dir = name.replace("/", "_").replace(":", "_")
        dest = TMP_DIR / safe_dir

        print(f"🔎 Validating: {name} ({category}) -> {url}")

        errors: List[str] = []
        warnings: List[str] = []

        success, clone_error = clone_repo(url, dest)
        if not success:
            errors.append(clone_error)
            print(f"❌ FAIL: {name}")
            results.append(PluginResult(name=name, category=category, url=url, errors=errors, warnings=warnings))
            continue

        try:
            repo_errors, repo_warnings, cmd_names = validate_plugin_repo(dest)
            errors.extend(repo_errors)
            warnings.extend(repo_warnings)

            # collect command names for cross-plugin collision warnings
            for c in cmd_names:
                all_command_index.setdefault(c, []).append(name)

            if errors:
                print(f"❌ FAIL: {name}")
            else:
                print(f"✅ OK: {name}")

        except Exception as e:
            errors.append(f"Unhandled error: {e}")
            print(f"❌ FAIL: {name}")

        results.append(PluginResult(name=name, category=category, url=url, errors=errors, warnings=warnings))

    cleanup_tmp()

    # Cross-plugin command collision warnings (not a hard fail because plugins are namespaced)
    collisions = {cmd: pls for cmd, pls in all_command_index.items() if len(pls) > 1}

    failed = [r for r in results if r.errors]
    passed = [r for r in results if not r.errors]

    print("\n====================")
    print("📦 Validation report")
    print("====================\n")

    for r in results:
        print(f"• {r.name} [{r.category}]")
        print(f"  url: {r.url}")
        if r.errors:
            for e in r.errors:
                print(f"  ❌ {e}")
        if r.warnings:
            for w in r.warnings:
                print(f"  ⚠️  {w}")
        print("")

    if collisions:
        print("⚠️  Command name collisions detected (warning only):")
        for cmd, pls in sorted(collisions.items(), key=lambda x: x[0]):
            print(f"  - '{cmd}' appears in: {', '.join(pls)}")
        print("  Note: This is usually OK because Claude Code namespaces commands by plugin name.\n")

    print(f"✅ Passed: {len(passed)}")
    print(f"❌ Failed: {len(failed)}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
