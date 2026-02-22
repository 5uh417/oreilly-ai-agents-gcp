# Puppet 7 → 8 Migration Quick Reference

## Legacy Fact Mappings

| Puppet 7 (Legacy) | Puppet 8 (Structured) |
|---|---|
| `$::osfamily` | `$facts['os']['family']` |
| `$::operatingsystem` | `$facts['os']['name']` |
| `$::operatingsystemrelease` | `$facts['os']['release']['full']` |
| `$::fqdn` | `$facts['networking']['fqdn']` |
| `$::hostname` | `$facts['networking']['hostname']` |
| `$::ipaddress` | `$facts['networking']['ip']` |
| `$::kernelversion` | `$facts['kernelversion']` |
| `$::memorysize` | `$facts['memory']['system']['total']` |
| `$::memorysize_mb` | `$facts['memory']['system']['total_bytes']` |
| `$::processorcount` | `$facts['processors']['count']` |
| `$::uptime_seconds` | `$facts['system_uptime']['seconds']` |
| `$::environment` | `$server_facts['environment']` |
| `$::clientcert` | `$trusted['certname']` |

## Deprecated Function Replacements

### Type Validation (remove calls, use type annotations)

| Remove | Replace With |
|---|---|
| `validate_string($x)` | Parameter type: `String $x` |
| `validate_bool($x)` | Parameter type: `Boolean $x` |
| `validate_hash($x)` | Parameter type: `Hash $x` |
| `validate_array($x)` | Parameter type: `Array $x` |
| `validate_integer($x)` | Parameter type: `Integer $x` |
| `is_numeric($x)` | `$x =~ Numeric` |
| `is_string($x)` | `$x =~ String` |
| `is_ip_address($x)` | `$x =~ Stdlib::IP::Address` |
| `is_ipv4_address($x)` | `$x =~ Stdlib::IP::Address::V4` |

### String Functions (use method syntax)

| Puppet 7 | Puppet 8 |
|---|---|
| `upcase($x)` | `$x.upcase` |
| `downcase($x)` | `$x.downcase` |
| `strip($x)` | `$x.strip` |
| `capitalize($x)` | `$x.capitalize` |
| `chomp($x)` | `$x.chomp` |

### Collection Functions

| Puppet 7 | Puppet 8 |
|---|---|
| `has_key($h, 'k')` | `'k' in $h` |
| `unique($arr)` | `$arr.unique` |
| `sort($arr)` | `$arr.sort` |

### Hiera Functions

| Puppet 7 | Puppet 8 |
|---|---|
| `hiera('key')` | `lookup('key')` |
| `hiera('key', 'default')` | `lookup('key', undef, undef, 'default')` |
| `hiera_hash('key', {})` | `lookup('key', {merge => 'hash', default_value => {}})` |
| `hiera_array('key', [])` | `lookup('key', {merge => 'unique', default_value => []})` |

## Ruby 3.2 Changes (Custom Types/Providers/Facts)

| Puppet 7 (Ruby 2.7) | Puppet 8 (Ruby 3.2) |
|---|---|
| `File.exists?(path)` | `File.exist?(path)` |
| `Dir.exists?(path)` | `Dir.exist?(path)` |
| `Puppet::Util.get_env('X')` | `ENV['X']` |
| `Puppet::Util.set_env('X', v)` | `ENV['X'] = v` |
| `Puppet::Util.clear_env('X')` | `ENV.delete('X')` |

## Hiera v3 → v5

```yaml
# BEFORE (v3 - broken in Puppet 8)
---
:backends:
  - yaml
:yaml:
  :datadir: data
:hierarchy:
  - "nodes/%{::clientcert}"
  - "os/%{::osfamily}"
  - common

# AFTER (v5 - required for Puppet 8)
---
version: 5
defaults:
  datadir: data
  data_hash: yaml_data
hierarchy:
  - name: "Per-node data"
    path: "nodes/%{trusted.certname}.yaml"
  - name: "Per-OS data"
    path: "os/%{facts.os.family}.yaml"
  - name: "Common data"
    path: "common.yaml"
```

## puppet.conf Defaults Changed

| Setting | Puppet 7 | Puppet 8 |
|---|---|
| `strict` | `warning` | `error` |
| `strict_variables` | `false` | `true` |
| `include_legacy_facts` | `true` (collected) | `false` (not collected) |
| `allow_pson_serialization` | `true` | `false` |
