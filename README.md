# Egern · Meta Muse 分流规则集

给 [Egern](https://egernapp.com) 用的 Meta Muse / Meta AI 规则集，原生 YAML 格式，支持远程订阅与自动更新。

> **先说一个实测结论**：截至 2026-11-11，`muse.meta.com` 在公共 DNS 中**查不到解析记录**，而 `meta.ai`、`ai.meta.com`、`www.meta.com` 均解析到 Meta 的 Facebook IP 段。所以本规则集同时收录了「传闻中的入口域名」和「实际在跑的 AI 域名」——前者现在不生效也不影响任何东西，一旦上线自动命中。

---

## 一、订阅地址

把下面地址里的仓库路径换成你自己的 fork 即可使用（当前指向 `TuTu10750/egern-muse`）。

| 线路 | 地址 | 说明 |
|---|---|---|
| jsDelivr（推荐） | `https://cdn.jsdelivr.net/gh/TuTu10750/egern-muse@main/Rules/MetaMuse.yaml` | 全球 CDN，带缓存，最稳 |
| jsDelivr 国内备用 | `https://testingcf.jsdelivr.net/gh/TuTu10750/egern-muse@main/Rules/MetaMuse.yaml` | 主线路被墙时替换域名 |
| GitHub Raw | `https://raw.githubusercontent.com/TuTu10750/egern-muse/main/Rules/MetaMuse.yaml` | 国内可能直连失败 |
| ghproxy 加速 | `https://ghproxy.net/https://raw.githubusercontent.com/TuTu10750/egern-muse/main/Rules/MetaMuse.yaml` | 前两个都挂时用 |

完整版把文件名换成 `MetaMuse-Full.yaml`。

> ⚠️ 拉规则集这一步本身可能就需要代理。如果 Egern 在规则加载阶段还连不上外网，先用 Raw + ghproxy，或临时切全局。

---

## 二、Egern 里怎么加（三步）

**1. 打开主配置的 `rules` 段**，在 `GEOIP` / `FINAL` 之前插入：

```yaml
rules:
  - rule_set:
      match: "https://cdn.jsdelivr.net/gh/TuTu10750/egern-muse@main/Rules/MetaMuse.yaml"
      policy: Proxy          # ← 改成你配置里真实存在的策略组名
      update_interval: 86400 # 每 24 小时自动更新一次，单位秒
```

**2. `policy` 必须写对**。填 `Proxy`、`节点选择`、`美国节点` 都行，但必须是你的配置里已经定义过的策略组，写错会整条规则集加载失败。

**3. 保存后手动刷新一次规则**，然后打开 Muse 验证。

顺序很关键：Egern 从上往下匹配，**第一条命中的规则生效**。规则集放在 `MATCH,DIRECT` 后面就等于没写。

---

## 三、规则内容

### 精简版 `MetaMuse.yaml`（默认推荐）

| 域名 | 类型 | 作用 | 当前解析状态 |
|---|---|---|---|
| `muse.meta.com` | 后缀 | Muse 网页版入口 | **未解析**（预留，上线即生效） |
| `meta.ai` | 后缀 | Meta AI 主域，覆盖 `www.` / `api.` 等 | 已解析 |
| `ai.meta.com` | 后缀 | Meta AI 控制台 | 已解析 |

只碰这三个域名族，不误伤 Facebook、Instagram、WhatsApp。

### 完整版 `MetaMuse-Full.yaml`

在精简版基础上追加：

| 域名 | 类型 | 为什么加 |
|---|---|---|
| `fbcdn.net` | 后缀 | 头像、图片、静态资源 CDN |
| `fbsbx.com` | 后缀 | Meta 前端资源 CDN |
| `graph.facebook.com` | 精确 | OAuth 登录鉴权端点 |
| `b-graph.facebook.com` | 精确 | 登录备用端点 |

**什么时候换完整版**：精简版下页面白屏、一直转圈、登录跳不过去、图片全裂。这几个症状基本都是 CDN 或 OAuth 被漏掉了。

**为什么不直接写 `facebook.com`**：那会把整个 Facebook 流量都拽进代理，影响面太大。所以登录端点只做精确匹配。

---

## 四、仓库结构

```
egern-muse/
├── Rules/
│   ├── MetaMuse.yaml          # 精简版
│   └── MetaMuse-Full.yaml     # 完整版
├── snippets/
│   └── egern-config.yaml      # 可直接抄的配置片段
├── scripts/
│   └── check.py               # YAML 校验 + 匹配行为测试
└── ci/
    └── validate.yml.disabled  # 每日体检工作流（需手动移到 .github/workflows/，见下）
```

`scripts/check.py` 除了校验 YAML 结构，还会跑一组匹配用例，专门防这类误判：

- `notmeta.ai` 不能被 `meta.ai` 的后缀规则吞掉
- `meta.ai.evil.com` 不能命中（后缀匹配必须落在 label 边界上）
- `muse.meta.com.cn` 不能命中

跑一次看结果：

```bash
pip install pyyaml
python3 scripts/check.py
```

---

## 五、启用自动体检（可选）

`ci/validate.yml.disabled` 是每日自检工作流。它没有直接放在 `.github/workflows/` 下，原因是创建仓库所用的 token 只有 `repo` 权限，缺少 `workflow` scope，GitHub 会拒绝推送该目录下的任何文件。启用方式：

1. **网页操作（最快）**：本地新建 `.github/workflows/validate.yml`，把 `ci/validate.yml.disabled` 的内容整段粘进去并提交。网页端提交不受 token scope 限制。
2. **命令行**：`mkdir -p .github/workflows && mv ci/validate.yml.disabled .github/workflows/validate.yml` 后推送，token 需带 `workflow` scope。

启用后每天北京时间 08:30 自动跑一次 YAML 校验，并在 Actions 运行摘要里输出 `muse.meta.com`、`meta.ai` 等域名的实时解析状态——哪天 Muse 入口真上线了，你能第一时间看到。

启用后每天北京时间 08:30 自动跑一次 YAML 校验，并在 Actions 运行摘要里输出 `muse.meta.com`、`meta.ai` 等域名的实时解析状态——哪天 Muse 入口真上线了，你能第一时间看到。

---

## 六、常见问题

**加了规则还是不走代理？**
按顺序排查：① `policy` 名是否和策略组完全一致（大小写、空格）；② 规则是否在 `MATCH` 之后；③ 规则集 URL 是否拉取成功（Egern 规则页能看到条数，0 条就是没拉到）；④ 域名是否真的在列表里——`muse.meta.com` 现在解析不了，走不了代理是正常的。

**怎么确认命中了？**
Egern 的请求日志里每条连接会显示命中的规则名，看是否显示 `MetaMuse`。

**要抓的域名不在列表里怎么办？**
开 Egern 的请求日志，打开 Muse 操作一遍，把日志里出现的陌生域名补进 `domain_suffix_set`，提 PR 或自己 fork 改。

**规则集会拖慢启动吗？**
`no_resolve: true` 让域名规则不做 DNS 预解析，三条规则的开销可以忽略。

---

## 七、免责

本项目仅用于个人网络调试与学习，规则内容全部来自公开 DNS 信息与域名命名惯例，不包含任何破解、绕过付费或侵入性手段。请遵守所在地法律法规及目标服务的用户协议。
