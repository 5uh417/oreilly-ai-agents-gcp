"""
Pattern 3: Loop Agent — Iterative Migration Validator

Implements a feedback loop where migrated Puppet 8 code is repeatedly
validated against the Puppet 8 compatibility ruleset. If issues remain,
the fixer agent corrects them and the loop continues until either all
issues are resolved or max_iterations is hit.

This wraps the loop inside a SequentialAgent so we can prepend an
initial analysis step before entering the refinement cycle.
"""

from google.adk.agents import LlmAgent, LoopAgent, SequentialAgent
from google.adk.tools.tool_context import ToolContext
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────────────────
# Tool: Escalation checker — allows the loop to terminate early
# ─────────────────────────────────────────────────────────────────────
def check_validation_result(validation_report: str, tool_context: ToolContext) -> str:
    """Checks if the validation passed all checks and terminates the loop early if so.

    Args:
        validation_report: The validation report text to check for PASS/FAIL status.
        tool_context: ADK tool context for controlling agent flow.

    Returns:
        A status message indicating whether the loop should continue or stop.
    """
    report_upper = validation_report.upper()

    critical_count = report_upper.count("CRITICAL")
    fail_count = report_upper.count("❌")
    missed_count = report_upper.count("MISSED")

    if critical_count == 0 and fail_count == 0 and missed_count == 0:
        # All clear — tell the LoopAgent to stop
        tool_context.actions.escalate = True
        return (
            "VALIDATION PASSED: All Puppet 8 compatibility checks passed. "
            "No critical issues, no failures, no missed migrations. "
            "The code is ready for Puppet 8."
        )

    return (
        f"VALIDATION INCOMPLETE: Found {critical_count} critical issues, "
        f"{fail_count} failures, {missed_count} missed items. "
        "Continue fixing."
    )


# ─────────────────────────────────────────────────────────────────────
# Initial Parser: Accepts user input and sets session state
# ─────────────────────────────────────────────────────────────────────
initial_parser = LlmAgent(
    name="InitialCodeParser",
    model="gemini-2.0-flash",
    description="Parses the user's input and prepares the code for iterative validation.",
    instruction="""You are a Puppet code preparation agent. Take the user's Puppet code input
and output it as-is. Your only job is to make the code available for the
validation loop. If the code is already migrated (partially or fully),
pass it through. If it's Puppet 7 code, pass it through — the loop will
handle the migration.

Output the complete code exactly as received.""",
    output_key="current_code",
)

# ─────────────────────────────────────────────────────────────────────
# Loop Sub-agent 1: Validator
# ─────────────────────────────────────────────────────────────────────
validator_agent = LlmAgent(
    name="Puppet8Validator",
    model="gemini-2.0-flash",
    description="Validates Puppet code against the complete Puppet 8 compatibility ruleset.",
    instruction="""You are a strict Puppet 8 compatibility validator. Examine the current code:
'{current_code}'

Run these validation checks and report PASS ✅ or FAIL ❌ for each:

**CHECK 1: Legacy Facts**
Scan for ANY of these patterns:
- $::osfamily, $::fqdn, $::ipaddress, $::operatingsystem, $::operatingsystemrelease
- $::hostname, $::kernelversion, $::memorysize, $::memorysize_mb
- $::processorcount, $::uptime_seconds, $::environment, $::clientcert
- $facts['osfamily'], $facts['ipaddress'], $facts['fqdn'] (flat keys)
If ANY found → ❌ FAIL. List every occurrence.

**CHECK 2: Deprecated stdlib Functions**
Scan for: validate_string, validate_bool, validate_hash, validate_array,
validate_integer, validate_numeric, validate_absolute_path, validate_ip_address,
is_numeric, is_string, is_array, is_bool, is_ip_address, is_ipv4_address,
is_ipv6_address, upcase(), downcase(), strip(), capitalize(), chomp(), chop(),
has_key(), unique(), sort(), max(), min(), abs(), ceiling(), round(),
hiera(), hiera_hash(), hiera_array(), hiera_include()
If ANY found → ❌ FAIL. List every occurrence.

**CHECK 3: Type Annotations**
Check ALL class/define parameters have explicit Puppet type annotations.
- $param without a type → ❌ FAIL
- String $param → ✅ PASS
If ANY untyped parameter → ❌ FAIL. List every occurrence.

**CHECK 4: Strict Mode Compliance**
- Implicit string-to-integer coercion ($string_var + number)
- Undefined variable access
If ANY found → ❌ FAIL.

**CHECK 5: Hiera Configuration**
If hiera.yaml present, verify it's version 5 format.
If version 3 (:backends:) → ❌ FAIL.

**CHECK 6: Ruby 3.2 Compliance**
If Ruby files present:
- File.exists? → ❌ FAIL (must be File.exist?)
- Puppet::Util.get_env/set_env → ❌ FAIL (must use ENV[])
If ANY found → ❌ FAIL.

**OVERALL VERDICT**:
ALL PASSED → State "ALL CHECKS PASSED — CODE IS PUPPET 8 READY"
ANY FAILED → List every failure with exact code and required fix

Use the check_validation_result tool with your complete report to determine
if the loop should continue or stop.""",
    tools=[check_validation_result],
    output_key="validation_report",
)

# ─────────────────────────────────────────────────────────────────────
# Loop Sub-agent 2: Fixer
# ─────────────────────────────────────────────────────────────────────
fixer_agent = LlmAgent(
    name="Puppet8Fixer",
    model="gemini-2.0-flash",
    description="Fixes all Puppet 8 compatibility issues found by the validator.",
    instruction="""You are a Puppet code fixer. You have:
- Current code: '{current_code}'
- Validation report: '{validation_report}'

For every ❌ FAIL in the validation report, apply the fix.

**Fix Reference:**
Legacy facts → structured facts:
  $::osfamily → $facts['os']['family']
  $::operatingsystem → $facts['os']['name']
  $::operatingsystemrelease → $facts['os']['release']['full']
  $::fqdn → $facts['networking']['fqdn']
  $::hostname → $facts['networking']['hostname']
  $::ipaddress → $facts['networking']['ip']
  $::memorysize → $facts['memory']['system']['total']
  $::memorysize_mb → $facts['memory']['system']['total_bytes']
  $::processorcount → $facts['processors']['count']
  $::uptime_seconds → $facts['system_uptime']['seconds']
  $::clientcert → $trusted['certname']

Deprecated functions → modern equivalents:
  validate_*() → remove call, add type annotation to parameter
  is_numeric($x) → $x =~ Numeric
  is_ip_address($x) → $x =~ Stdlib::IP::Address
  is_ipv4_address($x) → $x =~ Stdlib::IP::Address::V4
  upcase($x) → $x.upcase
  downcase($x) → $x.downcase
  strip($x) → $x.strip
  capitalize($x) → $x.capitalize
  has_key($h, 'k') → 'k' in $h
  hiera('k') → lookup('k')
  hiera_hash('k') → lookup('k', {merge => 'hash'})
  hiera_array('k') → lookup('k', {merge => 'unique'})

Ruby fixes:
  File.exists? → File.exist?
  Puppet::Util.get_env('X') → ENV['X']
  Puppet::Util.set_env('X', v) → ENV['X'] = v

Output the COMPLETE fixed code. Do not truncate.""",
    output_key="current_code",
)

# ─────────────────────────────────────────────────────────────────────
# The Refinement Loop
# ─────────────────────────────────────────────────────────────────────
validation_loop = LoopAgent(
    name="ValidationRefinementLoop",
    description="Iteratively validates and fixes Puppet code until all Puppet 8 checks pass.",
    sub_agents=[validator_agent, fixer_agent],
    max_iterations=5,
)

# ─────────────────────────────────────────────────────────────────────
# Root Agent: Sequential wrapper (parse → loop)
# ─────────────────────────────────────────────────────────────────────
root_agent = SequentialAgent(
    name="Puppet8IterativeValidator",
    description="Parses input code, then iteratively validates and fixes it until Puppet 8 compatible.",
    sub_agents=[initial_parser, validation_loop],
)
