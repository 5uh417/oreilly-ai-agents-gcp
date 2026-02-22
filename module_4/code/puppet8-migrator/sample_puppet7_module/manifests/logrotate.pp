# @summary Manages log rotation for the web application
#
# @param app_name The application name
# @param deploy_dir The deployment directory
# @param rotate_days Number of days to keep logs
# @param compress Whether to compress rotated logs
#
class webapp::logrotate (
  $app_name    = undef,
  $deploy_dir  = undef,
  $rotate_days = '30',
  $compress    = true,
) {

  # ---- PUPPET 7 ANTI-PATTERN: validate_* functions ----
  validate_string($app_name)
  validate_string($deploy_dir)
  validate_bool($compress)

  # ---- PUPPET 7 ANTI-PATTERN: is_numeric check ----
  if !is_numeric($rotate_days) {
    fail("rotate_days must be numeric, got: ${rotate_days}")
  }

  # ---- PUPPET 7 ANTI-PATTERN: Legacy top-scope fact ----
  $log_dir = $::osfamily ? {
    'RedHat' => '/var/log/httpd',
    'Debian' => '/var/log/apache2',
    default  => '/var/log/webapp',
  }

  file { "/etc/logrotate.d/${app_name}":
    ensure  => file,
    owner   => 'root',
    group   => 'root',
    mode    => '0644',
    content => template('webapp/logrotate.conf.erb'),
  }
}
