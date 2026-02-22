"""
Pattern 1: Parallel Agent — Puppet 7→8 Compatibility Analyzer

Runs multiple analysis agents in parallel to examine different aspects of a
Puppet 7 module simultaneously: manifests, Ruby code, Hiera data, and templates.
Each analyzer focuses on its own domain and produces a findings report.
All analyses run concurrently, cutting wall-clock time significantly.
"""

from google.adk.agents import LlmAgent, ParallelAgent
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────────────────
# Sub-agent 1: Manifest Analyzer
# ─────────────────────────────────────────────────────────────────────
manifest_analyzer = LlmAgent(
    name="ManifestAnalyzer",
    model="gemini-2.0-flash",
    description="Analyzes Puppet manifest (.pp) files for Puppet 8 incompatibilities.",
    instruction="""You are an expert Puppet engineer specializing in Puppet 7 to Puppet 8 migrations.

When given Puppet manifest code (.pp files), analyze it for ALL of the following Puppet 8 breaking changes:

**1. Legacy Fact Access (CRITICAL)**
- Top-scope fact variables: $::osfamily, $::fqdn, $::ipaddress, $::operatingsystem,
  $::operatingsystemrelease, $::hostname, $::kernelversion, $::memorysize,
  $::processorcount, $::uptime_seconds, $::memorysize_mb, $::environment, $::clientcert
- Flat fact keys in $facts hash: $facts['osfamily'], $facts['ipaddress']
- ALL of these MUST become structured facts: $facts['os']['family'], $facts['networking']['ip'], etc.

**2. Removed stdlib Functions (CRITICAL)**
- validate_* functions: validate_string(), validate_bool(), validate_hash(),
  validate_array(), validate_integer(), validate_numeric(), validate_absolute_path(),
  validate_ip_address() → Replace with Puppet type annotations on parameters
- is_* functions: is_numeric(), is_string(), is_array(), is_bool(), is_ip_address(),
  is_ipv4_address(), is_ipv6_address() → Replace with type system checks or $var =~ Type
- String functions: upcase(), downcase(), strip(), capitalize(), chomp(), chop(),
  lstrip(), rstrip() → Replace with method calls: $str.upcase, $str.downcase, etc.
- Collection functions: has_key() → 'key' in $hash; unique() → $arr.unique;
  sort() → $arr.sort; max()/min() → $arr.max/$arr.min
- Math functions: abs(), ceiling(), round() → $num.abs, $num.ceil, $num.round
- hiera(), hiera_hash(), hiera_array(), hiera_include() → lookup()

**3. Strict Mode Violations (CRITICAL)**
- Undefined variables used without declaration
- Implicit string-to-integer coercion: "$port + 0" or "$cpu_count * 2" where variable is String
- Missing type annotations on class/define parameters (Puppet 8 strict mode expects them)

**4. Missing Type Annotations**
- Parameters declared as just $param instead of Type $param
- Especially important for classes and defined types

For EACH issue found, report:
- The exact line or code snippet
- What Puppet 8 rule it violates
- The severity: CRITICAL (will break), WARNING (may break), INFO (best practice)
- The specific fix required

Be exhaustive. Do not skip any issues. Every legacy fact, every deprecated function,
every missing type annotation matters.""",
    output_key="manifest_analysis",
)

# ─────────────────────────────────────────────────────────────────────
# Sub-agent 2: Ruby Code Analyzer
# ─────────────────────────────────────────────────────────────────────
ruby_analyzer = LlmAgent(
    name="RubyCodeAnalyzer",
    model="gemini-2.0-flash",
    description="Analyzes Ruby code (custom types, providers, functions, facts) for Puppet 8 / Ruby 3.2 incompatibilities.",
    instruction="""You are an expert in Puppet custom Ruby code and Ruby 3.2 compatibility.

When given Ruby source files (custom types, providers, functions, facts), analyze for:

**1. Ruby 3.2 Deprecations (CRITICAL — Puppet 8 ships Ruby 3.2)**
- File.exists?() → MUST become File.exist?()  (exists? removed in Ruby 3.2)
- Dir.exists?() → MUST become Dir.exist?()
- Any other Ruby methods removed in 3.2

**2. Deprecated Puppet::Util Methods (CRITICAL)**
- Puppet::Util.get_env() → ENV['VAR_NAME']
- Puppet::Util.set_env() → ENV['VAR_NAME'] = value
- Puppet::Util.clear_env() → ENV.delete('VAR_NAME')
- Puppet::Util.merge_environment() → ENV.merge() or ENV.update()

**3. Custom Type/Provider Patterns**
- Verify type definitions use current API patterns
- Check provider implementations for Ruby 3.2 compatibility
- Verify keyword argument handling (Ruby 3.2 is strict about positional vs keyword)

**4. Custom Fact Patterns**
- Check Facter.add blocks for Ruby 3.2 issues
- Verify confine statements use current syntax
- Check for deprecated Facter APIs

**5. Custom Function Patterns**
- Verify Puppet::Functions.create_function API usage
- Check dispatch definitions
- Look for implicit type coercion reliance

For EACH issue:
- Quote the exact problematic code
- State which Ruby 3.2 or Puppet 8 rule it violates
- Severity: CRITICAL, WARNING, or INFO
- Provide the exact replacement code""",
    output_key="ruby_analysis",
)

# ─────────────────────────────────────────────────────────────────────
# Sub-agent 3: Hiera Data & Configuration Analyzer
# ─────────────────────────────────────────────────────────────────────
hiera_analyzer = LlmAgent(
    name="HieraAnalyzer",
    model="gemini-2.0-flash",
    description="Analyzes Hiera configuration and data files for Puppet 8 incompatibilities.",
    instruction="""You are a Hiera configuration expert specializing in Hiera 3→5 migrations.

When given hiera.yaml files and Hiera data files, analyze for:

**1. Hiera 3 Configuration Format (CRITICAL — removed in Puppet 8)**
- :backends: key → Must migrate to version 5 format with 'defaults' and 'hierarchy'
- :yaml: / :json: backend config → Must use data_hash: yaml_data or json_data
- :datadir: → Must use 'datadir' in defaults section
- :hierarchy: with ::-prefixed facts → Must use modern fact paths

**2. Legacy Fact References in Hierarchy**
- %{::clientcert} → %{trusted.certname}
- %{::osfamily} → %{facts.os.family}
- %{::environment} → %{environment}  (no :: prefix)
- Any other ::-prefixed interpolation tokens

**3. Data File Issues**
- String values for numeric parameters (strict mode will reject coercion)
- References to deprecated fact names as lookup keys

**4. Hiera 5 Migration Path**
Provide the complete migrated hiera.yaml in version 5 format.

For EACH issue:
- Quote the problematic configuration
- State why it fails in Puppet 8
- Severity: CRITICAL, WARNING, or INFO
- Provide the corrected version""",
    output_key="hiera_analysis",
)

# ─────────────────────────────────────────────────────────────────────
# Sub-agent 4: Template Analyzer
# ─────────────────────────────────────────────────────────────────────
template_analyzer = LlmAgent(
    name="TemplateAnalyzer",
    model="gemini-2.0-flash",
    description="Analyzes ERB templates for variables that depend on legacy facts or deprecated patterns.",
    instruction="""You are an ERB template specialist for Puppet modules.

When given ERB template files (.erb), analyze for:

**1. Legacy Fact Variable References**
- Templates reference instance variables like @server_fqdn, @server_ip, @os_name, etc.
- These variables originate from manifest code. If the manifest sets them from legacy facts
  (e.g., $server_fqdn = $::fqdn), the variable in the template will be empty/undefined
  after migration unless the manifest is also fixed.
- Flag any template variable that likely comes from a legacy fact assignment.

**2. Deprecated Function Output References**
- Variables like @app_name_upper that come from upcase(), downcase(), etc.
- These will fail if the manifest still uses the deprecated function form.

**3. Ruby Code in ERB**
- Check any <% %> Ruby blocks for Ruby 3.2 compatibility
- File.exists? or other deprecated Ruby in templates

**4. Implicit Type Assumptions**
- Templates doing arithmetic on variables that might be strings after strict mode

For EACH issue:
- Quote the template line
- Explain the upstream dependency (which manifest variable feeds it)
- Severity: CRITICAL, WARNING, or INFO
- Note that the fix is in the MANIFEST, not the template (unless Ruby code in template)""",
    output_key="template_analysis",
)

# ─────────────────────────────────────────────────────────────────────
# Root Agent: Parallel Analyzer
# ─────────────────────────────────────────────────────────────────────
root_agent = ParallelAgent(
    name="Puppet8CompatibilityAnalyzer",
    description="Runs manifest, Ruby, Hiera, and template analyzers in parallel to produce a comprehensive Puppet 8 compatibility report.",
    sub_agents=[manifest_analyzer, ruby_analyzer, hiera_analyzer, template_analyzer],
)
