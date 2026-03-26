#!/usr/bin/env python3
"""
Convert source JSON rule-sets to all output formats:
  - sing-box JSON (.json)
  - sing-box binary (.srs)   — requires `sing-box` CLI
  - mihomo domain YAML (.yaml)
  - mihomo domain binary (.mrs) — requires `mihomo` CLI
  - mihomo IP YAML (.yaml)
  - mihomo IP binary (.mrs)   — requires `mihomo` CLI
"""

import json
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyyaml"])
    import yaml


def to_mihomo_domain_yaml(domains, domain_suffixes):
    """Convert domain rules to mihomo domain rule-provider payload."""
    payload = []
    for d in sorted(set(domains)):
        payload.append(d)
    for s in sorted(set(domain_suffixes)):
        # mihomo uses +. prefix for domain_suffix matching
        payload.append(f"+.{s}")
    return payload


def to_mihomo_ip_yaml(ip_cidrs):
    """Convert IP CIDR rules to mihomo ipcidr rule-provider payload."""
    return sorted(set(ip_cidrs))


def write_yaml_payload(path, payload):
    """Write mihomo rule-provider YAML file."""
    with open(path, "w") as f:
        f.write("payload:\n")
        for item in payload:
            f.write(f"  - '{item}'\n")
    print(f"  📄 Written: {path}")


def compile_singbox_srs(json_path, srs_path):
    """Compile sing-box JSON to binary SRS via sing-box CLI."""
    try:
        result = subprocess.run(
            ["sing-box", "rule-set", "compile", str(json_path), "-o", str(srs_path)],
            check=True, capture_output=True, text=True
        )
        print(f"  📦 Compiled: {srs_path}")
        return True
    except FileNotFoundError:
        print("  ⚠️  sing-box CLI not found, skipping .srs")
        return False
    except subprocess.CalledProcessError as e:
        print(f"  ❌ sing-box compile error: {e.stderr.strip()}")
        return False


def compile_mihomo_mrs(yaml_path, mrs_path, rule_type="domain"):
    """Compile mihomo YAML to binary MRS via mihomo CLI."""
    try:
        result = subprocess.run(
            ["mihomo", "convert-ruleset", rule_type, "yaml", str(yaml_path), str(mrs_path)],
            check=True, capture_output=True, text=True
        )
        print(f"  📦 Compiled: {mrs_path}")
        return True
    except FileNotFoundError:
        print("  ⚠️  mihomo CLI not found, skipping .mrs")
        return False
    except subprocess.CalledProcessError as e:
        print(f"  ❌ mihomo compile error: {e.stderr.strip()}")
        return False


def process_ruleset(name, source_path, singbox_dir, mihomo_dir):
    """Process one source JSON and generate all output formats."""
    print(f"\n{'='*50}")
    print(f"Processing: {name}")
    print(f"{'='*50}")

    with open(source_path) as f:
        ruleset = json.load(f)

    rule = ruleset["rules"][0]
    domains = rule.get("domain", [])
    domain_suffixes = rule.get("domain_suffix", [])
    ip_cidrs = rule.get("ip_cidr", [])

    print(f"  Domains: {len(domains)} | Suffixes: {len(domain_suffixes)} | IPs: {len(ip_cidrs)}")

    # --- sing-box JSON ---
    sb_json = singbox_dir / f"{name}.json"
    with open(sb_json, "w") as f:
        json.dump(ruleset, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"  📄 Written: {sb_json}")

    # --- sing-box SRS ---
    sb_srs = singbox_dir / f"{name}.srs"
    compile_singbox_srs(sb_json, sb_srs)

    # --- mihomo domain YAML + MRS ---
    if domains or domain_suffixes:
        mh_dom_yaml = mihomo_dir / f"{name}-domain.yaml"
        payload = to_mihomo_domain_yaml(domains, domain_suffixes)
        write_yaml_payload(mh_dom_yaml, payload)

        mh_dom_mrs = mihomo_dir / f"{name}-domain.mrs"
        compile_mihomo_mrs(mh_dom_yaml, mh_dom_mrs, "domain")

    # --- mihomo IP YAML + MRS ---
    if ip_cidrs:
        mh_ip_yaml = mihomo_dir / f"{name}-ip.yaml"
        payload = to_mihomo_ip_yaml(ip_cidrs)
        write_yaml_payload(mh_ip_yaml, payload)

        mh_ip_mrs = mihomo_dir / f"{name}-ip.mrs"
        compile_mihomo_mrs(mh_ip_yaml, mh_ip_mrs, "ipcidr")


def main():
    root_dir = Path(__file__).resolve().parent.parent
    source_dir = root_dir / "source"
    singbox_dir = root_dir / "sing-box"
    mihomo_dir = root_dir / "mihomo"

    singbox_dir.mkdir(exist_ok=True)
    mihomo_dir.mkdir(exist_ok=True)

    rule_sets = ["apple-intelligence", "apple-services"]

    for name in rule_sets:
        source_path = source_dir / f"{name}.json"
        if not source_path.exists():
            print(f"⚠️  Source not found: {source_path}, skipping")
            continue
        process_ruleset(name, source_path, singbox_dir, mihomo_dir)

    print(f"\n{'='*50}")
    print("✅ All conversions complete.")
    print(f"  sing-box outputs: {singbox_dir}")
    print(f"  mihomo outputs:   {mihomo_dir}")


if __name__ == "__main__":
    main()
