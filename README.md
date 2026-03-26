# Apple Proxy Rules

自动抓取 Apple 官方企业网络域名列表，生成 **sing-box** 和 **mihomo (Clash Meta)** 格式的分流规则。

通过 GitHub Actions 每日自动运行，检测 Apple 官方页面变化并更新规则文件。

## 📁 规则文件

分为两个分流集：

| 分流集 | 用途 |
|--------|------|
| `apple-intelligence` | Apple Intelligence、Siri 搜索、Private Cloud Compute、ChatGPT 调用 |
| `apple-services` | iCloud、App Store、Apple TV、HomeKit、Apple Music、Maps、推送等所有其他服务 |

### sing-box 格式

| 文件 | 格式 |
|------|------|
| `sing-box/apple-intelligence.json` | JSON 文本 |
| `sing-box/apple-intelligence.srs` | 二进制 (推荐) |
| `sing-box/apple-services.json` | JSON 文本 |
| `sing-box/apple-services.srs` | 二进制 (推荐) |

### mihomo (Clash Meta) 格式

| 文件 | 格式 | 类型 |
|------|------|------|
| `mihomo/apple-intelligence-domain.yaml` | YAML | 域名规则 |
| `mihomo/apple-intelligence-domain.mrs` | 二进制 | 域名规则 |
| `mihomo/apple-intelligence-ip.yaml` | YAML | IP 规则 |
| `mihomo/apple-intelligence-ip.mrs` | 二进制 | IP 规则 |
| `mihomo/apple-services-domain.yaml` | YAML | 域名规则 |
| `mihomo/apple-services-domain.mrs` | 二进制 | 域名规则 |
| `mihomo/apple-services-ip.yaml` | YAML | IP 规则 |
| `mihomo/apple-services-ip.mrs` | 二进制 | IP 规则 |

## 🔧 使用方式

### sing-box 配置示例

```json
{
    "route": {
        "rule_set": [
            {
                "tag": "apple-intelligence",
                "type": "remote",
                "format": "binary",
                "url": "https://raw.githubusercontent/YOUR_USER/apple-proxy-rules/main/sing-box/apple-intelligence.srs",
                "download_detour": "proxy"
            },
            {
                "tag": "apple-services",
                "type": "remote",
                "format": "binary",
                "url": "https://raw.githubusercontent/YOUR_USER/apple-proxy-rules/main/sing-box/apple-services.srs",
                "download_detour": "proxy"
            }
        ],
        "rules": [
            {
                "rule_set": "apple-intelligence",
                "outbound": "🇺🇸 美国节点"
            },
            {
                "rule_set": "apple-services",
                "outbound": "🇺🇸 美国节点"
            }
        ]
    }
}
```

### mihomo (Clash Meta) 配置示例

```yaml
rule-providers:
  apple-intelligence-domain:
    type: http
    behavior: domain
    url: "https://raw.githubusercontent/YOUR_USER/apple-proxy-rules/main/mihomo/apple-intelligence-domain.yaml"
    interval: 86400
    path: ./ruleset/apple-intelligence-domain.yaml

  apple-services-domain:
    type: http
    behavior: domain
    url: "https://raw.githubusercontent/YOUR_USER/apple-proxy-rules/main/mihomo/apple-services-domain.yaml"
    interval: 86400
    path: ./ruleset/apple-services-domain.yaml

  apple-services-ip:
    type: http
    behavior: ipcidr
    url: "https://raw.githubusercontent/YOUR_USER/apple-proxy-rules/main/mihomo/apple-services-ip.yaml"
    interval: 86400
    path: ./ruleset/apple-services-ip.yaml

rules:
  - RULE-SET,apple-intelligence-domain,🇺🇸 美国节点
  - RULE-SET,apple-services-domain,🇺🇸 美国节点
  - RULE-SET,apple-services-ip,🇺🇸 美国节点,no-resolve
```

## 📡 数据来源

- **Apple 官方**: [Use Apple products on enterprise networks (HT101555)](https://support.apple.com/en-us/101555)
- **手动补充**: `extra_domains.json`（包含 OpenAI/ChatGPT 等 Apple 官方未列出但功能必须的域名）

## 🔄 自动更新

GitHub Actions 每日 UTC 04:00（北京时间 12:00）自动运行：
1. 抓取 Apple 官方页面最新域名列表
2. 与现有规则比对
3. 如有变化，重新生成所有格式文件并自动提交

也可在 GitHub 仓库的 Actions 页面手动触发更新。

## 🛠 本地开发

```bash
# 安装依赖
pip install requests beautifulsoup4 pyyaml

# 抓取最新域名
python scripts/scrape.py

# 生成所有格式（需要 sing-box 和 mihomo CLI 才能生成二进制格式）
python scripts/convert.py
```

## License

MIT
