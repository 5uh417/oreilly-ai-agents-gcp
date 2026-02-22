"""
Pattern 4: Coordinator-Dispatcher — Puppet File Type Router

An LlmAgent coordinator examines the user's input and routes it to the
appropriate specialist agent based on file type:
  - Manifest files (.pp) → ManifestMigrator
  - Ruby files (.rb)     → RubyMigrator
  - Hiera files (.yaml)  → HieraMigrator
  - Template files (.erb) → TemplateAdvisor

The coordinator uses a transfer tool to hand off to the right specialist.
This is the pattern you'd use in a production system where users paste
individual files and need targeted migration for that file type.
"""

from google.adk.agents import LlmAgent
from google.adk.tools.tool_context import ToolContext
from dotenv import load_dotenv

load_dotenv()


# ─────────────────────────────────────────────────────────────────────
# Transfer Tool
# ─────────────────────────────────────────────────────────────────────
def route_to_specialist(file_content: str, file_type: str, tool_context: ToolContext) -> str:
    """Routes the file to the appropriate migration specialist based on file type.

    Args:
        file_content: The content of the file to migrate.
        file_type: The detected file type: 'manifest', 'ruby', 'hiera', or 'template'.
        tool_context: ADK tool context for agent transfer.

    Returns:
        A message indicating which specialist will handle the file.
    """
    file_type_lower = file_type.lower().strip()

    routing_map = {
        "manifest": "manifest_migrator",
        "pp": "manifest_migrator",
        ".pp": "manifest_migrator",
        "ruby": "ruby_migrator",
        "rb": "ruby_migrator",
        ".rb": "ruby_migrator",
        "type": "ruby_migrator",
        "provider": "ruby_migrator",
        "function": "ruby_migrator",
        "fact": "ruby_migrator",
        "facter": "ruby_migrator",
        "hiera": "hiera_migrator",
        "yaml": "hiera_migrator",
        ".yaml": "hiera_migrator",
        "yml": "hiera_migrator",
        "hieradata": "hiera_migrator",
        "template": "template_advisor",
        "erb": "template_advisor",
        ".erb": "template_advisor",
        "epp": "template_advisor",
    }

    target_agent = routing_map.get(file_type_lower)

    if target_agent:
        tool_context.actions.transfer_to_agent = target_agent
        agent_labels = {
            "manifest_migrator": "Puppet Manifest Migration Specialist",
            "ruby_migrator": "Ruby Code Migration Specialist (Ruby 3.2 / Puppet 8)",
            "hiera_migrator": "Hiera Configuration Migration Specialist",
            "template_advisor": "Template Migration Advisor",
        }
        label = agent_labels[target_agent]
        return f"Routing to {label} for {file_type} file migration..."

    return (
        f"Could not determine specialist for file type '{file_type}'. "
        "Please specify: manifest (.pp), ruby (.rb), hiera (.yaml), or template (.erb)."
    )


# ─────────────────────────────────────────────────────────────────────
# Specialist 1: Manifest Migrator
# ─────────────────────────────────────────────────────────────────────
manifest_migrator = LlmAgent(
    name="manifest_migrator",
    model="gemini-2.0-flash",
    description="Migrates Puppet manifest (.pp) files from Puppet 7 to Puppet 8.",
    instruction="""You are a Puppet manifest migration specialist. When you receive a Puppet 7
manifest file, perform a COMPLETE migration to Puppet 8.

Apply ALL of these transformations:

**1. Legacy Facts → Structured Facts**
$::osfamily → $facts['os']['family']
$::operatingsystem → $facts['os']['name']
$::operatingsystemrelease → $facts['os']['release']['full']
$::fqdn → $facts['networking']['fqdn']
$::hostname → $facts['networking']['hostname']
$::ipaddress → $facts['networking']['ip']
$::kernelversion → $facts['kernelversion']
$::memorysize → $facts['memory']['system']['total']
$::memorysize_mb → $facts['memory']['system']['total_bytes'] (note: this is in bytes now)
$::processorcount → $facts['processors']['count']
$::uptime_seconds → $facts['system_uptime']['seconds']
$::environment → $server_facts['environment']
$::clientcert → $trusted['certname']

**2. Deprecated Functions → Modern Replacements**
validate_string($x) → REMOVE (rely on type annotation)
validate_bool($x) → REMOVE (rely on type annotation)
validate_hash($x) → REMOVE (rely on type annotation)
validate_array($x) → REMOVE (rely on type annotation)
is_numeric($x) → $x =~ Numeric
is_string($x) → $x =~ String
is_ip_address($x) → $x =~ Stdlib::IP::Address
is_ipv4_address($x) → $x =~ Stdlib::IP::Address::V4
upcase($x) → $x.upcase
downcase($x) → $x.downcase
strip($x) → $x.strip
capitalize($x) → $x.capitalize
has_key($h, 'k') → 'k' in $h
hiera('key') → lookup('key')
hiera('key', default) → lookup('key', undef, undef, default)
hiera_hash('key', {}) → lookup('key', {merge => 'hash', default_value => {}})
hiera_array('key', []) → lookup('key', {merge => 'unique', default_value => []})

**3. Type Annotations**
Add Puppet type annotations to ALL parameters:
  $param = 'value' → String $param = 'value'
  $param = true → Boolean $param = true
  $param = {} → Hash $param = {}
  $param = [] → Array $param = []
  $param = 8080 → Integer $param = 8080
  $param = undef → Optional[Type] $param = undef

**4. Strict Mode Fixes**
  $string_var + 0 → Integer($string_var)
  $string_var * 2 → Integer($string_var) * 2

Output the COMPLETE migrated file with a summary of all changes made.""",
)

# ─────────────────────────────────────────────────────────────────────
# Specialist 2: Ruby Migrator
# ─────────────────────────────────────────────────────────────────────
ruby_migrator = LlmAgent(
    name="ruby_migrator",
    model="gemini-2.0-flash",
    description="Migrates Puppet Ruby code (types, providers, functions, facts) for Puppet 8 / Ruby 3.2.",
    instruction="""You are a Ruby migration specialist for Puppet 8 (Ruby 3.2).

When you receive Puppet Ruby code (custom types, providers, functions, or facts),
perform a COMPLETE migration:

**1. Ruby 3.2 Method Changes**
File.exists?(path) → File.exist?(path)
Dir.exists?(path) → Dir.exist?(path)

**2. Deprecated Puppet::Util Methods**
Puppet::Util.get_env('VAR') → ENV['VAR']
Puppet::Util.set_env('VAR', val) → ENV['VAR'] = val
Puppet::Util.clear_env('VAR') → ENV.delete('VAR')
Puppet::Util.merge_environment(hash) → ENV.update(hash)

**3. Keyword Argument Handling (Ruby 3.2)**
In Ruby 3.2, you cannot pass a Hash as keyword arguments implicitly.
  func(opts) where opts is a Hash → func(**opts) if keywords expected

**4. Provider Pattern Updates**
Ensure providers use current Puppet API patterns.

**5. Custom Fact Updates**
Ensure Facter.add blocks use current API.
Replace any deprecated Facter methods.

Output the COMPLETE migrated file with a summary of all changes.""",
)

# ─────────────────────────────────────────────────────────────────────
# Specialist 3: Hiera Migrator
# ─────────────────────────────────────────────────────────────────────
hiera_migrator = LlmAgent(
    name="hiera_migrator",
    model="gemini-2.0-flash",
    description="Migrates Hiera configuration from v3 to v5 format for Puppet 8.",
    instruction="""You are a Hiera configuration migration specialist.

When you receive a hiera.yaml or Hiera data file, perform a COMPLETE migration
to Puppet 8 / Hiera 5:

**1. hiera.yaml v3 → v5 Conversion**
Convert:
  :backends: → version: 5 with defaults.data_hash
  :yaml: :datadir: → defaults.datadir
  :hierarchy: → hierarchy: list with name/path entries
  %{::fact} → %{facts.structured.path} or %{trusted.certname}

Example v5 format:
```yaml
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

**2. Legacy Fact References in Hierarchy Paths**
%{::clientcert} → %{trusted.certname}
%{::osfamily} → %{facts.os.family}
%{::environment} → %{environment}
%{::operatingsystem} → %{facts.os.name}

**3. Data File Cleanup**
- Flag string values that should be integers (for strict mode)
- Flag deprecated fact names used as keys

Output the COMPLETE migrated hiera.yaml and any data file corrections.""",
)

# ─────────────────────────────────────────────────────────────────────
# Specialist 4: Template Advisor
# ─────────────────────────────────────────────────────────────────────
template_advisor = LlmAgent(
    name="template_advisor",
    model="gemini-2.0-flash",
    description="Advises on ERB/EPP template changes needed for Puppet 8 migration.",
    instruction="""You are a Puppet template migration advisor.

When you receive ERB (.erb) or EPP (.epp) templates, analyze them for
Puppet 8 migration impacts:

**1. Variable Dependency Analysis**
ERB templates use instance variables (@var) that come from the Puppet manifest.
If the manifest changes variable names during migration, the templates may
reference stale variables. Identify ALL template variables and trace their
likely manifest origin.

For example: @server_fqdn likely comes from $server_fqdn = $::fqdn in the manifest.
After migration, if the manifest now uses $server_fqdn = $facts['networking']['fqdn'],
the template variable @server_fqdn still works — but ONLY if the manifest variable
name didn't change.

**2. Ruby Code in Templates**
Check <% %> blocks for Ruby 3.2 compatibility:
- File.exists? → File.exist?
- Any deprecated Ruby method calls

**3. Recommendations**
- Templates themselves usually don't need changes IF the manifest variables
  keep the same names (which they should in a good migration).
- Flag any template that uses @-prefixed variables that don't appear to
  have a manifest counterpart.
- Recommend converting ERB templates to EPP where practical.

Output a detailed analysis with file-by-file recommendations.""",
)

# ─────────────────────────────────────────────────────────────────────
# Root Agent: Coordinator
# ─────────────────────────────────────────────────────────────────────
root_agent = LlmAgent(
    name="PuppetMigrationRouter",
    model="gemini-2.0-flash",
    description="Routes Puppet files to the appropriate migration specialist based on file type.",
    instruction="""You are the Puppet 7→8 Migration Coordinator. Your job is to examine
the user's input and route it to the correct specialist.

**Detection Rules:**
- If the input contains `class `, `define `, `node `, or looks like Puppet manifest
  syntax (.pp file) → file_type = "manifest"
- If the input contains `Puppet::Type`, `Puppet::Functions`, `Facter.add`,
  `.provide(`, or is clearly Ruby code → file_type = "ruby"
- If the input contains `:backends:`, `version: 5`, `hierarchy:`, or looks like
  YAML Hiera config → file_type = "hiera"
- If the input contains `<%= `, `<% `, or ERB template syntax → file_type = "template"

Use the route_to_specialist tool to transfer to the correct specialist.
Pass the file content and detected file type.

If the user provides MULTIPLE files, process the first one and ask them
to submit others individually, OR explain which specialists they'll need.

Always be helpful and explain what you're doing.""",
    tools=[route_to_specialist],
    sub_agents=[manifest_migrator, ruby_migrator, hiera_migrator, template_advisor],
)
