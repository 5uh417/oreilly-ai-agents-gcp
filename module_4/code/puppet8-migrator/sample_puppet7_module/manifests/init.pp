# @summary Manages web application deployment and configuration
#
# This is a sample Puppet 7 module intentionally written with patterns
# that are deprecated or broken in Puppet 8, for migration demonstration.
#
# @param app_name The name of the web application
# @param app_port The port the application listens on
# @param deploy_dir The deployment directory
# @param app_user The user to run the application as
# @param manage_firewall Whether to manage firewall rules
# @param config_hash Additional configuration options
# @param allowed_ips List of IPs allowed to access the app
#
class webapp (
  $app_name        = 'mywebapp',
  $app_port        = '8080',
  $deploy_dir      = '/opt/webapp',
  $app_user        = 'webapp',
  $manage_firewall = true,
  $config_hash     = {},
  $allowed_ips     = [],
) {

  # ---- PUPPET 7 ANTI-PATTERN: Legacy top-scope facts ----
  case $::osfamily {
    'RedHat': {
      $package_name    = 'httpd'
      $service_name    = 'httpd'
      $config_dir      = '/etc/httpd/conf.d'
      $default_docroot = '/var/www/html'
    }
    'Debian': {
      $package_name    = 'apache2'
      $service_name    = 'apache2'
      $config_dir      = '/etc/apache2/sites-available'
      $default_docroot = '/var/www/html'
    }
    default: {
      fail("Unsupported operating system family: ${::osfamily}")
    }
  }

  # ---- PUPPET 7 ANTI-PATTERN: Legacy fact variables ----
  $server_fqdn     = $::fqdn
  $server_ip       = $::ipaddress
  $os_version      = $::operatingsystemrelease
  $os_name         = $::operatingsystem
  $kernel_version  = $::kernelversion
  $memory_size     = $::memorysize
  $cpu_count       = $::processorcount

  # ---- PUPPET 7 ANTI-PATTERN: Deprecated stdlib validate_* functions ----
  validate_string($app_name)
  validate_string($deploy_dir)
  validate_bool($manage_firewall)
  validate_hash($config_hash)
  validate_array($allowed_ips)

  # ---- PUPPET 7 ANTI-PATTERN: Deprecated is_* functions ----
  if is_numeric($app_port) {
    $real_port = $app_port
  } else {
    fail("app_port must be numeric, got: ${app_port}")
  }

  # ---- PUPPET 7 ANTI-PATTERN: Deprecated string functions ----
  $app_name_upper   = upcase($app_name)
  $app_name_lower   = downcase($app_name)
  $trimmed_deploy   = strip($deploy_dir)
  $app_name_capital = capitalize($app_name)

  # ---- PUPPET 7 ANTI-PATTERN: Deprecated hiera() calls ----
  $extra_packages = hiera('webapp::extra_packages', [])
  $global_config  = hiera_hash('webapp::global_config', {})
  $include_classes = hiera_array('webapp::include_classes', [])

  # ---- PUPPET 7 ANTI-PATTERN: has_key() instead of 'in' operator ----
  if has_key($config_hash, 'max_connections') {
    $max_conn = $config_hash['max_connections']
  } else {
    $max_conn = 256
  }

  # ---- PUPPET 7 ANTI-PATTERN: Implicit string-to-integer coercion ----
  $worker_count = $cpu_count * 2
  $listen_port  = $app_port + 0

  # Ensure the application user exists
  user { $app_user:
    ensure     => present,
    managehome => true,
    shell      => '/bin/bash',
    home       => "/home/${app_user}",
  }

  # Ensure deploy directory
  file { $deploy_dir:
    ensure => directory,
    owner  => $app_user,
    group  => $app_user,
    mode   => '0755',
  }

  # Install packages
  package { $package_name:
    ensure => installed,
  }

  # Install extra packages from hiera
  $extra_packages.each |$pkg| {
    package { $pkg:
      ensure => installed,
    }
  }

  # Include additional classes from hiera
  $include_classes.each |$klass| {
    include $klass
  }

  # Configuration file from template
  file { "${config_dir}/${app_name}.conf":
    ensure  => file,
    owner   => 'root',
    group   => 'root',
    mode    => '0644',
    content => template("webapp/${app_name}.conf.erb"),
    require => Package[$package_name],
    notify  => Service[$service_name],
  }

  # Application configuration
  file { "${deploy_dir}/config.yaml":
    ensure  => file,
    owner   => $app_user,
    group   => $app_user,
    mode    => '0640',
    content => template('webapp/config.yaml.erb'),
    require => File[$deploy_dir],
  }

  # Service management
  service { $service_name:
    ensure    => running,
    enable    => true,
    require   => Package[$package_name],
    subscribe => File["${config_dir}/${app_name}.conf"],
  }

  # Firewall management
  if $manage_firewall {
    class { 'webapp::firewall':
      port        => $real_port,
      allowed_ips => $allowed_ips,
    }
  }

  # Log rotation
  class { 'webapp::logrotate':
    app_name   => $app_name,
    deploy_dir => $deploy_dir,
  }
}
