# @summary Configures application monitoring and health checks
#
# @param enable_monitoring Whether monitoring is enabled
# @param check_interval Health check interval in seconds
# @param alert_email Email for alerts
# @param thresholds Hash of monitoring thresholds
#
class webapp::monitoring (
  $enable_monitoring = true,
  $check_interval    = '60',
  $alert_email       = undef,
  $thresholds        = {},
) {

  # ---- PUPPET 7 ANTI-PATTERN: validate_* functions ----
  validate_bool($enable_monitoring)
  validate_hash($thresholds)

  if $alert_email != undef {
    validate_string($alert_email)
  }

  # ---- PUPPET 7 ANTI-PATTERN: Legacy top-scope facts ----
  $server_fqdn    = $::fqdn
  $server_ip      = $::ipaddress
  $total_memory   = $::memorysize_mb
  $cpu_count      = $::processorcount
  $os_description = "${::operatingsystem} ${::operatingsystemrelease}"

  # ---- PUPPET 7 ANTI-PATTERN: hiera lookups ----
  $monitoring_config = hiera_hash('webapp::monitoring_config', {})
  $alert_recipients  = hiera_array('webapp::alert_recipients', [])

  # ---- PUPPET 7 ANTI-PATTERN: has_key() ----
  if has_key($thresholds, 'cpu_warn') {
    $cpu_warn = $thresholds['cpu_warn']
  } else {
    $cpu_warn = 80
  }

  if has_key($thresholds, 'mem_warn') {
    $mem_warn = $thresholds['mem_warn']
  } else {
    $mem_warn = 85
  }

  if has_key($monitoring_config, 'endpoint') {
    $health_endpoint = $monitoring_config['endpoint']
  } else {
    $health_endpoint = '/health'
  }

  # ---- PUPPET 7 ANTI-PATTERN: is_numeric() ----
  if !is_numeric($check_interval) {
    fail("check_interval must be numeric, got ${check_interval}")
  }

  # ---- PUPPET 7 ANTI-PATTERN: Implicit type coercion ----
  $real_interval = $check_interval + 0

  if $enable_monitoring {
    file { '/etc/webapp/monitoring.conf':
      ensure  => file,
      owner   => 'root',
      group   => 'root',
      mode    => '0644',
      content => template('webapp/monitoring.conf.erb'),
    }

    cron { 'webapp-healthcheck':
      command => "/usr/local/bin/check_webapp.sh --host ${server_fqdn} --port 8080 --endpoint ${health_endpoint} --interval ${real_interval}",
      user    => 'root',
      minute  => "*/$(( ${real_interval} / 60 ))",
    }
  }
}
