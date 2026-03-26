#!/usr/bin/env python3
"""
Scrape Apple's enterprise network requirements page (HT101555)
and extract domains/IPs, categorized into Apple Intelligence vs General Services.
Merges with extra_domains.json for manually-maintained entries.
"""

import json
import sys
import os
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "beautifulsoup4"])
    import requests
    from bs4 import BeautifulSoup

APPLE_URL = "https://support.apple.com/en-us/101555"

# Section titles that belong to Apple Intelligence category
AI_SECTIONS = {
    "Apple Intelligence, Siri, and Search",
}

# All other sections go to general Apple services
GENERAL_SECTIONS = {
    "Apple Push Notifications",
    "Device setup",
    "Device management",
    "Software updates",
    "Apps and additional content",
    "Carrier updates",
    "Content caching",
    "Beta updates",
    "Apple diagnostics",
    "Domain Name System resolution",
    "Certificate validation",
    "Apple Account",
    "iCloud",
    "Associated Domains",
    "Tap to Pay on iPhone",
    "ID Verifier on iPhone",
    "Apple Business Manager and Apple School Manager",
    "Apple Business Essentials device management",
    "Classroom and Schoolwork",
    # Sub-sections that may appear
    "Administrators and managers",
    "Employees and students",
}


def scrape_apple_page():
    """Scrape Apple HT101555 and return domains by section category."""
    print(f"Fetching {APPLE_URL} ...")
    resp = requests.get(APPLE_URL, timeout=30, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    })
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    result = {
        "ai": {"domain": set(), "domain_suffix": set()},
        "general": {"domain": set(), "domain_suffix": set()},
    }

    current_section = None
    # Walk through all h2, h3, and table elements in order
    for element in soup.find_all(["h2", "h3", "table"]):
        if element.name in ("h2", "h3"):
            current_section = element.get_text(strip=True)
            continue

        if element.name == "table" and current_section:
            # Determine which category
            if current_section in AI_SECTIONS:
                cat = "ai"
            elif current_section in GENERAL_SECTIONS:
                cat = "general"
            else:
                # Unknown section, skip
                continue

            # Parse table rows
            for row in element.find_all("tr"):
                cells = row.find_all(["td", "th"])
                if not cells:
                    continue
                host = cells[0].get_text(strip=True)

                # Skip headers and empty
                if not host or host.lower() in ("hosts", "host", "ports"):
                    continue

                # Wildcard -> domain_suffix
                if host.startswith("*."):
                    suffix = host[2:]
                    result[cat]["domain_suffix"].add(suffix)
                else:
                    result[cat]["domain"].add(host)

    return result


def load_extra_domains(root_dir):
    """Load manually-maintained extra domains."""
    extra_path = root_dir / "extra_domains.json"
    if not extra_path.exists():
        print(f"Warning: {extra_path} not found, using empty extras")
        return {}
    with open(extra_path) as f:
        return json.load(f)


def merge_domains(scraped, extras, category_key):
    """Merge scraped domains with extra domains for a given category."""
    domains = set(scraped.get("domain", set()))
    suffixes = set(scraped.get("domain_suffix", set()))
    ip_cidrs = set()

    if category_key in extras:
        extra = extras[category_key]
        domains.update(extra.get("domain", []))
        suffixes.update(extra.get("domain_suffix", []))
        ip_cidrs.update(extra.get("ip_cidr", []))

    return {
        "domain": sorted(domains),
        "domain_suffix": sorted(suffixes),
        "ip_cidr": sorted(ip_cidrs),
    }


def build_singbox_ruleset(merged):
    """Build sing-box rule-set JSON from merged domain data."""
    rule = {}
    if merged["domain"]:
        rule["domain"] = merged["domain"]
    if merged["domain_suffix"]:
        rule["domain_suffix"] = merged["domain_suffix"]
    if merged["ip_cidr"]:
        rule["ip_cidr"] = merged["ip_cidr"]
    return {"version": 2, "rules": [rule]}


def files_differ(path, new_content):
    """Check if file content differs from new content."""
    if not path.exists():
        return True
    with open(path) as f:
        return f.read() != new_content


def main():
    root_dir = Path(__file__).resolve().parent.parent
    source_dir = root_dir / "source"
    source_dir.mkdir(exist_ok=True)

    # 1. Scrape Apple's page
    scraped = scrape_apple_page()
    print(f"  Scraped AI domains: {len(scraped['ai']['domain'])} exact, "
          f"{len(scraped['ai']['domain_suffix'])} suffixes")
    print(f"  Scraped General domains: {len(scraped['general']['domain'])} exact, "
          f"{len(scraped['general']['domain_suffix'])} suffixes")

    # 2. Load extra domains
    extras = load_extra_domains(root_dir)

    # 3. Merge and generate source files
    changed = False
    for name, cat_key in [("apple-intelligence", "apple-intelligence"),
                           ("apple-services", "apple-services")]:
        scraped_cat = scraped["ai"] if "intelligence" in name else scraped["general"]
        merged = merge_domains(scraped_cat, extras, cat_key)
        ruleset = build_singbox_ruleset(merged)

        content = json.dumps(ruleset, indent=2, ensure_ascii=False) + "\n"
        out_path = source_dir / f"{name}.json"

        if files_differ(out_path, content):
            with open(out_path, "w") as f:
                f.write(content)
            print(f"  ✅ Updated: {out_path}")
            changed = True
        else:
            print(f"  ⏭️  No change: {out_path}")

    if changed:
        print("\n🔄 Source files updated — run convert.py to regenerate outputs.")
    else:
        print("\n✅ No changes detected.")

    # Set GitHub Actions output
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"changed={'true' if changed else 'false'}\n")

    return 0 if not changed else 1


if __name__ == "__main__":
    sys.exit(main())
