"""
Pattern 2: Sequential Agent — Puppet 7→8 Code Migrator Pipeline

Executes migration in strict order: analyze → migrate → review → finalize.
Each stage's output feeds the next stage via session state (output_key).
This models a real migration pipeline where you cannot migrate before
analyzing, and cannot review before migrating.
"""

from google.adk.agents import LlmAgent, SequentialAgent
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────────────────
# Stage 1: Deep Analysis
# ─────────────────────────────────────────────────────────────────────
deep_analyzer = LlmAgent(
    name="DeepAnalyzer",
    model="gemini-2.0-flash",
    description="Performs deep analysis of Puppet 7 code to catalog every required change.",
    instruction="""You are a Puppet migration analyst. Given Puppet 7 source code, produce
a structured migration manifest — a JSON-like report listing every single change needed.

For each file provided, produce entries in this format:

FILE: <filename>
CHANGES:
  1. LINE: <line number or code snippet>
     TYPE: <legacy_fact | deprecated_function | missing_type | strict_violation | ruby32 | hiera3>
     SEVERITY: <CRITICAL | WARNING | INFO>
     CURRENT: <exact current code>
     REPLACEMENT: <exact replacement code>
     REASON: <why this must change>

**Complete Reference for Replacements:**

Legacy Facts → Structured Facts:
  $::osfamily → $facts['os']['family']
  $::operatingsystem → $facts['os']['name']
  $::operatingsystemrelease → $facts['os']['release']['full']
  $::fqdn → $facts['networking']['fqdn']
  $::hostname → $facts['networking']['hostname']
  $::ipaddress → $facts['networking']['ip']
  $::kernelversion → $facts['kernelversion']  (this one stays as structured)
  $::memorysize → $facts['memory']['system']['total']
  $::memorysize_mb → $facts['memory']['system']['total_bytes'] (convert to MB in code)
  $::processorcount → $facts['processors']['count']
  $::uptime_seconds → $facts['system_uptime']['seconds']
  $::environment → $server_facts['environment'] or $environment
  $::clientcert → $trusted['certname']

Deprecated Functions → Replacements:
  validate_string($x) → add String type annotation to parameter
  validate_bool($x) → add Boolean type annotation to parameter
  validate_hash($x) → add Hash type annotation to parameter
  validate_array($x) → add Array type annotation to parameter
  is_numeric($x) → $x =~ Numeric  OR  $x =~ Pattern[/^\d+$/]
  is_string($x) → $x =~ String
  is_ip_address($x) → $x =~ Stdlib::IP::Address
  is_ipv4_address($x) → $x =~ Stdlib::IP::Address::V4
  upcase($x) → $x.upcase
  downcase($x) → $x.downcase
  strip($x) → $x.strip
  capitalize($x) → $x.capitalize
  has_key($hash, 'k') → 'k' in $hash
  hiera('key') → lookup('key')
  hiera_hash('key') → lookup('key', {merge => 'hash'})
  hiera_array('key') → lookup('key', {merge => 'unique'})

Be exhaustive. Missing a single change means the module will fail in production.""",
    output_key="migration_manifest",
)

# ─────────────────────────────────────────────────────────────────────
# Stage 2: Code Migration
# ─────────────────────────────────────────────────────────────────────
code_migrator = LlmAgent(
    name="CodeMigrator",
    model="gemini-2.0-flash",
    description="Applies all changes from the migration manifest to produce Puppet 8 compatible code.",
    instruction="""You are a Puppet code migration engine. You have the original Puppet 7 code
from the user's request and a detailed migration manifest: '{migration_manifest}'

Your job: produce the COMPLETE migrated Puppet 8 code for every file.

Rules:
1. Apply EVERY change listed in the migration manifest. Do not skip any.
2. Add proper Puppet type annotations to ALL class and define parameters.
   - String $param, Integer $param, Boolean $param, Hash $param, Array $param
   - Use Optional[Type] for parameters with undef defaults
   - Use Variant[String,Integer] where appropriate
3. Replace ALL legacy facts with structured facts.
4. Replace ALL deprecated functions with their modern equivalents.
5. Replace ALL hiera()/hiera_hash()/hiera_array() with lookup().
6. Replace has_key() with the 'in' operator.
7. Add explicit type conversions where implicit coercion was relied upon.
   - e.g., Integer($app_port) instead of $app_port + 0
8. For hiera.yaml: convert from version 3 to version 5 format.
9. For Ruby files: replace File.exists? with File.exist?,
   replace Puppet::Util.get_env/set_env with ENV[] equivalents.
10. Preserve ALL comments, structure, and logic. Only change what's needed.
11. Output COMPLETE files — do not truncate or summarize.

Format your output as:
--- BEGIN FILE: <filepath> ---
<complete migrated file content>
--- END FILE: <filepath> ---

For each file, repeat the above block.""",
    output_key="migrated_code",
)

# ─────────────────────────────────────────────────────────────────────
# Stage 3: Migration Review
# ─────────────────────────────────────────────────────────────────────
migration_reviewer = LlmAgent(
    name="MigrationReviewer",
    model="gemini-2.0-flash",
    description="Reviews migrated code to verify all changes were applied correctly.",
    instruction="""You are a senior Puppet engineer reviewing a Puppet 7→8 migration.

You have:
- The migration manifest (what should have changed): '{migration_manifest}'
- The migrated code: '{migrated_code}'

Perform a thorough code review:

1. **Completeness Check**: Verify EVERY item in the migration manifest was addressed.
   For each item, state: ✅ APPLIED or ❌ MISSED

2. **Correctness Check**: Verify the replacements are correct:
   - Are structured facts paths accurate? ($facts['os']['family'] not $facts['os']['osfamily'])
   - Are type annotations valid Puppet types?
   - Are function replacements semantically equivalent?
   - Is the hiera.yaml version 5 format valid?
   - Are Ruby replacements correct for Ruby 3.2?

3. **Regression Check**: Did the migration introduce any NEW issues?
   - Logic changes that alter behavior
   - Missing variables
   - Broken template references
   - Syntax errors

4. **Best Practice Suggestions**: Optional improvements beyond bare migration.

Produce a structured review report with pass/fail for each category.""",
    output_key="review_report",
)

# ─────────────────────────────────────────────────────────────────────
# Stage 4: Final Output
# ─────────────────────────────────────────────────────────────────────
finalizer = LlmAgent(
    name="MigrationFinalizer",
    model="gemini-2.0-flash",
    description="Produces the final migration deliverable with summary and any last fixes.",
    instruction="""You are the final stage of a Puppet 7→8 migration pipeline.

You have:
- The migrated code: '{migrated_code}'
- The review report: '{review_report}'

Your job:
1. If the review found ANY missed changes (❌ MISSED), apply those fixes now.
   Output the corrected complete files.
2. If the review found ANY correctness issues, fix them now.
3. Produce a MIGRATION SUMMARY with:
   - Total files migrated
   - Total changes applied
   - Breaking changes fixed (count by category)
   - Any remaining manual action items
   - Recommendations for testing

4. Output the FINAL corrected code in the same format:
--- BEGIN FILE: <filepath> ---
<complete final file content>
--- END FILE: <filepath> ---

Then the summary section:
--- MIGRATION SUMMARY ---
<summary content>
--- END SUMMARY ---""",
    output_key="final_output",
)

# ─────────────────────────────────────────────────────────────────────
# Root Agent: Sequential Pipeline
# ─────────────────────────────────────────────────────────────────────
root_agent = SequentialAgent(
    name="Puppet8MigrationPipeline",
    description="Sequential pipeline: Analyze → Migrate → Review → Finalize. Processes Puppet 7 code through a complete migration workflow.",
    sub_agents=[deep_analyzer, code_migrator, migration_reviewer, finalizer],
)
